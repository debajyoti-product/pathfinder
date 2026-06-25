from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import httpx
import json
import asyncio
import re
from pypdf import PdfReader
from io import BytesIO
from config import (
    SERPER_API_KEY, 
    FIRECRAWL_API_KEY
)
from firecrawl import V1FirecrawlApp
from agents.resume_parser import ResumeParser
from agents.jd_validator import extract_job_team_info
from agents.email_drafter import EmailDrafter

from services.serper_client import SerperClient
from agents.metadata_parser import MetadataParser

serper_client = SerperClient()
resume_parser = ResumeParser()
metadata_parser = MetadataParser()
email_drafter = EmailDrafter()
firecrawl_app = V1FirecrawlApp(api_key=FIRECRAWL_API_KEY) if FIRECRAWL_API_KEY else None

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Seniority Pre-Filter ────────────────────────────────────────────────────
# These title keywords indicate a role that requires significantly more
# experience than a 1-3 year candidate should apply for.
# This is a DETERMINISTIC Python check — not LLM-dependent.

SENIOR_TITLE_KEYWORDS = [
    "senior", "sr.", "sr ", "staff", "principal", "director",
    "head of", "head,", "head ", "vp ", "vp,", "vice president",
    "avp", "a]vp", "group product", "group pm", "chief",
    "fellow", "distinguished", "architect", "lead product",
    "lead pm", "specialist",  # specialist often implies 5+ yrs domain expertise
]

def is_title_too_senior(title: str, candidate_years: float) -> bool:
    """Deterministic pre-filter: reject senior titles for junior candidates.
    
    This runs BEFORE any LLM call or JD scraping, saving API credits.
    Candidates with 5+ years are not filtered.
    """
    if candidate_years >= 5:
        return False  # Senior enough — let LLM do fine-grained matching
    
    title_lower = title.lower()
    for keyword in SENIOR_TITLE_KEYWORDS:
        if keyword in title_lower:
            return True
    return False

def parse_years_from_requirement(req_str: str) -> Optional[float]:
    """Extract the minimum required years from strings like '5+ years', '3-5 years', '8 years'.
    
    Returns the lower bound as a float, or None if unparseable.
    """
    if not req_str or req_str in ("Unknown", "Not specified"):
        return None
    req_lower = req_str.lower()
    # "5-8 years" → 5.0
    match = re.search(r'(\d+)\s*[\-–]\s*(\d+)', req_lower)
    if match:
        return float(match.group(1))
    # "5+ years" → 5.0
    match = re.search(r'(\d+)\s*\+', req_lower)
    if match:
        return float(match.group(1))
    # "5 years" → 5.0
    match = re.search(r'(\d+)', req_lower)
    if match:
        return float(match.group(1))
    return None

def is_experience_mismatch(required_years_str: str, candidate_years: float) -> bool:
    """Deterministic post-filter: reject if JD's required years far exceed candidate's.
    
    This runs AFTER the LLM call as a safety net.
    Rejects if the JD's minimum requirement is > candidate_years + 1.
    """
    min_required = parse_years_from_requirement(required_years_str)
    if min_required is None:
        return False  # Can't parse — let the LLM decision stand
    
    # Reject if JD asks for significantly more than candidate has
    # A 2-year candidate should NOT see jobs asking for 4+ years
    if min_required > candidate_years + 1.5:
        return True
    return False


# ── Existing Utilities ───────────────────────────────────────────────────────

class RoleDetail(BaseModel):
    title: str
    years_exp: float

class ParsedProfile(BaseModel):
    roles: List[RoleDetail]
    skills: List[str]
    industry: str
    location: Optional[str] = None

class ProfileData(BaseModel):
    job_title: str
    skills: List[str]
    actual_years_exp: int
    search_range: List[str]
    industry: str
    location: Optional[str] = None
    remote_only: Optional[bool] = False

def extract_company_name(url: str, source: Optional[str] = None) -> str:
    """Heuristic fallback to extract company name from job board URLs."""
    company_name = "Unknown"
    try:
        if "greenhouse.io/" in url:
            company_name = url.split("greenhouse.io/")[1].split("/")[0].replace("-", " ").title()
        elif "lever.co/" in url:
            company_name = url.split("lever.co/")[1].split("/")[0].replace("-", " ").title()
        elif "ashbyhq.com/" in url:
            company_name = url.split("ashbyhq.com/")[1].split("/")[0].replace("-", " ").title()
        elif "myworkdayjobs.com" in url:
            company_name = url.split(".")[0].replace("https://", "").replace("http://", "").title()
        elif "smartrecruiters.com/" in url:
            company_name = url.split("smartrecruiters.com/")[1].split("/")[0].replace("-", " ").title()
        elif "linkedin.com" in url:
            try:
                slug = url.split("/jobs/view/")[1].split("?")[0]
                if "-at-" in slug:
                    company_name = slug.split("-at-")[1].rsplit("-", 1)[0].replace("-", " ").title()
            except:
                pass
    except:
        pass

    # Clean up suffixes
    company_name = company_name.split(" Careers")[0].split(" Jobs")[0].strip()
    if (not company_name or company_name == "Unknown") and source:
        company_name = source
    return company_name


def fetch_jina(url: str) -> str:
    """Fetch job description using Jina Reader — works for all sites including LinkedIn."""
    jina_url = f"https://r.jina.ai/{url}"
    try:
        with httpx.Client() as client:
            res = client.get(jina_url, timeout=30, headers={"Accept": "text/plain", "X-No-Cache": "true"})
            return res.text
    except:
        return ""

def strip_jd_noise(text: str) -> str:
    """Take a meaningful portion of scraped JD to remove nav/sidebar noise."""
    return text[:4000]

def fetch_jd(url: str) -> str:
    """Fetch job description via Firecrawl (primary) or Jina Reader (fallback)."""
    if "linkedin.com" in url or not firecrawl_app:
        return fetch_jina(url)
    
    try:
        res = firecrawl_app.scrape_url(url, params={"formats": ["markdown"], "onlyMainContent": True})
        return res.get("markdown", fetch_jina(url))
    except Exception as e:
        print(f"Firecrawl failed for {url}: {e}")
        return fetch_jina(url)


@app.post("/api/parse-resume")
async def parse_resume(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF allowed")
    
    try:
        content = await file.read()
        reader = PdfReader(BytesIO(content))
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    except Exception as e:
        import traceback
        err_msg = traceback.format_exc()
        raise HTTPException(status_code=500, detail=f"PDF Parsing Error: {str(e)} \n {err_msg}")

    try:
        result = resume_parser.parse(text)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))

    return result

class DiscoverRequest(BaseModel):
    profile: ProfileData

async def collect_job_urls(job_title: str, location: str) -> list:
    """Step 1: Collect job URLs from multiple sources concurrently.
    
    Returns list of (url, source, serper_title) tuples.
    The serper_title is used for deterministic seniority pre-filtering.
    """
    all_urls = []
    
    def search_li():
        try:
            res = serper_client.search(f'site:linkedin.com/jobs/view "{job_title}" "{location}"')
            return [
                (i.get("link"), "LinkedIn", i.get("title", ""))
                for i in res.get("organic", [])
                if "linkedin.com/jobs" in i.get("link", "")
            ]
        except Exception as e:
            print(f"LinkedIn Search Error: {e}")
            return []
            
    def search_nk():
        try:
            res = serper_client.search(f'site:naukri.com "{job_title}" "{location}"')
            return [
                (i.get("link"), "Naukri", i.get("title", ""))
                for i in res.get("organic", [])
                if "naukri.com" in i.get("link", "") and "/job-listings-" in i.get("link", "")
            ]
        except Exception as e:
            print(f"Naukri Search Error: {e}")
            return []

    def search_boards():
        try:
            res = serper_client.search(f'"{job_title}" "{location}" (site:boards.greenhouse.io OR site:jobs.lever.co OR site:myworkdayjobs.com OR site:zohorecruit.com OR site:smartrecruiters.com OR site:jobs.ashbyhq.com)')
            urls = []
            for item in res.get("organic", []):
                url = item.get("link")
                if url:
                    source = "Greenhouse" if "greenhouse" in url else "Lever" if "lever" in url else "Workday" if "workday" in url else "JobBoard"
                    urls.append((url, source, item.get("title", "")))
            return urls
        except Exception as e:
            print(f"Board Search Error: {e}")
            return []

    li_urls, nk_urls, board_urls = await asyncio.gather(
        asyncio.to_thread(search_li),
        asyncio.to_thread(search_nk),
        asyncio.to_thread(search_boards)
    )
    
    all_urls.extend(li_urls)
    all_urls.extend(nk_urls)
    all_urls.extend(board_urls)
    
    # Deduplicate while preserving order
    seen = set()
    unique_urls = []
    for url, source, title in all_urls:
        if url not in seen:
            seen.add(url)
            unique_urls.append((url, source, title))
            
    return unique_urls

async def fetch_and_clean_jd(url: str) -> str:
    """Step 2: Fetch JD and clean navigation noise."""
    jd_text = await asyncio.to_thread(fetch_jd, url)
    if not jd_text or len(jd_text) < 100:
        return ""
    return strip_jd_noise(jd_text)

def find_poc_profiles(company_name: str, team_name: str) -> list:
    """Step 4: Find POC profiles via Serper and Agent 5 (MetadataParser).
    
    Searches for current employees at the company in the relevant team/department.
    Does NOT include the job title to avoid filtering out hiring managers.
    """
    poc_search_res = serper_client.search_linkedin_pocs(company_name, team_name)
    extracted_pocs = metadata_parser.parse_poc_snippets(poc_search_res, company_name, team_name or "")
    return extracted_pocs.get("profiles", [])[:2]

def build_poc_list(poc_profiles: list) -> list:
    """Assemble POC profiles for the SSE payload (no email enrichment)."""
    return [
        {
            "name": poc.get("name", "Unknown"),
            "currentRole": poc.get("current_role"),
            "linkedinUrl": poc.get("linkedin_url"),
        }
        for poc in poc_profiles
    ]


@app.post("/api/discover-jobs")
async def discover_jobs(req: DiscoverRequest):
    profile = req.profile.dict()
    
    async def job_generator():
        try:
            job_title = profile.get("job_title", "Product Manager")
            location = profile.get("location", "India")
            candidate_years = float(profile.get("actual_years_exp", 0))
            
            print(f"--- Discovery Started ---")
            print(f"Title: {job_title}, Location: {location}, Candidate Years: {candidate_years}")
            print(f"Firecrawl Key Present: {bool(FIRECRAWL_API_KEY)}")
            
            yield f"data: {json.dumps({'status': 'Searching job boards concurrently...'})}\n\n"
            
            # Step 1: Collect URLs from LinkedIn, Naukri, and job boards
            urls = await collect_job_urls(job_title, location)
            print(f"Total Unique URLs found: {len(urls)}")
            
            jobs_found = 0
            pre_filtered = 0
            post_filtered = 0
            
            for url, source, serper_title in urls:
                if jobs_found >= 10:  # Cap at 10 results
                    break
                
                # ── GATE 0: Deterministic Title Pre-Filter (Python, no LLM) ─────
                # Check the Serper result title AND URL slug for senior keywords.
                # This saves Firecrawl/Jina credits and LLM API calls.
                check_text = f"{serper_title} {url}".lower()
                if is_title_too_senior(check_text, candidate_years):
                    pre_filtered += 1
                    print(f"PRE-FILTER REJECT [{source}]: '{serper_title[:60]}' — too senior for {candidate_years}yr candidate")
                    continue
                    
                yield f"data: {json.dumps({'status': f'Evaluating role from {source}...'})}\n\n"
                
                # Step 2: Fetch and clean the JD text
                jd_clean = await fetch_and_clean_jd(url)
                if not jd_clean:
                    continue
                    
                # Step 3: Validate using Agent 3 (Qwen) — experience gate is highest priority
                eval_res = await asyncio.to_thread(extract_job_team_info, jd_clean, profile)
                
                if eval_res.get("isValidRange") is not True:
                    trace = eval_res.get("reasoning_trace", {})
                    print(f"LLM REJECT [{source}]: Exp={trace.get('experience_gate', '?')} | Loc={trace.get('location_gate', '?')} | URL={url[:80]}")
                    continue
                
                # ── GATE POST: Deterministic Experience Post-Filter (Python) ────
                # Safety net: even if the LLM says "valid", reject if the
                # extracted experience requirement clearly exceeds candidate's years.
                req_years_str = eval_res.get("required_years_extracted", "Unknown")
                if is_experience_mismatch(req_years_str, candidate_years):
                    post_filtered += 1
                    print(f"POST-FILTER REJECT [{source}]: JD requires '{req_years_str}', candidate has {candidate_years}yr — URL={url[:80]}")
                    continue
                
                # ── All gates passed — build the job card ────────────────────────
                # Use LLM-extracted company name, fall back to URL heuristic
                company_name = eval_res.get("companyName") or extract_company_name(url, source)
                team_name = eval_res.get("teamName")  # Can be None, that's OK
                
                job_data = {
                    "id": f"{hash(url)}",
                    "company": company_name,
                    "jobTitle": job_title,
                    "url": url,
                    "linkedin": url,
                    "team": team_name,
                    "requiredExperience": req_years_str,
                    "reason": f"Exp: {eval_res.get('reasoning_trace', {}).get('experience_gate', '')} | Loc: {eval_res.get('reasoning_trace', {}).get('location_gate', '')}",
                    "confidence": eval_res.get("confidence"),
                    "pocProfiles": []
                }
                
                yield f"data: {json.dumps({'status': f'Finding contacts at {company_name}...'})}\n\n"
                
                # Step 4: Find POC profiles (current employees, relevant department)
                pocs = await asyncio.to_thread(find_poc_profiles, company_name, team_name)
                
                # Step 5: Assemble POC list
                job_data["pocProfiles"] = build_poc_list(pocs)
                    
                jobs_found += 1
                yield f"data: {json.dumps(job_data)}\n\n"

            print(f"--- Discovery Complete: {jobs_found} matched, {pre_filtered} pre-filtered, {post_filtered} post-filtered ---")

        except Exception as e:
            print(f"Generator Error: {e}")
            import traceback
            traceback.print_exc()
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            
        yield "event: close\ndata: {}\n\n"
            
    return StreamingResponse(job_generator(), media_type="text/event-stream")

class ReferralRequest(BaseModel):
    company: str
    jobTitle: str

@app.post("/api/discover-referrals")
async def discover_referrals(req: ReferralRequest):
    query = f'site:linkedin.com/in/ "{req.company}" ("Recruiter" OR "Lead" OR "Manager")'
    serper_res = serper_client.search(query)
    organic = serper_res.get("organic", [])
    
    referrers = []
    for r in organic[:5]:
        referrers.append({
            "name": r.get("title", "LinkedIn Member").split("-")[0].strip(),
            "linkedin": r.get("link"),
            "company": req.company
        })
        
    return {"referrers": referrers}

class DraftRequest(BaseModel):
    profile: ProfileData
    job_title: str
    company: str
    poc_name: Optional[str] = None


@app.post("/api/draft-email")
async def draft_email(req: DraftRequest):
    # News from last 6 months
    news_query = f'{req.company} news'
    serper_res = serper_client.search(news_query, search_type="news", tbs="qdr:m6")
    news_items = serper_res.get("news", [])

    news_snippet = "\n".join([n.get("title", "") for n in news_items[:3]])
    profile_summary = f"{req.profile.job_title} with {req.profile.actual_years_exp} years exp. Skills: {', '.join(req.profile.skills)}"

    result = email_drafter.draft(
        profile_summary=profile_summary,
        job_title=req.job_title,
        company=req.company,
        poc_name=req.poc_name or "Hiring Team",
        poc_role="Hiring Team",
        job_url="Unknown URL",
        news_snippet=news_snippet,
    )

    return {"email": result.get("body", ""), "news": news_items[:3]}

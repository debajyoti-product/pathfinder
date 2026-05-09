from fastapi import FastAPI, File, UploadFile, HTTPException, Body, BackgroundTasks
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import httpx
import json
import asyncio
from pypdf import PdfReader
from io import BytesIO
from config import (
    SERPER_API_KEY, 
    HUNTER_API_KEY, 
    GROQ_API_KEY, 
    FIRECRAWL_API_KEY
)
from firecrawl import V1FirecrawlApp
from evals import get_country
from agents.resume_parser import ResumeParser
from agents.jd_validator import extract_job_team_info
from agents.email_drafter import EmailDrafter

from services.serper_client import SerperClient
from agents.metadata_parser import MetadataParser
from services.hunter_client import HunterClient

serper_client = SerperClient()
resume_parser = ResumeParser()
metadata_parser = MetadataParser()
email_drafter = EmailDrafter()
hunter_client = HunterClient()
firecrawl_app = V1FirecrawlApp(api_key=FIRECRAWL_API_KEY) if FIRECRAWL_API_KEY else None

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    """Heuristic to extract company name from job board URLs."""
    company_name = "Unknown"
    try:
        if "greenhouse.io/" in url:
            company_name = url.split("greenhouse.io/")[1].split("/")[0].replace("-", " ").title()
        elif "lever.co/" in url:
            company_name = url.split("lever.co/")[1].split("/")[0].replace("-", " ").title()
        elif "ashbyhq.com/" in url:
            company_name = url.split("ashbyhq.com/")[1].split("/")[0].replace("-", " ").title()
        elif "myworkdayjobs.com" in url:
            # e.g. autodesk.wd1.myworkdayjobs.com -> Autodesk
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
    """Take only the first meaningful portion of a Jina dump to remove nav/sidebar noise."""
    # Jina dumps often have a clean header block, then navigation links. 
    # Grab the first 2500 chars which almost always contains title + requirements.
    return text[:2500]

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
    """Step 1: Collect job URLs from multiple sources concurrently."""
    all_urls = []
    
    def search_li():
        try:
            res = serper_client.search(f'site:linkedin.com/jobs/view "{job_title}" "{location}"')
            return [(i.get("link"), "LinkedIn") for i in res.get("organic", []) if "linkedin.com/jobs" in i.get("link", "")]
        except Exception as e:
            print(f"LinkedIn Search Error: {e}")
            return []
            
    def search_nk():
        try:
            res = serper_client.search(f'site:naukri.com "{job_title}" "{location}"')
            return [(i.get("link"), "Naukri") for i in res.get("organic", []) if "naukri.com" in i.get("link", "") and "/job-listings-" in i.get("link", "")]
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
                    urls.append((url, source))
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
    for url, source in all_urls:
        if url not in seen:
            seen.add(url)
            unique_urls.append((url, source))
            
    return unique_urls

async def fetch_and_clean_jd(url: str) -> str:
    """Step 2: Fetch JD and clean navigation noise."""
    jd_text = await asyncio.to_thread(fetch_jd, url)
    if not jd_text or len(jd_text) < 100:
        return ""
    return strip_jd_noise(jd_text)

def find_poc_profiles(company_name: str, team_name: str, job_title: str) -> list:
    """Step 4: Find POC profiles via Serper and Agent 5 (MetadataParser)."""
    poc_search_res = serper_client.search_linkedin_pocs(company_name, team_name, job_title)
    extracted_pocs = metadata_parser.parse_poc_snippets(poc_search_res, company_name, job_title)
    return extracted_pocs.get("profiles", [])[:2]

def enrich_with_emails(poc_profiles: list, company_name: str) -> list:
    """Step 5: Enrich POC profiles with email addresses from Hunter.io."""
    cached_domain = serper_client.find_company_domain(company_name)
    enriched = []
    
    for poc in poc_profiles:
        name = poc.get("name", "")
        first_name, last_name = "", ""
        if " " in name:
            parts = name.split(" ")
            first_name = parts[0]
            last_name = " ".join(parts[1:])
        
        email = hunter_client.find_email(first_name, last_name, cached_domain) if cached_domain else None
            
        enriched.append({
            "name": name,
            "currentRole": poc.get("current_role"),
            "linkedinUrl": poc.get("linkedin_url"),
            "email": email
        })
    return enriched


# Apify removed in favor of Firecrawl

@app.post("/api/discover-jobs")
async def discover_jobs(req: DiscoverRequest):
    profile = req.profile.dict()
    
    async def job_generator():
        try:
            job_title = profile.get("job_title", "Product Manager")
            location = profile.get("location", "India")
            
            print(f"--- Discovery Started ---")
            print(f"Title: {job_title}, Location: {location}")
            print(f"Firecrawl Key Present: {bool(FIRECRAWL_API_KEY)}")
            
            yield f"data: {json.dumps({'status': 'Searching job boards concurrently...'})}\n\n"
            
            # Step 1: Collect
            urls = await collect_job_urls(job_title, location)
            print(f"Total Unique URLs found: {len(urls)}")
            
            jobs_found = 0
            
            for url, source in urls:
                if jobs_found >= 10: # Cap at 10 results
                    break
                    
                yield f"data: {json.dumps({'status': f'Fetching JD from {source}...'})}\n\n"
                
                # Step 2: Fetch and Clean
                jd_clean = await fetch_and_clean_jd(url)
                if not jd_clean:
                    continue
                    
                # Validate using Agent 3 (Qwen)
                eval_res = await asyncio.to_thread(extract_job_team_info, jd_clean, profile)
                
                if eval_res.get("isValidRange") is True:
                    # Step 3: Extract Company Name
                    company_name = extract_company_name(url, source)
                    team_name = eval_res.get("teamName")
                    
                    job_data = {
                        "id": f"{hash(url)}",
                        "company": company_name,
                        "jobTitle": job_title,
                        "url": url,
                        "linkedin": url,
                        "team": team_name,
                        "requiredExperience": eval_res.get("required_years_extracted", "Unknown"),
                        "reason": f"Loc: {eval_res.get('reasoning_trace', {}).get('location_gate', '')} | Exp: {eval_res.get('reasoning_trace', {}).get('experience_gate', '')} | Remote: {eval_res.get('reasoning_trace', {}).get('remote_gate', '')}",
                        "pocProfiles": []
                    }
                    
                    yield f"data: {json.dumps({'status': f'Finding contacts at {company_name}...'})}\n\n"
                    
                    # Step 4: Find POCs
                    pocs = await asyncio.to_thread(find_poc_profiles, company_name, team_name, job_title)
                    
                    # Step 5: Enrich with Emails
                    job_data["pocProfiles"] = await asyncio.to_thread(enrich_with_emails, pocs, company_name)
                        
                    jobs_found += 1
                    yield f"data: {json.dumps(job_data)}\n\n"

        except Exception as e:
            print(f"Generator Error: {e}")
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

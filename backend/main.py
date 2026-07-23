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

@app.on_event("startup")
async def startup_event():
    print("=== Pathfinder AI Suite Booting ===")
    from config import GROQ_API_KEY, SERPER_API_KEY, FIRECRAWL_API_KEY
    print(f"Llama 3.1 8B (Groq): {'ENABLED' if GROQ_API_KEY else 'MISSING (Using GROQ_API_KEY)'}")
    print(f"Qwen 32B (Groq): {'ENABLED' if GROQ_API_KEY else 'MISSING (Using GROQ_API_KEY)'}")
    print(f"Serper.dev: {'ENABLED' if SERPER_API_KEY else 'MISSING'}")
    print(f"Firecrawl: {'ENABLED' if FIRECRAWL_API_KEY else 'MISSING'}")
    if not GROQ_API_KEY:
        print("CRITICAL: GROQ_API_KEY is missing. Pipeline LLM validation will fail.")
    print("===================================")

# ── Tuning Constants ────────────────────────────────────────────────────────
RECENCY_FILTER = "qdr:m"  # "qdr:w" for last week, "qdr:m" for last month

def smart_round_years(value: float) -> float:
    """Round experience years: if decimal >= 0.3, round up; otherwise round down.
    e.g. 1.67 -> 2, 4.56 -> 5, 1.2 -> 1, 6.2 -> 6
    """
    import math
    decimal_part = value - int(value)
    if decimal_part >= 0.3:
        return float(math.ceil(value))
    return float(math.floor(value))

EXPIRED_PHRASES = [
    "position has been filled",
    "no longer accepting applications",
    "job posting expired",
    "no longer available",
    "this job is closed",
    "this role has been closed",
    "page you are looking for doesn't exist",
    "page you are looking for does not exist"
]

# ── Seniority Pre-Filter ────────────────────────────────────────────────────
# These title keywords indicate a role that requires significantly more
# experience than a 1-3 year candidate should apply for.
# This is a DETERMINISTIC Python check — not LLM-dependent.

SENIOR_TITLE_KEYWORDS = [
    "senior", "sr.", "sr ", "staff", "principal", "director",
    "head of", "head,", "head ", "vp ", "vp,", "vice president",
    "avp", "a]vp", "group product", "group pm", "chief",
    "fellow", "distinguished", "architect", "lead product",
    "lead pm",
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
    """Deterministic post-filter: reject if JD's required years exceed candidate's.
    
    Rules:
    - X+ format: X must be <= candidate_years (for <5yr candidates) or <= candidate_years - 1 (for 5+yr)
    - X-Y range: X (lower bound) must be <= candidate_years
    """
    if not required_years_str or required_years_str in ("Unknown", "Not specified"):
        return False
    req_lower = required_years_str.lower()
    
    # "5-8 years" range format → check lower bound X <= candidate_years
    match = re.search(r'(\d+)\s*[\-–]\s*(\d+)', req_lower)
    if match:
        lower_bound = float(match.group(1))
        return lower_bound > candidate_years
    
    # "5+ years" format → stricter for senior candidates
    match = re.search(r'(\d+)\s*\+', req_lower)
    if match:
        min_required = float(match.group(1))
        if candidate_years >= 5:
            return min_required > candidate_years - 1
        return min_required > candidate_years
    
    # Plain "5 years" → treat as X+
    match = re.search(r'(\d+)', req_lower)
    if match:
        min_required = float(match.group(1))
        if candidate_years >= 5:
            return min_required > candidate_years - 1
        return min_required > candidate_years
    
    return False  # Can't parse — let the LLM decision stand


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
    actual_years_exp: float
    search_range: List[str]
    industry: str
    location: Optional[str] = None
    remote_only: Optional[bool] = False

def is_location_mismatch_postllm(detected_location: str, user_location: str) -> bool:
    """
    Deterministic post-filter for location (runs AFTER LLM validation).
    Matches extracted location against user location via substring and alias tables.
    Returns True if it's a definite mismatch.
    (Note: See is_location_mismatch_pretext for the pre-LLM raw text version).
    """
    if not detected_location:
        return False
        
    det_low = detected_location.lower()
    usr_low = user_location.lower()
    
    if det_low in ["unknown", "remote", "not specified"]:
        return False
        
    if usr_low in det_low or det_low in usr_low:
        return False
        
    # Alias mappings (User Location -> Valid Detected Terms)
    aliases = {
        "india": ["bangalore", "bengaluru", "pune", "mumbai", "delhi", "noida", "gurgaon", "gurugram", "chennai", "hyderabad", "kolkata", "ahmedabad", "remote - india", "remote (india)"],
        "bangalore": ["india", "bengaluru"],
        "bengaluru": ["india", "bangalore"],
        "united states": ["us", "usa", "remote - us", "remote (us)"],
        "us": ["united states", "usa"],
        "usa": ["united states", "us"]
    }
    
    for key, valid_terms in aliases.items():
        if key in usr_low:
            if any(term in det_low for term in valid_terms):
                return False
                
    # If no substring match and no alias match, it's a mismatch
    return True

def is_location_mismatch_pretext(jd_lower: str, user_location: str) -> bool:
    """
    Very loose deterministic pre-filter for JD text (runs BEFORE LLM validation).
    If the JD text doesn't contain the user's location, any aliases, or the word 'remote',
    we can confidently reject it before calling the LLM.
    (Note: See is_location_mismatch_postllm for the post-LLM extraction version).
    """
    if not jd_lower or not user_location:
        return False
        
    usr_low = user_location.lower()
    
    if "remote" in jd_lower or "anywhere" in jd_lower:
        return False
        
    if usr_low in jd_lower:
        return False
        
    aliases = {
        "india": ["bangalore", "bengaluru", "pune", "mumbai", "delhi", "noida", "gurgaon", "gurugram", "chennai", "hyderabad", "kolkata", "ahmedabad", "remote - india", "remote (india)"],
        "bangalore": ["india", "bengaluru"],
        "bengaluru": ["india", "bangalore"],
        "united states": ["us", "usa", "remote - us", "remote (us)"],
        "us": ["united states", "usa"],
        "usa": ["united states", "us"]
    }
    
    for key, valid_terms in aliases.items():
        if key in usr_low:
            if any(term in jd_lower for term in valid_terms):
                return False
                
    return True

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
    import re
    # Strip common boilerplate patterns that pad the top of JDs
    patterns_to_remove = [
        r"(?i)accept all cookies",
        r"(?i)cookie policy",
        r"(?i)privacy policy",
        r"(?i)terms of service",
        r"(?i)skip to main content",
        r"(?i)skip to content",
        r"(?i)apply now",
        r"(?i)save job",
        r"(?i)search jobs",
        r"(?i)sign in",
    ]
    
    clean_text = text
    for pattern in patterns_to_remove:
        clean_text = re.sub(pattern, "", clean_text)
        
    # Strip multiple blank lines resulting from deletion
    clean_text = re.sub(r'\n\s*\n', '\n\n', clean_text).strip()
    
    return clean_text[:4000]

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
            res = serper_client.search(f'site:linkedin.com/jobs/view "{job_title}" "{location}"', tbs=RECENCY_FILTER)
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
            res = serper_client.search(f'site:naukri.com "{job_title}" "{location}"', tbs=RECENCY_FILTER)
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
            res = serper_client.search(f'"{job_title}" "{location}" (site:boards.greenhouse.io OR site:jobs.lever.co OR site:myworkdayjobs.com OR site:zohorecruit.com OR site:smartrecruiters.com OR site:jobs.ashbyhq.com)', tbs=RECENCY_FILTER)
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


async def evaluate_single_job(url, source, serper_title, queue, sem, profile_dict, candidate_years, stats):
    async with sem:
        try:
            job_title = profile_dict.get("job_title", "Product Manager")
            location = profile_dict.get("location", "India")
            
            # ── GATE 0: Deterministic Title Pre-Filter (Python, no LLM) ─────
            check_text = f"{serper_title} {url}".lower()
            if is_title_too_senior(check_text, candidate_years):
                stats["pre_filtered"] += 1
                print(f"PRE-FILTER REJECT [{source}]: '{serper_title[:60]}' — too senior for {candidate_years}yr candidate")
                await queue.put(f"data: {json.dumps({'type': 'remove', 'jobId': hash(url)})}\n\n")
                return
                
            await queue.put(f"data: {json.dumps({'type': 'status', 'jobId': hash(url), 'company': serper_title[:30], 'status': f'Evaluating role from {source}...'})}\n\n")
            
            # Step 2: Fetch and clean the JD text
            jd_clean = await fetch_and_clean_jd(url)
            if not jd_clean:
                await queue.put(f"data: {json.dumps({'type': 'remove', 'jobId': hash(url)})}\n\n")
                return
                
            # ── GATE 1: Deterministic Expired Posting Check (Python, no LLM) ──
            jd_lower = jd_clean.lower()
            is_expired = any(phrase in jd_lower for phrase in EXPIRED_PHRASES)
            if is_expired:
                stats["pre_filtered"] += 1
                print(f"PRE-FILTER REJECT [{source}]: Job appears to be expired — URL={url[:80]}")
                await queue.put(f"data: {json.dumps({'type': 'remove', 'jobId': hash(url)})}\n\n")
                return
                
            # ── GATE 2: Deterministic Location Pre-Filter (Python, no LLM) ────
            if is_location_mismatch_pretext(jd_lower, location):
                stats["pre_filtered"] += 1
                print(f"PRE-FILTER REJECT (Location) [{source}]: Location mismatch (JD does not contain '{location}') — URL={url[:80]}")
                await queue.put(f"data: {json.dumps({'type': 'remove', 'jobId': hash(url)})}\n\n")
                return
                
            await queue.put(f"data: {json.dumps({'type': 'status', 'jobId': hash(url), 'company': serper_title[:30], 'status': 'Analyzing fit with Qwen...'})}\n\n")
            # Step 3: Validate using Agent 3 (Qwen)
            eval_res = await asyncio.to_thread(extract_job_team_info, jd_clean, profile_dict)
            
            if eval_res.get("isValidRange") is not True:
                trace = eval_res.get("reasoning_trace", {})
                if "error" in eval_res:
                    print(f"LLM PARSE/API ERROR [{source}]: {eval_res['error']} | URL={url[:80]}")
                else:
                    print(f"LLM REJECT [{source}]: Exp={trace.get('experience_gate', '?')} | Loc={trace.get('location_gate', '?')} | URL={url[:80]}")
                await queue.put(f"data: {json.dumps({'type': 'remove', 'jobId': hash(url)})}\n\n")
                return
                
            # ── GATE POST: Deterministic Experience Post-Filter (Python) ────
            req_years_str = eval_res.get("required_years_extracted", "Unknown")
            if is_experience_mismatch(req_years_str, candidate_years):
                stats["post_filtered"] += 1
                print(f"POST-FILTER REJECT [{source}]: JD requires '{req_years_str}', candidate has {candidate_years}yr — URL={url[:80]}")
                await queue.put(f"data: {json.dumps({'type': 'remove', 'jobId': hash(url)})}\n\n")
                return
                
            # ── GATE POST 2: Deterministic Location Post-Filter (Python) ────
            detected_loc = eval_res.get("detected_location", "Unknown")
            if is_location_mismatch_postllm(detected_loc, profile_dict.get("location", "India")):
                stats["post_filtered"] += 1
                print(f"POST-FILTER REJECT (Location) [{source}]: Location mismatch (Required: {detected_loc}, User: {profile_dict.get('location', 'India')}) — URL={url[:80]}")
                await queue.put(f"data: {json.dumps({'type': 'remove', 'jobId': hash(url)})}\n\n")
                return
                
            # ── All gates passed — build the job card ────────────────────────
            company_name = eval_res.get("companyName") or extract_company_name(url, source)
            team_name = eval_res.get("teamName")
            
            job_data = {
                "type": "job",
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
            
            await queue.put(f"data: {json.dumps({'type': 'status', 'jobId': hash(url), 'company': company_name, 'status': f'Finding contacts at {company_name}...'})}\n\n")
            
            # Step 4: Find POC profiles (current employees, relevant department)
            pocs = await asyncio.to_thread(find_poc_profiles, company_name, team_name)
            job_data["pocProfiles"] = build_poc_list(pocs)
            
            # Fix 2: atomic cap check (no overshoot)
            # The jobs_found >= 10 check-and-increment must happen as a single non-await-interrupted block.
            # Multiple concurrent tasks can reach this check simultaneously between awaits.
            # We increment and check before putting the result into the queue, inside one synchronous section.
            if stats["jobs_found"] >= 10:
                print(f"OVERSHOOT AVOIDED [{source}]: Discarding valid job because cap (10) was hit concurrently — URL={url[:80]}")
                await queue.put(f"data: {json.dumps({'type': 'remove', 'jobId': hash(url)})}\n\n")
                return
                
            stats["jobs_found"] += 1
            await queue.put(f"data: {json.dumps(job_data)}\n\n")
            
        except Exception as e:
            print(f"Worker Error on {url}: {e}")
            import traceback
            traceback.print_exc()

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
            
            # Step 1: Collect URLs from LinkedIn, Naukri, and job boards
            urls = await collect_job_urls(job_title, location)
            print(f"Total Unique URLs found: {len(urls)}")
            
            stats = {"jobs_found": 0, "pre_filtered": 0, "post_filtered": 0}
            queue = asyncio.Queue()
            sem = asyncio.Semaphore(3)
            
            tasks = []
            for url, source, serper_title in urls:
                task = asyncio.create_task(
                    evaluate_single_job(url, source, serper_title, queue, sem, profile, candidate_years, stats)
                )
                tasks.append(task)
                
            # Create a supervisor task to push a sentinel when all workers finish
            async def worker_supervisor():
                await asyncio.gather(*tasks, return_exceptions=True)
                await queue.put(None)
                
            supervisor_task = asyncio.create_task(worker_supervisor())
            
            # Yield from queue as tasks complete
            while True:
                msg = await queue.get()
                if msg is None:  # All tasks done
                    break
                yield msg
                if stats["jobs_found"] >= 10:
                    break
            
            # Fix 3: best-effort cancellation
            if not supervisor_task.done():
                supervisor_task.cancel()
                for t in tasks:
                    if not t.done():
                        t.cancel()
                # Explicitly log the tradeoff: in-flight HTTP calls aren't stopped
                # NOTE: Cancelling the asyncio task does not stop in-flight asyncio.to_thread 
                # calls to Firecrawl/Jina/Serper. Those API calls will complete in the 
                # background and their cost/latency is already spent. This is an accepted tradeoff.
                print("Cancelling pending/in-flight asyncio tasks. Note: this does not stop in-flight asyncio.to_thread calls to Firecrawl/Jina/Serper; those API calls will complete in the background and their cost is already spent.")
                
            yield f"data: {json.dumps({'type': 'stats', 'searched': len(urls), 'matched': stats['jobs_found'], 'passed': stats['jobs_found'], 'rejected': stats['pre_filtered'] + stats['post_filtered']})}\n\n"
            print(f"--- Discovery Complete: {stats['jobs_found']} matched, {stats['pre_filtered']} pre-filtered, {stats['post_filtered']} post-filtered ---")

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
    # Try to derive a team heuristic from the job title, or default to general
    team_name = req.jobTitle.split()[-1] if req.jobTitle else ""
    
    # Use the same verified MetadataParser path as the main discovery flow
    poc_profiles = await asyncio.to_thread(find_poc_profiles, req.company, team_name)
    
    referrers = []
    for p in poc_profiles:
        referrers.append({
            "name": p.get("name", "LinkedIn Member"),
            "linkedin": p.get("linkedin_url", ""),
            "company": req.company
        })
        
    return {"referrers": referrers}

class DraftRequest(BaseModel):
    profile: ProfileData
    job_title: str
    company: str
    poc_name: Optional[str] = None
    poc_role: Optional[str] = None
    job_url: Optional[str] = None


# Simple in-memory cache for news during the session
NEWS_CACHE = {}

@app.post("/api/draft-email")
async def draft_email(req: DraftRequest):
    # News from last 6 months
    company_key = req.company.lower().strip()
    if company_key in NEWS_CACHE:
        news_items = NEWS_CACHE[company_key]
    else:
        news_query = f'{req.company} news'
        serper_res = serper_client.search(news_query, search_type="news", tbs="qdr:m6")
        news_items = serper_res.get("news", [])
        NEWS_CACHE[company_key] = news_items

    news_snippet = "\n".join([n.get("title", "") for n in news_items[:3]])
    if not news_snippet.strip():
        news_snippet = "No recent news available — focus on the company mission and role fit instead."

    profile_summary = f"{req.profile.job_title} with {req.profile.actual_years_exp} years exp. Skills: {', '.join(req.profile.skills)}"

    result = email_drafter.draft(
        profile_summary=profile_summary,
        job_title=req.job_title,
        company=req.company,
        poc_name=req.poc_name or "Hiring Team",
        poc_role=req.poc_role or "Hiring Team",
        job_url=req.job_url or "Not provided",
        news_snippet=news_snippet,
    )

    return {"email": result.get("body", ""), "news": news_items[:3]}

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
            
            # Sources to iterate through
            all_urls = []
            
            # 1. Serper - LinkedIn Jobs
            yield f"data: {json.dumps({'status': 'Searching LinkedIn jobs...'})}\n\n"
            try:
                li_query = f'site:linkedin.com/jobs/view "{job_title}" "{location}"'
                li_serper = await asyncio.to_thread(serper_client.search, li_query)
                li_results = li_serper.get("organic", [])
                print(f"LinkedIn Results: {len(li_results)}")
                for item in li_results[:10]:
                    url = item.get("link")
                    if url and "linkedin.com/jobs" in url:
                        all_urls.append((url, "LinkedIn"))
            except Exception as e:
                print(f"LinkedIn Search Error: {e}")

            # 2. Serper - Naukri Jobs
            yield f"data: {json.dumps({'status': 'Searching Naukri jobs...'})}\n\n"
            try:
                nk_query = f'site:naukri.com "{job_title}" "{location}"'
                nk_serper = await asyncio.to_thread(serper_client.search, nk_query)
                nk_results = nk_serper.get("organic", [])
                print(f"Naukri Results: {len(nk_results)}")
                for item in nk_results[:10]:
                    url = item.get("link")
                    # Only accept individual job pages, not listing/category pages
                    if url and "naukri.com" in url and "/job-listings-" in url:
                        all_urls.append((url, "Naukri"))
            except Exception as e:
                print(f"Naukri Search Error: {e}")

            # 3. Serper - Other Job Boards
            yield f"data: {json.dumps({'status': 'Searching job boards...'})}\n\n"
            try:
                board_query = f'"{job_title}" "{location}" (site:boards.greenhouse.io OR site:jobs.lever.co OR site:myworkdayjobs.com OR site:zohorecruit.com OR site:smartrecruiters.com OR site:jobs.ashbyhq.com)'
                board_serper = await asyncio.to_thread(serper_client.search, board_query)
                board_results = board_serper.get("organic", [])
                print(f"Board Results: {len(board_results)}")
                for item in board_results[:10]:
                    url = item.get("link")
                    if url:
                        source = "Greenhouse" if "greenhouse" in url else "Lever" if "lever" in url else "Workday" if "workday" in url else "JobBoard"
                        all_urls.append((url, source))
            except Exception as e:
                print(f"Board Search Error: {e}")

            print(f"Total Unique URLs found: {len(set(u for u, s in all_urls))}")

            jobs_found = 0
            seen_urls = set()
            
            for url, source in all_urls:
                if jobs_found >= 10: # Cap at 10 results
                    break
                
                if url in seen_urls: continue
                seen_urls.add(url)
                    
                yield f"data: {json.dumps({'status': f'Fetching JD from {source}...'})}\n\n"
                jd_text = await asyncio.to_thread(fetch_jd, url)
                if not jd_text or len(jd_text) < 100:
                    continue
                
                # Strip navigation noise before LLM
                jd_clean = strip_jd_noise(jd_text)
                    
                # Evaluate using Llama (Groq) — only title + years of exp
                eval_res = extract_job_team_info(jd_clean, profile)
                
                if eval_res.get("isValidRange") is True:
                    # Extract company name from URL slug heuristics
                    company_name = extract_company_name(url, source)
                    
                    # Clean up suffixes
                    company_name = company_name.split(" Careers")[0].split(" Jobs")[0].strip()
                    if not company_name or company_name == "Unknown":
                        company_name = source
                        
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
                    
                    # Improved POC Discovery using MetadataParser (Agent 5)
                    yield f"data: {json.dumps({'status': f'Finding contacts at {company_name}...'})}\n\n"
                    
                    # Discover company domain once per job
                    cached_domain = serper_client.find_company_domain(company_name)
                    poc_search_res = serper_client.search_linkedin_pocs(company_name, team_name, job_title)
                    extracted_pocs = metadata_parser.parse_poc_snippets(poc_search_res, company_name, job_title)
                    poc_profiles = extracted_pocs.get("profiles", [])[:2]
                    
                    for poc in poc_profiles:
                        name = poc.get("name", "")
                        first_name = ""
                        last_name = ""
                        if " " in name:
                            parts = name.split(" ")
                            first_name = parts[0]
                            last_name = " ".join(parts[1:])
                        
                        email = hunter_client.find_email(first_name, last_name, cached_domain)
                            
                        job_data["pocProfiles"].append({
                            "name": name,
                            "currentRole": poc.get("current_role"),
                            "linkedinUrl": poc.get("linkedin_url"),
                            "email": email
                        })
                        
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

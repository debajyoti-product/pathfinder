from fastapi import FastAPI, File, UploadFile, HTTPException, Body, BackgroundTasks
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import httpx
import json
import asyncio
import urllib.parse
from pypdf import PdfReader
from io import BytesIO

from config import GEMINI_API_KEY, SERPER_API_KEY, HUNTER_API_KEY, GROQ_API_KEY
from evals import evaluate_job_match, evaluate_email_draft, _call_gemini_json, extract_job_team_info, get_country

from services.serper_client import SerperClient
from agents.metadata_parser import MetadataParser
from services.hunter_client import HunterClient

serper_client = SerperClient()
metadata_parser = MetadataParser()
hunter_client = HunterClient()

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

def call_serper(query: str, search_type: str = "search", tbs: Optional[str] = None) -> dict:
    url = f"https://google.serper.dev/{search_type}"
    payload = {"q": query}
    if tbs:
        payload["tbs"] = tbs # E.g., for last 6 months news: "qdr:m6"
    
    headers = {
        'X-API-KEY': SERPER_API_KEY,
        'Content-Type': 'application/json'
    }
    with httpx.Client() as client:
        response = client.post(url, headers=headers, json=payload, timeout=30)
        return response.json()

def fetch_jina(url: str) -> str:
    jina_url = f"https://r.jina.ai/{url}"
    try:
        with httpx.Client() as client:
            res = client.get(jina_url, timeout=30)
            return res.text
    except:
        return ""

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
        
    prompt = f"""
You are a precise Data Extraction Agent. Your goal is to convert a resume into a structured search profile.
Identify ALL distinct roles held by the candidate and the duration for each.

Output Schema (JSON):
{{
  "roles": [
    {{
      "title": "Role Title (e.g. Product Manager)",
      "years_exp": 2.5
    }}
  ],
  "skills": ["skill1", "skill2"],
  "industry": "e.g. Fintech, SaaS",
  "location": "e.g. San Francisco, CA"
}}

Logic for roles:
- Extract every distinct role title mentioned in the experience section.
- Calculate years of experience for EACH role based on the dates.
- Be precise (e.g. 1.5 years).

Resume Text:
{text[:5000]}
    """
    
    result = _call_gemini_json(prompt)
    if "error" in result:
        raise HTTPException(status_code=500, detail=f"LLM Error: {result['error']}")
    
    return result

class DiscoverRequest(BaseModel):
    profile: ProfileData

from config import (
    GEMINI_API_KEY, 
    DEEPSEEK_API_KEY, 
    GROQ_API_KEY, 
    SERPER_API_KEY, 
    HUNTER_API_KEY,
    APIFY_API_TOKEN
)

async def call_apify_actor(actor_id: str, input_data: dict):
    if not APIFY_API_TOKEN:
        return []
    
    # Apify API uses ~ instead of / for username/actor slugs
    safe_actor_id = actor_id.replace("/", "~")
    url = f"https://api.apify.com/v2/acts/{safe_actor_id}/run-sync-get-dataset-items?token={APIFY_API_TOKEN}"
    try:
        async with httpx.AsyncClient() as client:
            res = await client.post(url, json=input_data, timeout=120.0)
            if res.status_code in [200, 201]:
                return res.json()
            else:
                print(f"Apify Error {res.status_code}: {res.text}")
    except Exception as e:
        print(f"Apify Exception ({actor_id}): {e}")
    return []

@app.post("/api/discover-jobs")
async def discover_jobs(req: DiscoverRequest):
    profile = req.profile.dict()
    
    async def job_generator():
        try:
            job_title = profile.get("job_title", "Product Manager")
            location = profile.get("location", "India")
            
            print(f"--- Discovery Started ---")
            print(f"Title: {job_title}, Location: {location}")
            print(f"Apify Token Present: {bool(APIFY_API_TOKEN)}")
            
            # Sources to iterate through
            all_urls = []
            
            # 1. Apify - LinkedIn (bebity/linkedin-jobs-scraper)
            if APIFY_API_TOKEN:
                yield f"data: {json.dumps({'status': 'Searching LinkedIn via Apify...'})}\n\n"
                li_results = await call_apify_actor("bebity/linkedin-jobs-scraper", {
                    "keywords": job_title,
                    "location": location,
                    "maxResults": 5,
                })
                print(f"LinkedIn Results: {len(li_results)}")
                for item in li_results:
                    url = item.get("jobUrl") or item.get("url")
                    if url: all_urls.append((url, "LinkedIn"))

                # 2. Apify - Indeed (misceres/indeed-scraper)
                yield f"data: {json.dumps({'status': 'Searching Indeed via Apify...'})}\n\n"
                ind_results = await call_apify_actor("misceres/indeed-scraper", {
                    "position": job_title,
                    "location": location,
                    "maxItemsPerSearch": 5
                })
                print(f"Indeed Results: {len(ind_results)}")
                for item in ind_results:
                    url = item.get("url")
                    if url: all_urls.append((url, "Indeed"))

                # 3. Apify - Naukri (muhammetakkurtt/naukri-job-scraper)
                yield f"data: {json.dumps({'status': 'Searching Naukri via Apify...'})}\n\n"
                nk_results = await call_apify_actor("muhammetakkurtt/naukri-job-scraper", {
                    "searchQuery": job_title,
                    "location": location,
                    "maximumJobs": 5
                })
                print(f"Naukri Results: {len(nk_results)}")
                for item in nk_results:
                    url = item.get("jobUrl") or item.get("url")
                    if url: all_urls.append((url, "Naukri"))
            else:
                print("WARNING: APIFY_API_TOKEN is missing!")

            print(f"Total Unique URLs found: {len(set(u for u, s in all_urls))}")

            jobs_found = 0
            seen_urls = set()
            
            for url, source in all_urls:
                if jobs_found >= 5: # Cap at 5 results
                    break
                
                if url in seen_urls: continue
                seen_urls.add(url)
                    
                yield f"data: {json.dumps({'status': f'Fetching JD from {source}...'})}\n\n"
                jd_text = fetch_jina(url)
                if not jd_text or len(jd_text) < 100:
                    continue
                    
                # Evaluate using Llama (Groq)
                eval_res = extract_job_team_info(jd_text, profile)
                
                if eval_res.get("isValidRange") is True:
                    # Basic Title cleaning
                    company_name = "Unknown"
                    if "greenhouse.io/" in url:
                        company_name = url.split("greenhouse.io/")[1].split("/")[0].replace("-", " ").title()
                    elif "lever.co/" in url:
                        company_name = url.split("lever.co/")[1].split("/")[0].replace("-", " ").title()
                    elif "linkedin.com" in url:
                        company_name = source
                    else:
                        company_name = url.split(".")[1].title() if "." in url else source
                    
                    # Clean company name
                    company_name = company_name.split(" Careers")[0].split(" Jobs")[0].strip()
                        
                    team_name = eval_res.get("teamName")
                    
                    job_data = {
                        "id": f"{hash(url)}",
                        "company": company_name,
                        "jobTitle": job_title,
                        "url": url,
                        "linkedin": url,
                        "team": team_name,
                        "requiredExperience": eval_res.get("requiredExperience"),
                        "reason": eval_res.get("reason"),
                        "pocProfiles": []
                    }
                    
                    # Improved POC Discovery
                    yield f"data: {json.dumps({'status': f'Finding contacts at {company_name}...'})}\n\n"
                    search_queries = []
                    if team_name:
                        search_queries.append(f'"{company_name}" "{team_name}" (Lead OR Manager OR Director OR Head) linkedin')
                    
                    search_queries.append(f'"{company_name}" "{job_title}" (Lead OR Manager OR Director OR Head) linkedin')
                    search_queries.append(f'"{company_name}" ("Technical Recruiter" OR "Talent Acquisition" OR "Talent Lead") linkedin')
                    
                    profile_organic = []
                    for q in search_queries:
                        res = call_serper(q)
                        profile_organic.extend(res.get("organic", []))
                    
                    profiles_added = 0
                    seen_poc_links = set()
                    
                    for p in profile_organic:
                        if profiles_added >= 4:
                            break
                        
                        link = p.get("link", "")
                        if "linkedin.com/in/" not in link or link in seen_poc_links:
                            continue
                        
                        seen_poc_links.add(link)
                            
                        title = p.get("title", "")
                        if " - " in title:
                            name = title.split(" - ")[0].strip()
                            current_role = title.split(" - ")[1].split("|")[0].strip()
                        else:
                            name = title.strip()
                            current_role = "Unknown"
                            
                        # Fetch email
                        email = None
                        if name and " " in name:
                            first_name, *last_names = name.split(" ")
                            last_name = " ".join(last_names)
                            domain = company_name.replace(" ", "").lower() + ".com"
                            
                            hunter_url = f"https://api.hunter.io/v2/email-finder?domain={domain}&first_name={first_name}&last_name={last_name}&api_key={HUNTER_API_KEY}"
                            try:
                                with httpx.Client() as client:
                                    h_res = client.get(hunter_url, timeout=10)
                                    if h_res.status_code == 200:
                                        email = h_res.json().get("data", {}).get("email")
                            except: pass
                                
                        job_data["pocProfiles"].append({
                            "name": name,
                            "currentRole": current_role,
                            "linkedinUrl": link,
                            "email": email
                        })
                        profiles_added += 1
                        
                    jobs_found += 1
                    yield f"data: {json.dumps(job_data)}\n\n"

            yield "event: close\ndata: {}\n\n"
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
    serper_res = call_serper(query)
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

@app.post("/api/v1/search-and-match")
async def search_and_match(req: DiscoverRequest):
    profile = req.profile.dict()
    job_title = profile.get("job_title", "Engineer")
    skills = profile.get("skills", [])
    exp = profile.get("actual_years_exp", 0)
    location = profile.get("location", "")
    
    # Identify country for broader search
    country = get_country(location)
    location_str = f"in {country}" if country else ""
    
    # 1. Search for jobs
    query = f'"{job_title}" {location_str} site:boards.greenhouse.io OR site:jobs.lever.co'
    serper_res = serper_client.search_jobs(query)
    organic_jobs = serper_res.get("organic", [])
    
    results = []
    jobs_processed = 0
    
    for job in organic_jobs:
        if jobs_processed >= 2:
            break
            
        job_url = job.get("link")
        if not job_url:
            continue
            
        # 2. Extract JD and Validate
        jd_text = fetch_jina(job_url)
        if not jd_text or len(jd_text) < 100:
            continue
            
        validation = extract_job_team_info(jd_text, profile)
        if not validation.get("isValidRange"):
            continue
            
        # Determine Company Name
        company_name = "Unknown"
        if "greenhouse.io/" in job_url:
            company_name = job_url.split("greenhouse.io/")[1].split("/")[0].replace("-", " ").title()
        elif "lever.co/" in job_url:
            company_name = job_url.split("lever.co/")[1].split("/")[0].replace("-", " ").title()
        
        team_name = validation.get("teamName")
        
        # 3. Find Company Domain for Hunter.io
        domain = serper_client.find_company_domain(company_name)
        
        # 4. Search for LinkedIn POCs
        poc_search_res = serper_client.search_linkedin_pocs(company_name, team_name, job_title)
        
        # 5. Extract POC Metadata (Limit 2)
        extracted_pocs = metadata_parser.parse_poc_snippets(poc_search_res)
        poc_profiles = extracted_pocs.get("profiles", [])[:2]
        
        # 6. Hunter.io Email Lookup
        final_pocs = []
        for poc in poc_profiles:
            name = poc.get("name", "")
            first_name = ""
            last_name = ""
            if " " in name:
                parts = name.split(" ")
                first_name = parts[0]
                last_name = " ".join(parts[1:])
            
            # email = hunter_client.find_email(first_name, last_name, domain)
            email = None # Temporarily bypassed for strict POC validation phase
            
            final_pocs.append({
                "name": name,
                "title": poc.get("currentRole"),
                "linkedinUrl": poc.get("linkedinUrl"),
                "email": email
            })
            
        results.append({
            "jobTitle": job_title,
            "company": company_name,
            "jobUrl": job_url,
            "pocProfiles": final_pocs
        })
        
        jobs_processed += 1
        
    return results

@app.post("/api/draft-email")
async def draft_email(req: DraftRequest):
    # News from last 6 months
    news_query = f'{req.company} news'
    serper_res = call_serper(news_query, search_type="news", tbs="qdr:m6")
    news_items = serper_res.get("news", [])
    
    news_snippet = "\n".join([n.get("title", "") for n in news_items[:3]])
    
    profile_summary = f"{req.profile.job_title} with {req.profile.actual_years_exp} years exp. Skills: {', '.join(req.profile.skills)}"
    
    prompt = f"""
You are an Expert Career Coach. Write a high-conversion cold email.
Inputs:
- User Resume Summary: {profile_summary}
- Job Title: {req.job_title}
- Company: {req.company}
- Company News/Product Snippet: {news_snippet}
Tone: Professional, brief, and high-signal. No fluff.
Possible structure: greeting, hook (specific job with url & 1-2 core skills), body (connect user experience to company news wherever applicable), ask for referral.
Max 150 words.
Return JSON with key 'email': 'drafted text'
    """
    
    result = _call_gemini_json(prompt)
    email_text = result.get("email", "")
    
    # Eval
    eval_res = evaluate_email_draft(news_snippet, email_text)
    if not eval_res.get("has_intent_line", False):
        # Retry once
        result = _call_gemini_json(prompt + "\nCRITICAL: Ensure you include a specific Intent line that mentions the news naturally.")
        email_text = result.get("email", "")
        
    return {"email": email_text, "news": news_items[:3]}

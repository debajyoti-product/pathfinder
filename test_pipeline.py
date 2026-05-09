import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath('backend'))

from backend.main import call_serper, fetch_jd, strip_jd_noise
from backend.evals import extract_job_team_info

async def full_test():
    job_title = "Product Manager"
    location = "India"
    user_profile = {
        "job_title": "Product Manager",
        "skills": ["SQL", "Analytics", "Product Roadmap"],
        "actual_years_exp": 2,
        "search_range": ["2-4 years"],
        "industry": "Tech"
    }

    all_urls = []

    # Job boards only (most reliable)
    board_query = f'"{job_title}" "{location}" (site:boards.greenhouse.io OR site:jobs.lever.co OR site:myworkdayjobs.com OR site:zohorecruit.com OR site:smartrecruiters.com OR site:jobs.ashbyhq.com)'
    board_res = call_serper(board_query)
    items = board_res.get("organic", [])
    for item in items[:5]:
        u = item.get("link", "")
        if u:
            all_urls.append(u)

    print(f"Testing {len(all_urls)} board URLs\n")

    valid = 0
    for url in all_urls:
        print(f"URL: {url[:80]}")
        jd_text = fetch_jd(url)
        jd_clean = strip_jd_noise(jd_text)
        print(f"  JD full: {len(jd_text)} chars | stripped: {len(jd_clean)} chars")
        result = extract_job_team_info(jd_clean, user_profile)
        ok = result.get('isValidRange')
        print(f"  Valid: {ok} | Exp required: {result.get('requiredExperience')}")
        if ok:
            valid += 1
            # Company name from URL
            if "lever.co/" in url:
                company = url.split("lever.co/")[1].split("/")[0].title()
            elif "ashbyhq.com/" in url:
                company = url.split("ashbyhq.com/")[1].split("/")[0].title()
            elif "myworkdayjobs.com" in url:
                company = url.split(".")[0].replace("https://", "").title()
            else:
                company = "Unknown"
            print(f"  Company: {company}")
        print()

    print(f"\nResult: {valid}/{len(all_urls)} jobs valid")

asyncio.run(full_test())

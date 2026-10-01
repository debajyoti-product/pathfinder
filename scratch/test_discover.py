import asyncio
import json
import sys
import os

sys.path.append(os.path.join(os.getcwd(), 'backend'))

from main import ProfileData, DiscoverRequest, discover_jobs

async def main():
    profile = ProfileData(
        job_titles=["Product Manager", "Associate Product Manager"],
        skills=["PRD", "Prototyping", "Market research", "API integration", "Data analysis", "Gen AI", "LLM", "SQL"],
        actual_years_exp=3.92,
        search_range=["1-3 years", "3-5 years"],
        industry="Technology",
        location="India",
        remote_only=False
    )
    req = DiscoverRequest(profile=profile)
    
    print("Starting Job Discovery...")
    response = await discover_jobs(req)
    
    async for chunk in response.body_iterator:
        try:
            text = chunk.decode('utf-8').strip()
            if text.startswith('data: '):
                data = json.loads(text[6:])
                if data.get('type') == 'job':
                    print(f"\n✅ FOUND JOB: {data.get('title')} at {data.get('company')}")
                    print(f"URL: {data.get('url')}")
                    print(f"Score: {data.get('score')} - Location: {data.get('location')}")
                elif data.get('type') == 'status':
                    print(f"Status [{data.get('company')}]: {data.get('status')}")
        except Exception as e:
            pass

if __name__ == "__main__":
    asyncio.run(main())

import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath('backend'))
from backend.main import call_serper

async def test():
    job_title = 'Product Manager'
    location = 'India'
    query = f'"{job_title}" "{location}" (site:boards.greenhouse.io OR site:jobs.lever.co OR site:myworkdayjobs.com OR site:zohorecruit.com OR site:smartrecruiters.com OR site:jobs.ashbyhq.com)'
    print('Query:', query)
    try:
        res = call_serper(query)
        organic = res.get('organic', [])
        print('Results count:', len(organic))
        for item in organic[:3]:
            print(item.get('link'))
    except Exception as e:
        print('Error:', e)

asyncio.run(test())

import os, json, sys
sys.path.append(os.path.join(os.getcwd(), 'backend'))
from services.serper_client import SerperClient

c = SerperClient()
res = c.search('site:linkedin.com/jobs/view ("Product Manager" OR "Associate Product Manager") "India"', tbs='qdr:m')
print("LinkedIn:", len(res.get("organic", [])))
for i in res.get("organic", [])[:3]:
    print(i.get("title"), i.get("link"))

res2 = c.search('site:naukri.com/job-listings ("Product Manager" OR "Associate Product Manager") "India"', tbs='qdr:m')
print("\nNaukri:", len(res2.get("organic", [])))
for i in res2.get("organic", [])[:3]:
    print(i.get("title"), i.get("link"))

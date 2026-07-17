import json
import sys
import os

# Add backend to path so imports work
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from agents.resume_parser import ResumeParser

resume_text = """
Debajyoti Biswas
iamdebajyoti850@gmail.com
9903777698
Linkedin, Portfolio, github

Summary: Product Manager with 2+ years of experience in building products to drive engagement & retention for 2mn+ users & additionally, yielding INR 60L+ in incremental growth

Skills: Prototyping, Prompt engineering, Market research, API integration, Documentation, Data analysis, Funnel optimization
Tools: JIRA, Figma, Lovable, Replit, Postman, DBeaver, Claude, GPT, Firebase, Google analytics, Gupshup

Experience:
SaveIN (YC W22) - Product Manager (04/2025 - 09/2025)
Cashkaro - Associate Product Manager (09/2023 - 05/2024)
Guide - Founder (12/2022 - 09/2023)
Swift - Associate Product Manager (04/2022 - 11/2022)
Digit Insurance - Analyst (01/2020 - 04/2021)

Education: Heritage Institute of Technology, Kolkata - B.Tech
"""

def main():
    parser = ResumeParser()
    result = parser.parse(resume_text)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()

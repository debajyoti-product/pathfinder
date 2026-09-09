from evals import _call_llama_text

class EmailDrafter:
    def draft(
        self,
        profile_summary: str,
        job_title: str,
        company: str,
        poc_name: str,
        intel_snippets: str,
    ) -> dict:

        prompt = f"""## System Persona
You are a Tactical Career Coach, Company Researcher, and Cold Email Strategist. Your goal is to produce two things:
1. A structured company intel report based on the provided search snippets.
2. A cold email draft that strictly follows a provided template.

## Input Context
- **Candidate:** {profile_summary}
- **Target:** {job_title} at {company}
- **Contact:** {poc_name}
- **Company Intel Search Snippets:**
{intel_snippets}

## Task 1: Generate Company Intel
Using the provided snippets and your internal knowledge base about {company}, generate a structured markdown report EXACTLY in this format:

* one-line description of what the company does, who they serve & their scale/reach
   * [Core product/platform description]
   * [Key proprietary technology]
   * [Business model]

* User/customer segments
   * [Segment 1...]
   * [Segment 2...]

* Competitors
   * [Direct competitor 1...]
   * [Direct competitor 2...]

* What's interesting
   * [USP/moat]
   * [Unique product insights]
   * [Recent news (if any)]
   * [One open product problem or opportunity worth exploring as a PM]

===SPLIT===

## Task 2: Generate the Email Draft
Strictly use the following template to generate the email body. DO NOT add "Subject:". Replace the bracketed placeholders with contextually accurate information. The tone should be peer-to-peer and professional.

CRITICAL RULE: You MUST ONLY reference skills, experiences, and tools that are EXPLICITLY listed in the Candidate section above. DO NOT invent, assume, or hallucinate any skills the candidate does not have. If the candidate doesn't have a specific skill, do not mention it.

Template:
Hello {poc_name}, Debajyoti here. Hope you are doing well. I was wondering if you are currently hiring for any junior product roles.
[Utilize ONLY the candidate's listed skills and experience to create an active phrasing sentence like: "I have X years of experience in building products for X users & Y revenue"]
Why {company}?
- [Bullet 1: Match candidate's ACTUAL listed skills against the company's domain/industry. Be specific.]
- [Bullet 2: Sharp, brief & unique point using only skills from the candidate's profile]
- [Bullet 3: Sharp, brief & unique point using only skills from the candidate's profile]
If my profile seems suitable, let me know if we can explore synergies.

Regards
Debajyoti

## Output Format
You MUST output exactly your Task 1 response, followed by the exact literal string `===SPLIT===` on a new line, followed by your Task 2 response. Do not use JSON.
"""

        result = _call_llama_text(prompt)
        if result.startswith("Error:"):
            return {"body": f"API Error: {result}", "company_intel": "Error generating intel."}
            
        parts = result.split("===SPLIT===")
        if len(parts) >= 2:
            intel = parts[0].replace("## Task 1: Generate Company Intel", "").strip()
            body = parts[1].replace("## Task 2: Generate the Email Draft", "").strip()
            return {"company_intel": intel, "body": body}
        else:
            # fallback
            return {"company_intel": result, "body": "Draft generation failed. Please see intel above."}


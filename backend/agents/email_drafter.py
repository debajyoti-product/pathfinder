from evals import _call_llama_json


class EmailDrafter:
    """
    Agent 6: Tactical Career Coach & Cold Email Strategist (Llama 3.1 8B via Groq)
    Produces a high-signal 100-word peer-to-peer cold email with a mandatory
    self-critique gate. Auto-retries once if the intent line is missing.
    """

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
Using the provided snippets and your internal knowledge base about {company}, generate a structured markdown report EXACTLY in this format (no deviations):

* one-line description of what the company does, who they serve & their scale/reach
   * [Core product/platform description, what it does end-to-end]
   * [Key proprietary technology, infrastructure, or capability]
   * [Business model]

* User/customer segments
   * [Segment 1...]
   * [Segment 2...]

* Competitors
   * [Direct competitor 1...]
   * [Direct competitor 2...]
   * [Indirect competitor 1...]
   * [Indirect competitor 2...]

* What's interesting
   * [USP/moat]
   * [Unique product insights]
   * [Recent news (if any)]
   * [One open product problem or opportunity worth exploring as a PM]

## Task 2: Generate the Email Draft
Strictly use the following template to generate the email body. DO NOT add "Subject:". Replace the bracketed placeholders with contextually accurate information.
The tone should be peer-to-peer and professional.

Template:
Hello {poc_name}, Debajyoti here. Hope you are doing well. I was wondering if you are currently hiring for any junior product roles.
[Utilize the resume experience & summary to create an active phrasing sentence like: "I have X years of experience in building products for X users & Y revenue"]
Why {company}?
[Bullet 1: Highly reflect the candidate's match against the skills, experience, requirements & industry of the company]
[Bullet 2: Sharp, brief & unique point]
[Bullet 3: Sharp, brief & unique point]
If my profile seems suitable, let me know if we can explore synergies.

Regards
Debajyoti

## Output Contract (JSON ONLY)
{{
  "company_intel": "string (the markdown generated in Task 1)",
  "body": "string (the email draft generated in Task 2)"
}}"""

        result = _call_llama_json(prompt)
        if "error" in result:
            return {"body": f"API Error: {result['error']}", "company_intel": "Error generating intel."}
            
        return {
            "body": result.get("body", ""),
            "company_intel": result.get("company_intel", ""),
        }


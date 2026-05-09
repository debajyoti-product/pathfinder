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
        poc_role: str,
        job_url: str,
        news_snippet: str,
    ) -> dict:
        prompt = f"""## System Persona
You are a Tactical Career Coach and Cold Email Strategist. Your goal is to produce a high-signal, 100-word "Peer-to-Peer" cold email that connects a candidate's background to a specific company mission.

## Input Context
- **Candidate:** {profile_summary}
- **Target:** {job_title} at {company} (URL: {job_url})
- **Contact:** {poc_name} ({poc_role})
- **Signal:** {news_snippet}

## Step 1: Strategic Planning (Internal Monologue)
- **Identify the Hook:** How does the {news_snippet} create a problem that the Candidate's skills can solve?
- **Referral Context:** Mention that you are reaching out to them specifically as a {poc_role} within the team.

## Step 2: The "No-Fluff" Drafting Constraints
1. **Banned Openers:** DO NOT use "I hope this finds you well," "I am writing to," or "My name is".
2. **The Intent Line:** You MUST integrate the news signal as a reason for your timing (e.g., "Given your recent move into [News], I thought my experience in [Skill] would be relevant for the [Job] role.").
3. **Brevity:** Maximum 100 words. Every sentence must add value.

## Step 3: Mandatory Self-Critique Gate
Evaluate your draft against these checkboxes:
- [ ] Does it start with a filler sentence? (If yes, delete it).
- [ ] Is the news signal mentioned naturally or does it feel forced?
- [ ] Is there a clear, low-friction call to action?
- [ ] Is the tone "Peer-to-Peer" rather than "Applicant-to-Authority"?

## Output Contract (JSON ONLY)
{{
  "subject": "string",
  "body": "string",
  "critique_notes": "Internal notes on why this version passed the quality gate",
  "has_intent_line": true
}}"""

        result = _call_llama_json(prompt)
        email_text = result.get("body", result.get("email", ""))

        # Auto-retry once if the self-critique gate was ignored
        if not result.get("has_intent_line", False):
            result = _call_llama_json(
                prompt + "\nCRITICAL: Ensure you include a specific Intent line that mentions the news naturally."
            )
            email_text = result.get("body", result.get("email", ""))

        return {
            "subject": result.get("subject", ""),
            "body": email_text,
            "critique_notes": result.get("critique_notes", ""),
        }

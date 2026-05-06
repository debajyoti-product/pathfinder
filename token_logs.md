# Token Optimization Logs

> **⚠️ READ THIS FILE** alongside `context.md` before making architectural or LLM-related changes to optimize context window and token usage.

This document tracks the estimated token expenditure for core AI actions in the Pathfinder AI Suite, along with actionable strategies to reduce token bloat.

---

## 1. Action Token Categorization & Optimizations

### Action: Resume Parsing (`/api/parse-resume`)
* **Context Required:** PDF Resume text (truncated to 5000 chars) + Extraction instructions (JSON schema).
* **Estimated Tokens Spent:** ~1,500 - 2,000 input tokens | ~150 output tokens (per upload).
* **Optimization Strategy:** (Truncate the resume text to the first 3000 characters instead of 5000, as core experience and skills are almost always at the top. Additionally, we could switch to a smaller, faster model like Llama-3-8B instead of 70B, as extracting JSON from structured text is well within the capabilities of smaller models.)

### Action: Job Match Validation (`extract_job_team_info`)
* **Context Required:** Full Job Description text (from Firecrawl/Jina) + User Profile JSON + Evaluation rules.
* **Estimated Tokens Spent:** ~2,000 - 4,000 input tokens per URL | ~100 output tokens. **[HIGH COST]** Since we evaluate up to 30 URLs per discovery session, this can consume up to 60k-120k input tokens per search!
* **Optimization Strategy:** (Massive token sink. We must aggressively truncate the scraped JD text to the first 3000-4000 characters. The "Requirements" and "About the Role" sections are usually near the top, making the bottom boilerplate irrelevant. We should also route this specific task to `Llama-3-8b-8192` instead of the 70B model, as it is a simple binary classification + short extraction task.)

### Action: Email Drafting (`/api/draft-email`)
* **Context Required:** User Profile JSON + Target Job Details + Serper News Snippets (recent company news) + Drafting rules.
* **Estimated Tokens Spent:** ~1,000 input tokens | ~250 output tokens.
* **Optimization Strategy:** (Strictly limit the Serper news context to the top 1 or 2 most relevant articles to prevent prompt bloat. If the user drafts multiple emails for the same company, we should implement a basic server-side cache for the generated draft or the parsed news.)

### Action: Draft Evaluation (`evaluate_email_draft`)
* **Context Required:** The generated draft email from the previous step + Evaluation rules.
* **Estimated Tokens Spent:** ~400 input tokens | ~100 output tokens.
* **Optimization Strategy:** (This is a redundant LLM call. We can optimize this by baking the "intent line" and quality constraints directly into the system prompt of the original drafting step, forcing the model to generate it correctly the first time. This completely eliminates this secondary LLM call.)

---

## 2. Model Roster & Credits

The application currently relies heavily on free-tier APIs. Usage is monitored by `backend/services/usage_tracker.py`.

| Provider | Model Name | Primary Use Case | Credits / Quota |
|----------|------------|------------------|-----------------|
| **Groq** | `llama-3.3-70b-versatile` | **ACTIVE** - Resume parsing, JD validation, Drafting, Eval | ~14,400 Requests/Day (Groq Free Tier limits apply: ~30k Tokens/Min) |
| **Gemini** | `gemini-1.5-flash` / `pro` | *Unused* - Keys present but traffic routed to Groq | Standard free tier limits |
| **DeepSeek** | `deepseek-chat` | *Unused* - Keys present but traffic routed to Groq | Standard API balance |
| **Serper** | N/A (Search API) | Job discovery, LinkedIn POC search, News search | ~2,500 queries free |
| **Hunter.io** | N/A (Email Lookup) | Fetching emails for discovered POCs | 25 requests/month (Free Tier) |
| **Firecrawl** | N/A (Web Scraper) | Web scraping Job Descriptions (Markdown) | 500 credits (Free Tier) |

# Token Optimization Logs

> **⚠️ READ THIS FILE** alongside `context.md` before making architectural or LLM changes to optimize context window and token usage.

---

## 1. Action Token Expenditure & Optimizations

| Flow / Action | Context Passed | Est. Input Tokens | Est. Output | 💡 Future Optimization Strategy |
|--------------|----------------|-------------------|-------------|--------------------------------|
| **Resume Parsing** <br/>(`/api/parse-resume`) | Resume Text + JSON Schema | ~1,500 - 2,000 | ~150 | Truncate resume to first 3000 chars. Switch to a smaller, faster model (e.g., Llama-3-8B) as JSON extraction is easy. |
| **Job Validation** <br/>(`extract_job_team_info`) | Scraped JD (Markdown) + User Profile JSON | **~2,000 - 4,000**<br/>*(Up to 120k total/search)* | ~100 | **Massive token sink.** Aggressively truncate scraped JD to the first 3000 chars. Switch to an 8B model instead of 70B. |
| **Email Drafting** <br/>(`/api/draft-email`) | Profile + Job Details + Serper News Snippets | ~1,000 | ~250 | Restrict Serper news to top 1-2 articles. Cache drafts for the same company to prevent redundant runs. |
| **Draft Evaluation** <br/>(`evaluate_email_draft`) | Generated Draft + Eval Rules | ~400 | ~100 | **Redundant call.** Bake strict constraints directly into the drafting system prompt to eliminate this step entirely. |

---

## 2. IDE Assistant Models (Agent Credits)

*This tracks the LLMs you use to converse with me (the agent).*

| Model Name | Primary Capability | Total Credits | Credits Left |
|------------|--------------------|---------------|--------------|
| **Gemini 3.1 Pro (High)** | Deep reasoning, complex coding, high context | *(IDE Managed)* | *(IDE Managed)* |
| **Gemini 3.1 Flash (Fast)** | Fast execution, simpler edits | *(IDE Managed)* | *(IDE Managed)* |
| **Claude Opus 4.6** | Advanced coding, precise file editing | *(IDE Managed)* | *(IDE Managed)* |

*(Note: Since I cannot automatically read your IDE's internal billing quota, you can manually update the credits here if you wish to track them).*

---

## 3. Application API Providers (Project Dependencies)

*This tracks the third-party APIs used by the Pathfinder codebase. Tracked via `backend/services/usage_tracker.py`.*

| Provider | Purpose | Model / Type | Total Quota | Status / Remaining |
|----------|---------|--------------|-------------|--------------------|
| **Groq** | All core LLM logic | `llama-3.3-70b-versatile` | ~14,400 Requests/Day | **ACTIVE** (~30k Tok/Min) |
| **Gemini API** | Unused backup | `gemini-1.5-flash` | Standard Free Tier | *Keys in `.env`* |
| **DeepSeek API** | Unused backup | `deepseek-chat` | Standard Balance | *Keys in `.env`* |
| **Serper.dev** | Job & LinkedIn search | Google Search API | 2,500 queries | **ACTIVE** |
| **Hunter.io** | Email Lookup | Email Finder API | 25 requests/month | **ACTIVE** |
| **Firecrawl** | JD Markdown Scraping| Web Scraper API | 500 credits | **ACTIVE** |

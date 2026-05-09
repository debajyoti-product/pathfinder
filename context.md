# Pathfinder AI Suite — Project Context (Single Source of Truth)

> **⚠️ READ THIS FILE FIRST before making any changes.** This is the persistent memory for all AI agents working on this project. Update this file after every significant change.
**Last Updated:** 2026-05-09

---

## 1. Project Overview

**Objective:** AI-driven career discovery platform. Automates: resume → structured profile → job discovery → contact finding → personalized cold email drafting.

**Repo:** `https://github.com/debajyoti-product/pathfinder.git` (redirected from `pathfinder-ai-suite`)
**Deployment:** Vercel (frontend + serverless Python backend)

---

## 2. Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 18, Vite 5, TypeScript, Tailwind CSS 3, Shadcn UI, Lucide Icons |
| **Backend** | FastAPI (Python), Uvicorn, SSE (Server-Sent Events) |
| **LLMs** | Groq / Llama-3.3-70b (Resume parsing, POC extraction, email drafting) & Qwen 3 32B (JD validation) |
| **Job Discovery** | Serper API (Google search for LinkedIn/Naukri/Greenhouse/Lever job URLs) |
| **JD Extraction** | Firecrawl `scrape_url` (primary, via `V1FirecrawlApp`) → Jina Reader (fallback for LinkedIn, which Firecrawl blocks) |
| **Contact Search** | Serper API (LinkedIn profile search) |
| **Email Lookup** | Hunter.io API |
| **Deployment** | Vercel (rewrites `/api/*` → `api/index.py` serverless function) |

---

## 3. Environment Variables

Stored in `backend/.env`. Must also be set in **Vercel Dashboard → Settings → Environment Variables** for production.

| Variable | Purpose |
|----------|---------|
| `GEMINI_API_KEY` | Legacy — currently unused (all LLM calls use Groq) |
| `DEEPSEEK_API_KEY` | Legacy — currently unused |
| `GROQ_API_KEY` | **Active.** All LLM calls (resume parsing, JD eval, email drafting, email quality check) |
| `SERPER_API_KEY` | **Active.** Google search for job URLs and LinkedIn POC profiles |
| `HUNTER_API_KEY` | **Active.** Email lookup for discovered POC contacts |
| `FIRECRAWL_API_KEY` | **Active.** Scraping JD content from non-LinkedIn URLs (Naukri, Greenhouse, Lever) |
| `QWEN_API_KEY` | **Active.** JD Validation Agent (Qwen 3 32B via Groq) |

Config loaded via: `backend/config.py` → `python-dotenv` → `os.getenv()`

---

## 4. File Map

### Frontend (`src/`)
| File | Purpose |
|------|---------|
| `src/pages/Index.tsx` | Main page. Orchestrates 4-tab flow: Home → Profile → Results → Drafting |
| `src/components/HomeTab.tsx` | Landing tab with resume upload |
| `src/components/ProfileTab.tsx` | Displays parsed profile; user confirms before discovery |
| `src/components/ResultsTab.tsx` | Streams job results via SSE. Header: "Job Results for You", Subheader: "Includes job links & potential referral profiles" |
| `src/components/DraftingTab.tsx` | Cold email drafting for selected POC/company |
| `src/components/NavLink.tsx` | Tab navigation component |
| `src/lib/api.ts` | All backend API calls — `parseResume()`, `streamDiscoverJobs()`, `discoverReferrals()`, `draftEmail()` |
| `src/lib/mockData.ts` | TypeScript types/interfaces (`ProfileData`, `JobResult`, `ProfileLead`, etc.) |

### Backend (`backend/`)
| File | Purpose |
|------|---------|
| `backend/main.py` | FastAPI app. Endpoints: `/api/parse-resume`, `/api/discover-jobs` (SSE), `/api/discover-referrals`, `/api/v1/search-and-match`, `/api/draft-email` |
| `backend/evals.py` | Shared LLM callers: `_call_llama_json()`, `_call_qwen_json()`, `evaluate_job_match()`, `get_country()` |
| `backend/config.py` | Loads all env vars from `.env` |
| `backend/services/serper_client.py` | Serper API wrapper class |
| `backend/services/hunter_client.py` | Hunter.io API wrapper class |
| `backend/services/usage_tracker.py` | API usage monitoring (free-tier limits) |

### Agents (`backend/agents/`) — All LLM agents live here
| File | Agent | Model |
|------|-------|-------|
| `agents/resume_parser.py` | Agent 1: Resume Data Extraction + Python Date Math | Llama 3.1 8B (Groq) |
| `agents/jd_validator.py` | Agent 3: Cynical Gatekeeper (3 Hard Gates) | Qwen 3 32B (Groq) |
| `agents/metadata_parser.py` | Agent 5: High-Precision POC Entity Resolution | Llama 3.3 70B (Groq) |
| `agents/email_drafter.py` | Agent 6: Tactical Career Coach + Self-Critique Loop | Llama 3.1 8B (Groq) |

### Vercel Deployment (`api/`)
| File | Purpose |
|------|---------|
| `api/index.py` | Serverless entry point — imports `app` from `backend/main.py` |
| `api/requirements.txt` | Python deps for Vercel: `fastapi, uvicorn, python-multipart, pypdf, httpx, python-dotenv, google-generativeai, groq, firecrawl-py` |
| `vercel.json` | Rewrites: `/api/*` → `api/index.py`, `/*` → `index.html` |

---

## 5. Data Flow (Pipeline)

### Step 1: Extraction (`POST /api/parse-resume`)
```
PDF Upload → pypdf text extraction → Groq/Llama prompt → Python Date Math Override → Structured JSON
Output: { experience_summary: [{role_type, total_years_numeric}], roles: [{title, start_date, end_date}], skills: [], industry }
```
- Text truncated to first 5000 chars before LLM call.

### Step 2: Discovery (`POST /api/discover-jobs` — SSE stream)
```
Profile → Serper search (3 sources) → URL collection → JD scraping → LLM validation → POC search → Email lookup → SSE yield
```

**Source searches (via Serper, up to 10 results each):**
1. `site:linkedin.com/jobs/view "{job_title}" "{location}"`
2. `site:naukri.com "{job_title}" "{location}"`
3. `"{job_title}" "{location}" (site:boards.greenhouse.io OR site:jobs.lever.co OR site:myworkdayjobs.com OR site:zohorecruit.com OR site:smartrecruiters.com OR site:jobs.ashbyhq.com)`

**JD extraction (per URL):**
- Non-LinkedIn → `Firecrawl V1FirecrawlApp.scrape_url()` (markdown, main content only)
- LinkedIn → Jina Reader fallback (`https://r.jina.ai/{url}`) — Firecrawl blocks LinkedIn
- Skip if extracted text < 100 chars

**LLM validation (`extract_job_team_info`):**
- Uses **Qwen 3 32B** (Cynical Gatekeeper Persona).
- Hard gates for Geography (India only), Seniority (Implicit/Explicit floors), and Remote Policy.
- Extracts: `isValidRange`, `reasoning_trace` (Loc/Exp/Remote breakdown), `detected_location`, `required_years_extracted`.

**POC discovery (per valid job):**
- Serper searches for LinkedIn profiles at the company (team leads, managers, recruiters)
- **Metadata Parser Agent (Llama 3.3 70B)** applies High-Precision Entity Resolution (filters "Ex-" employees, Name-Company collisions, and verifies current employer).
- **Cap: 2 POC profiles per job**
- Hunter.io email lookup per POC

**Caps:**
- **Max 10 matched jobs** returned total
- **Max 2 POC profiles** per job
- **Max 10 URLs** processed per source

### Step 3: Drafting (`POST /api/draft-email`)
```
Company + Profile → Serper news search (last 6 months) → Groq/Llama email generation (with Self-Critique Gate) → Auto-retry if no intent line
Output: { email: "drafted text", news: [...], critique_notes: "..." }
```

---

## 6. UI Flow & State Management

**Tab navigation is state-locked:**
1. **Home** → Always accessible. Upload resume.
2. **Profile** → Unlocked after `resumeUploaded = true`. Shows parsed profile for confirmation.
3. **Results** → Unlocked after `profileConfirmed = true`. Streams jobs via SSE.
4. **Drafting** → Unlocked after user clicks "Generate Draft" on a job/POC.

**Results display:**
- Header: **"Job Results for You"**
- Subheader: **"Includes job links & potential referral profiles"**
- Each job card shows: company, title, experience, match reason, job link, up to 2 POC profiles
- POC profiles have: name, role, LinkedIn link, email, thumbs up/down feedback, "Draft" button
- Badge shows total match count

**Link handling:** All external links are protocol-prefixed (`https://`) to prevent relative routing errors.

---

## 7. Completed Milestones

- [x] Resume parsing with structured JSON output
- [x] Streamed job matching with real-time SSE UI updates
- [x] Protocol-safe link handling for external career boards
- [x] Location-aware job searching (country extraction via LLM)
- [x] Contact-specific drafting (select a POC to draft for)
- [x] Migrated from Apify to Firecrawl for JD scraping (2026-05-06)
- [x] Migrated job discovery from Apify actors to Serper search (2026-05-06)
- [x] LLM-based company name extraction from JD text (2026-05-06)
- [x] Increased job results cap to 10, POC cap to 2 (2026-05-06)
- [x] Updated results header/subheader copy (2026-05-06)
- [x] Vercel deployment configured with serverless Python backend

---

## 8. Known Constraints & Gotchas

| Issue | Details |
|-------|---------|
| **LinkedIn blocked by Firecrawl** | `V1FirecrawlApp.scrape_url()` returns "Website Not Supported" for `linkedin.com`. JD extraction falls back to Jina Reader for LinkedIn URLs. |
| **Firecrawl SDK versioning** | `firecrawl-py v4.24.1` default `FirecrawlApp` is v2 (only `parse`). Must use `V1FirecrawlApp` for `scrape_url` and `search`. |
| **Resume text limit** | Gemini/Groq prompt truncates resume to first 5000 characters. |
| **Domain heuristic** | Hunter.io email lookup assumes `companyname.com` — fails for non-standard TLDs or subsidiaries. |

| **Dual requirements.txt** | `backend/requirements.txt` for local dev; `api/requirements.txt` for Vercel. **Both must be kept in sync.** |
| **Vercel env vars** | Must be set manually in Vercel Dashboard. `.env` file is gitignored and not deployed. |
| **API throttling** | Usage tracker in `backend/services/usage_tracker.py` warns at 60% of free-tier limits. |
| **ALERTS_FILE path** | Hardcoded path in `usage_tracker.py` needs fixing to a relative path. |

---

## 9. Key API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/parse-resume` | Upload PDF → structured profile JSON |
| POST | `/api/discover-jobs` | SSE stream of matched jobs with POC contacts |
| POST | `/api/discover-referrals` | Find referrers at a specific company |
| POST | `/api/v1/search-and-match` | Non-streaming job search (Greenhouse/Lever only, legacy) |
| POST | `/api/draft-email` | Generate cold email with company news integration |

---

## 10. Local Development

```bash
# Backend
cd backend
source venv/Scripts/activate   # Windows: .\venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend
cd ..  # project root
npm install
npm run dev   # Vite dev server with proxy to :8000
```

Vite proxy config in `vite.config.ts` forwards `/api` requests to `http://localhost:8000`.

---

## 11. Deployment Checklist (Vercel)

1. Push to `main` branch → auto-deploys via GitHub integration
2. Ensure `api/requirements.txt` matches `backend/requirements.txt` + `google-generativeai, groq`
3. Ensure all env vars are set in Vercel Dashboard (Section 3 above)
4. `FIRECRAWL_API_KEY` must be `fc-a5f5d16dae064efca5b26883e438d298`

---

## 12. Change Log

| Date | Change |
|------|--------|
| 2026-05-06 | Migrated from Apify to Firecrawl (`V1FirecrawlApp.scrape_url`) for JD extraction |
| 2026-05-06 | Migrated job URL discovery from Apify actors to Serper Google search |
| 2026-05-06 | Added LLM-based `companyName` extraction in `extract_job_team_info()` |
| 2026-05-06 | Increased job results cap: 5→10, per-source URLs: 5→10 |
| 2026-05-06 | Reduced POC profiles per job: 4→2 |
| 2026-05-06 | Updated ResultsTab header to "Job Results for You" |
| 2026-05-06 | Installed `firecrawl-py` in both global Python and `backend/venv` |
| 2026-05-06 | Removed reason text from UI job cards to clean up design |
| 2026-05-06 | Added filtering logic to avoid fetching generic company profiles masquerading as POCs |
| 2026-05-06 | Broadened Serper job board search to include Workday, ZohoRecruit, SmartRecruiters, and AshbyHQ |
| 2026-05-09 | Refactored Resume Parser LLM to strictly extract dates and offloaded duration/duplicate calculations to Python backend. |
| 2026-05-09 | Upgraded Metadata Parser to High-Precision Entity Resolution Agent (filters Ex-employees and Name-Company collisions). |
| 2026-05-09 | Refactored Job Validation to "Cynical Gatekeeper" persona with 3 strict hardware gates (Geo, Seniority, Remote). |
| 2026-05-09 | Switched JD validation agent to Qwen 3 32B via Groq and added `QWEN_API_KEY` mapping. |
| 2026-05-09 | Fixed Python date parser fallback bugs using `dateutil.parser` for perfectly accurate LLM date math overrides. |
| 2026-05-09 | Upgraded Email Drafting Agent to Tactical Career Coach persona with an integrated self-critique loop. |
| 2026-05-09 | Removed the standalone critique agent (`evaluate_email_draft`) to halve API latency and tokens. |
| 2026-05-09 | Reorganized all 4 LLM agents into `backend/agents/` folder (`resume_parser`, `jd_validator`, `metadata_parser`, `email_drafter`). |
| 2026-05-09 | Fixed a silent bug in `_call_llama_json` where `last_error` was not being returned on failure. |
| 2026-05-09 | **Silent Bug Sweep:** Added generic `Exception` handler to `_call_llama_json` (DNS/connection failures). |
| 2026-05-09 | **Silent Bug Sweep:** `call_serper()` in `main.py` now catches HTTP errors instead of crashing the SSE stream. |
| 2026-05-09 | **Silent Bug Sweep:** `metadata_parser.py` now catches API and parse errors, returns empty `{"profiles": []}` gracefully. |
| 2026-05-09 | **Silent Bug Sweep:** `jd_validator.py` now checks for `"error"` key in Qwen response and logs it. |
| 2026-05-09 | **Silent Bug Sweep:** `usage_tracker.py` — fixed relative USAGE_FILE path (broke on Vercel), removed hardcoded ALERTS_FILE, added crash-safe JSON reads/writes. |

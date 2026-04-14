# Project State Manifesto: Pathfinder

## 1. Project Essence
**Objective:** An AI-driven career discovery platform that automates the transition from resume parsing to job matching and personalized cold outreach.

**Tech Stack:**
- **Frontend:** React (Vite), TypeScript, Tailwind CSS, Lucide Icons, Shadcn UI.
- **Backend:** FastAPI (Python), Uvicorn, SSE (Server-Sent Events).
- **AI/LLMs:** Gemini (Resume parsing, Drafting), Groq/Llama-3 (JD validation).
- **External APIs:** Serper (Google Search for Jobs/Profiles), Hunter.io (Email discovery), Jina Reader (JD scraping).

## 2. Current Architecture & State
**File Map:**
- `src/pages/Index.tsx`: Orchestrates the tab-based flow (Home -> Profile -> Results -> Drafting).
- `src/lib/api.ts`: Centralized fetch logic with SSE support for streaming discovery.
- `backend/main.py`: Core API entry point; manages the complex job/POC discovery pipeline.
- `backend/evals.py`: LLM utility functions for parsing unstructured JDs and evaluating email quality.
- `backend/services/usage_tracker.py`: Monitors API limits for Serper/Hunter/Groq.

**Data Flow:**
1. **Extraction:** PDF Resume -> `backend/parse-resume` (Gemini) -> Structured JSON Profile.
2. **Discovery:** Profile -> `backend/discover-jobs` (Streaming SSE) -> Serper Job Search -> Jina JD Scraping -> Groq Validation -> Serper Profile Search -> Hunter Email Lookup.
3. **Drafting:** Selected POC + Profile -> `backend/draft-email` -> Serper News Search -> Gemini Email Gen -> LLM Quality Evaluation.

**Completed Milestones:**
- [x] Protocol-safe link handling (Prefixing `https://` for external career boards).
- [x] Streamed job matching with real-time UI updates.
- [x] Location-aware job searching (Country-wide discovery via Nominatim).
- [x] Contact-specific drafting (User can select a specific POC to draft for).

## 3. Active Context
**Current Logic:**
- **Tab Control:** State-locked navigation (`resumeUploaded` -> `profileConfirmed` -> `draftSelected`).
- **Discovery logic:** `/api/discover-jobs` yields individual `JobResult` objects as SSE events.
- **Link Handling:** `ResultsTab` & `DraftingTab` use protocol-aware prefixing to prevent relative routing errors.

**Known Constraints:**
- **Context Limits:** Gemini resume parsing limited to first 5000 characters.
- **API Throttling:** Usage tracker triggers warnings at 60% of free-tier limits.
- **Browser Geolocation:** Requires user permission; falls back to manual entry.

## 4. The "Next Step" Queue
**Immediate Task:** Correct the hardcoded `ALERTS_FILE` path in `backend/services/usage_tracker.py` to use a dynamic conversation-agnostic path (or a relative path within the project).

**Unresolved Bugs:**
- **Domain Heuristic:** Hunter.io email lookup currently assumes `companyname.com`, which fails for non-standard TLDs or subsidiary brands.
- **POC Validation:** Deep-level POC verification (filtering former employees) is requested but not fully hardened in the snippet parsing logic.

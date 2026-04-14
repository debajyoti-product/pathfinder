# Pathfinder

Pathfinder is an intelligent, AI-driven platform designed to automate the most tedious parts of the modern job search. By bridging the gap between resume parsing, real-time job discovery, and personalized outreach, Pathfinder empowers candidates to find and apply for roles seamlessly.

## Overview

### The Problem
The current job market requires candidates to manually search through dozens of boards, parse dense job descriptions for relevance, find key stakeholders (Points of Contact), and craft hundreds of personalized "cold" emails. This process is fragmented, time-consuming, and prone to "application fatigue."

### The Solution
Pathfinder automates this entire lifecycle:
1.  **Extracts** structured data from messy PDF resumes.
2.  **Discovers** high-relevance job postings across the web via real-time search.
3.  **Validates** matches using LLM-grade scoring (Match > 0.7).
4.  **Enriches** data by finding verified emails for hiring managers.
5.  **Drafts** personalized outreach based on the candidate's unique profile and company news.


### Core User Flow
```mermaid
graph TD
    A[PDF Resume] -->|PDF Parsing| B(llama 3.3: Structured Profile)
    B -->|Serper API| C(Job Discovery Engine)
    C -->|SSE Streaming| D{llama 3.3: Match Validation}
    D -->|Passed| E(Hunter.io: POC Discovery)
    E -->|Verified Email| F(Claude 3.1 haiku: Personalized Draft)
    F -->|Validation| G[Candidate Outreach Ready]


---

## 💻 Tech Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | React (Vite), TypeScript, Tailwind CSS, Shadcn UI, Lucide Icons |
| **Backend** | FastAPI (Python), Uvicorn, Server-Sent Events (SSE) |
| **Generative AI**| Claude Haiku 3.1, Groq (Llama-3.3-70b-versatile) |
| **External APIs**| Serper (Search), Hunter.io (Emails), Jina reader (Web Scraping) |

---

## 🚀 Getting Started

### Prerequisites
*   Node.js (v18+)
*   Python 3.10+
*   API Keys: Claude, Groq, Serper, Hunter.io

## 📂 Project Organization

```text
├── backend/
│   ├── main.py            # API Gateway & SSE Routing
│   ├── evals.py           # LLM logic for JD matching & drafting
│   ├── services/          # usage_tracker, email_services, etc.
│   └── config.py          # API Key Management
├── src/
│   ├── pages/             # Main Application Tabs (Index.tsx)
│   ├── components/        # Shadcn/Custom UI Components
│   └── lib/api.ts         # SSE & Fetch handlers
└── context.md             # Project State Manifesto (Dev Reference)

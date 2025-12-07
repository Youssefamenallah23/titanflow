# TitanFlow: Autonomous AI Sales Agent 🚀

TitanFlow is an Agentic AI system designed to automate the inbound sales lifecycle. It acts as a gatekeeper, analyst, and CRM manager, capable of reading complex PDFs, verifying service pricing against an internal database, scoring leads based on business logic, and drafting personalized responses.

**Role:** AI Systems Engineering Portfolio  
**Status:** v1.0 (Local Containerized Deployment)

---

## 🏗 Architecture

The system follows a **Microservices Architecture** orchestrated by Docker:

1.  **The Orchestrator (n8n):** Handles the event triggers (Email/Webhooks), initial classification, and communication channels (Slack/Gmail).
2.  **The Brain (FastAPI + Python):** A custom containerized API that hosts the reasoning engine.
3.  **The Intelligence (Gemini 2.5 Flash):** Used for decision-making and context generation.
4.  **The Protocol (MCP - Model Context Protocol):**
    *   Connects the AI to a local **SQLite Database**.
    *   Provides tools for **Lead Scoring** (Business Logic).
    *   Provides tools for **Write-Back** (Saving qualified leads to the CRM).

### 🔄 The Workflow Flow
1.  **Ingestion:** Listens for emails containing "RFP" (Request for Proposal).
2.  **Classification:** Gemini Flash classifies the email intent.
3.  **Deep Analysis:**
    *   Python Brain extracts text from the attached PDF.
    *   **Tool Call 1:** Checks `pricing.db` to see if we offer the service.
    *   **Tool Call 2:** Calculates a "VIP Score" based on client industry.
    *   **Tool Call 3:** If Approved, executes a SQL `INSERT` to save the lead.
4.  **Action:**
    *   **Approved:** Sends VIP Alert to Slack + Drafts Quote Email.
    *   **Declined:** Auto-replies with valid service list.

---

## 🛠 Tech Stack

- **Language:** Python 3.11 (FastAPI, Uvicorn)
- **AI Framework:** Google Gemini 2.5 Flash (via Google Generative AI SDK)
- **Tooling Standard:** Model Context Protocol (MCP) by Anthropic
- **Database:** SQLite (Embedded relational data)
- **Orchestration:** n8n (Dockerized)
- **Containerization:** Docker & Docker Compose

---

## 🚀 How to Run Locally

### Prerequisites
- Docker Desktop installed.
- A Google Gemini API Key.

### Installation

1. **Clone the Repo**
   ```bash
   git clone https://github.com/YOUR_USERNAME/titanflow.git
   cd titanflow

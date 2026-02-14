# Intelligent HR Recruitment Platform

## Overview

Welcome to the **Intelligent HR Recruitment Platform**, a cutting-edge application powered by multi-agent AI (using LangGraph) to streamline and automate the entire recruitment lifecycle.

This platform simulates a real-world HR team with two specialized AI agents working together under a Supervisor:

1.  **Lead Recruiter Agent**: Focuses on candidate analysis, parsing CVs, extracting skills, and ranking applicants against job descriptions.
2.  **Hiring Manager Agent**: Handles the "hiring" side, including generating job offers, checking market salaries, retrieving company templates, and drafting communication.

## Key Features

### 🔍 Candidate Analysis (Recruiter Agent)
-   **CV Parsing**: diverse support for PDF and DOCX formats.
-   **Skill Extraction**: Automatically identifies technical skills, years of experience, and education.
-   **Smart Ranking**: Users semantic search (embeddings) to rank candidates based on job relevance, not just keyword matching.
-   **Bias Reduction**: Integrated PII anonymization (removes names/emails/phones) for fair screening.

### 📝 Hiring & Operations (Manager Agent)
-   **Job Offer Generator**: Creates professional offer letters using company templates.
-   **Market Salary Check**: Provides real-time salary ranges and recommendations for common tech roles.
-   **Template Retrieval**: Intelligently searches the company knowledge base for relevant policy/benefit documents.
-   **Email Drafting**: Composes interview invitations and rejection emails automatically.

## How to Run

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Prepare Knowledge Base (Optional)**:
    Populate the system with company data (templates, values).
    ```bash
    python scripts/ingest_knowledge.py
    ```

3.  **Launch the Application**:
    ```bash
    .\run_app.bat
    ```
    *Or manually:*
    ```bash
    python -m streamlit run app.py
    ```
    *(Note: Use `python -m streamlit` to avoid path issues on Windows)*

## Architecture

The system is built on **LangGraph** with a Supervisor-Worker architecture:

-   **Supervisor**: Routes user requests (e.g., "Analyze this CV" -> Recruiter, "Draft an offer" -> Manager).
-   **State**: Shared context (messages, job details) is passed between agents.
-   **Tools**: Each agent possesses specialized tools (Scrapers, Parsers, Vector DB Retrievers).

## Contact

Developed by the **Integration Project Team**.
For support or inquiries, please contact the development team.

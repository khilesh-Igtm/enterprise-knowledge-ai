# Enterprise Knowledge AI

A multi-tenant document intelligence platform powered by
Retrieval-Augmented Generation (RAG).

## Features (Planned)

- Multi-user authentication
- Knowledge base management
- PDF, DOCX and TXT document uploads
- Asynchronous document processing
- Document chunking and embeddings
- Semantic vector search
- AI-powered document conversations
- Source citations and page references
- Conversation history
- User-level data isolation

## Tech Stack

### Backend
- Python 3.12+
- FastAPI
- SQLAlchemy 2
- Alembic
- Pydantic Settings

### Infrastructure
- PostgreSQL
- Redis
- Qdrant
- Docker Compose

### Frontend
- Next.js
- TypeScript

## Project Structure

enterprise-knowledge-ai/
├── apps/
│   ├── api/
│   │   ├── app/
│   │   │   ├── api/
│   │   │   ├── core/
│   │   │   ├── db/
│   │   │   ├── integrations/
│   │   │   └── main.py
│   │   ├── alembic/
│   │   ├── tests/
│   │   ├── pyproject.toml
│   │   └── alembic.ini
│   └── web/
├── infrastructure/
│   └── docker-compose.yml
├── docs/
├── .env.example
├── .gitignore
└── README.md

## Prerequisites

- Python 3.12+
- uv
- Docker Desktop
- Node.js 20+
- Git

## Local Development

### 1. Clone repository

```bash
git clone <repository-url>
cd enterprise-knowledge-ai
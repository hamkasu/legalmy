# LegalMY — Malaysian Legal Research & Analytics Platform

A cutting-edge SaaS platform for Malaysian legal professionals to search, analyse, and understand court judgments, judges, and legislation. Built with Flask, PostgreSQL, and Anthropic's Claude API.

## Features

- **Judgment Search**: Full-text + AI semantic search across Malaysian courts (Federal, Appeal, High, Sessions, Magistrates, Industrial, Syariah)
- **Judge Analytics**: Analyse ruling patterns, win rates, and landmark decisions by judge
- **AI Legal Tools**: Case analysers, judgment summarisers, argument generators, and more
- **Legislation Browser**: All Acts of Malaysia with case cross-references and AI explanations
- **Citation Graph**: Visualise how cases connect and precedent relationships
- **Alerts**: Monitor new judgments matching your practice areas

## Tech Stack

- **Backend**: Flask 3.0 (Python)
- **Database**: PostgreSQL 14+ with pgvector for semantic search
- **API**: Anthropic Claude Sonnet 4.6
- **Task Queue**: Celery + Redis
- **Deployment**: Railway.app
- **Frontend**: Jinja2 templates with Chart.js and D3.js

## Project Structure

```
legalmy/
├── app/
│   ├── __init__.py              # Flask app factory
│   ├── config.py                # Configuration classes
│   ├── extensions.py            # Flask extensions
│   ├── models/                  # SQLAlchemy models
│   ├── blueprints/              # Flask blueprints (auth, search, judgments, etc.)
│   ├── services/                # Business logic (search, ingest, analytics)
│   ├── templates/               # Jinja2 templates
│   └── static/                  # CSS, JS, assets
├── migrations/                  # Alembic migrations
├── tests/                       # Pytest tests
├── requirements.txt             # Python dependencies
├── Procfile                     # Heroku/Railway deployment
├── railway.toml                 # Railway.app config
├── celery_worker.py             # Celery worker entry point
└── wsgi.py                      # WSGI entry point
```

## Quick Start

### Prerequisites

- Python 3.10+
- PostgreSQL 14+
- Redis 6+
- Anthropic API key

### Installation

1. Clone the repository
   ```bash
   git clone https://github.com/hamkasu/legalmy.git
   cd legalmy
   ```

2. Create a virtual environment
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. Initialize the database
   ```bash
   flask db upgrade
   ```

6. Run the development server
   ```bash
   flask run
   ```

   The app will be available at `http://localhost:5000`

## Development

### Running Celery worker
```bash
celery -A celery_worker worker --loglevel=info
```

### Running tests
```bash
pytest
```

### Creating migrations
```bash
flask db migrate -m "description"
flask db upgrade
```

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for Railway deployment instructions.

## Build Roadmap (Prompts)

- [x] Prompt 01: Project Scaffold & Repository Structure
- [ ] Prompt 02: Database Models (SQLAlchemy)
- [ ] Prompt 03: Data Ingestion Pipeline
- [ ] Prompt 04: Search Engine (Full-text + Semantic)
- [ ] Prompt 05: Judge Analytics Module
- [ ] Prompt 06: AI Tools Suite
- [ ] Prompt 07: Legislation Browser
- [ ] Prompt 08: User Authentication & Subscription System
- [ ] Prompt 09: Dashboard & Alerts
- [ ] Prompt 10: Public REST API
- [ ] Prompt 11: Landing Page & Marketing Site
- [ ] Prompt 12: Admin Panel & Data Quality Dashboard
- [ ] Prompt 13: Citation Graph Visualisation
- [ ] Prompt 14: Testing, Error Handling & Deployment

## License

Proprietary — Calmic Sdn Bhd

## Contributing

Contact the development team at Calmic for contribution guidelines.
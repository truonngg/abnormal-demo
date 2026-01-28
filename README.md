# AI-Enhanced Incident Communications Assistant

An intelligent system that generates customer-appropriate incident status updates from raw technical signals, helping incident commanders communicate faster and more effectively during production incidents.

## 🎯 Overview

This application processes incident data from multiple sources (PagerDuty, logs, metrics, deployments, Slack threads) and generates clear, consistent, customer-facing status update drafts with quality evaluation and evidence tracing.

### Key Features

- **Multi-source data ingestion**: Parse incident signals from PagerDuty, CloudWatch, Prometheus, GitHub, and Slack
- **Phase-aware draft generation**: Select the incident phase/status and generate an appropriate status update draft (UI currently supports **Investigating** and **Identified**)
- **Quality evaluation**: Deterministic guardrails + LLM-as-Judge scoring across 5 dimensions
- **LLM-as-Judge model**: gpt-4o-mini
- **Evidence tracing**: See what data supports each claim in the generated draft
- **Confidence scoring**: Get transparency into draft quality and reliability

## 🏗️ Architecture

```
┌─────────────────┐
│  User Browser   │
└────────┬────────┘
         │ HTTP
         ▼
┌─────────────────────┐
│ Streamlit Frontend  │  Port 8501
│  - File Upload      │
│  - Draft Display    │
│  - Quality Scores   │
└────────┬────────────┘
         │ REST API
         ▼
┌─────────────────────┐
│  FastAPI Backend    │  Port 8000
│  - /api/generate-draft │
│  - /health          │
└────────┬────────────┘
         │
    ┌────┴──────┬──────────────┐
    ▼           ▼              ▼
┌─────────┐ ┌──────────┐ ┌─────────┐
│Ingestion│ │Generator │ │Evaluator│
│ Service │ │ Service  │ │ Service │
└─────────┘ └──────────┘ └─────────┘
                │
                ▼
         ┌─────────────┐
         │ OpenAI API  │
         │(or OpenRouter│
         │ compatible) │
         └─────────────┘
```

## 📁 Project Structure

```
abnormal-demo/
├── backend/                    # FastAPI backend service
│   ├── main.py                # API entry point
│   ├── api/
│   │   └── routes.py          # API endpoints
│   ├── models/
│   │   └── schemas.py         # Pydantic models
│   ├── services/
│   │   ├── ingestion.py       # Data parsing & normalization
│   │   ├── generator.py       # LLM draft generation
│   │   └── evaluator.py       # Quality evaluation
│   └── requirements.txt
├── frontend/                   # Streamlit frontend
│   ├── app.py                 # Main UI application
│   ├── components/
│   │   ├── upload.py          # File upload widget
│   │   ├── display.py         # Results display
│   │   └── sidebar.py         # Configuration sidebar
│   └── requirements.txt
├── data/data/                  # Sample incident data
│   ├── incident_context.txt
│   ├── cloudwatch_logs.json
│   ├── prometheus_metrics.json
│   ├── pagerduty_incident.json
│   ├── github_deployments.json
│   └── status_page_examples.md
├── .env.example               # Environment variable template
├── .gitignore
└── README.md                  # This file
```

## 🚀 Getting Started

### Prerequisites

- Python 3.9 or higher
- pip (Python package installer)
- OpenAI API key (or OpenRouter API key)

### Installation

1. **Clone the repository**
   ```bash
   cd abnormal-demo
   ```

2. **Create and activate a virtual environment** (recommended)
   ```bash
   # Create virtual environment
   python3 -m venv venv
   
   # Activate it
   source venv/bin/activate  # macOS/Linux
   # or: venv\Scripts\activate  # Windows
   ```
   
   You should see `(venv)` in your terminal prompt when activated.

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your_actual_api_key_here
   OPENAI_BASE_URL=https://openrouter.ai/api/v1
   ```

4. **Install backend dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   cd ..
   ```

5. **Install frontend dependencies**
   ```bash
   cd frontend
   pip install -r requirements.txt
   cd ..
   ```

> **Note**: Keep the virtual environment activated for all subsequent commands. If you close your terminal, you'll need to reactivate it with `source venv/bin/activate`.

### Running the Application

You'll need two terminal windows - one for the backend and one for the frontend.

**Terminal 1 - Start the Backend:**
```bash
# Make sure you're in the project root directory (abnormal-demo/)
# and virtual environment is activated
uvicorn backend.main:app --reload --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

**Terminal 2 - Start the Frontend:**
```bash
cd frontend
streamlit run app.py
```

Streamlit will automatically open your browser to `http://localhost:8501`

### Using the Application

1. **Select incident phase/status**: Choose the current phase (currently supports **Investigating** and **Identified**)
2. **Upload incident data**: Use the file uploader or click "Quick Load: Use Sample Data" to load the provided incident files
3. **Generate draft**: Click "Generate Draft" to create a phase-appropriate status update
4. **Review results**: Examine the draft, evaluation results, and evidence trace
5. **Copy and use**: Copy the draft text to post on your status page

## 🔧 API Documentation

Once the backend is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### Available Endpoints

- `GET /health` - Health check
- `POST /api/generate-draft` - Generate status update draft
- `GET /api/status-examples` - Fetch example status page messages

## 📊 Data Sources

The application ingests data from multiple sources:

| File | Description | Purpose |
|------|-------------|---------|
| `incident_context.txt` | Slack thread excerpts, engineer notes | Timeline, affected services, root cause hypotheses |
| `cloudwatch_logs.json` | Application error logs | Error frequency, failure modes |
| `prometheus_metrics.json` | Performance metrics | Latency spikes, error rates |
| `pagerduty_incident.json` | Alert metadata | Severity, incident timing |
| `github_deployments.json` | Deployment history | Recent changes, potential causes |

## 🧪 Development

### Backend Development

Run with auto-reload:
```bash
# Run from the project root so Python treats `backend/` as a package.
# This avoids relative-import errors like:
# "ImportError: attempted relative import with no known parent package"
uvicorn backend.main:app --reload --port 8000
```

Run tests:
```bash
pytest
```

### Frontend Development

Streamlit auto-reloads on file changes:
```bash
cd frontend
streamlit run app.py
```

## 🎯 Current MVP Scope

This prototype focuses on:

✅ **Implemented:**
- Multi-source data ingestion
- LLM-powered evidence extraction
- LLM-powered draft generation (generator supports all four phases; UI exposes Investigating + Identified)
- Quality evaluation (deterministic checks + LLM-as-Judge)
- Evidence tracing / grounding (per-claim source mappings)
- Web-based UI

🚧 **Placeholder (for future implementation):**
- Advanced timestamp correlation
- Sophisticated symptom extraction
- Support additional phases in the UI (Monitoring, Resolved)

## 📝 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI/OpenRouter API key | (required) |
| `OPENAI_BASE_URL` | API base URL | `https://openrouter.ai/api/v1` |
| `BACKEND_PORT` | Backend server port | `8000` |
| `FRONTEND_PORT` | Frontend server port | `8501` |

## 🔒 Security Notes

- Never commit `.env` file (it's in `.gitignore`)
- API keys should be kept secret
- The application checks for internal information leakage in drafts
- Sample data has been anonymized

## 🐛 Troubleshooting

### Virtual environment issues
- **"Command not found" errors**: Make sure the virtual environment is activated (`source venv/bin/activate`)
- **Wrong Python version**: Create venv with specific version: `python3.9 -m venv venv`
- **To deactivate**: Run `deactivate` in your terminal

### Backend won't start
- **Import errors (e.g., "Could not import module 'main'" or "attempted relative import with no known parent package")**:
  Make sure you're running uvicorn from the **project root** directory (not from inside `backend/`), so `backend/` is treated as a package:
  ```bash
  # Correct (from project root):
  uvicorn backend.main:app --reload --port 8000
  
  # Incorrect (from backend/ directory):
  cd backend && uvicorn main:app --reload  # This won't work!
  ```
- Check that port 8000 is not already in use: `lsof -i :8000` (macOS/Linux)
- Verify all dependencies are installed: `pip install -r backend/requirements.txt`
- Ensure Python 3.9+ is being used: `python --version`
- Make sure virtual environment is activated (you should see `(venv)` in prompt)

### Frontend won't connect to backend
- Verify backend is running at http://localhost:8000
- Check the backend URL in the sidebar configuration
- Look for CORS errors in browser console

### "Cannot connect to backend" error
- Start the backend first before starting the frontend
- Make sure the backend health check returns 200: `curl http://localhost:8000/health`

### Import errors or module not found
- Verify you're in the correct directory (backend/ or frontend/)
- Check that virtual environment is activated
- Reinstall dependencies: `pip install -r requirements.txt`

## 📚 Additional Documentation

- [Product Requirements Document]([Abnormal] Take Home.md) - Detailed product vision and requirements
- [Take-Home Instructions](TAKEHOME_README.md) - Original assignment details
- [Data README](data/data/README.md) - Detailed description of incident data files
- [Status Page Examples](data/data/status_page_examples.md) - Example messages for tone/style

## 🎥 Demo Video

[Link to demo video to be added]

## 🚦 Roadmap

### Phase 1: Crawl (Current MVP)
- ✅ Basic data ingestion
- ✅ Phase selection (Investigating + Identified)
- ✅ LLM evidence extraction → LLM draft generation
- ✅ Quality evaluation (deterministic checks + LLM-as-Judge)
- ✅ Evidence grounding / transparency (evidence mappings, internal-term avoidance)

### Phase 2: Walk
- Broaden to higher-severity incidents and support additional phases (Monitoring, Resolved) while maintaining evidence grounding
- Improve signal extraction/correlation reliability via feedback loops from human edits and post-incident reviews
- Add richer edit/refinement workflows (e.g., guided revisions without full regeneration, edits with AI)

### Phase 3: Run
- Fully embed into incident response workflows with real-time / near real-time ingestion
- Native integrations with incident tooling (e.g., Slack, PagerDuty) and status page publishing
- Automated “surgical fixes” and stronger confidence controls using LLM-as-Judge + guardrails
- Full incident communication lifecycle across all phases, with continuous improvement/analytics

## 📄 License

This is a prototype built for evaluation purposes.

## 👤 Author

Truong Nguyen


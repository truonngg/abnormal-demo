"""FastAPI application entry point."""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import routes
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = FastAPI(
    title="AI-Enhanced Incident Communications API",
    description="Backend service for generating customer-appropriate incident status updates",
    version="0.1.0",
)

# Configure CORS to allow Streamlit frontend
allowed_origins = [
    "http://localhost:8501",  # Streamlit default port
    "http://127.0.0.1:8501",
]

# Add frontend URL from environment if provided (for Railway deployment)
if frontend_url := os.getenv("FRONTEND_URL"):
    allowed_origins.append(frontend_url)

# For demo purposes, also allow Railway's auto-generated URLs
# Railway URLs follow pattern: https://*.up.railway.app
if railway_url := os.getenv("RAILWAY_PUBLIC_DOMAIN"):
    allowed_origins.append(f"https://{railway_url}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(routes.router, prefix="/api")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "incident-comms-api"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

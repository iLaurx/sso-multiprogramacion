from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="SSO - Multiprogramacion")

@app.get("/api/health")
def health():
    return {"status": "ok"}

frontend = Path(__file__).resolve().parents[1] / "frontend"
app.mount("/", StaticFiles(directory=frontend, html=True),
        name="frontend")
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from backend.routes import router as simulations_router
from backend.service import SimulationService

def create_app(auto_clock: bool = True) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.service = SimulationService(auto_clock=auto_clock)
        yield
        await app.state.service.close()

    app = FastAPI(title="SSO Multiprogramación", lifespan=lifespan)

    @app.get("/api/health")
    def health():
        return {"status": "ok"}

    app.include_router(simulations_router)
    app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
    
    return app

app = create_app(auto_clock=True)
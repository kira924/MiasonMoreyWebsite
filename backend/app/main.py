from fastapi import FastAPI
from app.api import auth

# Initialize FastAPI application
app = FastAPI(title="Maison Morey API")

# Include all module routers
app.include_router(auth.router)
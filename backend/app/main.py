from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, products, addresses

# Initialize FastAPI application
app = FastAPI(title="Maison Morey API")

# Configure CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"], 
)

# Include all module routers
app.include_router(auth.router)
app.include_router(products.router)
app.include_router(addresses.router)
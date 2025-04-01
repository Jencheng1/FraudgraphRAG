from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import router
from ..core.database import db_manager

app = FastAPI(
    title="Fraud Detection System",
    description="Graph-based fraud detection system using GraphRAG and GNN",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router, prefix="/api/v1")

@app.on_event("startup")
async def startup_event():
    """Initialize database connections on startup"""
    if not db_manager.verify_connections():
        raise Exception("Failed to connect to databases")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up database connections on shutdown"""
    db_manager.close_neo4j()

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to the Fraud Detection System API",
        "version": "1.0.0",
        "status": "operational"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "database_connections": {
            "neo4j": db_manager.neo4j_driver is not None,
            "supabase": db_manager.supabase is not None
        }
    } 
from fastapi import APIRouter

from app.api.v1 import auth, documents, health, knowledge_bases

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(knowledge_bases.router)
api_router.include_router(documents.router)

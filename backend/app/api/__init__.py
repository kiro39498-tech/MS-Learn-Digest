from fastapi import APIRouter
from . import auth, users, topics, teams, newsletters, digests, admin, learning

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(topics.router, prefix="/topics", tags=["topics"])
api_router.include_router(teams.router, prefix="/teams", tags=["teams"])
api_router.include_router(newsletters.router, prefix="/newsletters", tags=["newsletters"])
api_router.include_router(digests.router, prefix="/digests", tags=["digests"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(learning.router, prefix="/learning", tags=["learning"])

from fastapi import APIRouter

from app.api.v1.endpoints import auth_controller, credentials_controller, aws_controller

api_router = APIRouter()

api_router.include_router(auth_controller.router, tags=["auth"])
api_router.include_router(aws_controller.router, tags=["aws"])
api_router.include_router(credentials_controller.router)
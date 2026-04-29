"""API v1 routes."""
from fastapi import APIRouter

api_router = APIRouter()

# Individual routers are imported and included on demand.
# The datasource router is always available.
# Other routers (auth, students, predictions, etc.) require
# sqlalchemy and are included when the full DB stack is running.

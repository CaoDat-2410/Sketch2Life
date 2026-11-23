"""Implemented Admin additions to the older FE API projection."""

from fastapi.routing import APIRoute

from sketch2life.interfaces.http.routers.lesson_feedback import router as feedback
from sketch2life.interfaces.http.routers.password_recovery import router as recovery
from sketch2life.interfaces.http.routers.platform_admin import router as admin
from sketch2life.interfaces.http.routers.platform_admin_accounts import router as accounts

ADMIN_OPERATIONS = frozenset(
    (method.lower(), route.path)
    for router in (admin, accounts, recovery, feedback)
    for route in router.routes
    if isinstance(route, APIRoute)
    for method in route.methods
)
ADMIN_OPERATIONS = ADMIN_OPERATIONS | {("get", "/api/auth/v1/me")}

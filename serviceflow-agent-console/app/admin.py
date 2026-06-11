from __future__ import annotations

from fastapi import APIRouter

from app.admin_routes.conversations import router as conversations_router
from app.admin_routes.feedback_metrics import router as feedback_metrics_router
from app.admin_routes.knowledge import router as knowledge_router
from app.admin_routes.tickets import router as tickets_router
from app.admin_routes.traces_reports import router as traces_reports_router

router = APIRouter()

# 后台管理能力按业务域拆分，主入口只负责聚合路由，避免 admin.py 继续膨胀。
router.include_router(conversations_router)
router.include_router(tickets_router)
router.include_router(knowledge_router)
router.include_router(feedback_metrics_router)
router.include_router(traces_reports_router)

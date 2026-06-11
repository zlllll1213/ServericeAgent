from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.admin_routes.common import REPORTS_DIR, PROJECT_ROOT, not_found
from app.agent.persistence import decode_json
from app.database import get_db
from app.models import AgentTrace

router = APIRouter()


@router.get("/admin/traces")
def list_agent_traces(
    conversation_id: str | None = None,
    trace_id: str | None = None,
    node_name: str | None = None,
    success: bool | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    query = db.query(AgentTrace)
    if conversation_id:
        query = query.filter(AgentTrace.conversation_id == conversation_id)
    if trace_id:
        query = query.filter(AgentTrace.trace_id == trace_id)
    if node_name:
        query = query.filter(AgentTrace.node_name == node_name)
    if success is not None:
        query = query.filter(AgentTrace.success == success)
    rows = query.order_by(AgentTrace.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return [trace.to_dict() for trace in rows]


@router.get("/admin/traces/{trace_id}")
def get_agent_trace_chain(trace_id: str, db: Session = Depends(get_db)):
    rows = db.query(AgentTrace).filter(AgentTrace.trace_id == trace_id).order_by(AgentTrace.id.asc()).all()
    if not rows:
        not_found("Trace")
    items = []
    for row in rows:
        data = row.to_dict()
        data["input_state"] = decode_json(row.input_state, {})
        data["output_state"] = decode_json(row.output_state, {})
        items.append(data)
    return {"trace_id": trace_id, "nodes": items}


@router.get("/admin/evaluation-reports")
def list_evaluation_reports():
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    reports = sorted(REPORTS_DIR.glob("eval_report_*.md"), key=lambda item: item.stat().st_mtime, reverse=True)
    return [
        {
            "filename": item.name,
            "path": str(item.relative_to(PROJECT_ROOT)),
            "updated_at": datetime.fromtimestamp(item.stat().st_mtime).isoformat(),
            "size": item.stat().st_size,
        }
        for item in reports[:20]
    ]


@router.get("/admin/evaluation-reports/latest")
def get_latest_evaluation_report():
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    reports = sorted(REPORTS_DIR.glob("eval_report_*.md"), key=lambda item: item.stat().st_mtime, reverse=True)
    if not reports:
        return {"filename": None, "content": "暂无评测报告，请先执行 make eval。", "download_url": None}
    latest = reports[0]
    return {
        "filename": latest.name,
        "content": latest.read_text(encoding="utf-8"),
        "download_url": f"/api/admin/evaluation-reports/{latest.name}/download",
    }


@router.get("/admin/evaluation-reports/{filename}/download")
def download_evaluation_report(filename: str):
    if "/" in filename or "\\" in filename or not filename.startswith("eval_report_") or not filename.endswith(".md"):
        raise HTTPException(status_code=400, detail="非法报告文件名")
    path = REPORTS_DIR / filename
    if not path.exists():
        not_found("评测报告")
    return FileResponse(path, media_type="text/markdown", filename=filename)

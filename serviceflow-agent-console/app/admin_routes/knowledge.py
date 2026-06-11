from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter
from sqlalchemy import or_

from app.admin_routes.common import doc_id_from_title, not_found, reindex_best_effort, write_knowledge_file
from app.config import KNOWLEDGE_BASE_DIR
from app.database import SessionLocal
from app.models import KnowledgeDocument
from app.schemas import KnowledgeDocumentCreate, KnowledgeDocumentUpdate

router = APIRouter()


@router.get("/admin/knowledge-documents")
def list_knowledge_documents(knowledge_base: str | None = None, status: str | None = None, keyword: str | None = None):
    with SessionLocal() as db:
        query = db.query(KnowledgeDocument)
        if knowledge_base:
            query = query.filter(KnowledgeDocument.knowledge_base == knowledge_base)
        if status:
            query = query.filter(KnowledgeDocument.status == status)
        if keyword:
            like = f"%{keyword}%"
            query = query.filter(or_(KnowledgeDocument.title.like(like), KnowledgeDocument.content.like(like)))
        return [doc.to_dict() for doc in query.order_by(KnowledgeDocument.updated_at.desc()).all()]


@router.post("/admin/knowledge-documents")
def create_knowledge_document(request: KnowledgeDocumentCreate):
    now = datetime.now()
    doc_id = doc_id_from_title(request.title)
    with SessionLocal() as db:
        suffix = 1
        base_doc_id = doc_id
        while db.query(KnowledgeDocument).filter(KnowledgeDocument.doc_id == doc_id).first():
            suffix += 1
            doc_id = f"{base_doc_id}_{suffix}"
        doc = KnowledgeDocument(
            doc_id=doc_id,
            title=request.title,
            knowledge_base=request.knowledge_base,
            source_file=None,
            content=request.content,
            status="DRAFT",
            version=1,
            created_by=request.created_by,
            created_at=now,
            updated_at=now,
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        return doc.to_dict()


@router.put("/admin/knowledge-documents/{doc_id}")
def update_knowledge_document(doc_id: str, request: KnowledgeDocumentUpdate):
    with SessionLocal() as db:
        doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.doc_id == doc_id).first()
        if doc is None:
            not_found("知识库文档")
        if request.title is not None:
            doc.title = request.title
        if request.content is not None:
            doc.content = request.content
        if request.knowledge_base is not None:
            doc.knowledge_base = request.knowledge_base
        doc.version += 1
        doc.updated_at = datetime.now()
        db.commit()
        db.refresh(doc)
        return doc.to_dict()


@router.post("/admin/knowledge-documents/{doc_id}/publish")
def publish_knowledge_document(doc_id: str):
    with SessionLocal() as db:
        doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.doc_id == doc_id).first()
        if doc is None:
            not_found("知识库文档")
        path = write_knowledge_file(doc)
        doc.source_file = str(path.relative_to(KNOWLEDGE_BASE_DIR.parent))
        doc.status = "PUBLISHED"
        doc.updated_at = datetime.now()
        db.commit()
        db.refresh(doc)
    reindex_best_effort()
    return doc.to_dict()


@router.post("/admin/knowledge-documents/{doc_id}/archive")
def archive_knowledge_document(doc_id: str):
    with SessionLocal() as db:
        doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.doc_id == doc_id).first()
        if doc is None:
            not_found("知识库文档")
        doc.status = "ARCHIVED"
        doc.updated_at = datetime.now()
        db.commit()
        db.refresh(doc)
        return doc.to_dict()


@router.post("/admin/knowledge-documents/reindex")
def reindex_knowledge_documents():
    return {"success": True, "indexed_chunks": reindex_best_effort()}


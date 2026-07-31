from __future__ import annotations

import os, tempfile

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models import Document, Project
from app.schemas import DocumentRead

router = APIRouter()

SERVE_DIR = os.path.join(tempfile.gettempdir(), "erp_platform_files")
os.makedirs(SERVE_DIR, exist_ok=True)


@router.get("/files/{filename}")
async def download_file(filename: str):
    """Serve generated files (PPTX, XLSX, etc.) from temp directory."""
    file_path = os.path.join(SERVE_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    ext = os.path.splitext(filename)[1].lower()
    media_types = {".pptx": "application/vnd.openxmlformats-officedocument.presentationml.document", ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", ".pdf": "application/pdf", ".json": "application/json"}
    return FileResponse(file_path, media_type=media_types.get(ext, "application/octet-stream"), filename=filename)


@router.post("/{project_id}/documents", response_model=DocumentRead, status_code=201)
async def upload_document(
    project_id: str,
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
):
    project = (await db.execute(select(Project).where(Project.id == project_id))).scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    content = await file.read()
    filename = file.filename or "unknown"
    minio_key = f"projects/{project_id}/{filename}"

    # Save file to disk so parse_document can read it
    project_dir = os.path.join(SERVE_DIR, "uploads", project_id)
    os.makedirs(project_dir, exist_ok=True)
    file_path = os.path.join(project_dir, filename)
    with open(file_path, "wb") as f:
        f.write(content)

    doc = Document(
        project_id=project_id,
        filename=filename,
        minio_key=file_path,  # Use actual file path for parse_document
        mime_type=file.content_type,
        size_bytes=len(content),
        doc_type="requirement",
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    return doc


@router.get("/{project_id}/documents", response_model=list[DocumentRead])
async def list_documents(project_id: str, db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(Document).where(Document.project_id == project_id))).scalars().all()
    return [DocumentRead.model_validate(r) for r in rows]

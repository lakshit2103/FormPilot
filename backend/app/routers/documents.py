from __future__ import annotations

import uuid
from typing import List

from fastapi import APIRouter, Form, UploadFile, status
from fastapi.responses import FileResponse

from app.deps import DBSession, VerifiedUser
from app.schemas.documents import DocumentResponse
from app.services.document_service import document_service

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    document_type: str = Form(...),
    file: UploadFile = ...,
    current_user: VerifiedUser = ...,
    db: DBSession = ...,
):
    return await document_service.upload(db, current_user.id, document_type, file)


@router.get("", response_model=List[DocumentResponse])
async def list_documents(current_user: VerifiedUser, db: DBSession):
    return await document_service.list_documents(db, current_user.id)


@router.patch("/{doc_id}/set-default", response_model=DocumentResponse)
async def set_default(doc_id: uuid.UUID, current_user: VerifiedUser, db: DBSession):
    return await document_service.set_default(db, current_user.id, doc_id)


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(doc_id: uuid.UUID, current_user: VerifiedUser, db: DBSession):
    await document_service.delete_document(db, current_user.id, doc_id)


@router.get("/{doc_id}/download")
async def download_document(doc_id: uuid.UUID, current_user: VerifiedUser, db: DBSession):
    path = await document_service.get_file_path(db, current_user.id, doc_id)
    return FileResponse(path=path, filename=path.split("/")[-1])

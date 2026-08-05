from __future__ import annotations

import os
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.models.documents import Document

ALLOWED_TYPES = {
    "resume": ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"],
    "cover_letter": ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"],
    "photograph": ["image/jpeg", "image/png", "image/webp"],
    "signature": ["image/jpeg", "image/png", "image/webp"],
    "marksheet": ["application/pdf", "image/jpeg", "image/png"],
    "degree_cert": ["application/pdf", "image/jpeg", "image/png"],
    "internship_cert": ["application/pdf", "image/jpeg", "image/png"],
    "experience_letter": ["application/pdf", "image/jpeg", "image/png"],
    "portfolio": ["application/pdf"],
    "other": ["application/pdf", "image/jpeg", "image/png", "image/webp",
               "application/vnd.openxmlformats-officedocument.wordprocessingml.document"],
}


class DocumentService:

    def _get_upload_dir(self, user_id: uuid.UUID) -> Path:
        path = Path(settings.UPLOAD_DIR) / str(user_id)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _safe_filename(self, filename: str) -> str:
        from slugify import slugify
        stem = Path(filename).stem
        suffix = Path(filename).suffix.lower()
        return f"{slugify(stem)}{suffix}"

    async def upload(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        document_type: str,
        file: UploadFile,
    ) -> Document:
        # Validate type
        if document_type not in ALLOWED_TYPES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported document type: {document_type}")

        # Read content
        content = await file.read()
        if len(content) > settings.max_upload_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File exceeds maximum size of {settings.MAX_UPLOAD_SIZE_MB} MB.",
            )

        # Validate MIME type via content-type header (python-magic is optional on Windows)
        mime_type = file.content_type or "application/octet-stream"
        allowed_mimes = ALLOWED_TYPES[document_type]
        if mime_type not in allowed_mimes:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"File type {mime_type} is not allowed for {document_type}.",
            )

        # Save file
        safe_name = self._safe_filename(file.filename or "document")
        unique_name = f"{uuid.uuid4().hex}_{safe_name}"
        upload_dir = self._get_upload_dir(user_id)
        file_path = upload_dir / unique_name

        with open(file_path, "wb") as f:
            f.write(content)

        doc = Document(
            user_id=user_id,
            document_type=document_type,
            file_name=file.filename or safe_name,
            storage_path=str(file_path),
            mime_type=mime_type,
            file_size=len(content),
            is_default=False,
        )
        db.add(doc)
        await db.commit()
        await db.refresh(doc)
        return doc

    async def list_documents(self, db: AsyncSession, user_id: uuid.UUID) -> list[Document]:
        result = await db.execute(
            select(Document).where(
                Document.user_id == user_id,
                Document.is_deleted.is_(False),
            ).order_by(Document.created_at.desc())
        )
        return list(result.scalars().all())

    async def set_default(self, db: AsyncSession, user_id: uuid.UUID, doc_id: uuid.UUID) -> Document:
        result = await db.execute(
            select(Document).where(Document.id == doc_id, Document.user_id == user_id, Document.is_deleted.is_(False))
        )
        doc = result.scalar_one_or_none()
        if not doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

        # Unset default for same type
        all_docs = await db.execute(
            select(Document).where(
                Document.user_id == user_id,
                Document.document_type == doc.document_type,
                Document.is_deleted.is_(False),
            )
        )
        for d in all_docs.scalars():
            d.is_default = (d.id == doc_id)

        await db.commit()
        await db.refresh(doc)
        return doc

    async def delete_document(self, db: AsyncSession, user_id: uuid.UUID, doc_id: uuid.UUID) -> None:
        result = await db.execute(
            select(Document).where(Document.id == doc_id, Document.user_id == user_id, Document.is_deleted.is_(False))
        )
        doc = result.scalar_one_or_none()
        if not doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")
        doc.is_default = False
        doc.is_deleted = True
        await db.commit()

    async def get_file_path(self, db: AsyncSession, user_id: uuid.UUID, doc_id: uuid.UUID) -> str:
        result = await db.execute(
            select(Document).where(Document.id == doc_id, Document.user_id == user_id, Document.is_deleted.is_(False))
        )
        doc = result.scalar_one_or_none()
        if not doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")
        if not Path(doc.storage_path).exists():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found on server.")
        return doc.storage_path


document_service = DocumentService()

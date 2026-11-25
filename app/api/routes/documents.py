import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import current_user
from app.core.config import settings
from app.db.session import get_db
from app.models.models import Document, Role, User
from app.schemas.schemas import ORM

router = APIRouter(prefix="/documents", tags=["documents"])

ALLOWED = {"application/pdf": ".pdf", "image/jpeg": ".jpg", "image/png": ".png"}
MAGIC = {"application/pdf": b"%PDF", "image/jpeg": b"\xff\xd8\xff", "image/png": b"\x89PNG"}
KINDS = {"Relevé de notes", "Pièce d’identité", "Attestation de réussite", "Autre document"}
STAFF = {Role.iit_head, Role.isb_head, Role.interviewer, Role.admin}


class DocumentOut(ORM):
    id: int
    kind: str
    filename: str
    content_type: str
    size: int
    status: str
    created_at: datetime | None = None


@router.get("", response_model=list[DocumentOut])
def mine(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return db.scalars(select(Document).where(Document.user_id == user.id).order_by(Document.id.desc())).all()


@router.post("", response_model=DocumentOut, status_code=201)
async def upload(kind: str = Form("Relevé de notes"), file: UploadFile = File(...), user: User = Depends(current_user), db: Session = Depends(get_db)):
    if kind not in KINDS:
        raise HTTPException(422, "Type de document inconnu")
    if file.content_type not in ALLOWED:
        raise HTTPException(415, "Format non accepté : PDF, JPG ou PNG uniquement")
    data = await file.read(settings.max_upload_bytes + 1)
    if len(data) > settings.max_upload_bytes:
        raise HTTPException(413, "Fichier trop volumineux : 10 Mo maximum")
    if not data.startswith(MAGIC[file.content_type]):
        raise HTTPException(415, "Le contenu du fichier ne correspond pas à son format")
    folder = Path(settings.upload_dir) / str(user.id)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{uuid.uuid4().hex}{ALLOWED[file.content_type]}"  # never trust the client filename on disk
    path.write_bytes(data)
    doc = Document(user_id=user.id, kind=kind, filename=Path(file.filename or "document").name[:255], content_type=file.content_type, size=len(data), storage_path=str(path))
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


@router.get("/{doc_id}/file")
def download(doc_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    doc = db.get(Document, doc_id)
    if not doc or (doc.user_id != user.id and user.role not in STAFF):
        raise HTTPException(404, "Document introuvable")
    if not Path(doc.storage_path).is_file():
        raise HTTPException(410, "Fichier indisponible")
    return FileResponse(doc.storage_path, media_type=doc.content_type, filename=doc.filename)

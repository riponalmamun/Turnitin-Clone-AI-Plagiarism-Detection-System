from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import shutil
from pathlib import Path
from datetime import datetime
import logging
from app.database.session import get_db
from app.models.user import User
from app.models.document import Document
from app.schemas.document import DocumentResponse
from app.core.dependencies import get_current_user
from app.core.config import settings
from app.services.document_parser import DocumentParser
from app.services.text_processor import TextProcessor
from app.services.embedding_service import EmbeddingService
from app.database.vector_db import vector_db

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload a document for plagiarism checking"""
    
    # Validate file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext.lstrip('.') not in settings.allowed_extensions_list:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed: {settings.ALLOWED_EXTENSIONS}"
        )
    
    # Check file size
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset to beginning
    
    if file_size > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE / 1024 / 1024}MB"
        )
    
    # Create storage directory if not exists
    storage_path = Path(settings.STORAGE_PATH)
    storage_path.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_filename = f"{current_user.id}_{timestamp}_{file.filename}"
    file_path = storage_path / unique_filename
    
    # Save file
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error saving file: {str(e)}"
        )
    
    # Parse document and extract text
    try:
        parser = DocumentParser()
        content = parser.parse_document(str(file_path))
    except Exception as e:
        # Delete file if parsing fails
        os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error parsing document: {str(e)}"
        )
    
    # Process text
    text_processor = TextProcessor()
    clean_content = text_processor.clean_text(content)
    content_hash = text_processor.generate_fingerprint(clean_content)
    word_count = text_processor.calculate_word_count(clean_content)
    
    # Check if document already exists (by hash)
    existing_doc = db.query(Document).filter(
        Document.content_hash == content_hash,
        Document.user_id == current_user.id
    ).first()
    
    if existing_doc:
        # Delete newly uploaded file
        os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This document has already been uploaded"
        )
    
    # Create document record
    document = Document(
        filename=unique_filename,
        original_filename=file.filename,
        file_path=str(file_path),
        file_size=file_size,
        file_type=file_ext.lstrip('.'),
        content=clean_content,
        content_hash=content_hash,
        word_count=word_count,
        char_count=len(clean_content),
        user_id=current_user.id,
        institution_id=current_user.institution_id
    )
    
    db.add(document)
    db.commit()
    db.refresh(document)
    
    # Generate and store embedding in background (optional if ChromaDB available)
    if vector_db.is_available():
        try:
            embedding_service = EmbeddingService()
            embedding = embedding_service.generate_embedding(clean_content[:1000])  # First 1000 chars
            
            vector_db.add_document(
                doc_id=str(document.id),
                text=clean_content[:1000],
                embedding=embedding,
                metadata={
                    'user_id': current_user.id,
                    'institution_id': current_user.institution_id,
                    'filename': file.filename,
                    'word_count': word_count
                }
            )
            
            document.embedding_stored = True
            db.commit()
            logger.info(f"Embedding stored for document {document.id}")
        except Exception as e:
            logger.error(f"Error storing embedding: {e}")
    else:
        logger.warning(f"Vector DB not available. Skipping embedding for document {document.id}")
    
    return DocumentResponse.model_validate(document)


@router.get("/", response_model=List[DocumentResponse])
def get_documents(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all documents uploaded by current user"""
    
    documents = db.query(Document).filter(
        Document.user_id == current_user.id
    ).order_by(Document.uploaded_at.desc()).offset(skip).limit(limit).all()
    
    return [DocumentResponse.model_validate(doc) for doc in documents]


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific document"""
    
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    return DocumentResponse.model_validate(document)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a document"""
    
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Delete file from storage
    try:
        if os.path.exists(document.file_path):
            os.remove(document.file_path)
    except Exception as e:
        logger.error(f"Error deleting file: {e}")
    
    # Delete from vector database (if available)
    if vector_db.is_available():
        try:
            vector_db.delete_document(str(document.id))
            logger.info(f"Deleted document {document.id} from vector DB")
        except Exception as e:
            logger.error(f"Error deleting from vector DB: {e}")
    
    # Delete from database
    db.delete(document)
    db.commit()
    
    return None
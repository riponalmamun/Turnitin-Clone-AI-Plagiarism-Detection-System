from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from app.database.session import get_db
from app.models.user import User
from app.models.document import Document
from app.models.submission import Submission, SubmissionStatus
from app.schemas.plagiarism import (
    PlagiarismCheckRequest,
    PlagiarismCheckResponse,
    MatchResponse
)
from app.core.dependencies import get_current_user
from app.tasks.plagiarism_tasks import check_plagiarism_task
from app.services.cache_service import cache_service

router = APIRouter()


@router.post("/check", response_model=PlagiarismCheckResponse, status_code=status.HTTP_202_ACCEPTED)
def check_plagiarism(
    request: PlagiarismCheckRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Start plagiarism check for a document"""
    
    # Get document
    document = db.query(Document).filter(
        Document.id == request.document_id,
        Document.user_id == current_user.id
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Check cache first
    cached_result = cache_service.get_cached_check(document.content_hash)
    if cached_result:
        # Return cached result
        submission = db.query(Submission).filter(
            Submission.id == cached_result['submission_id']
        ).first()
        
        if submission:
            matches = [MatchResponse.model_validate(m) for m in submission.matches]
            return PlagiarismCheckResponse(
                submission_id=submission.id,
                task_id=submission.task_id,
                status=submission.status,
                originality_score=submission.originality_score,
                plagiarism_percentage=submission.plagiarism_percentage,
                total_matches=submission.total_matches,
                web_matches=submission.web_matches,
                database_matches=submission.database_matches,
                processing_time=submission.processing_time,
                submitted_at=submission.submitted_at,
                completed_at=submission.completed_at,
                matches=matches
            )
    
    # Create submission record
    submission = Submission(
        document_id=document.id,
        user_id=current_user.id,
        status=SubmissionStatus.PENDING,
        check_settings={
            'check_web': request.check_web,
            'check_database': request.check_database,
            'check_institution': request.check_institution
        }
    )
    
    db.add(submission)
    db.commit()
    db.refresh(submission)
    
    # Start background task
    task = check_plagiarism_task.delay(
        submission_id=submission.id,
        check_web=request.check_web,
        check_database=request.check_database,
        check_institution=request.check_institution
    )
    
    # Update task ID
    submission.task_id = task.id
    db.commit()
    
    return PlagiarismCheckResponse(
        submission_id=submission.id,
        task_id=task.id,
        status=SubmissionStatus.PENDING,
        originality_score=None,
        plagiarism_percentage=None,
        total_matches=0,
        web_matches=0,
        database_matches=0,
        processing_time=None,
        submitted_at=submission.submitted_at,
        completed_at=None,
        matches=[]
    )


@router.get("/status/{submission_id}", response_model=PlagiarismCheckResponse)
def get_check_status(
    submission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get status of a plagiarism check"""
    
    submission = db.query(Submission).filter(
        Submission.id == submission_id,
        Submission.user_id == current_user.id
    ).first()
    
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found"
        )
    
    matches = [MatchResponse.model_validate(m) for m in submission.matches]
    
    return PlagiarismCheckResponse(
        submission_id=submission.id,
        task_id=submission.task_id,
        status=submission.status,
        originality_score=submission.originality_score,
        plagiarism_percentage=submission.plagiarism_percentage,
        total_matches=submission.total_matches,
        web_matches=submission.web_matches,
        database_matches=submission.database_matches,
        processing_time=submission.processing_time,
        submitted_at=submission.submitted_at,
        completed_at=submission.completed_at,
        matches=matches
    )


@router.get("/history", response_model=List[PlagiarismCheckResponse])
def get_check_history(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get plagiarism check history"""
    
    submissions = db.query(Submission).filter(
        Submission.user_id == current_user.id
    ).order_by(Submission.submitted_at.desc()).offset(skip).limit(limit).all()
    
    results = []
    for submission in submissions:
        matches = [MatchResponse.model_validate(m) for m in submission.matches]
        results.append(PlagiarismCheckResponse(
            submission_id=submission.id,
            task_id=submission.task_id,
            status=submission.status,
            originality_score=submission.originality_score,
            plagiarism_percentage=submission.plagiarism_percentage,
            total_matches=submission.total_matches,
            web_matches=submission.web_matches,
            database_matches=submission.database_matches,
            processing_time=submission.processing_time,
            submitted_at=submission.submitted_at,
            completed_at=submission.completed_at,
            matches=matches
        ))
    
    return results
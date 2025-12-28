from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, FileResponse
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.user import User
from app.models.submission import Submission
from app.models.report import Report
from app.schemas.report import ReportResponse
from app.core.dependencies import get_current_user

router = APIRouter()


@router.get("/{submission_id}", response_model=ReportResponse)
def get_report(
    submission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get plagiarism report for a submission"""
    
    submission = db.query(Submission).filter(
        Submission.id == submission_id,
        Submission.user_id == current_user.id
    ).first()
    
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found"
        )
    
    report = db.query(Report).filter(Report.submission_id == submission_id).first()
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    
    return ReportResponse.model_validate(report)


@router.get("/{submission_id}/html", response_class=HTMLResponse)
def get_html_report(
    submission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get HTML version of plagiarism report"""
    
    submission = db.query(Submission).filter(
        Submission.id == submission_id,
        Submission.user_id == current_user.id
    ).first()
    
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found"
        )
    
    report = db.query(Report).filter(Report.submission_id == submission_id).first()
    
    if not report or not report.html_content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="HTML report not available"
        )
    
    return HTMLResponse(content=report.html_content)


@router.get("/{submission_id}/pdf")
def get_pdf_report(
    submission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Download PDF version of report"""
    
    submission = db.query(Submission).filter(
        Submission.id == submission_id,
        Submission.user_id == current_user.id
    ).first()
    
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found"
        )
    
    report = db.query(Report).filter(Report.submission_id == submission_id).first()
    
    if not report or not report.pdf_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PDF report not available"
        )
    
    import os
    if not os.path.exists(report.pdf_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PDF file not found"
        )
    
    return FileResponse(
        path=report.pdf_path,
        media_type='application/pdf',
        filename=f"plagiarism_report_{submission_id}.pdf"
    )
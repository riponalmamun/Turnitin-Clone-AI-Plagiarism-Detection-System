from celery import Task
from sqlalchemy.orm import Session
from datetime import datetime
import time
from app.tasks.celery_app import celery_app
from app.database.session import SessionLocal
from app.models.document import Document
from app.models.submission import Submission, SubmissionStatus
from app.models.match import Match
from app.models.report import Report
from app.services.plagiarism_detector import PlagiarismDetector
from app.services.report_generator import ReportGenerator
from app.services.cache_service import cache_service


class DatabaseTask(Task):
    """Base task with database session"""
    _db = None
    
    @property
    def db(self):
        if self._db is None:
            self._db = SessionLocal()
        return self._db
    
    def after_return(self, *args, **kwargs):
        if self._db is not None:
            self._db.close()


@celery_app.task(base=DatabaseTask, bind=True)
def check_plagiarism_task(
    self,
    submission_id: int,
    check_web: bool = True,
    check_database: bool = True,
    check_institution: bool = True
):
    """Background task for plagiarism checking"""
    
    db: Session = self.db
    start_time = time.time()
    
    try:
        # Get submission
        submission = db.query(Submission).filter(Submission.id == submission_id).first()
        if not submission:
            return {"error": "Submission not found"}
        
        # Update status
        submission.status = SubmissionStatus.PROCESSING
        db.commit()
        
        # Get document
        document = db.query(Document).filter(Document.id == submission.document_id).first()
        if not document:
            submission.status = SubmissionStatus.FAILED
            submission.error_message = "Document not found"
            db.commit()
            return {"error": "Document not found"}
        
        # Initialize detector
        detector = PlagiarismDetector(db)
        
        # Perform plagiarism check
        originality_score, matches_data = detector.check_plagiarism(
            document=document,
            check_web=check_web,
            check_database=check_database,
            check_institution=check_institution
        )
        
        # Count matches by type
        web_matches = sum(1 for m in matches_data if m['source_type'].value == 'web')
        db_matches = sum(1 for m in matches_data if m['source_type'].value == 'database')
        
        # Save matches
        for match_data in matches_data:
            match = Match(
                submission_id=submission.id,
                match_type=match_data['match_type'],
                source_type=match_data['source_type'],
                matched_text=match_data['matched_text'],
                source_text=match_data['source_text'],
                similarity_score=match_data['similarity_score'],
                source_url=match_data.get('source_url'),
                source_title=match_data.get('source_title'),
                source_document_id=match_data.get('source_document_id'),
                start_position=match_data['start_position'],
                end_position=match_data['end_position']
            )
            db.add(match)
        
        # Update submission
        submission.status = SubmissionStatus.COMPLETED
        submission.originality_score = originality_score
        submission.plagiarism_percentage = 100 - originality_score
        submission.total_matches = len(matches_data)
        submission.web_matches = web_matches
        submission.database_matches = db_matches
        submission.processing_time = time.time() - start_time
        submission.completed_at = datetime.utcnow()
        
        db.commit()
        db.refresh(submission)
        
        # Generate report
        report_generator = ReportGenerator()
        
        # Get all matches
        matches = db.query(Match).filter(Match.submission_id == submission.id).all()
        
        # Generate HTML report
        html_content = report_generator.generate_html_report(
            submission=submission,
            matches=matches,
            document_content=document.content
        )
        
        # Generate JSON report
        json_data = report_generator.generate_json_report(
            submission=submission,
            matches=matches
        )
        
        # Save report
        report = Report(
            submission_id=submission.id,
            html_content=html_content,
            json_data=json_data,
            summary=f"Originality Score: {originality_score:.1f}%"
        )
        
        db.add(report)
        db.commit()
        
        # Cache result
        cache_service.cache_document_check(
            content_hash=document.content_hash,
            result={
                'submission_id': submission.id,
                'originality_score': originality_score,
                'plagiarism_percentage': 100 - originality_score
            }
        )
        
        return {
            "submission_id": submission.id,
            "status": "completed",
            "originality_score": originality_score,
            "total_matches": len(matches_data)
        }
    
    except Exception as e:
        # Handle errors
        submission = db.query(Submission).filter(Submission.id == submission_id).first()
        if submission:
            submission.status = SubmissionStatus.FAILED
            submission.error_message = str(e)
            submission.processing_time = time.time() - start_time
            db.commit()
        
        return {"error": str(e)}
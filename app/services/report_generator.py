from typing import List, Dict
from jinja2 import Template
from datetime import datetime
from app.models.submission import Submission
from app.models.match import Match


class ReportGenerator:
    """Generate plagiarism reports in various formats"""
    
    def __init__(self):
        self.html_template = self._get_html_template()
    
    def generate_html_report(
        self,
        submission: Submission,
        matches: List[Match],
        document_content: str
    ) -> str:
        """Generate HTML report with highlighted matches"""
        
        # Prepare matches data
        matches_data = []
        for match in matches:
            matches_data.append({
                'type': match.match_type.value,
                'source': match.source_type.value,
                'text': match.matched_text,
                'similarity': round(match.similarity_score, 2),
                'source_url': match.source_url,
                'source_title': match.source_title
            })
        
        # Generate highlighted content
        highlighted_content = self._highlight_matches(document_content, matches)
        
        # Render template
        report_html = self.html_template.render(
            submission=submission,
            matches=matches_data,
            highlighted_content=highlighted_content,
            generated_at=datetime.now()
        )
        
        return report_html
    
    def generate_json_report(
        self,
        submission: Submission,
        matches: List[Match]
    ) -> Dict:
        """Generate JSON report"""
        
        matches_data = []
        for match in matches:
            matches_data.append({
                'id': match.id,
                'match_type': match.match_type.value,
                'source_type': match.source_type.value,
                'matched_text': match.matched_text,
                'source_text': match.source_text,
                'similarity_score': match.similarity_score,
                'source_url': match.source_url,
                'source_title': match.source_title,
                'start_position': match.start_position,
                'end_position': match.end_position
            })
        
        return {
            'submission_id': submission.id,
            'originality_score': submission.originality_score,
            'plagiarism_percentage': submission.plagiarism_percentage,
            'total_matches': submission.total_matches,
            'status': submission.status.value,
            'submitted_at': submission.submitted_at.isoformat(),
            'completed_at': submission.completed_at.isoformat() if submission.completed_at else None,
            'matches': matches_data
        }
    
    def _highlight_matches(self, content: str, matches: List[Match]) -> str:
        """Highlight matched text in HTML"""
        words = content.split()
        highlighted = []
        
        # Create a map of positions to highlight
        highlight_map = {}
        for match in matches:
            for pos in range(match.start_position, match.end_position):
                if pos not in highlight_map:
                    highlight_map[pos] = []
                highlight_map[pos].append({
                    'type': match.match_type.value,
                    'similarity': match.similarity_score
                })
        
        # Build highlighted HTML
        for i, word in enumerate(words):
            if i in highlight_map:
                match_info = highlight_map[i][0]  # Take first match
                color = self._get_color_by_similarity(match_info['similarity'])
                highlighted.append(
                    f'<span class="match {match_info["type"]}" '
                    f'style="background-color: {color};" '
                    f'title="Similarity: {match_info["similarity"]:.1f}%">{word}</span>'
                )
            else:
                highlighted.append(word)
        
        return ' '.join(highlighted)
    
    def _get_color_by_similarity(self, similarity: float) -> str:
        """Get color based on similarity score"""
        if similarity >= 95:
            return '#ff4444'  # Red - Exact match
        elif similarity >= 85:
            return '#ff8844'  # Orange - High similarity
        elif similarity >= 75:
            return '#ffbb44'  # Yellow - Medium similarity
        else:
            return '#ffee88'  # Light yellow - Low similarity
    
    def _get_html_template(self) -> Template:
        """Get HTML template for report"""
        template_str = """
<!DOCTYPE html>
<html>
<head>
    <title>Plagiarism Report</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            background: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .header {
            border-bottom: 3px solid #007bff;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }
        .score-box {
            display: inline-block;
            padding: 20px 40px;
            background: #f8f9fa;
            border-radius: 8px;
            margin: 10px;
            text-align: center;
        }
        .score-value {
            font-size: 48px;
            font-weight: bold;
            color: #007bff;
        }
        .score-label {
            color: #666;
            margin-top: 5px;
        }
        .matches-section {
            margin: 30px 0;
        }
        .match-item {
            border-left: 4px solid #ff4444;
            padding: 15px;
            margin: 15px 0;
            background: #fff3f3;
            border-radius: 4px;
        }
        .content-section {
            margin-top: 30px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
            line-height: 1.8;
        }
        .match {
            padding: 2px 4px;
            border-radius: 3px;
            cursor: pointer;
        }
        .match.exact {
            border-bottom: 2px solid #ff0000;
        }
        .match.paraphrase {
            border-bottom: 2px solid #ff8800;
        }
        .match.semantic {
            border-bottom: 2px solid #ffbb00;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Plagiarism Detection Report</h1>
            <p>Generated: {{ generated_at.strftime('%Y-%m-%d %H:%M:%S') }}</p>
        </div>
        
        <div class="scores">
            <div class="score-box">
                <div class="score-value">{{ submission.originality_score|round(1) }}%</div>
                <div class="score-label">Originality Score</div>
            </div>
            <div class="score-box">
                <div class="score-value">{{ submission.plagiarism_percentage|round(1) }}%</div>
                <div class="score-label">Plagiarism</div>
            </div>
            <div class="score-box">
                <div class="score-value">{{ submission.total_matches }}</div>
                <div class="score-label">Matches Found</div>
            </div>
        </div>
        
        <div class="matches-section">
            <h2>Detected Matches</h2>
            {% for match in matches %}
            <div class="match-item">
                <strong>Match {{ loop.index }}</strong> - 
                Type: {{ match.type|upper }} | 
                Similarity: {{ match.similarity }}%<br>
                <small>Source: {{ match.source }}</small><br>
                {% if match.source_url %}
                <small><a href="{{ match.source_url }}" target="_blank">{{ match.source_title or match.source_url }}</a></small>
                {% endif %}
            </div>
            {% endfor %}
        </div>
        
        <div class="content-section">
            <h2>Document with Highlighted Matches</h2>
            <div>{{ highlighted_content|safe }}</div>
        </div>
    </div>
</body>
</html>
        """
        return Template(template_str)
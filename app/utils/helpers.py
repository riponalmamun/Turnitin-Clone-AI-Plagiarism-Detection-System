import hashlib
import secrets
from typing import Optional
from datetime import datetime, timedelta


def generate_random_string(length: int = 32) -> str:
    """Generate random string"""
    return secrets.token_urlsafe(length)


def hash_string(text: str) -> str:
    """Create SHA256 hash of string"""
    return hashlib.sha256(text.encode()).hexdigest()


def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to max length"""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."


def calculate_percentage(part: float, whole: float) -> float:
    """Calculate percentage"""
    if whole == 0:
        return 0.0
    return (part / whole) * 100


def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def get_time_ago(dt: datetime) -> str:
    """Get human readable time ago"""
    now = datetime.utcnow()
    diff = now - dt
    
    if diff.days > 365:
        years = diff.days // 365
        return f"{years} year{'s' if years > 1 else ''} ago"
    elif diff.days > 30:
        months = diff.days // 30
        return f"{months} month{'s' if months > 1 else ''} ago"
    elif diff.days > 0:
        return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    else:
        return "just now"


def clean_filename(filename: str) -> str:
    """Clean filename to remove special characters"""
    import re
    # Remove special characters
    clean = re.sub(r'[^\w\s\-\.]', '', filename)
    # Replace spaces with underscore
    clean = clean.replace(' ', '_')
    return clean
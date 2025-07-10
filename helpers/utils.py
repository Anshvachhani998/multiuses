import os
import re
import hashlib
import mimetypes
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class FileUtils:
    """Utility functions for file operations"""
    
    @staticmethod
    def get_file_size(file_path: str) -> int:
        """Get file size in bytes"""
        try:
            return os.path.getsize(file_path)
        except Exception as e:
            logger.error(f"Error getting file size: {e}")
            return 0
    
    @staticmethod
    def get_file_extension(file_path: str) -> str:
        """Get file extension"""
        return os.path.splitext(file_path)[1].lower()
    
    @staticmethod
    def get_mime_type(file_path: str) -> Optional[str]:
        """Get MIME type of file"""
        try:
            return mimetypes.guess_type(file_path)[0]
        except Exception as e:
            logger.error(f"Error getting MIME type: {e}")
            return None
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0 ʙ"
        
        size_names = ['ʙ', 'ᴋʙ', 'ᴍʙ', 'ɢʙ', 'ᴛʙ']
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"
    
    @staticmethod
    def create_safe_filename(filename: str) -> str:
        """Create a safe filename by removing invalid characters"""
        # Remove invalid characters
        safe_name = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        # Remove multiple underscores
        safe_name = re.sub(r'_+', '_', safe_name)
        
        # Limit length
        if len(safe_name) > 100:
            name, ext = os.path.splitext(safe_name)
            safe_name = name[:100-len(ext)] + ext
        
        return safe_name
    
    @staticmethod
    def generate_unique_filename(base_path: str, extension: str) -> str:
        """Generate unique filename with timestamp"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{base_path}_{timestamp}{extension}"
    
    @staticmethod
    def cleanup_old_files(directory: str, max_age_hours: int = 24) -> int:
        """Clean up old files from directory"""
        try:
            count = 0
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            
            for filename in os.listdir(directory):
                file_path = os.path.join(directory, filename)
                if os.path.isfile(file_path):
                    file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    if file_time < cutoff_time:
                        os.remove(file_path)
                        count += 1
            
            return count
        except Exception as e:
            logger.error(f"Error cleaning up files: {e}")
            return 0
    
    @staticmethod
    def get_file_hash(file_path: str) -> Optional[str]:
        """Get MD5 hash of file"""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            logger.error(f"Error getting file hash: {e}")
            return None

class TextUtils:
    """Utility functions for text operations"""
    
    @staticmethod
    def truncate_text(text: str, max_length: int = 100) -> str:
        """Truncate text to specified length"""
        if len(text) <= max_length:
            return text
        return text[:max_length-3] + "..."
    
    @staticmethod
    def escape_markdown(text: str) -> str:
        """Escape markdown special characters"""
        escape_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        for char in escape_chars:
            text = text.replace(char, f'\\{char}')
        return text
    
    @staticmethod
    def format_duration(seconds: int) -> str:
        """Format duration in human readable format"""
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            minutes = seconds // 60
            secs = seconds % 60
            return f"{minutes}ᴍ {secs}s"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}ʜ {minutes}ᴍ"
    
    @staticmethod
    def to_small_caps(text: str) -> str:
        """Convert text to small caps unicode"""
        small_caps_map = {
            'a': 'ᴀ', 'b': 'ʙ', 'c': 'ᴄ', 'd': 'ᴅ', 'e': 'ᴇ', 'f': 'ꜰ', 'g': 'ɢ', 'h': 'ʜ',
            'i': 'ɪ', 'j': 'ᴊ', 'k': 'ᴋ', 'l': 'ʟ', 'm': 'ᴍ', 'n': 'ɴ', 'o': 'ᴏ', 'p': 'ᴘ',
            'q': 'ǫ', 'r': 'ʀ', 's': 's', 't': 'ᴛ', 'u': 'ᴜ', 'v': 'ᴠ', 'w': 'ᴡ', 'x': 'x',
            'y': 'ʏ', 'z': 'ᴢ'
        }
        
        result = ""
        for char in text.lower():
            result += small_caps_map.get(char, char)
        return result
    
    @staticmethod
    def extract_user_id_from_text(text: str) -> Optional[int]:
        """Extract user ID from text"""
        # Look for patterns like @username or user ID
        patterns = [
            r'@(\w+)',
            r'(\d{6,})',
            r'user_id[:\s]*(\d+)',
            r'id[:\s]*(\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    continue
        
        return None
    
    @staticmethod
    def sanitize_html(text: str) -> str:
        """Remove HTML tags from text"""
        return re.sub(r'<[^>]+>', '', text)
    
    @staticmethod
    def is_valid_url(url: str) -> bool:
        """Check if URL is valid"""
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        return url_pattern.match(url) is not None

class VideoUtils:
    """Utility functions for video operations"""
    
    @staticmethod
    def get_video_info(file_path: str) -> Dict[str, Any]:
        """Get video information"""
        try:
            import subprocess
            from config import Config
            
            cmd = [
                Config.FFPROBE_PATH,
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                file_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                import json
                return json.loads(result.stdout)
            else:
                logger.error(f"Error getting video info: {result.stderr}")
                return {}
        except Exception as e:
            logger.error(f"Error in get_video_info: {e}")
            return {}
    
    @staticmethod
    def is_video_file(file_path: str) -> bool:
        """Check if file is a video"""
        video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v']
        return FileUtils.get_file_extension(file_path) in video_extensions
    
    @staticmethod
    def is_audio_file(file_path: str) -> bool:
        """Check if file is an audio file"""
        audio_extensions = ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a']
        return FileUtils.get_file_extension(file_path) in audio_extensions
    
    @staticmethod
    def get_video_duration(file_path: str) -> Optional[float]:
        """Get video duration in seconds"""
        try:
            video_info = VideoUtils.get_video_info(file_path)
            if 'format' in video_info and 'duration' in video_info['format']:
                return float(video_info['format']['duration'])
            return None
        except Exception as e:
            logger.error(f"Error getting video duration: {e}")
            return None
    
    @staticmethod
    def get_video_resolution(file_path: str) -> Optional[tuple]:
        """Get video resolution (width, height)"""
        try:
            video_info = VideoUtils.get_video_info(file_path)
            if 'streams' in video_info:
                for stream in video_info['streams']:
                    if stream.get('codec_type') == 'video':
                        width = stream.get('width')
                        height = stream.get('height')
                        if width and height:
                            return (width, height)
            return None
        except Exception as e:
            logger.error(f"Error getting video resolution: {e}")
            return None

class DateUtils:
    """Utility functions for date operations"""
    
    @staticmethod
    def format_datetime(dt: datetime, format_str: str = "%d/%m/%Y %H:%M:%S") -> str:
        """Format datetime to string"""
        return dt.strftime(format_str)
    
    @staticmethod
    def time_ago(dt: datetime) -> str:
        """Get human readable time ago"""
        now = datetime.now()
        diff = now - dt
        
        if diff.days > 0:
            return f"{diff.days} ᴅᴀʏs ᴀɢᴏ"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} ʜᴏᴜʀs ᴀɢᴏ"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} ᴍɪɴᴜᴛᴇs ᴀɢᴏ"
        else:
            return "ᴊᴜsᴛ ɴᴏᴡ"
    
    @staticmethod
    def is_expired(dt: datetime) -> bool:
        """Check if datetime is expired"""
        return datetime.now() > dt
    
    @staticmethod
    def add_days(dt: datetime, days: int) -> datetime:
        """Add days to datetime"""
        return dt + timedelta(days=days)
    
    @staticmethod
    def get_today_start() -> datetime:
        """Get start of today"""
        return datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    @staticmethod
    def get_today_end() -> datetime:
        """Get end of today"""
        return datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999)

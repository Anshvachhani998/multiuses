import asyncio
import time
from pyrogram import Client
from pyrogram.types import Message
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class ProgressTracker:
    def __init__(self, client: Client):
        self.client = client
        self.active_progresses: Dict[str, Dict[str, Any]] = {}
    
    def format_bytes(self, size: int) -> str:
        """Format bytes to human readable format"""
        for unit in ['ʙ', 'ᴋʙ', 'ᴍʙ', 'ɢʙ']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} ᴛʙ"
    
    def format_time(self, seconds: int) -> str:
        """Format seconds to human readable time"""
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
    
    def create_progress_bar(self, percentage: float, length: int = 20) -> str:
        """Create a visual progress bar"""
        filled_length = int(length * percentage // 100)
        bar = '█' * filled_length + '░' * (length - filled_length)
        return f"[{bar}] {percentage:.1f}%"
    
    def generate_progress_text(self, 
                             operation: str,
                             percentage: float,
                             current_size: int,
                             total_size: int,
                             speed: float,
                             eta: int) -> str:
        """Generate progress message text"""
        progress_bar = self.create_progress_bar(percentage)
        current_size_str = self.format_bytes(current_size)
        total_size_str = self.format_bytes(total_size)
        speed_str = self.format_bytes(int(speed)) + "/s"
        eta_str = self.format_time(eta)
        
        return f"""
🎬 **ᴘʀᴏᴄᴇssɪɴɢ ᴠɪᴅᴇᴏ**

**ᴏᴘᴇʀᴀᴛɪᴏɴ:** {operation}

{progress_bar}

**sɪᴢᴇ:** {current_size_str} / {total_size_str}
**sᴘᴇᴇᴅ:** {speed_str}
**ᴇᴛᴀ:** {eta_str}

⚡ ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ ᴡʜɪʟᴇ ᴡᴇ ᴘʀᴏᴄᴇss ʏᴏᴜʀ ᴠɪᴅᴇᴏ...
"""
    
    async def start_progress(self, 
                           chat_id: int,
                           message_id: int,
                           operation: str,
                           total_size: int,
                           progress_id: str) -> None:
        """Start progress tracking"""
        self.active_progresses[progress_id] = {
            "chat_id": chat_id,
            "message_id": message_id,
            "operation": operation,
            "total_size": total_size,
            "current_size": 0,
            "start_time": time.time(),
            "last_update": 0,
            "percentage": 0.0,
            "speed": 0.0,
            "eta": 0
        }
    
    async def update_progress(self, 
                            progress_id: str,
                            current_size: int,
                            force_update: bool = False) -> None:
        """Update progress"""
        if progress_id not in self.active_progresses:
            return
        
        progress = self.active_progresses[progress_id]
        current_time = time.time()
        
        # Update only every 2 seconds unless forced
        if not force_update and current_time - progress["last_update"] < 2:
            return
        
        progress["current_size"] = current_size
        progress["percentage"] = (current_size / progress["total_size"]) * 100
        
        # Calculate speed and ETA
        elapsed_time = current_time - progress["start_time"]
        if elapsed_time > 0:
            progress["speed"] = current_size / elapsed_time
            if progress["speed"] > 0:
                remaining_size = progress["total_size"] - current_size
                progress["eta"] = int(remaining_size / progress["speed"])
            else:
                progress["eta"] = 0
        
        progress["last_update"] = current_time
        
        # Update message
        try:
            progress_text = self.generate_progress_text(
                progress["operation"],
                progress["percentage"],
                progress["current_size"],
                progress["total_size"],
                progress["speed"],
                progress["eta"]
            )
            
            await self.client.edit_message_text(
                chat_id=progress["chat_id"],
                message_id=progress["message_id"],
                text=progress_text
            )
        except Exception as e:
            logger.error(f"Failed to update progress: {e}")
    
    async def complete_progress(self, progress_id: str, success: bool = True) -> None:
        """Complete progress tracking"""
        if progress_id not in self.active_progresses:
            return
        
        progress = self.active_progresses[progress_id]
        
        if success:
            final_text = f"""
✅ **ᴠɪᴅᴇᴏ ᴘʀᴏᴄᴇssɪɴɢ ᴄᴏᴍᴘʟᴇᴛᴇᴅ**

**ᴏᴘᴇʀᴀᴛɪᴏɴ:** {progress["operation"]}
**sɪᴢᴇ:** {self.format_bytes(progress["total_size"])}
**ᴛɪᴍᴇ ᴛᴀᴋᴇɴ:** {self.format_time(int(time.time() - progress["start_time"]))}

🚀 ᴜᴘʟᴏᴀᴅɪɴɢ ᴘʀᴏᴄᴇssᴇᴅ ᴠɪᴅᴇᴏ...
"""
        else:
            final_text = f"""
❌ **ᴠɪᴅᴇᴏ ᴘʀᴏᴄᴇssɪɴɢ ꜰᴀɪʟᴇᴅ**

**ᴏᴘᴇʀᴀᴛɪᴏɴ:** {progress["operation"]}

🔄 ᴘʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ ᴏʀ ᴄᴏɴᴛᴀᴄᴛ sᴜᴘᴘᴏʀᴛ
"""
        
        try:
            await self.client.edit_message_text(
                chat_id=progress["chat_id"],
                message_id=progress["message_id"],
                text=final_text
            )
        except Exception as e:
            logger.error(f"Failed to complete progress: {e}")
        
        # Remove from active progresses
        del self.active_progresses[progress_id]
    
    async def upload_progress(self, current: int, total: int) -> None:
        """Upload progress callback"""
        # This is used for file uploads
        pass
    
    async def download_progress(self, current: int, total: int) -> None:
        """Download progress callback"""
        # This is used for file downloads
        pass

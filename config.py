import os
from info import LOG_CHANNEL, ADMINS, MONGO_URI, MONGO_NAME

class Config:

    MONGODB_URI = MONGO_URI
    DATABASE_NAME = MONGO_NAME
    
    # Channel Configuration
    LOG_CHANNEL_ID = LOG_CHANNEL
    MEDIA_CHANNEL_ID = LOG_CHANNEL
  
    # Bot Owner and Admins
    OWNER_ID = ADMINS
    ADMINS = ADMINS
    
    # Credit System
    DEFAULT_CREDITS = int(os.getenv("DEFAULT_CREDITS", "100"))
    PROCESS_COST = int(os.getenv("PROCESS_COST", "10"))
    REFERRAL_BONUS = int(os.getenv("REFERRAL_BONUS", "100"))
    DAILY_LIMIT = int(os.getenv("DAILY_LIMIT", "10"))
    
    # Premium System
    PREMIUM_PRICES = {
        "monthly": {"credits": 4000, "days": 30},
        "yearly": {"credits": 20000, "days": 365}
    }
    
    # File Paths
    DOWNLOADS_DIR = os.getenv("DOWNLOADS_DIR", "downloads")
    UPLOADS_DIR = os.getenv("UPLOADS_DIR", "uploads")
    TEMP_DIR = os.getenv("TEMP_DIR", "temp")
    
    # FFmpeg Configuration
    FFMPEG_PATH = os.getenv("FFMPEG_PATH", "ffmpeg")
    FFPROBE_PATH = os.getenv("FFPROBE_PATH", "ffprobe")
    
    # Bot Messages
    START_MESSAGE = """
🎬 **ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ᴠɪᴅᴇᴏ ᴘʀᴏᴄᴇssᴏʀ ʙᴏᴛ**

ɪ ᴄᴀɴ ʜᴇʟᴘ ʏᴏᴜ ᴘʀᴏᴄᴇss ʏᴏᴜʀ ᴠɪᴅᴇᴏs ᴡɪᴛʜ ᴠᴀʀɪᴏᴜs ᴏᴘᴛɪᴏɴs!

**ᴀᴠᴀɪʟᴀʙʟᴇ ᴘʀᴏᴄᴇssɪɴɢ ᴏᴘᴛɪᴏɴs:**
• ᴛʀɪᴍ ᴠɪᴅᴇᴏ
• ᴄᴏᴍᴘʀᴇss ᴠɪᴅᴇᴏ
• ʀᴏᴛᴀᴛᴇ ᴠɪᴅᴇᴏ
• ᴍᴇʀɢᴇ ᴠɪᴅᴇᴏs
• ᴀᴅᴅ ᴡᴀᴛᴇʀᴍᴀʀᴋ
• ᴍᴜᴛᴇ ᴠɪᴅᴇᴏ
• ʀᴇᴘʟᴀᴄᴇ ᴀᴜᴅɪᴏ
• ʀᴇᴠᴇʀsᴇ ᴠɪᴅᴇᴏ
• ᴀᴅᴅ sᴜʙᴛɪᴛʟᴇs
• ᴄʜᴀɴɢᴇ ʀᴇsᴏʟᴜᴛɪᴏɴ
• ᴇxᴛʀᴀᴄᴛ ᴀᴜᴅɪᴏ
• ᴛᴀᴋᴇ sᴄʀᴇᴇɴsʜᴏᴛ

**ᴇᴀᴄʜ ᴘʀᴏᴄᴇss ᴄᴏsᴛs {process_cost} ᴄʀᴇᴅɪᴛs**

sᴇɴᴅ ᴍᴇ ᴀ ᴠɪᴅᴇᴏ ᴛᴏ ɢᴇᴛ sᴛᴀʀᴛᴇᴅ!
"""


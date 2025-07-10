import os

class Config:
    # Bot Configuration
    API_ID = int(os.getenv("API_ID", "22141398"))
    API_HASH = os.getenv("API_HASH", "0c8f8bd171e05e42d6f6e5a6f4305389")
    BOT_TOKEN = os.getenv("BOT_TOKEN", "6346317908:AAEEtPcj59TcbUGKLMFLIIeiZFDZFT6Nq40")
    
    # Database Configuration
    MONGO_URI = os.getenv("MONGODB_URI", "mongodb+srv://Ansh089:Ansh089@cluster0.y8tpouc.mongodb.net/?retryWrites=true&w=majority")
    MONGO_NAME = os.getenv("DATABASE_NAME", "MUlTI")
    
    # Channel Configuration
    LOG_CHANNEL = int(os.getenv("LOG_CHANNEL_ID", "-1002858808929")) if os.getenv("LOG_CHANNEL_ID") else None
    MEDIA_CHANNEL = int(os.getenv("MEDIA_CHANNEL_ID", "-1002858808929")) if os.getenv("MEDIA_CHANNEL_ID") else None
    
    # Bot Owner and Admins
    OWNER_ID = int(os.getenv("OWNER_ID", "7744665378"))
    ADMINS = [int(x) for x in os.getenv("ADMINS", "5660839376,6167872503,5961011848,7744665378").split(",") if x.strip().isdigit()]
    if OWNER_ID:
        ADMINS.append(OWNER_ID)
    
    # Credit System
    DEFAULT_CREDITS = int(os.getenv("DEFAULT_CREDITS", "100"))
    PROCESS_COST = int(os.getenv("PROCESS_COST", "10"))
    REFERRAL_BONUS = int(os.getenv("REFERRAL_BONUS", "100"))
    DAILY_LIMIT = int(os.getenv("DAILY_LIMIT", "20"))
    
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
    START_MESSAGE = f"""
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

**ᴇᴀᴄʜ ᴘʀᴏᴄᴇss ᴄᴏsᴛs {PROCESS_COST} ᴄʀᴇᴅɪᴛs**

sᴇɴᴅ ᴍᴇ ᴀ ᴠɪᴅᴇᴏ ᴛᴏ ɢᴇᴛ sᴛᴀʀᴛᴇᴅ!
"""
    
    # Create directories if they don't exist
    @classmethod
    def create_directories(cls):
        for dir_path in [cls.DOWNLOADS_DIR, cls.UPLOADS_DIR, cls.TEMP_DIR]:
            os.makedirs(dir_path, exist_ok=True)

# Create directories on import
Config.create_directories()

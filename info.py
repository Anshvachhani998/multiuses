import os

SESSION = "teraboxdl"
API_ID = int(os.getenv("API_ID", "22141398"))
API_HASH = os.getenv("API_HASH", "0c8f8bd171e05e42d6f6e5a6f4305389")
BOT_TOKEN = os.getenv("BOT_TOKEN", "6346317908:AAEEtPcj59TcbUGKLMFLIIeiZFDZFT6Nq40")
LOG_CHANNEL = int(os.getenv("LOG_CHANNEL", "-1002858808929"))
DUMP_CHANNEL = int(os.getenv("DUMP_CHANNEL", "-1002858808929"))
PORT = int(os.getenv("PORT", "8080"))
FORCE_CHANNEL = int(os.getenv("FORCE_CHANNEL", "-1002858808929"))
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://Ansh089:Ansh089@cluster0.y8tpouc.mongodb.net/?retryWrites=true&w=majority")
MONGO_NAME = os.getenv("MONGO_NAME", "MUlTI")
ADMINS = [5660839376, 6167872503, 5961011848, 7744665378]
DAILY_LIMITS = 20
MAINTENANCE_MODE = False

MAINTENANCE_MESSAGE = (
    "⚠️ **Maintenance Mode Activated** ⚙️\n\n"
    "Our bot is currently undergoing scheduled maintenance to improve performance and add new features.\n\n"
    "Please check back in a while. We’ll be back soon, better than ever!\n\n"
    "💬 **Support Group:** [SUPPORT](https://t.me/AnSBotsSupports)\n\n"
    "**– Team Support**"
)

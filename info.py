import os

SESSION = "teraboxdl"
API_ID = int(os.getenv("API_ID", "22141398"))
API_HASH = os.getenv("API_HASH", "0c8f8bd171e05e42d6f6e5a6f4305389")
BOT_TOKEN = os.getenv("BOT_TOKEN", "7277194738:AAHrewQsvKcPqeXYeMIbSk-nyUjgJ14kW8U")
LOG_CHANNEL = int(os.getenv("LOG_CHANNEL", "-1002284232975"))
DUMP_CHANNEL = int(os.getenv("DUMP_CHANNEL", "-1002284232975"))
PORT = int(os.getenv("PORT", "8080"))

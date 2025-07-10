import motor.motor_asyncio
from datetime import datetime, timedelta

from info import MONGO_URI, MONGO_NAME, DAILY_LIMITS, LOG_CHANNEL

class Database:
    def __init__(self):
        self.client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
        self.db = self.client[MONGO_NAME]
        self.col = self.db["users"]
        


db = Database()

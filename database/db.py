import motor.motor_asyncio
from datetime import datetime, timedelta
from info import MONGO_URI, MONGO_NAME, DAILY_LIMITS, LOG_CHANNEL

class Database:
    def __init__(self):
        self.client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
        self.db = self.client[MONGO_NAME]
        
        # Collections
        self.users = self.db["users"]
        self.operations = self.db["operations"]
        self.premium_codes = self.db["premium_codes"]
        self.referrals = self.db["referrals"]

    async def create_indexes(self):
        await self.users.create_index("user_id", unique=True)
        await self.users.create_index("referral_code", unique=True)
        await self.users.create_index("referred_by")

        await self.operations.create_index([("user_id", 1), ("date", -1)])
        await self.operations.create_index("date", expireAfterSeconds=86400 * 30)

        await self.premium_codes.create_index("code", unique=True)
        await self.premium_codes.create_index("used")

        await self.referrals.create_index("referrer_id")
        await self.referrals.create_index("referred_id")

    async def get_user(self, user_id: int):
        return await self.users.find_one({"user_id": user_id})

    async def create_user(self, user_id: int, username=None, first_name=None, referred_by=None):
        user_data = {
            "user_id": user_id,
            "username": username,
            "first_name": first_name,
            "credits": 10,  # Default credits
            "premium_until": None,
            "banned": False,
            "daily_usage": 0,
            "last_usage_reset": datetime.now(),
            "referral_code": f"ref_{user_id}",
            "referred_by": referred_by,
            "total_operations": 0,
            "joined_date": datetime.now(),
            "last_activity": datetime.now()
        }
        result = await self.users.insert_one(user_data)
        if referred_by:
            await self.handle_referral(referred_by, user_id)
        return result.inserted_id

    async def update_user(self, user_id: int, update_data: dict):
        update_data["last_activity"] = datetime.now()
        return await self.users.update_one({"user_id": user_id}, {"$set": update_data})

    async def add_credits(self, user_id: int, amount: int):
        return await self.users.update_one({"user_id": user_id}, {"$inc": {"credits": amount}})

    async def deduct_credits(self, user_id: int, amount: int):
        user = await self.get_user(user_id)
        if not user or user["credits"] < amount:
            return False
        await self.users.update_one({"user_id": user_id}, {"$inc": {"credits": -amount}})
        return True

    async def reset_daily_usage(self, user_id: int):
        return await self.users.update_one(
            {"user_id": user_id},
            {"$set": {"daily_usage": 0, "last_usage_reset": datetime.now()}}
        )

    async def check_daily_limit(self, user_id: int):
        user = await self.get_user(user_id)
        if not user:
            return False

        if user.get("premium_until") and user["premium_until"] > datetime.now():
            return True

        if (datetime.now() - user.get("last_usage_reset", datetime.now())).days >= 1:
            await self.reset_daily_usage(user_id)
            return True

        return user.get("daily_usage", 0) < DAILY_LIMITS

    async def increment_daily_usage(self, user_id: int):
        return await self.users.update_one(
            {"user_id": user_id},
            {"$inc": {"daily_usage": 1, "total_operations": 1}}
        )

    async def handle_referral(self, referrer_id: int, referred_id: int):
        existing = await self.referrals.find_one({"referrer_id": referrer_id, "referred_id": referred_id})
        if not existing:
            await self.referrals.insert_one({
                "referrer_id": referrer_id,
                "referred_id": referred_id,
                "date": datetime.now(),
                "bonus_given": True
            })
            await self.add_credits(referrer_id, 5)  # Example referral bonus
            return True
        return False

    async def create_premium_code(self, code: str, days: int, created_by: int):
        return await self.premium_codes.insert_one({
            "code": code,
            "days": days,
            "created_by": created_by,
            "created_date": datetime.now(),
            "used": False,
            "used_by": None,
            "used_date": None
        })

    async def redeem_premium_code(self, code: str, user_id: int):
        premium_code = await self.premium_codes.find_one({"code": code, "used": False})
        if not premium_code:
            return False

        await self.premium_codes.update_one(
            {"code": code},
            {"$set": {"used": True, "used_by": user_id, "used_date": datetime.now()}}
        )

        user = await self.get_user(user_id)
        current_premium = user.get("premium_until") or datetime.now()
        if current_premium < datetime.now():
            current_premium = datetime.now()

        new_premium = current_premium + timedelta(days=premium_code["days"])
        await self.update_user(user_id, {"premium_until": new_premium})
        return premium_code["days"]

    async def is_user_premium(self, user_id: int):
        user = await self.get_user(user_id)
        return user and user.get("premium_until", datetime.now()) > datetime.now()

db = Database()

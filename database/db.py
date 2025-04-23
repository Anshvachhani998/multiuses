import motor.motor_asyncio
from datetime import datetime, timedelta

from info import MONGO_URI, MONGO_NAME, DAILY_LIMITS, LOG_CHANNEL

class Database:
    def __init__(self):
        self.client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
        self.db = self.client[MONGO_NAME]
        self.col = self.db["users"]
        self.downloads_collection = self.db["downloads"]
        
    def new_user(self, id, name):
        return {
            "user_id": int(id),
            "name": name,
            "joined_at": datetime.utcnow(),
            "user_type": "free",
            "upload_type": "video",
            "tasks_used": 0,
            "total_tasks": 0,
            "last_reset": datetime.utcnow().strftime("%Y-%m-%d")
        }

    async def delete_all_users(self):
        result = await self.col.delete_many({})
        return result.deleted_count
    
    async def add_user(self, id, name):
        user = self.new_user(id, name)
        await self.col.insert_one(user)

    async def is_user_exist(self, id):      
        user = await self.col.find_one({"user_id": int(id)})
        return bool(user)


    async def reset_daily_tasks(self, bot):
        await self.col.update_many({}, {"$set": {"tasks_used": 0}})
        await bot.send_message(LOG_CHANNEL, "🔄 **Daily task limits have been reset for all users!** ✅ ")

    
    async def check_task_limit(self, user_id):
        user = await self.col.find_one({"user_id": user_id}, {"tasks_used": 1, "user_type": 1}, limit=1)
    
        if not user:  # User agar exist nahi karta
            return True  # ✅ Allow task

        if user.get("user_type") == "premium":
            return True  # ✅ Premium users ke liye unlimited tasks

        return user.get("tasks_used", 0) < DAILY_LIMITS  # ✅ Free users ke liye limit check

    async def get_task_limit(self, user_id):
        user = await self.col.find_one({"user_id": user_id}, {"tasks_used": 1, "user_type": 1, "total_tasks": 1}, limit=1)

        if not user:  # User exist nahi karta
            return True, 0, "Free", 0  # ✅ Default values (Allow task, 0 used, Free user, 0 total tasks)

        user_type = user.get("user_type", "Free")
        tasks_used = user.get("tasks_used", 0)
        total_tasks = user.get("total_tasks", 0)  # Total completed tasks

        if user_type.lower() == "premium":
            return True, tasks_used, "Premium", total_tasks  # ✅ Premium user ke liye unlimited

        return tasks_used < DAILY_LIMITS, tasks_used, user_type, total_tasks  # ✅ Free user limit check
        
    async def increment_task(self, user_id):
        """Task complete hone ke baad task count ko update karega"""
        result = await self.col.update_one(
            {"user_id": int(user_id)},
            {"$inc": {"tasks_used": 1, "total_tasks": 1}},
            upsert=True
        )
        return result.modified_count > 0
        
    
    
    async def add_premium_users(self, user_id, time_value, time_unit):
        """ ✅ User ko premium access dega specific time units ke saath (Plan remove kar diya) """

        time_unit = time_unit.lower()

        if time_unit == "seconds":
            expiry_time = datetime.utcnow() + timedelta(seconds=time_value)
        elif time_unit == "minutes":
            expiry_time = datetime.utcnow() + timedelta(minutes=time_value)
        elif time_unit == "hours":
            expiry_time = datetime.utcnow() + timedelta(hours=time_value)
        elif time_unit == "days":
            expiry_time = datetime.utcnow() + timedelta(days=time_value)
        elif time_unit == "weeks":
            expiry_time = datetime.utcnow() + timedelta(weeks=time_value)
        elif time_unit == "months":
            expiry_time = datetime.utcnow() + timedelta(days=time_value * 30)  # Approx 30 days per month
        elif time_unit == "years":
            expiry_time = datetime.utcnow() + timedelta(days=time_value * 365)  # Approx 365 days per year
        else:
            return None  # Invalid time unit

        await self.col.update_one(
            {"user_id": user_id},
            {"$set": {"user_type": "premium", "expiry_date": expiry_time}},
            upsert=True
        )
        return expiry_time  # Expiry date return karega
    

    async def remove_premium_access(self, user_id):
        """ ❌ Premium access remove karega """
        self.col.update_one(
            {"user_id": user_id},
            {"$set": {"user_type": "free"}, "$unset": {"expiry_date": "", "plan": ""}}
        )

    async def check_user_premium(self, user_id):
        """ 🔎 User ka premium status aur expiry date check karega """
        user = await self.col.find_one(
            {"user_id": int(user_id)},
            {"user_type": 1, "expiry_date": 1}
        )
        
        if user and user.get("user_type") == "premium":
            expiry_date = user.get("expiry_date")
            if expiry_date and expiry_date > datetime.utcnow():
                return expiry_date  # ✅ Valid premium user ka expiry date return karega
            else:
                # ✅ Expired premium users ko downgrade karega
                await self.col.update_one(
                    {"user_id": int(user_id)},
                    {"$set": {"user_type": "free"}, "$unset": {"expiry_date": ""}}
                )
        return None  # ❌ Not a premium user

    async def get_expired(self, current_time):
        expired_users = []
        cursor = self.col.find({"user_type": "premium", "expiry_date": {"$lte": current_time}})

        async for user in cursor:  # ✅ Correct way to iterate AsyncIOMotorCursor
            expired_users.append(user)

        return expired_users  # ✅ Proper list return

    
    
    async def get_all_users(self):
        return self.col.find({})

    
    async def total_users_count(self):
        count = await self.col.count_documents({})
        return count
    
    async def delete_user(self, user_id):
        await self.col.delete_many({'id': int(user_id)})

    async def block_user(self, user_id):
        await self.col.delete_many({'id': int(user_id)})

    async def save_thumbnail(self, user_id, file_id):
        """Save the thumbnail file_id for a user"""
        existing_user = await self.col.find_one({"user_id": int(user_id)})
        
        if existing_user:
            # If user exists, update their thumbnail
            await self.col.update_one(
                {"user_id": int(user_id)},
                {"$set": {"thumbnail": file_id}}
            )
        else:
            user_data = self.new_user(user_id, "Unknown")
            user_data["thumbnail"] = file_id
            await self.col.insert_one(user_data)

    async def get_user_thumbnail(self, user_id):
        """Get the user's thumbnail file_id"""
        user = await self.col.find_one({"user_id": int(user_id)})
        if user and "thumbnail" in user:
            return user["thumbnail"]
        return None

    async def remove_thumbnail(self, user_id):
        """Remove user's thumbnail (soft delete)"""
        result = await self.col.update_one(
            {"user_id": int(user_id)},
            {"$unset": {"thumbnail": ""}}
        )
        return result.modified_count > 0

    async def increment_download_count(self):
        await self.downloads_collection.update_one(
            {}, 
            {"$setOnInsert": {"total_downloads": 0}},
            upsert=True
        )
        
        await self.downloads_collection.update_one({}, {"$inc": {"total_downloads": 1}})
    
    async def get_total_downloads(self):  
        result = await self.db["downloads"].find_one({}, {"total_downloads": 1})
        if result:
            return result.get("total_downloads", 0)
        return 0

db = Database()

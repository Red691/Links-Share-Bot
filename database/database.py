import motor.motor_asyncio
import base64
from config import DB_URI, DB_NAME
from datetime import datetime
from typing import List, Optional

class Rohit:
    def __init__(self, db_uri: str, db_name: str):
        self.dbclient = motor.motor_asyncio.AsyncIOMotorClient(db_uri)
        self.database = self.dbclient[db_name]

        # Collections
        self.user_data = self.database['users']
        self.channels_collection = self.database['channels']
        self.fsub_channels_collection = self.database['fsub_channels']
        self.admins_collection = self.database['admins']

        # For the second block
        self.fsub_data = self.fsub_channels_collection
        self.rqst_fsub_Channel_data = self.database['rqst_fsub_channels']

    # ---------------- USER MANAGEMENT ----------------
    async def add_user(self, user_id: int) -> bool:
        if not isinstance(user_id, int) or user_id <= 0:
            return False
        existing_user = await self.user_data.find_one({'_id': user_id})
        if existing_user:
            return False
        await self.user_data.insert_one({'_id': user_id, 'created_at': datetime.utcnow()})
        return True

    async def present_user(self, user_id: int) -> bool:
        return bool(await self.user_data.find_one({'_id': user_id}))

    async def full_userbase(self) -> List[int]:
        return [doc['_id'] async for doc in self.user_data.find()]

    async def del_user(self, user_id: int) -> bool:
        result = await self.user_data.delete_one({'_id': user_id})
        return result.deleted_count > 0

    async def is_admin(self, user_id: int) -> bool:
        return bool(await self.admins_collection.find_one({'_id': int(user_id)}))

    async def add_admin(self, user_id: int) -> bool:
        await self.admins_collection.update_one({'_id': int(user_id)}, {'$set': {'_id': int(user_id)}}, upsert=True)
        return True

    async def remove_admin(self, user_id: int) -> bool:
        result = await self.admins_collection.delete_one({'_id': user_id})
        return result.deleted_count > 0

    async def list_admins(self) -> List[int]:
        admins = await self.admins_collection.find().to_list(None)
        return [admin['_id'] for admin in admins]

    # ---------------- CHANNEL MANAGEMENT ----------------
    async def save_channel(self, channel_id: int) -> bool:
        await self.channels_collection.update_one(
            {"channel_id": channel_id},
            {"$set": {"channel_id": channel_id, "invite_link_expiry": None, "created_at": datetime.utcnow(), "status": "active"}},
            upsert=True
        )
        return True

    async def get_channels(self) -> List[int]:
        channels = await self.channels_collection.find({"status": "active"}).to_list(None)
        return [c["channel_id"] for c in channels if "channel_id" in c]

    async def delete_channel(self, channel_id: int) -> bool:
        result = await self.channels_collection.delete_one({"channel_id": channel_id})
        return result.deleted_count > 0

    # ---------------- FORCE-SUB CHANNEL MANAGEMENT ----------------
    async def channel_exist(self, channel_id: int) -> bool:
        found = await self.fsub_data.find_one({'_id': channel_id})
        return bool(found)

    async def add_channel(self, channel_id: int):
        if not await self.channel_exist(channel_id):
            await self.fsub_data.insert_one({'_id': channel_id})

    async def rem_channel(self, channel_id: int):
        if await self.channel_exist(channel_id):
            await self.fsub_data.delete_one({'_id': channel_id})

    async def show_channels(self) -> List[int]:
        channel_docs = await self.fsub_data.find().to_list(length=None)
        return [doc['_id'] for doc in channel_docs]

    async def get_channel_mode(self, channel_id: int) -> str:
        data = await self.fsub_data.find_one({'_id': channel_id})
        return data.get("mode", "off") if data else "off"

    async def set_channel_mode(self, channel_id: int, mode: str):
        await self.fsub_data.update_one({'_id': channel_id}, {'$set': {'mode': mode}}, upsert=True)

    # ---------------- REQUEST FORCE-SUB ----------------
    async def req_user(self, channel_id: int, user_id: int):
        await self.rqst_fsub_Channel_data.update_one(
            {'_id': int(channel_id)},
            {'$addToSet': {'user_ids': int(user_id)}},
            upsert=True
        )

    async def del_req_user(self, channel_id: int, user_id: int):
        await self.rqst_fsub_Channel_data.update_one(
            {'_id': channel_id}, 
            {'$pull': {'user_ids': user_id}}
        )

    async def req_user_exist(self, channel_id: int, user_id: int) -> bool:
        found = await self.rqst_fsub_Channel_data.find_one({
            '_id': int(channel_id),
            'user_ids': int(user_id)
        })
        return bool(found)

    async def reqChannel_exist(self, channel_id: int) -> bool:
        channel_ids = await self.show_channels()
        return channel_id in channel_ids

# ---------------- USAGE ----------------
db = Rohit(DB_URI, DB_NAME)

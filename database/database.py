import motor.motor_asyncio
import base64
from config import DB_URI, DB_NAME
from datetime import datetime
from typing import List, Optional

# MongoDB client
dbclient = motor.motor_asyncio.AsyncIOMotorClient(DB_URI)
database = dbclient[DB_NAME]

# Collections
user_data = database['users']
channels_collection = database['channels']
fsub_channels_collection = database['fsub_channels']
admins_collection = database['admins']
rqst_fsub_channel_data = database['rqst_fsub_channel_data']  # force-sub requests


# ---------------- USER MANAGEMENT ---------------- #

async def add_user(user_id: int) -> bool:
    """Add a user to the database if they don't exist."""
    if not isinstance(user_id, int) or user_id <= 0:
        print(f"Invalid user_id: {user_id}")
        return False
    try:
        if await user_data.find_one({'_id': user_id}):
            return False
        await user_data.insert_one({'_id': user_id, 'created_at': datetime.utcnow()})
        return True
    except Exception as e:
        print(f"Error adding user {user_id}: {e}")
        return False


async def present_user(user_id: int) -> bool:
    """Check if a user exists in the database."""
    if not isinstance(user_id, int):
        return False
    return bool(await user_data.find_one({'_id': user_id}))


async def full_userbase() -> List[int]:
    """Get all user IDs from the database."""
    try:
        user_docs = user_data.find()
        return [doc['_id'] async for doc in user_docs]
    except Exception as e:
        print(f"Error fetching userbase: {e}")
        return []


async def del_user(user_id: int) -> bool:
    """Delete a user from the database."""
    try:
        result = await user_data.delete_one({'_id': user_id})
        return result.deleted_count > 0
    except Exception as e:
        print(f"Error deleting user {user_id}: {e}")
        return False


async def is_admin(user_id: int) -> bool:
    """Check if a user is an admin."""
    try:
        return bool(await admins_collection.find_one({'_id': int(user_id)}))
    except Exception as e:
        print(f"Error checking admin status for {user_id}: {e}")
        return False


async def add_admin(user_id: int) -> bool:
    """Add a user as admin."""
    try:
        await admins_collection.update_one({'_id': int(user_id)}, {'$set': {'_id': int(user_id)}}, upsert=True)
        return True
    except Exception as e:
        print(f"Error adding admin {user_id}: {e}")
        return False


async def remove_admin(user_id: int) -> bool:
    """Remove a user from admins."""
    try:
        result = await admins_collection.delete_one({'_id': int(user_id)})
        return result.deleted_count > 0
    except Exception as e:
        print(f"Error removing admin {user_id}: {e}")
        return False


async def list_admins() -> list:
    """List all admin user IDs."""
    try:
        admins = await admins_collection.find().to_list(None)
        return [admin['_id'] for admin in admins]
    except Exception as e:
        print(f"Error listing admins: {e}")
        return []


# ---------------- CHANNEL MANAGEMENT ---------------- #

async def channel_exist(channel_id: int) -> bool:
    """Check if a channel exists in FSub collection."""
    found = await fsub_channels_collection.find_one({'_id': channel_id})
    return bool(found)


async def add_channel(channel_id: int):
    """Add a channel to FSub collection."""
    if not await channel_exist(channel_id):
        await fsub_channels_collection.insert_one({'_id': channel_id, 'created_at': datetime.utcnow()})


async def rem_channel(channel_id: int):
    """Remove a channel from FSub collection."""
    if await channel_exist(channel_id):
        await fsub_channels_collection.delete_one({'_id': channel_id})


async def show_channels() -> List[int]:
    """List all FSub channel IDs."""
    channel_docs = await fsub_channels_collection.find().to_list(length=None)
    return [doc['_id'] for doc in channel_docs]


async def get_channel_mode(channel_id: int) -> str:
    """Get current mode of a channel."""
    data = await fsub_channels_collection.find_one({'_id': channel_id})
    return data.get("mode", "off") if data else "off"


async def set_channel_mode(channel_id: int, mode: str):
    """Set mode of a channel."""
    await fsub_channels_collection.update_one(
        {'_id': channel_id},
        {'$set': {'mode': mode}},
        upsert=True
    )


# ---------------- REQUEST FORCE-SUB MANAGEMENT ---------------- #

async def req_user(channel_id: int, user_id: int):
    """Add a user to the set of requested users for a specific channel."""
    try:
        await rqst_fsub_channel_data.update_one(
            {'_id': int(channel_id)},
            {'$addToSet': {'user_ids': int(user_id)}},
            upsert=True
        )
    except Exception as e:
        print(f"[DB ERROR] Failed to add user to request list: {e}")


async def del_req_user(channel_id: int, user_id: int):
    """Remove a user from the request set of a channel."""
    await rqst_fsub_channel_data.update_one(
        {'_id': int(channel_id)},
        {'$pull': {'user_ids': int(user_id)}}
    )


async def req_user_exist(channel_id: int, user_id: int) -> bool:
    """Check if a user exists in a channel's request set."""
    try:
        found = await rqst_fsub_channel_data.find_one({
            '_id': int(channel_id),
            'user_ids': int(user_id)
        })
        return bool(found)
    except Exception as e:
        print(f"[DB ERROR] Failed to check request list: {e}")
        return False


async def req_channel_exist(channel_id: int) -> bool:
    """Check if a channel exists using show_channels."""
    channel_ids = await show_channels()
    return channel_id in channel_ids


# ---------------- ADDITIONAL CHANNEL OPERATIONS ---------------- #

async def save_channel(channel_id: int) -> bool:
    """Save a channel with default values."""
    if not isinstance(channel_id, int):
        print(f"Invalid channel_id: {channel_id}")
        return False
    try:
        await channels_collection.update_one(
            {"channel_id": channel_id},
            {
                "$set": {
                    "channel_id": channel_id,
                    "invite_link_expiry": None,
                    "created_at": datetime.utcnow(),
                    "status": "active"
                }
            },
            upsert=True
        )
        return True
    except Exception as e:
        print(f"Error saving channel {channel_id}: {e}")
        return False


async def get_channels() -> List[int]:
    """Get all active channels."""
    try:
        channels = await channels_collection.find({"status": "active"}).to_list(None)
        valid_channels = [c["channel_id"] for c in channels if "channel_id" in c]
        return valid_channels
    except Exception as e:
        print(f"Error fetching channels: {e}")
        return []


async def delete_channel(channel_id: int) -> bool:
    """Delete a channel from the database."""
    try:
        result = await channels_collection.delete_one({"channel_id": channel_id})
        return result.deleted_count > 0
    except Exception as e:
        print(f"Error deleting channel {channel_id}: {e}")
        return False

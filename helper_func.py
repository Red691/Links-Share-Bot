# +++ Modified By Yato [telegram username: @i_killed_my_clan & @ProYato] +++ #
import base64
import asyncio
from pyrogram import filters
from pyrogram.enums import ChatMemberStatus
from pyrogram.filters import Filter
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import OWNER_ID
from database import db

# ---------------- ADMIN FILTERS ---------------- #

class IsAdmin(Filter):
    async def __call__(self, client, message):
        return await db.is_admin(message.from_user.id)

is_admin_filter = IsAdmin()

class IsOwnerOrAdmin(Filter):
    async def __call__(self, client, message):
        user_id = message.from_user.id
        return user_id == OWNER_ID or await db.is_admin(user_id)

is_owner_or_admin = IsOwnerOrAdmin()

# ---------------- FORCE SUBSCRIBE SYSTEM ---------------- #

async def is_subscribed(client, user_id):
    channel_ids = await db.show_channels()
    if not channel_ids:
        return True
    if user_id == OWNER_ID:
        return True

    for cid in channel_ids:
        if not await is_sub(client, user_id, cid):
            mode = await db.get_channel_mode(cid)
            if mode == "on":
                await asyncio.sleep(2)
                if await is_sub(client, user_id, cid):
                    continue
            return False
    return True

async def is_sub(client, user_id, channel_id):
    try:
        member = await client.get_chat_member(channel_id, user_id)
        status = member.status
        return status in {
            ChatMemberStatus.OWNER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.MEMBER
        }
    except Exception as e:
        from pyrogram.errors import UserNotParticipant
        if isinstance(e, UserNotParticipant):
            mode = await db.get_channel_mode(channel_id)
            if mode == "on":
                return await db.req_user_exist(channel_id, user_id)
            return False
        print(f"[!] Error in is_sub(): {e}")
        return False

subscribed = filters.create(is_subscribed)

# ---------------- BASE64 ENCODE / DECODE ---------------- #

async def encode(string):
    string_bytes = string.encode("ascii")
    base64_bytes = base64.urlsafe_b64encode(string_bytes)
    return base64_bytes.decode("ascii").strip("=")

async def decode(base64_string):
    base64_string = base64_string.strip("=")
    base64_bytes = (base64_string + "=" * (-len(base64_string) % 4)).encode("ascii")
    string_bytes = base64.urlsafe_b64decode(base64_bytes)
    return string_bytes.decode("ascii")

# ---------------- READABLE TIME ---------------- #

def get_readable_time(seconds: int) -> str:
    count = 0
    up_time = ""
    time_list = []
    time_suffix_list = ["s", "m", "h", "days"]
    while count < 4:
        count += 1
        remainder, result = divmod(seconds, 60) if count < 3 else divmod(seconds, 24)
        if seconds == 0 and remainder == 0:
            break
        time_list.append(int(result))
        seconds = int(remainder)
    hmm = len(time_list)
    for x in range(hmm):
        time_list[x] = str(time_list[x]) + time_suffix_list[x]
    if len(time_list) == 4:
        up_time += f"{time_list.pop()}, "
    time_list.reverse()
    up_time += ":".join(time_list)
    return up_time

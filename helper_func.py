import base64
from pyrogram import filters
from pyrogram.enums import ChatMemberStatus
from pyrogram.errors import UserNotParticipant
from pyrogram.filters import Filter

from config import OWNER_ID
from database.database import (
    is_admin,
    get_fsub_channels,
    is_approval_off
)

# ----------------- ADMIN FILTERS -----------------

class IsAdmin(Filter):
    async def __call__(self, client, message):
        return await is_admin(message.from_user.id)

is_admin_filter = IsAdmin()


class IsOwnerOrAdmin(Filter):
    async def __call__(self, client, message):
        user_id = message.from_user.id
        return user_id == OWNER_ID or await is_admin(user_id)

is_owner_or_admin = IsOwnerOrAdmin()


# ----------------- FORCE SUB -----------------

async def is_subscribed(client, user_id):
    channel_ids = await get_fsub_channels()

    if not channel_ids:
        return True

    if user_id == OWNER_ID:
        return True

    for cid in channel_ids:
        if not await is_sub(client, user_id, cid):
            return False

    return True


async def is_sub(client, user_id, channel_id):
    try:
        member = await client.get_chat_member(channel_id, user_id)
        return member.status in {
            ChatMemberStatus.OWNER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.MEMBER
        }

    except UserNotParticipant:
        approval_off = await is_approval_off(channel_id)

        # If approval system ON → allow pending join-request
        if not approval_off:
            try:
                member = await client.get_chat_member(channel_id, user_id)
                return member.status == ChatMemberStatus.RESTRICTED
            except:
                return False

        return False

    except Exception as e:
        print(f"[!] Error in is_sub(): {e}")
        return False


# ----------------- BASE64 -----------------

async def encode(string):
    b = string.encode("ascii")
    return base64.urlsafe_b64encode(b).decode("ascii").strip("=")


async def decode(base64_string):
    base64_string = base64_string.strip("=")
    b = (base64_string + "=" * (-len(base64_string) % 4)).encode("ascii")
    return base64.urlsafe_b64decode(b).decode("ascii")


# ----------------- TIME HELPERS -----------------

def get_readable_time(seconds: int) -> str:
    count = 0
    up_time = ""
    time_list = []
    suffix = ["s", "m", "h", "days"]

    while count < 4:
        count += 1
        remainder, result = divmod(seconds, 60) if count < 3 else divmod(seconds, 24)
        if seconds == 0 and remainder == 0:
            break
        time_list.append(int(result))
        seconds = int(remainder)

    for x in range(len(time_list)):
        time_list[x] = str(time_list[x]) + suffix[x]

    if len(time_list) == 4:
        up_time += f"{time_list.pop()}, "

    time_list.reverse()
    up_time += ":".join(time_list)
    return up_time


def get_exp_time(seconds):
    periods = [('days', 86400), ('hours', 3600), ('mins', 60), ('secs', 1)]
    result = ''
    for name, sec in periods:
        if seconds >= sec:
            val, seconds = divmod(seconds, sec)
            result += f'{int(val)} {name} '
    return result.strip()


# ----------------- PYROGRAM FILTER -----------------

subscribed = filters.create(is_subscribed)

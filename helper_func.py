# +++ Modified By Yato [telegram username: @i_killed_my_clan & @ProYato] +++ #
# aNDI BANDI SANDI JISNE BHI CREDIT HATAYA USKI BANDI RAndi 

import base64
import re
import asyncio
from pyrogram import filters
from pyrogram.enums import ChatMemberStatus
from config import ADMINS, FORCE_SUB, FSUB_PIC, REQUEST_FSUB_MODE
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant
from pyrogram.errors import FloodWait
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.filters import Filter
from config import OWNER_ID
from database.database import is_admin, get_fsub, get_channels


# ========================= FILTERS ========================= #

class IsAdmin(Filter):
    async def __call__(self, client, message):
        return await is_admin(message.from_user.id)

is_admin_filter = IsAdmin()


class IsOwnerOrAdmin(Filter):
    async def __call__(self, client, message):
        user_id = message.from_user.id
        return user_id == OWNER_ID or await is_admin(user_id)

is_owner_or_admin = IsOwnerOrAdmin()


# ========================= ENCODE / DECODE ========================= #

async def encode(string):
    string_bytes = string.encode("ascii")
    base64_bytes = base64.urlsafe_b64encode(string_bytes)
    base64_string = (base64_bytes.decode("ascii")).strip("=")
    return base64_string


async def decode(base64_string):
    base64_string = base64_string.strip("=")
    base64_bytes = (base64_string + "=" * (-len(base64_string) % 4)).encode("ascii")
    string_bytes = base64.urlsafe_b64decode(base64_bytes)
    string = string_bytes.decode("ascii")
    return string


# ========================= TIME FORMATTER ========================= #

def get_readable_time(seconds: int) -> str:
    count = 0
    up_time = ""
    time_list = []
    time_suffix_list = ["s", "m", "h", "days"]

    while count < 4:
        count += 1
        if count < 3:
            remainder, result = divmod(seconds, 60)
        else:
            remainder, result = divmod(seconds, 24)

        if seconds == 0 and remainder == 0:
            break

        time_list.append(int(result))
        seconds = int(remainder)

    for i in range(len(time_list)):
        time_list[i] = str(time_list[i]) + time_suffix_list[i]

    if len(time_list) == 4:
        up_time += f"{time_list.pop()}, "

    time_list.reverse()
    up_time += ":".join(time_list)

    return up_time


# ========================= MULTI-FSUB CHECK ========================= #

async def check_fsub(client, user_id):
    """
    Check if user has joined **ALL** required FSUB channels.
    Returns (True, None) if joined.
    Returns (False, missing_channels_list) if NOT joined.
    """
    channels = get_channels()  # list of usernames
    if not channels:
        return True, None

    missing = []

    for ch in channels:
        try:
            await client.get_chat_member(ch, user_id)
        except UserNotParticipant:
            missing.append(ch)

    if missing:
        return False, missing
    return True, None


# ========================= TRY AGAIN BUTTON ========================= #

def get_fsub_buttons(channels):
    btns = []
    for ch in channels:
        btns.append([InlineKeyboardButton(f"Join @{ch}", url=f"https://t.me/{ch}")])

    btns.append([InlineKeyboardButton("🔄 Try Again", callback_data="retry_fsub")])

    return InlineKeyboardMarkup(btns)


# ========================= OLD FORCE SUB (MODIFIED) ========================= #

async def force_sub(client, message):
    """
    This now uses NEW multi-channel check system
    + Supports REQUEST MODE
    """
    if FORCE_SUB == "False":
        return True

    if message.from_user.id in ADMINS:
        return True

    ok, missing = await check_fsub(client, message.from_user.id)

    if ok:
        return True

    # REQUEST MODE
    if REQUEST_FSUB_MODE:
        text = "⚠️ *Force Subscribe Required*\n\nPlease join all required channels."
    else:
        text = "❌ You must join required channels before using the bot."

    try:
        if FSUB_PIC:
            await message.reply_photo(
                photo=FSUB_PIC,
                caption=text,
                reply_markup=get_fsub_buttons(missing)
            )
        else:
            await message.reply_text(
                text,
                reply_markup=get_fsub_buttons(missing)
            )
    except Exception as e:
        print(e)

    return False

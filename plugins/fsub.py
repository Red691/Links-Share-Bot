from pyrogram import Client, filters
from pyrogram.types import Message
from config import OWNER_ID
from database.database import add_fsub, rm_fsub, get_fsub
from bot import Bot
from pyrogram.enums import ChatType


# =============== ADD FSUB CHANNEL ===============
@Bot.on_message(filters.command('addfsub') & filters.user(OWNER_ID))
async def add_fsub_command(client: Bot, message: Message):
    if len(message.command) != 2:
        return await message.reply_text("Channel ID do. Usage: /addfsub -100xxxxxxxx")

    try:
        channel_id = int(message.command[1])
    except ValueError:
        return await message.reply_text("Invalid channel ID. Please provide a valid integer.")

    try:
        chat = await client.get_chat(channel_id)
    except Exception as e:
        return await message.reply_text(f"Bot chat access nahi kar paaya! Error: {e}")

    if chat.type not in [ChatType.CHANNEL, ChatType.SUPERGROUP]:
        return await message.reply_text(f"Ye ID channel ya supergroup nahi hai. Type: {chat.type}")

    await add_fsub(channel_id, req_mode=True)
    await message.reply_text(f"FSUB set ho gaya: {chat.title}")


# =============== DELETE FSUB CHANNEL ===============
@Bot.on_message(filters.command(['rmfsub', 'delfsub']) & filters.user(OWNER_ID))
async def rm_fsub_command(client: Bot, message: Message):
    await rm_fsub()
    await message.reply_text("Force Subscribe Channel remove kar diya gaya.")


# =============== FSUB MODE ON/OFF ===============
@Bot.on_message(filters.command('reqfsub') & filters.user(OWNER_ID))
async def reqfsub_mode(client: Bot, message: Message):
    if len(message.command) != 2:
        return await message.reply_text("Usage: /reqfsub on | off")

    mode = message.command[1].lower()

    fsub = await get_fsub()
    if not fsub:
        return await message.reply_text("Pehle /addfsub se channel set karo!")

    if mode == "on":
        await add_fsub(fsub["chat_id"], req_mode=True)
        return await message.reply_text("Force Subscribe Mode **ON** kar diya gaya.")

    elif mode == "off":
        await add_fsub(fsub["chat_id"], req_mode=False)
        return await message.reply_text("Force Subscribe Mode **OFF** kar diya gaya.")

    else:
        return await message.reply_text("Usage: /reqfsub on | off")


# =============== SHOW CURRENT FSUB STATUS ===============
@Bot.on_message(filters.command('fsub') & filters.user(OWNER_ID))
async def fsub_command(client: Bot, message: Message):
    fsub_channel = await get_fsub()
    if not fsub_channel:
        return await message.reply_text("Abhi koi FSUB set nahi hai.")

    try:
        chat = await client.get_chat(fsub_channel['chat_id'])
    except Exception as e:
        return await message.reply_text(f"Error: {e}")

    status = "ON" if fsub_channel.get("req_mode") else "OFF"

    await message.reply_text(
        f"**FSUB Channel:** {chat.title} ({fsub_channel['chat_id']})\n"
        f"**Mode:** {status}"
    )

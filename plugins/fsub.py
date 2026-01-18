import asyncio
from pyrogram import filters, Client
from pyrogram.enums import ChatMemberStatus, ChatType
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, ChatMemberUpdated
from config import ADMINS
import database.database as db
from helper_func import is_owner_or_admin, is_subscribed

# ---------------- ADD CHANNEL ---------------- #
@Bot.on_message(filters.command('addchnl') & filters.private & is_owner_or_admin)
async def add_force_sub(client: Client, message: Message):
    temp = await message.reply("Wait a sec...", quote=True)
    args = message.text.split(maxsplit=1)

    if len(args) != 2:
        return await temp.edit("Usage:\n<code>/addchnl -100xxxxxxxxxx</code>")

    try:
        chat_id = int(args[1])
    except ValueError:
        return await temp.edit("❌ Invalid chat ID!")

    all_chats = await db.show_channels()
    if chat_id in all_chats:
        return await temp.edit(f"Already exists:\n<code>{chat_id}</code>")

    try:
        chat = await client.get_chat(chat_id)
        if chat.type not in [ChatType.CHANNEL, ChatType.SUPERGROUP]:
            return await temp.edit("❌ Only channels/supergroups allowed.")

        bot_member = await client.get_chat_member(chat.id, "me")
        if bot_member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            return await temp.edit("❌ Bot must be admin in that chat.")

        await db.add_channel(chat_id)
        return await temp.edit(f"✅ Added Successfully!\n\n<b>Name:</b> {chat.title}\n<b>ID:</b> <code>{chat_id}</code>")

    except Exception as e:
        return await temp.edit(f"❌ Failed to add chat:\n<code>{chat_id}</code>\n\n<i>{e}</i>")

# ---------------- DELETE CHANNEL ---------------- #
@Bot.on_message(filters.command('delchnl') & filters.private & is_owner_or_admin)
async def del_force_sub(client: Client, message: Message):
    temp = await message.reply("Wait...", quote=True)
    args = message.text.split(maxsplit=1)
    all_channels = await db.show_channels()

    if len(args) != 2:
        return await temp.edit("<b>Usage:</b> <code>/delchnl <channel_id | all></code>")

    if args[1].lower() == "all":
        for ch_id in all_channels:
            await db.rem_channel(ch_id)
        return await temp.edit("✅ All force-sub channels removed.")

    try:
        ch_id = int(args[1])
    except ValueError:
        return await temp.edit("<b>❌ Invalid Channel ID</b>")

    if ch_id in all_channels:
        await db.rem_channel(ch_id)
        return await temp.edit(f"✅ Channel removed: <code>{ch_id}</code>")
    else:
        return await temp.edit(f"❌ Channel not found: <code>{ch_id}</code>")

# ---------------- LIST CHANNELS ---------------- #
@Bot.on_message(filters.command('listchnl') & filters.private & is_owner_or_admin)
async def list_force_sub_channels(client: Client, message: Message):
    temp = await message.reply("Wait...", quote=True)
    channels = await db.show_channels()
    if not channels:
        return await temp.edit("❌ No force-sub channels found.")

    result = "<b>⚡ Force-sub Channels:</b>\n\n"
    for ch_id in channels:
        try:
            chat = await client.get_chat(ch_id)
            link = chat.invite_link or f"https://t.me/{chat.username}" if chat.username else f"https://t.me/c/{str(chat.id)[4:]}"
            result += f"• <a href='{link}'>{chat.title}</a> [<code>{ch_id}</code>]\n"
        except:
            result += f"• <code>{ch_id}</code> — <i>Unavailable</i>\n"

    await temp.edit(result, disable_web_page_preview=True)

# ---------------- HANDLE CHAT MEMBERS ---------------- #
@Bot.on_chat_member_updated()
async def handle_Chatmembers(client, chat_member_updated: ChatMemberUpdated):
    chat_id = chat_member_updated.chat.id
    if await db.req_channel_exist(chat_id):
        old_member = chat_member_updated.old_chat_member
        if old_member and old_member.status == ChatMemberStatus.MEMBER:
            user_id = old_member.user.id
            if await db.req_user_exist(chat_id, user_id):
                await db.del_req_user(chat_id, user_id)

# +++ Modified By @Codeflix_Bots
import asyncio
import sys
import os
from datetime import datetime
from pyrogram import Client
from pyrogram.enums import ParseMode
from config import API_HASH, APP_ID, LOGGER, TG_BOT_TOKEN, TG_BOT_WORKERS, PORT, OWNER_ID
from plugins import web_server
import pyrogram.utils
from aiohttp import web

# Force Pyrogram to support large channel IDs
pyrogram.utils.MIN_CHANNEL_ID = -1009147483647

# ---- MOST IMPORTANT FIX: FORCE TELEGRAM DC5 ----
TELEGRAM_DC_ID = 5
TELEGRAM_DC_SERVER = "149.154.171.5"   # DC5 main IPv4
TELEGRAM_DC_PORT = 443

# Clean old pyrogram session (important for DC migration)
os.system("rm -rf /tmp/.pyrogram")

name = """
Links Sharing Started
"""

class Bot(Client):
    def __init__(self):
        super().__init__(
            name="Bot",
            api_hash=API_HASH,
            api_id=APP_ID,
            plugins={"root": "plugins"},
            workers=TG_BOT_WORKERS,
            bot_token=TG_BOT_TOKEN,
            ipv6=False,
            in_memory=True,   # Force new session in memory
            device_model="Choreo Server",
            app_version="1.0",
            system_version="Linux",
            max_concurrent_transmissions=1,
            connect_timeout=20
        )
        self.LOGGER = LOGGER

    async def start(self, *args, **kwargs):

        # ---- FORCE TELEGRAM DC5 ----
        try:
            self.storage.dc_id = TELEGRAM_DC_ID
            self.storage.server_address = TELEGRAM_DC_SERVER
            self.storage.server_port = TELEGRAM_DC_PORT
        except Exception as e:
            print("Failed to force DC (but continuing):", e)

        await super().start()

        usr_bot_me = await self.get_me()
        self.uptime = datetime.now()

        # Notify owner on restart
        try:
            await self.send_message(
                chat_id=OWNER_ID,
                text="<b><blockquote>🤖 Bot Restarted ♻️</blockquote></b>",
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            self.LOGGER(__name__).warning(f"Failed to notify owner: {e}")

        self.set_parse_mode(ParseMode.HTML)
        self.LOGGER(__name__).info("Bot Running..!\nCreated by https://t.me/ProObito")
        self.LOGGER(__name__).info(f"{name}")
        self.username = usr_bot_me.username

        # Web server
        try:
            app = web.AppRunner(await web_server())
            await app.setup()
            bind_address = "0.0.0.0"
            await web.TCPSite(app, bind_address, PORT).start()
            self.LOGGER(__name__).info(f"Web server started on {bind_address}:{PORT}")
        except Exception as e:
            self.LOGGER(__name__).error(f"Failed to start web server: {e}")

    async def stop(self, *args):
        await super().stop()
        self.LOGGER(__name__).info("Bot stopped.")


# Global cancel flag for broadcast
is_canceled = False
cancel_lock = asyncio.Lock()

if __name__ == "__main__":
    Bot().run()

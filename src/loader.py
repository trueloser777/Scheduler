from apscheduler.schedulers.asyncio import AsyncIOScheduler

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from core.config import Config
from database import Database

# -=+=-=+=-=+=-=+=-=+=-=+=-=+=-=+=-=+=-

config = Config()

database = Database(
    host=config.database.host,
    port=config.database.port,
    user=config.database.user,
    password=config.database.password,
    database_name=config.database.database_name
)

# -=+=-=+=-=+=-=+=-=+=-=+=-=+=-=+=-=+=-

bot = Bot(
    config.telegram.bot_token,
    default=DefaultBotProperties(
        parse_mode='html',
        protect_content=False,
        link_preview_is_disabled=True
    )
)

dispatcher = Dispatcher(
    storage=MemoryStorage()
)

# -=+=-=+=-=+=-=+=-=+=-=+=-=+=-=+=-=+=-

scheduler = AsyncIOScheduler()

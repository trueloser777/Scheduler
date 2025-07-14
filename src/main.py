import logging
import asyncio

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI

from hypercorn import Config
from hypercorn.asyncio import serve

import api
from bot import handlers, schedule

from bot.middlewares.user_creation import CreateUserOnCommand
from loader import (
    config, database,
    bot, dispatcher,
    scheduler
)


def setup_logging():
    # TODO: Add FileHandler?
    log_levels_mapping = logging.getLevelNamesMapping()
    log_level = log_levels_mapping.get(config.settings.log_level, logging.INFO)

    formatter = '%(asctime)s || %(levelname)s || %(name)s || %(message)s'
    date_format = '%m/%d/%Y %I:%M:%S'
    
    logging.basicConfig(level=log_level, format=formatter, datefmt=date_format)
    logging.info('LogLevel: %s | %s', config.settings.log_level, log_level)


@asynccontextmanager # type: ignore
async def lifespan(
    _app: FastAPI
) -> Any: # type: ignore
    setup_logging()

    await database.initialize()

    # Scheduler setup
    scheduler.add_job(
        schedule.notify_about_events,
        kwargs={
            'database': database,
            'bot': bot
        },
        max_instances=1,  # Prevents the bot from sending notification multiple times
        trigger='interval',
        seconds=15,
    )
    scheduler.start()

    # Aiogram polling
    dispatcher.message.middleware(CreateUserOnCommand(database))
    dispatcher.callback_query.middleware(CreateUserOnCommand(database))

    dispatcher.include_router(handlers.router)

    polling_task = asyncio.create_task(
        dispatcher.start_polling(
            bot,
            handle_signals=False
        )
    )

    await bot.send_message(
        config.settings.owner_telegram_id,
        '☕️ Бот запущен.'
    )

    yield

    await bot.send_message(
        config.settings.owner_telegram_id,
        '💤 Бот отключен.'
    )

    if not polling_task.cancelled() or polling_task.cancelling():
        polling_task.cancel()

    await database.shutdown()
    scheduler.shutdown()


if __name__ == '__main__':
    app = FastAPI(
        lifespan=lifespan,
        root_path=config.fastapi.root_path,
        title=config.fastapi.title,
        description=config.fastapi.description
    )

    api.register_exception_handlers(app)
    api.register_routers(app)

    origins = [  ]

    hypercorn_config = Config()
    hypercorn_config.bind = [
        config.fastapi.ip + ':' + str(config.fastapi.port)
    ]

    # noinspection PyTypeChecker
    asyncio.run(serve(app, hypercorn_config))  # type: ignore

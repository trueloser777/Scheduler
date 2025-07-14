from logging import Logger
import logging
from typing import Final

from aiogram import Router

from . import create, edit

router: Final[Router] = Router(name=__name__)
logger: Final[Logger] = logging.getLogger(__name__)


router.include_routers(
    create.router,
    edit.router
)

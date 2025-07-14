from logging import Logger
import logging
from typing import Final

from aiogram import Router

from . import event_management, admin_panel
from . import (
    start, event_list, preferences, help
)

router: Final[Router] = Router(name=__name__)
logger: Final[Logger] = logging.getLogger(__name__)


router.include_routers(
    event_management.router,
    admin_panel.router,

    preferences.router,
    event_list.router,
    help.router,
    start.router
)

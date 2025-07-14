from contextlib import suppress
from datetime import datetime
import logging
from database import Database
from aiogram import Bot

from database.models.notification_log import NotificationLogCreate


logger = logging.getLogger(__name__)

already_sent = {}


async def notify_about_events(database: Database, bot: Bot):
    ongoing_events = await database.events.get_ongoing()
    current_time = datetime.now()

    for event in ongoing_events:
        subscription_list = await database.subscriptions.by_event_type_id(
            event_type_id=event.event_type_id
        ) or []
        
        for subscription in subscription_list:
            user_preferences = await database.user_preferences.by_user_id(
                user_id=subscription.user_id
            )
            if not user_preferences:
                logger.warning('Found a user without preferences')
                continue
            
            delta_time = event.starts_at - current_time
            if delta_time > user_preferences.notification_interval:
                continue

            if sent_events_to_user := already_sent.get(subscription.user_id):
                if event.id in sent_events_to_user:
                    continue
            else:
                already_sent[subscription.user_id] = []
            
            if await database.notification_logs.by_user_id_and_event_id(
                user_id=subscription.user_id,
                event_id=event.id
            ):
                already_sent[subscription.user_id].append(event.id)
                continue

            already_sent[subscription.user_id].append(event.id)
            user = await database.users.by_id(subscription.user_id)
            if not user:  # Shouldn't happen since it's DELETE CASCADE but why not?
                logger.warning('Cannot find a user with id %i', subscription.user_id)
                continue

            await database.notification_logs.create(NotificationLogCreate(
                user_id=user.id,
                event_id=event.id
            ))

            seconds = delta_time.total_seconds() + 30  # Hack
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60

            time_left = ''
            if hours != 0:
                time_left += f'{round(hours)} часов'

            if minutes != 0:
                if hours:
                    time_left += ' и '
                
                time_left += f'{round(minutes)} минут'

            with suppress(Exception):
                await bot.send_message(
                    user.telegram_id,
                    f'⚠️ До события {event.title} осталось {time_left}!'
                )

from datetime import datetime, timedelta
from io import BytesIO
from itertools import groupby
from random import choice
import sys
import logging
from typing import Final, List

from database.models.event import Event

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    logging.error("Pillow is not installed. Run the following command to install: `pip install Pillow`")
    sys.exit(1)

logger: Final[logging.Logger] = logging.getLogger(__name__)


DATE_FORMAT = '%d.%m.%Y'
WEEK_DAYS = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']

NO_EVENT_TEXTS = ['Свободный день', 'Нет запланированных мероприятий']


def _wrap_text_by_width(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont | ImageFont.FreeTypeFont, max_width: int) -> List[str]:
    if not text:
        return []
    
    lines = []
    words = text.split()
    
    if not words:
        return []

    current_line = words[0]
    for word in words[1:]:
        if draw.textlength(current_line + " " + word, font=font) <= max_width:
            current_line += " " + word
        else:
            lines.append(current_line)
            current_line = word

    lines.append(current_line)
    return lines


def generate_schedule_image(
        events: list[Event],
        start_date: datetime,
        end_date: datetime
) -> BytesIO:
    events.sort(key=lambda e: e.starts_at)
    events_by_day = {
        key: list(group)
        for key, group in groupby(
            events,
            key=lambda e: e.starts_at.date()
        )
    }

    padding = 65
    line_height = 52
    bg_color = (22, 22, 22)
    font_color = (255, 255, 255)
    header_color = (100, 150, 255)
    time_color = (180, 180, 180)
    description_color = (160, 160, 160)

    try:
        font_main = ImageFont.truetype("fonts/Inter-VariableFont_opsz,wght.ttf", 26)
        font_bold = ImageFont.truetype("fonts/Inter-VariableFont_opsz,wght.ttf", 28)
        font_header = ImageFont.truetype("fonts/Inter-VariableFont_opsz,wght.ttf", 34)
    except IOError:
        logger.error("Fallback to the default fonts")
        font_main = ImageFont.load_default(26)
        font_bold = ImageFont.load_default(28)
        font_header = ImageFont.load_default(34)


    width = 1080
    temp_height = 20000

    image = Image.new('RGB', (width, temp_height), color=bg_color)
    draw = ImageDraw.Draw(image)
    
    time_x_start = padding + 20
    text_x_start = padding + 150
    max_text_width = width - text_x_start - padding

    y_pos = padding
    current_date = start_date

    while current_date < end_date:
        day_of_week_str = WEEK_DAYS[current_date.weekday()]
        date_str = current_date.strftime('%d.%m')
        header_text = f'{day_of_week_str}, {date_str}'

        draw.text((padding, y_pos), header_text, font=font_header, fill=header_color)
        y_pos += line_height + 10

        day_events = events_by_day.get(current_date.date(), [])
        current_date += timedelta(days=1)
        
        if not day_events:
            draw.text(
                (padding + 20, y_pos),
                choice(NO_EVENT_TEXTS),
                font=font_main,
                fill=font_color
            )
            y_pos += line_height + padding // 2
            continue

        for event in day_events:
            event_start_y = y_pos

            # === Time Block
            time_str = event.starts_at.strftime('%H:%M')
            draw.text((time_x_start, y_pos), time_str, font=font_main, fill=time_color)
            
            time_block_height = font_main.getbbox(time_str)[3]

            if event.duration:
                end_time = event.starts_at + event.duration
                y_pos_end_time = y_pos + time_block_height + 10
                draw.text((time_x_start, y_pos_end_time), end_time.strftime('%H:%M'), font=font_main, fill=time_color)
                time_block_height += font_main.getbbox(end_time.strftime('%H:%M'))[3] + 5

            # === Text Block
            text_block_y = event_start_y
            
            # Rendering the title
            title_lines = _wrap_text_by_width(draw, event.title, font_bold, max_text_width)
            if not title_lines:
                title_lines = ['']

            for line in title_lines:
                draw.text((text_x_start, text_block_y), line, font=font_bold, fill=font_color)
                text_block_y += line_height
            
            # Rendering the description
            if event.description:
                text_block_y -= line_height * 0.3
                description_lines = _wrap_text_by_width(draw, event.description, font_main, max_text_width)
                desc_line_height = int(line_height * 0.6)
                
                for line in description_lines:
                    draw.text((text_x_start, text_block_y), line, font=font_main, fill=description_color)
                    text_block_y += desc_line_height
            
            # Getting the final block size of time and text
            final_time_y = event_start_y + time_block_height
            final_text_y = text_block_y

            y_pos = max(final_time_y, final_text_y) + 44  # Padding between events

        y_pos += padding // 2
    
    # Cropping height of the image
    content_height = y_pos
    image = image.crop((0, 0, width, content_height))

    image_byte_array = BytesIO()
    image_byte_array.name = 'schedule.png'
    image.save(image_byte_array, format='PNG')
    image_byte_array.seek(0)

    return image_byte_array

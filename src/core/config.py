import configparser
import json
from typing import TYPE_CHECKING, Optional
from pydantic import BaseModel

class FastAPI(BaseModel):
    ip: str
    port: int

    title: str
    description: str

    root_path: str = '/'


class Telegram(BaseModel):
    bot_token: str

    use_redis: bool = False
    redis_db: Optional[int] = None
    redis_str: Optional[str] = None


class Database(BaseModel):
    host: str
    port: int
    user: str
    password: str
    database_name: str


class Settings(BaseModel):
    owner_telegram_id: int

    log_level: str


class Config:
    if TYPE_CHECKING:
        __raw_data: dict
        __yoyo_raw_data: configparser.ConfigParser

        fastapi: FastAPI
        telegram: Telegram
        settings: Settings
        database: Database

    def __init__(
            self,
            file_path: str = './config.json',
            yoyo_config_path: str = './yoyo.ini'
    ) -> None:
        with open(file_path, 'r', encoding='utf-8') as file:
            self.__raw_data = json.load(file)
        
        self.fastapi = FastAPI(**self.__raw_data['fastapi'])
        self.telegram = Telegram(**self.__raw_data['telegram'])
        self.settings = Settings(**self.__raw_data['settings'])

        if self.__raw_data.get('database'):
            self.database = Database(**self.__raw_data['database'])
        else:
            self.__yoyo_raw_data = configparser.ConfigParser()
            self.__yoyo_raw_data.read(yoyo_config_path)

            database_settings = self.__yoyo_raw_data['DEFAULT']
            self.database = Database(
                host=database_settings['host'],
                port=int(database_settings['port']),
                user=database_settings['user'],
                password=database_settings['password'],
                database_name=database_settings['dbname']
            )


__all__ = ['Config']

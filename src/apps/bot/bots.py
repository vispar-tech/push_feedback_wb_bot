import logging
import os
from base64 import b64decode
from io import BytesIO
from pathlib import Path, PosixPath
from typing import Union

import telebot
from apps.bot.models import TelegramUser
from apps.bot.utils import constants, markups, tools, txts  # noqa
from django.conf import settings
from telebot.apihelper import ApiTelegramException as TelegramException
from telebot.types import (CallbackQuery, InlineKeyboardMarkup, Message,
                           ReplyKeyboardMarkup)

logger = telebot.logger
fh = logging.FileHandler(os.path.join(settings.BASE_DIR, 'logs/bot_log.log'))
logger.addHandler(fh)


class BaseBot(telebot.TeleBot):

    def __init__(self, token, *args, **kwargs):
        self.DEBUG = settings.DEBUG
        self.BASE_DIR = Path(__file__).resolve().parent
        self.TEMPORARY_DIR = os.path.join(self.BASE_DIR, 'temporary_files')
        self.ADMIN_USER_ID = constants.ADMIN_USER_ID
        self.markups = markups.Markups()
        self.logger = logger
        super().__init__(token=token, parse_mode='html', threaded=False, *args, **kwargs)

    def send_admin_message(self, message_text: str) -> Message:
        return self.send(self.ADMIN_USER_ID, message_text)

    def download_file(self, message: Message, file_id: str = None) -> Path:
        if file_id is None:
            file_id = message.document.file_id
            file_name = message.document.file_name
        else:
            file_name = 'photo'
        downloaded_file = super().download_file(self.get_file(file_id).file_path)
        src = os.path.join(self.TEMPORARY_DIR, f'{message.from_user.id}_{file_name}')
        with open(src, 'wb') as new_file:
            new_file.write(downloaded_file)
        return Path(src)

    def log_error(self, error: Exception, exc_info: bool = True):
        if hasattr(self, 'pill2kill'):
            self.stop_loading()
        if hasattr(self, 'loading_message') and self.loading_message is not None:
            self.delete(self.loading_message.chat.id, self.loading_message.id)
            self.loading_message = None
        self.logger.error(error, exc_info=exc_info)

    def send(self, chat_id: int, text: str,
             markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup] = None) -> Message:
        return super().send_message(chat_id, text, parse_mode='html', reply_markup=markup, disable_web_page_preview=True)

    def send_photo(self, chat_id: int, photo: Union[Path, str],
                   caption: str, markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup] = None) -> Message:
        return super().send_photo(chat_id, photo if type(photo) is str else open(photo, 'rb+'), caption=caption, parse_mode='html', reply_markup=markup)

    def send_document(self, chat_id: int, path: Union[Path, PosixPath, str],
                      markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup] = None,
                      caption: str = None, file_name: str = None) -> Message:
        if type(path) is PosixPath or (type(path) is str and path.startswith('/')):
            return super().send_document(chat_id, open(path, 'rb'), reply_markup=markup, caption=caption, parse_mode='html', visible_file_name=file_name)
        else:
            return super().send_document(chat_id, BytesIO(b64decode(path.encode('ascii'))), reply_markup=markup, caption=caption, parse_mode='html', visible_file_name=file_name)

    def delete(self, chat_id: int, message_id: int) -> bool:
        try:
            return super().delete_message(chat_id, message_id)
        except TelegramException:
            pass

    def answer_call(self, call: CallbackQuery, *args, **kwargs):
        super().answer_callback_query(call.id, *args, **kwargs)

    def edit(self, message: Message, text: str, markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup] = None,
             position: int = 0, message_id: int = None):
        if message_id is not None:
            change_id = message_id
        else:
            change_id = message.id + position
        try:
            return super().edit_message_text(text, message.chat.id, change_id, parse_mode='html', reply_markup=markup, disable_web_page_preview=True)
        except TelegramException:
            pass

    def _delete_file(self, path: Union[Path, list, tuple]) -> None:
        if type(path) is list or type(path) is tuple:
            for file in path:
                os.remove(file)
        os.remove(path)


class Bot(BaseBot):

    def __init__(self, *kwargs) -> None:
        self.token = settings.TELEGRAM_BOT_TOKEN
        # self.set_my_commands(
        #     commands=[]
        # )
        super().__init__(token=self.token, *kwargs)

    def get_user(self, user_id: int) -> TelegramUser:
        """
            Get telegram user object

            :return TelegramUser:
        """
        return TelegramUser.objects.get(user_id=user_id)

    def is_new_user(self, message: Message) -> bool:
        """
            Check if user is new or already exists in database

            :return bool:
        """
        return not TelegramUser.objects.filter(user_id=message.from_user.id).exists()

    def kick_user(self, user_id: int):
        """
            If user blocked bot when set unactive to True
        """
        if isinstance(user_id, str) and user_id.is_digit():
            user_id = int(user_id)
        if TelegramUser.objects.filter(user_id=user_id).exists():
            user = TelegramUser.objects.get(user_id=user_id)
            user.unactive = True
            user.save()

    def register_new_user(self, message: Message) -> None:
        """
            Recieve contact from message and create new user
        """
        if not TelegramUser.objects.filter(user_id=message.contact.user_id).exists():
            TelegramUser.objects.create(user_id=message.contact.user_id, username=message.from_user.username, phone_number=message.contact.phone_number)
        self.send(message.chat.id, 'Now you are registered in Django Telegram Bot', self.markups.welcome())

    def send_register_message(self, message: Message) -> Message:
        """
            Send message with keyboard to recieve contact from user
        """
        return self.send(message.chat.id, '<b>To register in the bot, you need to send a contact, if you agree, then click on the button below▶️</b>', self.markups.register())

    def send_welcome_message(self, message: Message) -> Message:
        """
            Send welcome text message
        """
        return self.send(message.chat.id, txts.welcome_text, self.markups.welcome())

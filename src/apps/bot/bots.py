import logging
import os
import threading
import time
from base64 import b64decode
from io import BytesIO
from pathlib import Path, PosixPath
from typing import Optional, Union

import telebot
from apps.bot.models import TelegramUser
from apps.bot.utils import constants, markups, tools, txts
from apps.bot.utils.tools import WBPersonalApiClient
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

    def send_error_message(self, chat_id: int) -> Message:
        return self.send(chat_id, txts.error_text)

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
        if type(photo) is PosixPath or (type(photo) is str and photo.startswith('/')):
            return super().send_photo(chat_id, photo if type(photo) is str else open(photo, 'rb+'), caption=caption, parse_mode='html', reply_markup=markup)
        else:
            return super().send_photo(chat_id, BytesIO(b64decode(photo.encode('ascii'))), caption=caption, parse_mode='html', reply_markup=markup)

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

    def loading(self, stop_event: threading.Event, message: Message, text: str, step: int, send: bool = True, markup: Optional[Union[InlineKeyboardMarkup, ReplyKeyboardMarkup]] = None) -> None:
        loading = {
            2: '...',
            1: '..',
            0: '.'
        }
        sim = 0
        if send:
            self.loading_message = self.send(message.chat.id, f'<b>{text}</b>', markup)
        while not stop_event.wait(1):
            time.sleep(0.2)
            self.loading_message = self.edit(message, f'<b>{text}{loading[sim]}</b>', markup, position=step)
            sim += 1
            if sim == 3:
                sim = 0

    def start_loading(self, message: Message, text: str, step: int = 1, send: bool = True, markup: Optional[Union[InlineKeyboardMarkup, ReplyKeyboardMarkup]] = None) -> None:
        self.pill2kill = threading.Event()
        t = threading.Thread(target=self.loading, args=(self.pill2kill, message, text, step, send, markup))
        t.start()
        self.loading_thread = t

    def stop_loading(self) -> None:
        self.pill2kill.set()
        self.loading_thread.join()


class Bot(BaseBot):

    def __init__(self, *kwargs) -> None:
        self.token = settings.TELEGRAM_BOT_TOKEN
        # self.set_my_commands(
        #     commands=[
        #         telebot.types.BotCommand("my", "👨🏼‍💼 Мои кабинеты"),
        #         telebot.types.BotCommand("articles", "🏷 Список отслеживаемых артикулов"),
        #         telebot.types.BotCommand("settings", "⚙️ Настройки"),
        #     ]
        # )
        super().__init__(token=self.token, *kwargs)

    def get_user(self, user_id: int) -> TelegramUser:
        """
            Возвращает объект пользователя телеграмма

            :return TelegramUser:
        """
        return TelegramUser.objects.get(user_id=user_id)

    def get_client(self, user: TelegramUser) -> WBPersonalApiClient:
        """
            Возвращает клиент для пользователя
        """
        return WBPersonalApiClient(WBToken=user.WBToken)

    def is_new_user(self, message: Message) -> bool:
        """
            Проверяет есть ли такой пользователь в базе данныъ

            :return bool:
        """
        return not TelegramUser.objects.filter(user_id=message.from_user.id).exists()

    def kick_user(self, user_id: int):
        """
            Если пользователь блокирует бота то ставит unactive в True
        """
        if isinstance(user_id, str) and user_id.is_digit():
            user_id = int(user_id)
        if TelegramUser.objects.filter(user_id=user_id).exists():
            user = TelegramUser.objects.get(user_id=user_id)
            user.unactive = True
            user.save()

    def register_new_user(self, message: Message) -> None:
        """
            Обрабатываем отправленный пользователем контает и создаем объект пользователя в базе данных
        """
        if not TelegramUser.objects.filter(user_id=message.contact.user_id).exists():
            TelegramUser.objects.create(user_id=message.contact.user_id, username=message.from_user.username, phone_number=message.contact.phone_number)
        self.send(message.chat.id, 'Теперь вы зарегистрированны в Джанго телеграмм боте!', self.markups._remove())

    def send_register_message(self, message: Message) -> Message:
        """
            Отправляет сообщение с клавиатурой для отправки контакта пользователем
        """
        return self.send(message.chat.id, '<b>Для регистрации в боте необходимо отправить контакт, если вы согласны, то нажмите на кнопку ниже⤵️</b>', self.markups.register())

    def send_welcome_message(self, message: Message) -> Message:
        """
            Отправляет привественное сообщение
        """
        return self.send(message.chat.id, txts.welcome_text, self.markups._remove())

    def send_my_personals(self, message: Message) -> Message:
        user = self.get_user(message.from_user.id)
        if user.WBToken is None:
            return self.send(message.chat.id, '<b>🤷🏼Авторизуйтесь в кабинете Wildberries по кнопке ниже ⤵️</b>', self.markups.authorize_wb())
        else:
            if len(user.personal_set.all()) == 0:
                user.reset_temp_token()
                user.WBToken = None
                user.save()
                return self.send(message.chat.id, '<b>🤷🏼‍♂️ К сожалению у вас нет ни одного кабинета</b>', self.markups.authorize_wb())
            else:
                message_text = '<b>👨🏼‍💼 Список ваших кабинетов:</b>\n\n'
                for i, personal in enumerate(user.personal_set.all()):
                    message_text += '<b>%i.</b> <i>%s</i>\n' % (i+1, personal.name)
                return self.send(message.chat.id, message_text, self.markups.logout_wb())

    def process_wb(self, call: CallbackQuery) -> Message:
        user = self.get_user(call.from_user.id)
        if 'auth' in call.data:
            if 'code_received' in call.data:
                return self.register_next_step_handler(
                    self.edit(call.message, '<b>🔢 Введите код из клиентского приложения Wildberries или раздела на сайте...</b>', self.markups.authorize_wb_cancel()),
                    self.fetch_verification_code_to_authorize_wb,
                    message_to_edit_id=call.message.message_id
                )
            elif 'code_no_received' in call.data:
                return self.edit(call.message, '<b>Попробуйте авторизоваться снова🤷🏼‍♂️</b>', self.markups.authorize_wb())
            elif 'back' in call.data:
                user.reset_temp_token()
                return self.edit(call.message, '<b>Авторизуйтесь в кабинете Wildberries по кнопке ниже ⤵️</b>', self.markups.authorize_wb())
            else:
                return self.register_next_step_handler(
                    self.edit(call.message, '<b>📱 Введите номер телефона привязанный к Wildberries...</b>\n<i>Например:</i> <code>+79999999999</code>', self.markups.authorize_wb_cancel()),
                    self.fetch_phone_number_to_authorize_wb,
                    message_to_edit_id=call.message.message_id
                )
        elif 'back' in call.data:
            self.clear_step_handler_by_chat_id(call.message.chat.id)
            return self.edit(call.message, '<b>Авторизуйтесь в кабинете Wildberries по кнопке ниже ⤵️</b>', self.markups.authorize_wb())

    def fetch_phone_number_to_authorize_wb(self, message: Message, message_to_edit_id: int = None) -> Message:
        self.delete(message.chat.id, message.id)
        phone_number = message.text
        user = self.get_user(message.from_user.id)
        client = self.get_client(user)
        response = client.send_login_code(phone_number)
        if response[0]:
            user.set_temp_token(response[1]['token'])
            return self.edit(message, '<i>✅💌 Код отправлен в клиентское приложение или раздел на <a href="https://www.wildberries.ru/lk/newsfeed/events">сайте</a></i>\nНа номер <b>%s</b>' % phone_number, self.markups.confirm_code_received(), message_id=message_to_edit_id)
        return self.edit(message, '<b>🤷🏼‍♂️ Похоже был введен неверный номер телефона</b>\n<i>Ошибка: %s</i>' % response[1], self.markups.authorize_wb(), message_id=message_to_edit_id)

    def fetch_verification_code_to_authorize_wb(self, message: Message, message_to_edit_id: int = None) -> Message:
        self.delete(message.chat.id, message.id)
        verify_code = message.text
        user = self.get_user(message.from_user.id)
        client = self.get_client(user)
        response = client.verify_login_code(user.temp_token, verify_code)
        if response[0]:
            user.set_WBToken(response[1]['WBToken'])
            user = self.get_user(message.from_user.id)
            suppliers = tools.get_suppliers(user)
            if suppliers[0] is None:
                return self.edit(message, '%s🤷🏼‍♂️' % suppliers[1], self.markups.authorize_wb(), message_id=message_to_edit_id)
            elif suppliers[0] is False:
                return self.edit(message, '%s🤷🏼‍♂️' % suppliers[1], message_id=message_to_edit_id)
            else:
                message_text = '<b>✅ Добавлено поставщиков: %i</b>\n<b>👨🏼‍💼 Список ваших кабинетов:</b>\n\n' % len(suppliers[1])
                for i, personal in enumerate(suppliers[1]):
                    message_text += '<b>%i.</b> <i>%s</i>\n' % (i+1, personal.name)
                return self.edit(message, message_text, self.markups.logout_wb(), message_id=message_to_edit_id)
        else:
            return self.register_next_step_handler(
                self.edit(message, '<b>🤷🏼‍♂️ Похоже вы ввели неверный код, попробуйте ввести код еще раз...</b>\n<i>Ошибка: %s</i>' % response[1], self.markups.authorize_wb_cancel(), message_id=message_to_edit_id),
                self.fetch_verification_code_to_authorize_wb,
                message_to_edit_id=message_to_edit_id
            )

    def send_tracked_articles(self, message: Message) -> Message:
        user = self.get_user(message.from_user.id)
        articles = tools.get_tracked_articles(user)
        if articles[0] is None:
            return self.send(message.chat.id, '<b>🤷🏼‍♂️ %s</b>' % articles[1], self.markups.tracked_articles())
        elif articles[0] is False:
            return self.send(message.chat.id, '<b>🤷🏼‍♂️ %s</b>' % articles[1])
        else:
            message_text = '<b>🕵️‍♀️ Список отслеживаемых артикулов:</b>\n'
            for i, article in enumerate(articles[1][:20]):
                message_text += '<b>%i.</b> <a href="https://www.wildberries.ru/catalog/%s/detail.aspx?targetUrl=SP">%s</a> | <i>%s</i>\n' % (i+1, article.nmId, article.nmId, article.article)
            if len(articles[1]) > 20:
                message_text += '<i>и еще %i шт.</i>' % (len(articles[1]) - 20)
            message_text += '\n\n<i>🔢 Всего: %i</i>\n' % len(articles[1])
            return self.send(message.chat.id, message_text, self.markups.tracked_articles(with_excel=True if len(articles[1]) > 20 else False, delete_button=True))

    def process_tracked_articles(self, call: CallbackQuery) -> Message:
        user = self.get_user(call.from_user.id)
        if 'excel' in call.data:
            file = tools.get_tracked_articles_excel(user)
            if file[0] is False or file[0] is None:
                return self.send(call.message.chat.id, '<b>🤷🏼‍♂️ %s</b>' % file[1])
            return self.send_document(call.message.chat.id, file[1], caption='<b>🕵️‍♀️ Excel файл отслеживаемых артикулов</b>', file_name='Excel файл отслеживаемых артикулов.xlsx')
        elif 'add' in call.data:
            if 'personal' in call.data:
                if 'page' in call.data:
                    page = tools.get_personals_pages_current_page(call.message.reply_markup.keyboard)
                    if 'next' in call.data:
                        page += 1
                        return self.edit(call.message, '<b>👨🏼‍💼 Выберите кабинет в котором будем искать артикул:</b>', self.markups.personals(user.personal_set.all(), take=page * constants.PERSONAL_PAGES_ITEMS_PER_PAGE + constants.PERSONAL_PAGES_ITEMS_PER_PAGE, offset=page * constants.PERSONAL_PAGES_ITEMS_PER_PAGE))
                    elif 'back' in call.data:
                        page -= 1
                        return self.edit(call.message, '<b>👨🏼‍💼 Выберите кабинет в котором будем искать артикул:</b>', self.markups.personals(user.personal_set.all(), take=page * constants.PERSONAL_PAGES_ITEMS_PER_PAGE + constants.PERSONAL_PAGES_ITEMS_PER_PAGE, offset=page * constants.PERSONAL_PAGES_ITEMS_PER_PAGE))
                    else:
                        self.answer_call(call)
                else:
                    personal_id = call.data.split('-')[-1]
                    if user.personal_set.filter(id=int(personal_id)).exists():
                        personal = user.personal_set.get(id=int(personal_id))
                        self.delete(call.message.chat.id, call.message.message_id)
                        self.start_loading(call.message, '🏷 Загрузка товаров кабинета %s' % personal.name)
                        file = tools.get_personal_cards_excel(user, personal)
                        self.stop_loading()
                        self.delete_message(call.message.chat.id, self.loading_message.id)
                        if file[0] is None or file[0] is False:
                            return self.edit(call.message, '<b>🤷🏼‍♂️ %s</b>' % file[1])
                        else:
                            return self.register_next_step_handler(
                                self.send_document(call.message.chat.id, file[1], self.markups.add_tracked_article_back(), '<b>✅ Выбран кабинет <i>%s</i></b>\n<i>🏷 Скачайте файл и заполните артикулы за отзывами которых вы хотите следить, после отправьте файл боту</i>' % personal, 'Товары кабинета.xlsx'),
                                self.find_personal_articles_to_track,
                                personal_id=personal.id
                            )
                    else:
                        return self.edit(call.message, '<b>🤷🏼‍♂️ Выбраного кабинета не существует</b>')
            elif 'back' in call.data:
                self.delete(call.message.chat.id, call.message.message_id)
                articles = tools.get_tracked_articles(user)
                if articles[0] is None:
                    return self.edit(call.message, '<b>🤷🏼‍♂️ %s</b>' % articles[1], self.markups.tracked_articles())
                elif articles[0] is False:
                    return self.edit(call.message, '<b>🤷🏼‍♂️ %s</b>' % articles[1])
                else:
                    message_text = '<b>🕵️‍♀️ Список отслеживаемых артикулов:</b>\n'
                    for i, article in enumerate(articles[1][:20]):
                        message_text += '<b>%i.</b> <a href="https://www.wildberries.ru/catalog/%s/detail.aspx?targetUrl=SP">%s</a> | <i>%s</i>\n' % (i+1, article.nmId, article.nmId, article.article)
                    if len(articles[1]) > 20:
                        message_text += '<i>и еще %i шт.</i>' % (len(articles[1]) - 20)
                    message_text += '\n\n<i>🔢 Всего: %i</i>\n' % len(articles[1])
                    return self.send(call.message.chat.id, message_text, self.markups.tracked_articles(with_excel=True if len(articles[1]) > 20 else False, delete_button=True))
            else:
                self.clear_step_handler_by_chat_id(call.message.chat.id)
                self.delete(call.message.chat.id, call.message.message_id)
                return self.send(call.message.chat.id, '<b>👨🏼‍💼 Выберите кабинет в котором будем искать артикул:</b>', self.markups.personals(user.personal_set.all()))
        elif 'remove' in call.data:
            self.delete(call.message.chat.id, call.message.message_id)
            file = tools.get_tracked_articles_excel(user, to_delete=True)
            if file[0]:
                return self.register_next_step_handler(
                    self.send_document(call.message.chat.id, file[1], self.markups.remove_tracked_article_back(), '<b>🏷 Скачайте файл и заполните артикулы за отзывами которых вы хотите следить, после отправьте файл боту</b>', 'Отслеживаемые артикулы.xlsx'),
                    self.remove_articles_from_track
                )
            else:
                return self.edit(call.message, '<b>🤷🏼‍♂️ %s</b>' % file[1])

    def find_personal_articles_to_track(self, message: Message, personal_id: int) -> Message:
        self.delete(message.chat.id, message.id)
        self.delete(message.chat.id, message.id-1)
        user = self.get_user(message.from_user.id)
        if user.personal_set.filter(id=int(personal_id)).exists():
            personal = user.personal_set.get(id=int(personal_id))
            file = self.download_file(message)
            added_articles = tools.add_articles_to_track(personal, file)
            tools.delete_files([file])
            if added_articles[0]:
                if len(added_articles[1]) == 0:
                    return self.send(message.chat.id, '<b>🤷🏼‍♂️ Вы не выбрали ни одного артикула для отслеживания</b>')
                message_text = '<b>✅ Всего добавлено артикулов в отслеживание: %i</b>\n' % len(added_articles[1])
                message_text += '<b>🏷 Список артикулов:</b>\n'
                for i, article in enumerate(added_articles[1][:20]):
                    message_text += '<b>%i.</b> <a href="https://www.wildberries.ru/catalog/%s/detail.aspx?targetUrl=SP">%s</a> | <i>%s</i>\n' % (i+1, article.nmId, article.nmId, article.article)
                if len(added_articles[1]) > 20:
                    message_text += '<i>и еще %i шт.</i>' % (len(added_articles[1]) - 20)
                return self.send(message.chat.id, message_text)
            else:
                return self.send(message.chat.id, '<b>🤷🏼‍♂️ %s</b>' % added_articles[1])
        else:
            return self.send(message.chat.id, '<b>🤷🏼‍♂️ Выбраного кабинета не существует</b>')

    def remove_articles_from_track(self, message: Message) -> Message:
        self.delete(message.chat.id, message.id)
        self.delete(message.chat.id, message.id-1)
        user = self.get_user(message.from_user.id)
        file = self.download_file(message)
        removed_articles = tools.remove_articles_from_track(user, file)
        tools.delete_files([file])
        if removed_articles[0]:
            if len(removed_articles[1]) == 0:
                return self.send(message.chat.id, '<b>🤷🏼‍♂️ Вы не выбрали ни одного артикула для удаления из отслеживания</b>')
            message_text = '<b>✅ Всего удалено %i артикулов из отслеживания</b>\n' % len(removed_articles[1])
            message_text += '<b>🏷 Список артикулов:</b>\n'
            for i, article in enumerate(removed_articles[1][:20]):
                message_text += '<b>%i.</b> <a href="https://www.wildberries.ru/catalog/%s/detail.aspx?targetUrl=SP">%s</a> | <i>%s</i>\n' % (i+1, article.nmId, article.nmId, article.article)
            if len(removed_articles[1]) > 20:
                message_text += '<i>и еще %i шт.</i>' % (len(removed_articles[1]) - 20)
            return self.send(message.chat.id, message_text)
        else:
            return self.send(message.chat.id, '<b>🤷🏼‍♂️ %s</b>' % removed_articles[1])

    def settings(self, message: Message) -> Message:
        user = self.get_user(message.from_user.id)
        return self.send(message.chat.id, self.get_settings_text(user), self.markups.settings(user))

    def get_settings_text(self, user: TelegramUser) -> Message:
        total_articles = 0
        tracked_articles = tools.get_tracked_articles(user)
        if tracked_articles[0]:
            total_articles = len(tracked_articles[1])
        return f'<b>🔢 ID:</b> <code>{user.user_id}</code>\n<b>👨🏼‍💼 Поставщики:</b> {len(user.personal_set.all())}\n<b>🏷 Всего артикулов на отслеживании:</b>: {total_articles} шт.\n<b>🔔 Уведомление придет если оценка отзыва будет меньше или равна </b> {tools.get_stars_display(user)}'

    def settings_process(self, call: CallbackQuery) -> Message:
        user = self.get_user(call.from_user.id)
        if 'change_stars' in call.data:
            self.delete(call.message.chat.id, call.message.message_id)
            return self.register_next_step_handler(
                self.send(call.message.chat.id, '<b>🔔 На данный момент уведомления приходят об отзывах с оценкой ниже или равной %s</b>\n<b>Введите число от 1 до 5...</b>' % tools.get_stars_display(user), self.markups.cancel_change_stars()),
                self.change_stars_process
            )
        elif 'notification' in call.data:
            if 'off' in call.data:
                user.notification = False
            elif 'on' in call.data:
                user.notification = True
            user.save()
            return self.edit(call.message, self.get_settings_text(user), self.markups.settings(user))
        elif 'back' in call.data:
            return self.edit(call.message, self.get_settings_text(user), self.markups.settings(user))

    def change_stars_process(self, message: Message):
        self.delete(message.chat.id, message.id)
        self.delete(message.chat.id, message.id-1)
        try:
            if int(message.text) > 0 and int(message.text) <= 5:
                user = self.get_user(message.from_user.id)
                user.notification_stars = int(message.text)
                user.save()
                return self.send(message.chat.id, self.get_settings_text(user), self.markups.settings(user))
            else:
                return self.register_next_step_handler(
                    self.send(message.chat.id, '<b>🤷🏼‍♂️ Неверное число, введите число в диапазоне от 1 до 5...</b>', self.markups.cancel_change_stars()),
                    self.change_stars_process
                )
        except ValueError:
            return self.register_next_step_handler(
                self.send(message.chat.id, '<b>🤷🏼‍♂️ Это не похоже на число, введите число в диапазоне от 1 до 5...</b>', self.markups.cancel_change_stars()),
                self.change_stars_process
            )

    def notify_new_feedback(self, feedback: object):
        if len(feedback.feedbackphoto_set.all()) != 0:
            return self.send_photo(feedback.article.personal.user.user_id, tools.merge_card_images([photo.url for photo in feedback.feedbackphoto_set.all()]), feedback.format_notification_message(), self.markups.href_nmid(feedback.article.nmId))
        else:
            return self.send(feedback.article.personal.user.user_id, feedback.format_notification_message(), self.markups.href_nmid(feedback.article.nmId))

# Пропишите markup клавиатур для ботов здесь
from apps.bot.utils import constants
from django.db.models import QuerySet
from telebot.callback_data import CallbackData
from telebot.types import (InlineKeyboardButton, InlineKeyboardMarkup,  # noqa
                           KeyboardButton, ReplyKeyboardMarkup,
                           ReplyKeyboardRemove)

personals_factory = CallbackData('personal_id', prefix='tracked_articles:add:personal', sep='-')


class Markups:

    def __init__(self) -> None:
        pass

    def _remove(self):
        return ReplyKeyboardRemove()

    def register(self) -> ReplyKeyboardMarkup:
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row(KeyboardButton('👤 Отправить контакт 👤', request_contact=True))
        return markup

    def personals(self, personals: QuerySet, take: int = constants.PERSONAL_PAGES_ITEMS_PER_PAGE, offset: int = 0) -> InlineKeyboardMarkup:
        markup = InlineKeyboardMarkup(
            keyboard=[
                [
                    InlineKeyboardButton(
                        text=personal.name,
                        callback_data=personals_factory.new(personal_id=personal.id)
                    )
                ]
                for personal in personals[offset:take]
            ]
        )
        if len(personals) > constants.PERSONAL_PAGES_ITEMS_PER_PAGE:
            if offset == 0:
                markup.row(InlineKeyboardButton('⏩', callback_data='tracked_articles:add:personal:page:next'))
            elif take >= len(personals):
                markup.row(InlineKeyboardButton('⏪', callback_data='tracked_articles:add:personal:page:back'))
            else:
                markup.row(
                    InlineKeyboardButton('⏪', callback_data='tracked_articles:add:personal:page:back'),
                    InlineKeyboardButton('⏩', callback_data='tracked_articles:add:personal:page:next')
                )
            page = round(offset / constants.PERSONAL_PAGES_ITEMS_PER_PAGE)
            total_pages = round(len(personals) / constants.PERSONAL_PAGES_ITEMS_PER_PAGE)
            markup.row(InlineKeyboardButton(f'📄 Страница {(page + 1)} из {(total_pages + 1)}', callback_data='tracked_articles:add:personal:page:%s' % page))
        markup.row(InlineKeyboardButton('↩️ Вернуться в меню', callback_data='tracked_articles:add:back'))
        return markup

    def authorize_wb(self):
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton('🟣 Авторизоваться в кабинете 🟣', callback_data='wb:auth'))
        return markup

    def logout_wb(self):
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton('🚪 Выйти из кабинета 🚪', callback_data='wb:logout'))
        return markup

    def confirm_code_received(self):
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton('✅ Код пришел', callback_data='wb:auth:code_received'))
        markup.row(InlineKeyboardButton('❌ Кода нет', callback_data='wb:auth:code_no_received'))
        markup.row(InlineKeyboardButton('⏪ Назад', callback_data='wb:auth:back'))
        return markup

    def authorize_wb_cancel(self):
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton('⏪ Назад', callback_data='wb:back'))
        return markup

    def tracked_articles(self, with_excel: bool = False, delete_button: bool = False):
        markup = InlineKeyboardMarkup()
        if with_excel:
            markup.row(InlineKeyboardButton('🗂 Скачать Excel 🗂', callback_data='tracked_articles:excel'))
        if delete_button:
            markup.row(InlineKeyboardButton('❌ Удалить артикул', callback_data='tracked_articles:remove'))
        markup.row(InlineKeyboardButton('✅ Добавить артикул', callback_data='tracked_articles:add'))
        return markup

    def add_tracked_article_back(self):
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton('⏪ Назад', callback_data='tracked_articles:add'))
        return markup

    def remove_tracked_article_back(self):
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton('⏪ Назад', callback_data='tracked_articles:add:back'))
        return markup

    def settings(self, user: object):
        markup = InlineKeyboardMarkup()
        if user.notification:
            markup.row(InlineKeyboardButton('✅ Уведомления', callback_data='settings:notification:off'))
        else:
            markup.row(InlineKeyboardButton('⭕️ Увед. выключены (включить?)', callback_data='settings:notification:on'))
        markup.row(InlineKeyboardButton('🔄 Изменить кол-во звезд', callback_data='settings:change_stars'))
        return markup

    def cancel_change_stars(self):
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton('⏪ Назад', callback_data='settings:back'))
        return markup

    def href_nmid(self, nmid: str):
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton('Открыть на WB🟪', url=f'https://www.wildberries.ru/catalog/{nmid}/detail.aspx?targetUrl=SP'))
        return markup

from apps.bot.bots import Bot
from django.conf import settings
from django.core.management import BaseCommand
from django.utils import autoreload

bot = Bot()


def restart_bot():
    bot.enable_save_next_step_handlers()
    bot.load_next_step_handlers()
    while True:
        try:
            print(f'Bot {bot.get_me().first_name}(@{bot.get_me().username}) started!')
            bot.polling(none_stop=True, timeout=360)
        except Exception as e:
            print(f'Bot {bot.get_me().first_name}(@{bot.get_me().username}) restarted by exception')
            bot.logger.error(e, exc_info=True)
            continue


class Command(BaseCommand):
    help = 'Run Telegram BOT'

    def handle(self, *args, **kwargs):
        if settings.DEBUG:
            autoreload.run_with_reloader(restart_bot)
        else:
            restart_bot()


@bot.my_chat_member_handler(func=lambda member: member.new_chat_member.status == 'kicked')
def bot_kicked(member):
    bot.kick_user(member.from_user.id)


@bot.message_handler(content_types=['contact'])
def recieve_contact(message):
    if message.contact.user_id == message.from_user.id:
        bot.register_new_user(message)
    else:
        bot.register_next_step_handler(bot.send(message.chat.id, '<b>Unfortunately, it doesn`t look like a your contact, try send again🤷🏼‍♂️</b>', bot.markups.register()), recieve_contact)


@bot.message_handler(commands=['start'])
def start(message):
    if bot.is_new_user(message):
        bot.send_register_message(message)
    else:
        bot.send_welcome_message(message)


@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    pass


@bot.message_handler(content_types=['text'])
def message_handler(message):
    pass

from apps.bot.models import TelegramUser
from django.contrib import admin


@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):
    pass

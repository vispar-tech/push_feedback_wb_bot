from apps.polls.models import Feedback, FeedbackPhoto, Personal, TrackedArticle
from django.contrib import admin  # noqa


@admin.register(Personal)
class PersonalAdmin(admin.ModelAdmin):
    pass


@admin.register(TrackedArticle)
class TrackedArticleAdmin(admin.ModelAdmin):
    pass


class FeedbackPhotoInline(admin.TabularInline):
    model = FeedbackPhoto
    extra = 1
    show_change_link = True


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    inlines = (FeedbackPhotoInline, )
    list_display = ('id', 'article', 'stars')

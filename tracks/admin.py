from django.contrib import admin

from . import models


@admin.register(models.Track)
class TrackAdmin(admin.ModelAdmin):
    list_display = ('song', 'file', 'stem')
    list_filter = ('stem',)
    search_fields = ('file',)
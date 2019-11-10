from django.contrib import admin

from tracks.models import Track
from . import models


class TrackInline(admin.TabularInline):
    model = Track
    extra = 0


@admin.register(models.Song)
class SongAdmin(admin.ModelAdmin):
    fields = ('file', 'url')
    list_display = ('name', 'spleeter_task_status')
    search_fields = ('name',)
    inlines = [TrackInline]

    def spleeter_task_status(self, obj):
        task = obj.spleeter_tasks.last()
        if task and task.result:
            return task.result.status

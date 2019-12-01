import os
from django.contrib import admin

from tracks.models import Track
from songs.tasks import generate_tracks, download_song_from_url
from . import models


class TrackInline(admin.TabularInline):
    model = Track
    extra = 0


@admin.register(models.Song)
class SongAdmin(admin.ModelAdmin):
    fields = ('file', 'url')
    list_display = (
        'name', 
        'file_exists', 
        'last_task_status',
        'last_task_date_done'
    )
    search_fields = ('name',)
    
    inlines = [TrackInline]
    
    actions = [
        'generate_tracks', 
        'download_from_url'
    ]

    def last_task_status(self, obj):
        try:
            task = obj.processing_tasks.last()
            return f"[{task.result.status}] {task.description}"
        except:
            pass

    def last_task_date_done(self, obj):
        try:
            return obj.processing_tasks.last().result.date_done
        except:
            pass

    def file_exists(self, obj):
        if obj.file:
            return os.path.exists(obj.file.path)
    
    file_exists.boolean = True

    def generate_tracks(self, request, queryset):
        for song in queryset:
            generate_tracks.delay(song.pk)

    def download_from_url(self, request, queryset):
        for song in queryset:
            download_song_from_url.delay(song.pk)


@admin.register(models.SongTask)
class SongTaskAdmin(admin.ModelAdmin):
    list_display = (
        'song',
        'description', 
        'status', 
        'date_done'
    )

    def status(self, obj):
        try:
            return obj.result.status
        except:
            pass

    def date_done(self, obj):
        try:
            return obj.result.date_done
        except:
            pass

    def has_add_permission(self, request):
        return False
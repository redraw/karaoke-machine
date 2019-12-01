import os

from django.db import models
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
from django.core.files import File

from celery.result import AsyncResult

from .tasks import generate_tracks, download_song_from_url


class Song(models.Model):
    name = models.CharField(_('Name'), max_length=128, blank=True)
    url = models.CharField(max_length=256, blank=True)

    file = models.FileField(
        upload_to='songs', 
        null=True, 
        blank=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=[
                    'wav',
                    'mp3'
                ]
            )
        ]
    )

    def __str__(self):
        return self.name or str(self.pk)

    def save(self, *args, **kwargs):
        if not self.name:
            self.name = str(self.file) or self.url
        super().save(*args, **kwargs)

    def download_from_url(self, delay=False):
        if not delay:
            return download_song_from_url(self.pk)
        return download_song_from_url.delay(self.pk)

    def clean(self):
        if not (self.file or self.url):
            raise ValidationError(_('Must have file or url'))


class SongTask(models.Model):
    task_id = models.UUIDField()
    description = models.CharField(max_length=128, blank=True, null=True)

    song = models.ForeignKey(
        Song, 
        on_delete=models.CASCADE, 
        related_name='processing_tasks'
    )

    def __str__(self):
        return str(self.task_id)

    @property
    def result(self):
        return AsyncResult(str(self.task_id))


@receiver(post_save, sender=Song)
def song_saved(sender, instance, **kwargs):
    if kwargs.get('created', False):
        if not instance.file and instance.url:
            transaction.on_commit(lambda: download_song_from_url.delay(instance.pk))
        
import os

from django.db import models
from django.db import transaction
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

from celery.result import AsyncResult

from .tasks import generate_tracks


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
        if self.file:
            self.name = os.path.basename(self.file.path)

        super().save(*args, **kwargs)

        if not self.tracks.exists():
            transaction.on_commit(lambda: generate_tracks.delay(self.pk))


    def clean(self):
        if not (self.file or self.url):
            raise ValidationError(_('Must have file or url'))


class SpleeterTask(models.Model):
    task_id = models.UUIDField()

    song = models.ForeignKey(
        Song, 
        on_delete=models.CASCADE, 
        related_name='spleeter_tasks'
    )

    def __str__(self):
        return str(self.task_id)

    @property
    def result(self):
        return AsyncResult(str(self.task_id))
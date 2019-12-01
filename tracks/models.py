from django.db import models
from django.conf import settings
from django.utils.translation import gettext as _


class Track(models.Model):
    INSTRUMENTAL = 'instrumental'
    VOICE = 'voice'

    STEM_CHOICES = (
        (INSTRUMENTAL, _('Instrumental')),
        (VOICE, _('Voice'))
    )

    song = models.ForeignKey('songs.Song', on_delete=models.CASCADE, related_name='tracks')
    file = models.FileField(upload_to=settings.SPLEETER_UPLOAD_TO, null=True, blank=True)
    stem = models.CharField(choices=STEM_CHOICES, max_length=32)

    def __str__(self):
        return f"{self.stem}:{str(self.file)}"
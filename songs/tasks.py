import os
from pathlib import Path
from django.apps import apps
from django.conf import settings

from celery import shared_task
from celery.utils.log import get_task_logger
from spleeter.separator import Separator


logger = get_task_logger(__name__)
separator = Separator('spleeter:2stems')


@shared_task(bind=True)
def generate_tracks(self, song_pk):
    Song = apps.get_model('songs.Song')
    Track = apps.get_model('tracks.Track')
    SpleeterTask = apps.get_model('songs.SpleeterTask')

    song = Song.objects.get(pk=song_pk)
    task = SpleeterTask.objects.create(task_id=self.request.id, song=song)

    codec = settings.SPLEETER_PARAMS.get('codec')
    
    output_relpath = os.path.join(
        settings.SPLEETER_UPLOAD_TO, 
        Path(song.file.path).stem
    )
    
    logger.info(f"Processing {song.file.path}...")

    # Spleet
    separator.separate_to_file(
        song.file.path,
        os.path.join(settings.MEDIA_ROOT, output_relpath),
        **settings.SPLEETER_PARAMS
    )

    instrumental_relpath = os.path.join(output_relpath, f"accompaniment.{codec}")
    voice_relpath = os.path.join(output_relpath, f"vocals.{codec}")

    logger.info("Finished separator.")

    # Create instrumental track
    if os.path.exists(
        os.path.join(settings.MEDIA_ROOT, instrumental_relpath)
    ):
        t1 = Track(song=song, stem=Track.INSTRUMENTAL)
        t1.file.name = instrumental_relpath
        t1.save()

    # Create voice track
    if os.path.exists(
        os.path.join(settings.MEDIA_ROOT, voice_relpath)
    ):
        t2 = Track(song=song, stem=Track.VOICE)
        t2.file.name = voice_relpath
        t2.save()

    # Delete original song file
    song.file.delete()
    
    logger.info("Done.")
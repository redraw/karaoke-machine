import os
import tempfile
import shutil
from pathlib import Path
from django.apps import apps
from django.conf import settings
from django.core.files import File
from django.utils.text import get_valid_filename

from celery import shared_task
from celery.utils.log import get_task_logger
from spleeter.separator import Separator
from youtube_dl import YoutubeDL


logger = get_task_logger(__name__)
separator = Separator('spleeter:2stems')


@shared_task(bind=True)
def generate_tracks(self, song_pk):
    Song = apps.get_model('songs.Song')
    Track = apps.get_model('tracks.Track')
    SongTask = apps.get_model('songs.SongTask')

    song = Song.objects.get(pk=song_pk)
    task = SongTask.objects.create(
        task_id=self.request.id, 
        description="Generate tracks",
        song=song
    )
    
    output_relpath = os.path.join(
        settings.SPLEETER_UPLOAD_TO, 
        Path(song.file.path).stem
    )

    logger.info(f"Processing {song.file.path}...")

    # Spleet
    separator.separate_to_file(
        song.file.path,
        os.path.join(settings.MEDIA_ROOT, settings.SPLEETER_UPLOAD_TO),
        **settings.SPLEETER_PARAMS
    )

    codec = settings.SPLEETER_PARAMS.get('codec')
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
    
    logger.info("Done.")


@shared_task(bind=True)
def download_song_from_url(self, song_pk):
    Song = apps.get_model('songs.Song')
    SongTask = apps.get_model('songs.SongTask')
    
    song = Song.objects.get(pk=song_pk)
    task = SongTask.objects.create(
        task_id=self.request.id, 
        description="Download song from URL",
        song=song
    )

    outdir = tempfile.mkdtemp()
    
    opts = dict(
        **settings.YOUTUBE_DL_OPTS,
        outtmpl=f"{outdir}/%(title)s-%(id)s.%(ext)s"
    )

    with YoutubeDL(opts) as ydl:
        data = ydl.extract_info(song.url)
        filename = f"{data['title']}-{data['id']}.mp3"
        output = os.path.join(outdir, filename)

        with open(output, 'rb') as fd:
            song.file = File(fd, name=get_valid_filename(filename))
            song.name = data['title']
            song.save()

    shutil.rmtree(outdir)
import os
import re
import shutil
from threading import Thread
import time
import traceback

import ffmpeg
import requests
import youtube_dl

import consts


class VideoDownload:

    backup_path: str
    mux_extension = 'mp4'

    def __init__(self, video_id: str):
        self.video_id = video_id

        self.url: str = ''
        self.title: str = ''
        self.description: str = ''
        self.uploader: str = ''

        self.thumbnail_url: str = ''
        self.thumbnail_filename: str = ''

        self.temp_video_path: str = ''

        self.thread = Thread(
            name=f'{self.video_id}-thread',
            target=self.process_video_download,
            daemon=True
        )
        self.thread.start()

    def extract_video_info(self):
        yt_dl = youtube_dl.YoutubeDL({'format': 'bestvideo+bestaudio/best'})
        while True:
            try:
                info = yt_dl.extract_info(consts.YT_VIDEO_URL.format(id=self.video_id), download=False)
                break
            except youtube_dl.utils.DownloadError as dl_ex:
                if re.match(r'^ERROR: This live event will begin in \d+? hours\.$', str(dl_ex)):
                    pass
                else:
                    traceback.print_exc()

                time.sleep(10)

        self.url = info['url']
        self.title = info['title']
        self.description = info['description']
        self.uploader = info['uploader']

        self.thumbnail_url = info['thumbnail']
        self.thumbnail_filename = f'{consts.TEMP_PATH}/{self.video_id}_thumbnail.jpg'

        self.temp_video_path = f'{consts.TEMP_PATH}/{self.video_id}'

    def download_thumbnail(self):
        thumbnail_request = requests.get(self.thumbnail_url, stream=True)
        if thumbnail_request.status_code == 200:
            with open(f'{self.thumbnail_filename}', 'wb') as f:
                thumbnail_request.raw.decode_content = True
                shutil.copyfileobj(thumbnail_request.raw, f)
                print(f'Thumbnail saved for: {self.video_id}')
        else:
            self.thumbnail_filename = None

    def download_video(self):
        print(f'Downloading video for: {self.title}_{self.video_id}')
        ffmpeg.input(self.url).output(f'{self.temp_video_path}.ts', c='copy').run(quiet=True)
        # mux to mp4, attach thumbnail, add description
        # https://github.com/abayochocoball/hollow_memories/blob/master/archiving_livestreams.md#post-processing
        if self.thumbnail_filename:
            (
                ffmpeg
                .input(f'{self.thumbnail_filename}', i=f'{self.temp_video_path}.ts')
                .output(f'{self.temp_video_path}.{VideoDownload.mux_extension}', **{
                    'map': [1, 0], 'c': 'copy', 'disposition:0': 'attached_pic',
                    'metadata': f'comment={self.description}'
                })
                .run(quiet=True)
            )
        else:
            (
                ffmpeg
                .input(f'{self.temp_video_path}.ts')
                .output(f'{self.temp_video_path}.{VideoDownload.mux_extension}', **{
                    'c': 'copy',
                    'metadata': f'comment={self.description}'
                })
                .run(quiet=True)
            )

        # mkv code if i want to support this in the future
        # ffmpeg.input(f'{TEMP_PATH}/{video_filename}.ts').output(f'{BACKUP_PATH}/{video_filename}.mp4', **{
        #     'c': 'copy', 'attach': f'{TEMP_PATH}/{thumbnail_filename}', 'metadata:s:t': 'mimetype=image/jpeg'
        # }).run(quiet=True)

        try:
            os.mkdir(f'{VideoDownload.backup_path}/{self.uploader}')
            print(f'Created directory: {VideoDownload.backup_path}/{self.uploader}')
        except FileExistsError:
            pass

        shutil.move(
            f'{self.temp_video_path}.{VideoDownload.mux_extension}',
            f'{VideoDownload.backup_path}/{self.uploader}/{self.title}_{self.video_id}.{VideoDownload.mux_extension}'
        )
        print(f'Finished downloading video for: {self.title}_{self.video_id}')

    def process_video_download(self):
        self.extract_video_info()
        self.download_thumbnail()
        self.download_video()

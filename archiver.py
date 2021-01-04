#!/usr/bin/env python3

import argparse
import os
import sys
import time
import traceback
from typing import List

import requests

import consts
from VideoDownload import VideoDownload

CAPTURED_VIDEOS: List[VideoDownload] = []


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='A tool for automatically recording HoloLive streams')
    parser.add_argument('-o', '--output', help='Directory to output videos to', default='./videos')
    args = parser.parse_args()

    backup_path = args.output
    VideoDownload.backup_path = backup_path

    try:
        os.mkdir(backup_path)
        print(f'Created directory: {backup_path}')
    except FileExistsError:
        pass

    try:
        os.mkdir(consts.TEMP_PATH)
    except FileExistsError:
        pass

    while True:
        with open('channels.txt', 'a+') as fin:
            fin.seek(0)
            channels_archive = [x.strip() for x in fin.readlines() if x.strip()]

        with open('videos.txt', 'a+') as fin:
            fin.seek(0)
            videos_archive = [x.strip() for x in fin.readlines() if x.strip()]

        if not channels_archive and not videos_archive:
            time.sleep(60)
            continue

        try:
            captured_ids = list(map(lambda v: v.video_id, CAPTURED_VIDEOS))
            hololive_json = requests.get(consts.SCHEDULE).json()

            for stream in hololive_json['live']:
                video_key: str = stream['yt_video_key']
                if video_key in captured_ids:
                    continue

                if (stream['channel']['name'] in channels_archive or video_key in videos_archive) and video_key not in captured_ids:
                    download = VideoDownload(video_key)
                    CAPTURED_VIDEOS.append(download)
        except KeyboardInterrupt:
            print('Waiting for stream downloads to finish, ctrl + c again to force close...')
            for video in CAPTURED_VIDEOS:
                video.thread.join()

            sys.exit(0)
        except Exception as ex:
            print("Uncaught error")
            traceback.print_exc()

        time.sleep(60)

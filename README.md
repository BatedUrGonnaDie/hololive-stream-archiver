# HoloLive Stream Archiver

A tool used for downloading HoloLive live streams when you will be away from your PC.

## Run locally

- Ensure that you have ffmpeg installed and on your path
- `$ pip install -r requirements.txt`
- `$ python archiver.py`
- This will generate `channels.txt` and `videos.txt`. Place YT channel names or video ID's in the respective files.

All done, as long as it's running you can dynamically add/remove channels or ID's on the fly, and it will be picked up
automatically.
from os import path, makedirs, system
import m3u8
import uuid
import requests


class BinaryDownloader:
    """Custom downloader for handling binary m3u8 content"""

    def download(self, uri, timeout=None, headers={}, verify_ssl=True):
        """Downloads content while handling binary data properly"""
        response = requests.get(
            uri, timeout=timeout, headers=headers, verify_ssl=verify_ssl
        )
        # Assume binary data should be decoded as latin1 if not UTF-8
        try:
            content = response.content.decode("utf-8")
        except UnicodeDecodeError:
            content = response.content.decode("latin1")
        return content, uri


def make_output_dir():
    """
    prepare output directories
    """
    base_dir = ("output/videos", "output/csv")

    for base in base_dir:
        makedirs(path.join(path.curdir, base), exist_ok=True)


# playlist_url example: "https://manifest.prod.boltdns.net/manifest/v1/hls/v4/clear/2985902027001/0493b63d-49fb-4d32-a3ee-470f732fa287/6s/master.m3u8?fastly_token=NjdiYjJlMzhfYzhiYzdlYzdmY2QyMzIyNmYwY2YzYTk0MzIxNzAxYzcyYmU5M2I3YzkzNjJiMGZjYmRlNzg2MTAzYjQ1MGIzZQ%3D%3D"
def parse_m3u8(paylist_url: str):
    """
    Parses an M3U8 playlist from the given URL and downloads the video using ffmpeg.

    Args:
        paylist_url (str): The URL of the M3U8 playlist to be parsed.

    Returns:
        None

    Side Effects:
        - Prints the M3U8 playlist content to the console.
        - Downloads the video specified in the M3U8 playlist using ffmpeg.
        - Writes the M3U8 playlist content to a file named 'playlist.m3u8'.
    """
    # Use custom downloader to handle binary content
    playlist = m3u8.load(paylist_url, http_client=BinaryDownloader())

    # Download the video using ffmpeg
    random_string = str(uuid.uuid4())
    output_filename = (
        f"output/videos/{paylist_url.split('/')[-2].split('?')[0]}_{random_string}.mp4"
    )
    system(f'ffmpeg -i "{paylist_url}" -c copy {output_filename}')

    # if you want to write a file from its content
    makedirs(path.join(path.curdir, "output/m3u8"), exist_ok=True)
    playlist.dump(f"output/m3u8/{paylist_url.split("/")[-1]}")

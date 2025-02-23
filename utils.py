from os import path, makedirs, system
import m3u8


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
        - Downloads the video specified in the M3U8 playlist using ffmpeg and saves it as 'output.mp4'.
        - Writes the M3U8 playlist content to a file named 'playlist.m3u8'.
    """
    playlist = m3u8.load(paylist_url)

    print(playlist.dumps())

    # Download the video using ffmpeg
    system(
        'ffmpeg -i "https://manifest.prod.boltdns.net/manifest/v1/hls/v4/clear/2985902027001/0493b63d-49fb-4d32-a3ee-470f732fa287/6s/master.m3u8?fastly_token=NjdiYjJlMzhfYzhiYzdlYzdmY2QyMzIyNmYwY2YzYTk0MzIxNzAxYzcyYmU5M2I3YzkzNjJiMGZjYmRlNzg2MTAzYjQ1MGIzZQ%3D%3D" -c copy output.mp4'
    )

    # if you want to write a file from its content
    playlist.dump("playlist.m3u8")

import os
import subprocess

from megakino.src.parser import args
from megakino.src.common import USER_AGENT


def download(direct_links, titles, path=None):
    download_path = path if path is not None else args.path
    total = len(direct_links)
    for counter, (link, title) in enumerate(zip(direct_links, titles), start=1):
        print(f"\nDownloading {title} ({counter}/{total})")
        output_file = os.path.join(download_path, title, f"{title}.mp4")
        progress_template = (
            f"[download] {title} ({counter}/{total})"
            " %(progress._percent_str)s of %(progress._total_bytes_estimate_str)s"
            " at %(progress._speed_str)s ETA %(progress._eta_str)s"
            " (frag %(progress.fragment_index)s/%(progress.fragment_count)s)"
        )
        command = [
            "yt-dlp",
            "--fragment-retries", "infinite",
            "--concurrent-fragments", "4",
            "--user-agent", USER_AGENT,
            "-o", output_file,
            "--quiet",
            "--no-warnings",
            "--progress",
            "--progress-template", progress_template,
            link,
        ]
        subprocess.run(command)

#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Expect a directory layout like this

/deliver
  audio.wav
  video.mov
  /mux
    mux-{timestamp}.mov
  /chunks
    1000.mov
    2000.mov
    ...
  /frames
    /1000
      000000.png
      000001.png
      ...
      001000.png
    /2000
      ...
"""

import argparse
import os
import subprocess
from datetime import datetime
from pathlib import Path


def create_file_list(directory=Path("chunks"), output_file_name="file_list.txt"):
    """
    Looks into a directory, finds all *.mov files (sorted alphabetically),
    and writes them to a 'files_list.txt' file in the format required by FFmpeg.
    """
    # Get a sorted list of .mov files in the directory
    mov_files = sorted([f for f in os.listdir(directory) if f.endswith('.mov')])

    # Write the file list in FFmpeg format
    output_file_pah = directory / output_file_name
    with open(output_file_pah, 'w') as file_list:
        for mov_file in mov_files:
            file_list.write(f"file '{mov_file}'\n")

    print(f"File list saved to {output_file_pah}")


def concatenate_videos(output_file=Path("video.mov"), file_list="file_list.txt"):
    """
    Runs the FFmpeg command to concatenate video files listed in file_list.txt.

    Parameters:
    - file_list: Path to the text file containing the list of files (e.g., file_list.txt).
    - output_file: Name of the resulting concatenated video file (e.g., output.mov).
    """
    # FFmpeg command
    command = [
        "ffmpeg",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        Path("chunks") / file_list,
        "-c",
        "copy",
        output_file,
        "-y",
    ]

    try:
        # Run the command
        subprocess.run(command, check=True)
        print(f"Concatenated video saved as {output_file}")
    except subprocess.CalledProcessError as e:
        print(f"Error while running FFmpeg: {e}")
    except FileNotFoundError:
        print("FFmpeg is not installed or not in your PATH.")


def mux_audio_video():
    """Given a video.mov and audio.mov, create a mux.

    The mux is named with a timestamp and placed in the mux directory.
    No re-encoding is needed here.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    output_dir = "mux"
    output_file = os.path.join(output_dir, f"mux-{timestamp}.mov")

    # Create the output directory
    os.makedirs(output_dir, exist_ok=True)

    # FFmpeg command to mux audio and video
    command = [
        "ffmpeg",
        "-i", "video.mov",  # Input video
        "-i", "audio.wav",  # Input audio
        "-c:v", "copy",     # Copy video codec
        "-c:a", "copy",     # Encode audio to AAC
        output_file
    ]
    subprocess.run(command, check=True)


def main():
    parser = argparse.ArgumentParser(description="Process video files for delivery.")

    parser.add_argument("--path", help="Path where to operate", type=str, required=True)
    args = parser.parse_args()

    # Go to the root of the delivery directory
    os.chdir(args.path)
    create_file_list()
    concatenate_videos()
    if Path("audio.wav").exists():
        mux_audio_video()


if __name__ == "__main__":
    main()

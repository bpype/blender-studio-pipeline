#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2024 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

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


def main():
    parser = argparse.ArgumentParser(description="Process video files for delivery.")

    parser.add_argument("--path", help="Path where to operate", type=str, required=True)
    args = parser.parse_args()

    # Go to the root of the delivery directory
    os.chdir(args.path)
    create_file_list()
    concatenate_videos()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2032 Blender Foundation
# SPDX-License-Identifier: MIT

"""Tool to deliver the final version of a movie file.

Given the following directory layout:

 - audio
    - old
 - deliver.py
 - frames
 - mux
 - old
Running deliver.py will:

- encode the content of 'audio' into an aac file .m4a file
- encode the frames found in 'frames' as high-quality x264 .m4v file
- mux the .m4a and .m4v files in a .mp4 in the 'mux' directory
"""

import argparse
import subprocess
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent

DEFAULT_FRAMES_DIR_PATH = str(CURRENT_DIR / 'frames')
DEFAULT_AUDIO_FILE_PATH = str(CURRENT_DIR / 'mux' / 'audio.m4a')
DEFAULT_VIDEO_FILE_PATH = str(CURRENT_DIR / 'mux' / 'video.m4v')
DEFAULT_MUX_FILE_PATH = str(CURRENT_DIR / 'mux.mp4')


def get_next_versioned_filename(base_filename):
    base_path = Path(base_filename)

    filename, file_extension = base_path.stem, base_path.suffix
    version = 1

    while True:
        versioned_filename = f"{filename}_v{version:03d}{file_extension}"
        versioned_path = base_path.with_name(versioned_filename)

        if not versioned_path.exists():
            return str(versioned_path)

        version += 1


def encode_audio(input_audio):
    cmd = ['ffmpeg', '-i', input_audio, '-c:a', 'aac', DEFAULT_AUDIO_FILE_PATH]
    subprocess.run(cmd, check=True)


def encode_frames(input_frames=DEFAULT_FRAMES_DIR_PATH, frames_extension='png'):
    ffmpeg_command = {
        'command': ['ffmpeg'],
        'framerate': ['-framerate', '24'],
        'pattern': ['-pattern_type', 'glob', '-i', f'{input_frames}/*.{frames_extension}'],
        'codec': ['-c:v', 'libx264'],
        'codec_preset': ['-preset', 'slow'],
        'codec_profile': ['-profile:v', 'high'],
        'codec_crf': ['-crf', '18'],
        'codec_coder': ['-coder', '1'],
        'codec_pix_fmt': ['-pix_fmt', 'yuv420p'],
        'codec_flags': ['-movflags', '+faststart'],
        'codec_gop': ['-g', '12'],
        'codec_b_frames': ['-bf', '2'],
        'output': [str(CURRENT_DIR / 'mux' / 'video.m4v')],
    }
    cmd = [arg for args_list in ffmpeg_command.values() for arg in args_list]
    subprocess.run(cmd, check=True)


def mux_av(
    video_input=DEFAULT_VIDEO_FILE_PATH,
    audio_input=DEFAULT_AUDIO_FILE_PATH,
    output_file=DEFAULT_MUX_FILE_PATH,
):

    output_file = get_next_versioned_filename(output_file)
    cmd = [
        "ffmpeg",
        "-i",
        video_input,
        "-i",
        audio_input,
        "-vcodec",
        "copy",
        "-acodec",
        "copy",
        output_file,
    ]
    subprocess.run(cmd, check=True)


def main():
    parser = argparse.ArgumentParser(description="Encode audio, encode frames, and mux AV.")
    parser.add_argument(
        "--encode_audio",
        required=False,
        help="Input audio file path",
    )
    parser.add_argument(
        "--encode_frames",
        nargs='?',
        const=DEFAULT_FRAMES_DIR_PATH,
        type=str,
        required=False,
        help="Input frames directory path",
    )
    parser.add_argument(
        "--mux",
        action='store_true',
        required=False,
        help="Mux audio and video",
    )

    args = parser.parse_args()

    if not (args.encode_audio or args.encode_frames or args.mux):
        print('Nothing to do.\nUse --help to learn more.')

    if args.encode_audio:
        encode_audio(args.encode_audio)
    if args.encode_frames:
        encode_frames(args.encode_frames)
    if args.mux:
        mux_av()

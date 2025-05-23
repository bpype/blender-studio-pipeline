#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2022 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
import os
import pathlib
import requests
import sys
import time

# Must set API Key as Enviroinment Variable or add to script here.
# API Key can be generated using an existing freesound.org account
# API Key can be created by accessing https://freesound.org/apiv2/apply
# To learn more about the API visit https://freesound.org/docs/api/authentication.htmlo
API_KEY = "" # Replace with "Client secret/Api key" from https://freesound.org/apiv2/apply

API_BASE_URL = 'https://freesound.org/apiv2' # Set the base URL for the Freesound API


def load_api_key():
    # Set the API key for accessing the Freesound API
    global API_KEY
    env_key = os.getenv('FREESOUND_API_KEY')
    if env_key:
        API_KEY = env_key
        return

def get_sound_list():
    sound_list = []

    # Iterate through all the sound strips in the current scene
    for s in bpy.context.scene.sequence_editor.sequences_all:
        if s.type == 'SOUND':
            filename = pathlib.Path(s.sound.filepath).stem
            sound_id = filename.split('__')[0]
            # Assume that if a file starts with an int, it's from freesound
            try:
                sound_id = int(sound_id)
                sound_list.append(filename)
            except ValueError:
                print(f'Skipping {sound_id}')
    return set(sound_list)


def fetch_sound_info(query):
    # Use the Freesound API to search for a sound with the given filename
    search_url = f'{API_BASE_URL}/search/text/'
    search_params = {'query': query, 'token': API_KEY}
    r = requests.get(search_url, params=search_params)

    # Check the status code of the response
    if r.status_code == 200:
        # If the search was successful, get the first sound in the results
        return r.json()['results'][0]
    else:
        print(f'Error searching for sound with filename "{query}"\n\n')
        return None


def generate_credits(sound_list):
    blendfile_name = bpy.path.basename(bpy.data.filepath)
    with open(f'{blendfile_name}-sound_credits.txt', 'w') as f:
        for sound in sound_list:
            print(f'Processing {sound}')
            time.sleep(0.5)

            info = fetch_sound_info(sound)
            if not info:
                continue
            f.write(f'Filename: {sound}\n')
            f.write(f'Credits: {info["username"]}\n')
            f.write(f'License: {info["license"]}\n\n')


def main():
    load_api_key()
    if API_KEY == "":
        print("FREESOUND_API_KEY not set")
        return
    sound_list = get_sound_list()
    generate_credits(sound_list)


main()

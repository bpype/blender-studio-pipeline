#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2024 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

import argparse

import json
import logging
import pathlib
import requests
import sys
from dataclasses import dataclass
from typing import Optional


logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

task_slug_to_name_map = {
    'anim': 'Animation',
    'lighting': 'Lighting',
    'render': 'Rendering',
}


@dataclass
class Config:
    """Configuration setup for Kitsu client."""

    dotenv_path = pathlib.Path(__file__).parent / '.env.local'
    base_url: Optional[str] = ''
    email: Optional[str] = ''
    password: Optional[str] = ''
    project_id: Optional[str] = ''

    @staticmethod
    def get_env_data_as_dict(path: pathlib.Path) -> dict:
        with open(path, 'r') as f:
            return dict(
                tuple(line.replace('\n', '').split('='))
                for line in f.readlines()
                if not line.startswith('#')
            )

    def __post_init__(self):
        if self.dotenv_path.exists():
            env_vars = self.get_env_data_as_dict(self.dotenv_path)
            self.base_url = env_vars['KITSU_DATA_SOURCE_URL']
            self.email = env_vars['KITSU_DATA_SOURCE_USER_EMAIL']
            self.password = env_vars['KITSU_DATA_SOURCE_USER_PASSWORD']
            self.project_id = env_vars['KITSU_DATA_SOURCE_PROJECT_ID']
        else:
            if not self.base_url or not self.email or not self.password:
                logging.error(
                    "Missing configuration for kitsu Config object."
                    "Please specify base_url, email and password."
                )
                sys.exit(1)


@dataclass
class KitsuClient:
    """Client to query the Kitsu API."""

    config: Config = None
    jwt: str = None

    @property
    def headers(self):
        return {'Authorization': f"Bearer {self.jwt}"}

    @property
    def base_url(self):
        return self.config.base_url

    def get(self, path, params=None):
        return requests.get(
            f"{self.base_url}{path}",
            params=params,
            headers=self.headers,
            allow_redirects=True,
        )

    def post(self, path, params=None):
        url = f"{self.base_url}{path}"
        return requests.post(
            url,
            params=params,
            headers=self.headers,
            allow_redirects=True,
        )

    def fetch_jwt(self, email, password) -> str:
        payload = {
            'email': email,
            'password': password,
        }
        r_jwt = requests.post(f"{self.config.base_url}/auth/login", data=payload)
        r_jwt = r_jwt.json()
        if 'error' in r_jwt:
            logging.error(r_jwt['message'])
            exit()
        return r_jwt['access_token']

    def __post_init__(self):
        if not self.config:
            self.config = Config()
        self.jwt = self.fetch_jwt(self.config.email, self.config.password)

    def add_preview_metadata_to_comment(self, task_id, comment_id):
        url = f"/actions/tasks/{task_id}/comments/{comment_id}/add-preview"
        response = self.post(url)
        return response.json()

    def add_preview_to_comment(task_id, comment_id, preview_file_id):
        url = f"/actions/tasks/{task_id}/comments/{comment_id}/preview-files/{preview_file_id}"

    def add_comment(self, task_id: str, task_status_id: str, comment_message=None) -> dict:
        data = json.dumps(
            {
                "task_status_id": task_status_id,
            }
        )
        url = f"{self.base_url}/actions/tasks/{task_id}/comment"
        headers = {
            **self.headers,
            "Content-Type": "application/json; charset=utf-8",
        }

        response = requests.post(
            url,
            headers=headers,
            data=data,
        )
        return response.json()

    def get_tasks(self):
        response = self.get("/data/tasks")
        return response.json()

    def get_task_editorial(self, edit_identifier) -> dict:
        # Split name by actual name and the task type
        # TODO: better handling of episodes
        prefix, edit_number, _ = edit_identifier.split('-')
        # Get all edits in the project
        response = self.get(f"/data/projects/{self.config.project_id}/edits")
        # Find the edit by name
        edit = next(
            (item for item in response.json() if item.get("name") == f"{prefix}-{edit_number}"),
            None,
        )
        if not edit:
            raise ValueError(f"No edit {edit_identifier} found.")
        # Get all task types
        response = self.get(f"/data/edits/{edit['id']}/tasks")
        # Find task by type name
        return next(
            (item for item in response.json() if item.get("task_type_name") == 'Edit'), None
        )

    def get_task_statuses(self):
        response = self.get(f"/data/projects/{self.config.project_id}/settings/task-status")
        return response.json()

    def get_task_status(self, name) -> dict:
        task_statuses = self.get_task_statuses()
        # pprint.pprint(task_statuses)
        return next((item for item in task_statuses if item.get("short_name") == name), None)

    def get_task_shot(self, shot_identifier) -> dict:
        # Split name by actual name and the task type
        shot_name, task_type_name, _ = shot_identifier.split('-')
        task_type_name = task_slug_to_name_map[task_type_name]
        # Get all shots in the project
        response = self.get(f"/data/projects/{self.config.project_id}/shots")
        # Find the shot by name
        shot = next((item for item in response.json() if item.get("name") == shot_name), None)
        if not shot:
            raise ValueError(f"No shot {shot_name} found.")
        # Get all task types
        response = self.get(f"/data/shots/{shot['id']}/tasks")
        # Find task by type name
        return next(
            (item for item in response.json() if item.get("task_type_name") == task_type_name), None
        )

    def upload_preview(self, preview_file_id, file_path: pathlib.Path):
        url = self.base_url + f"/pictures/preview-files/{preview_file_id}?normalize=false"
        try:
            with open(file_path, 'rb') as file:
                files = {'file': file}
                response = requests.post(url, files=files, headers=self.headers)
                if response.status_code == 201:
                    print("Upload successful!")
                    print("Response:", response.json())
                else:
                    print("Failed to upload. Status code:", response.status_code)
                    print("Response:", response.text)
        except FileNotFoundError:
            print("The specified file was not found.")
        except Exception as e:
            print(f"An error occurred: {e}")

    def add_comment_and_preview(self, task, file_path):
        # Create comment
        task_status = self.get_task_status('wfa')
        comment = self.add_comment(task['id'], task_status['id'])
        # Add Preview to comment
        preview_metadata = self.add_preview_metadata_to_comment(task['id'], comment['id'])
        # Upload file as preview
        self.upload_preview(
            preview_metadata['id'],
            file_path,
        )

    def upload_edit_preview(self, file_path: str):
        # Parse filename to get episode number (e.g. brc-01-v001.mp4)
        file_path = pathlib.Path(file_path)
        # Find editorial task
        task = self.get_task_editorial(file_path.stem)
        self.add_comment_and_preview(task, file_path)

    def upload_shot_preview(self, file_path: str):
        # Parse filename to get the shot id (01_010_0030-anim-v001.mp4)
        file_path = pathlib.Path(file_path)
        # Find the relevant task
        task = self.get_task_shot(file_path.stem)
        self.add_comment_and_preview(task, file_path)


def main():
    parser = argparse.ArgumentParser(description="Upload a video file as preview to Kitsu.")

    # Adding mutually exclusive group for shot and edit arguments
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--shot", help="Path to the shot file", type=str)
    group.add_argument("--edit", help="Path to the edit file", type=str)

    args = parser.parse_args()
    kitsu_client = KitsuClient()

    if args.shot:
        kitsu_client.upload_shot_preview(args.shot)
    if args.edit:
        kitsu_client.upload_edit_preview(args.edit)


if __name__ == "__main__":
    main()

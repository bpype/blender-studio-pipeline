#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2022 Blender Studio Tools Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later
import json
import requests
import sys
from pathlib import Path
from init_project_folder_structure import init_folder_structure
import subprocess
from typing import List, Tuple
import argparse
import getpass

# Example usage:
# ./setup_assistant.py -u http://localhost/api -e admin@example.com -p mysecretpassword -r /home/nicka/test_projects/

BUILDS_INDEX = "https://builder.blender.org/download/daily/?format=json&v=1"


def input_blender_branch(available_branches: dict) -> str:
    """
    Prompt the user to select a Blender branch from the available branches.
    """
    selected_branch = get_numbered_input(
        list(available_branches.keys()), "Select Blender Branch from List:"
    )
    return list(available_branches.keys())[selected_branch]


def get_available_blender_branches():
    reqs = requests.get(BUILDS_INDEX)
    available_downloads = json.loads(reqs.text)
    # Get only the latest of each branch using "file_mtime"
    latest_downloads = {}
    for download in available_downloads:
        branch = download["branch"]
        mtime = download.get("file_mtime", 0)
        if branch not in latest_downloads or mtime > latest_downloads[branch].get("file_mtime", 0):
            latest_downloads[branch] = download
    available_downloads = list(latest_downloads.values())

    available_branches = set(
        [(download["branch"], download["version"]) for download in available_downloads]
    )

    branch_dict = {}
    for branch, version in available_branches:
        name = version[:4] + "x" + " " + branch

        if float(version[:3]) < 4.5:
            continue  # Skip versions below 4.5

        if branch == "main":
            name = name + " (latest)"

        branch_dict[name] = branch

    # Sort available_branches by name
    available_branches = dict(sorted(branch_dict.items(), reverse=True, key=lambda item: item[0]))
    return available_branches


def input_kitsu_url(url_arg: str = None):
    global KITSU_URL
    while True:
        if url_arg:
            url = url_arg.strip()
        else:
            url = input("Input Kitsu Server URL: ").strip()
        # Check if the URL is reachable

        if not url.startswith("http"):
            url = "https://" + url
        if not url.rstrip("/").endswith("/api"):
            url = url.rstrip("/") + "/api"

        try:
            # Try HTTPS first, then fallback to HTTP if it fails
            try:
                response = requests.get(url, timeout=5)
            except requests.exceptions.ConnectionError:
                # If HTTPS fails, try HTTP
                url_http = url.replace("https://", "http://", 1)
                print(f"HTTPS failed, trying HTTP: {url_http}")
                response = requests.get(url_http, timeout=5)
                url = url_http
            if response.status_code != 200:
                print(
                    f"Warning: Unable to reach Kitsu server at {url} (status code: {response.status_code})"
                )
                url_arg = None
                continue
        except requests.RequestException as e:
            print(f"Warning: Unable to reach Kitsu server at {url}.")
            print(f"Error: {type(e).__name__}")
            print("Please try again")
            url_arg = None
            continue
        KITSU_URL = url
        print(f"Kitsu Server URL set to: {KITSU_URL}")
        break


def input_kitsu_login(email_arg: str = None, password_arg: str = None) -> dict:
    """
    Log in a user on Kitsu.
    """
    print("Login to Kitsu Account")
    while True:
        if email_arg:
            email = email_arg.strip()
        else:
            email = input("Email: ").strip()
        if password_arg:
            password = password_arg.strip()
        else:
            password = getpass.getpass("Password: ").strip()

        payload = {"email": email, "password": password}
        data = send_post_request("/auth/login", payload)
        if not data or 'access_token' not in data:
            print("Invalid login or missing access token. Please try again.")
            email_arg = None
            password_arg = None
            continue
        break
    return data


def kitsu_get_projects(access_token: str) -> dict:
    return send_get_request("/data/projects/open", access_token)


def send_post_request(url: str, data: dict, access_token: str = None):
    headers = {
        'Content-type': 'application/json',
    }
    if access_token:
        headers['Authorization'] = f"Bearer {access_token}"
    response = requests.post(
        url=f"{KITSU_URL}{url}",
        headers=headers,
        data=json.dumps(data),
    )
    if response.status_code != 200:
        print(f"{response.status_code}: {response.reason}")
        return None
    return response.json()


def send_put_request(url: str, data: dict, access_token: str = None):
    headers = {
        'Content-type': 'application/json',
    }
    if access_token:
        headers['Authorization'] = f"Bearer {access_token}"
    response = requests.put(
        url=f"{KITSU_URL}{url}",
        headers=headers,
        data=json.dumps(data),
    )
    if response.status_code not in (200, 204):
        print(f"{response.status_code}: {response.reason}")
        return None
    if response.content:
        return response.json()
    return None


def send_get_request(url: str, access_token: str = None):
    headers = {
        'accept': '*/*',
    }
    if access_token:
        headers['Authorization'] = f"Bearer {access_token}"
    response = requests.get(
        url=f"{KITSU_URL}{url}",
        headers=headers,
    )
    if response.status_code != 200:
        print(f"{response.status_code}: {response.reason}")
        print(response.text)
        sys.exit(1)
    return response.json()


def select_project(projects: List[dict]) -> str:
    project_names = [project["name"] for project in projects]
    selection = get_numbered_input(project_names, "Select a project by number:")
    return projects[selection]


def get_numbered_input(items: List[str], prompt: str) -> int:
    """
    Prompt the user to select an item from a numbered list.
    """
    for index, item in enumerate(items):
        print(f"({index}): {item}")

    while True:
        try:
            selected_index = int(input(prompt + " "))
            if selected_index in range(len(items)):
                return selected_index
            else:
                print(f"Invalid selection. Please select a number between 0 and {len(items) - 1}.")
        except ValueError:
            print("Invalid input. Please enter a number.")


def get_project_parent_path(project_name: str, project_root_arg: str = None) -> Path:
    """
    Prompt the user for a valid existing project path.
    Keeps prompting until a valid path is provided.
    """
    if project_root_arg:
        project_parent_path = project_root_arg.strip()
    else:
        project_parent_path = input("Enter the project path: ").strip()

    if not project_parent_path:
        print("Project path cannot be empty.")
        return get_project_parent_path(project_name)

    project_parent_path = Path(project_parent_path)
    if not project_parent_path.exists():
        print("Path does not exist. Please enter a valid path.")
        return get_project_parent_path(project_name)

    if not project_parent_path.is_dir():
        print(
            f"Path '{project_parent_path}' is not a directory. Please enter a valid directory path."
        )
        return get_project_parent_path(project_name)

    project_path = project_parent_path.joinpath(project_name)
    if project_path.exists():
        print(f"Project path '{project_name}' already exists in '{project_parent_path}'.")
        print(f"Are you sure this is what you want? ")
        while True:
            use_path = (
                input(f"Use '{project_parent_path} '? (y/n): ").strip().lower()
            )
            if use_path == "n":
                return get_project_parent_path(project_name)
            elif use_path == "y":
                return project_path
            else:
                print("Invalid input. Please enter 'y' or 'n'.")
    return project_path

def make_project_folder(project_name: str, project_root_arg: str = None) -> Path:
    """
    Create a project path from the project name.
    """
    project_path = get_project_parent_path(project_name, project_root_arg)
    project_path.mkdir(parents=False, exist_ok=True)
    return project_path


def write_config_file(
    kitsu_server_url: str, kitsu_project: dict, project_path: Path, version_control: bool
):
    config_data = {
        "login_data": {
            "host": kitsu_server_url,
            "project_id": kitsu_project['id'],
            "project_name": kitsu_project['name'],
            "project_code": kitsu_project['code'],
        },
        "project_root_dir": project_path.as_posix(),
        "project_paths": {
            "shot_playblast_root_dir": "shared/editorial/footage/pro/",
            "seq_playblast_root_dir": "shared/editorial/footage/pre/",
            "frames_root_dir": "shared/editorial/footage/post/",
            "edit_export_dir": "shared/editorial/export/",
        },
        "generic_prefs": {
            "version_control": version_control,
        },
    }
    config_file = project_path.joinpath("svn/tools/project_config.json")
    with open(config_file, "w") as f:
        json.dump(config_data, f, indent=4)


def write_blender_branch(branch_name: str, project_path: Path):
    update_script = project_path.joinpath("svn/tools/update_blender.py")
    if not update_script.exists():
        print(f"Config file not found: {update_script}")
        sys.exit()
    lines = update_script.read_text().splitlines()
    new_lines = []
    replaced = False
    for line in lines:
        if line.strip().startswith("BLENDER_BRANCH"):
            new_lines.append(f'BLENDER_BRANCH = "{branch_name}"')
            replaced = True
        else:
            new_lines.append(line)
    if not replaced:
        print("BLENDER_BRANCH variable not found in config file.")
        return
    update_script.write_text("\n".join(new_lines) + "\n")


def print_header(text: str, level: int = 1):
    """
    Prints a header surrounded by asterisks.
    The higher the level, the more rows of asterisks above and below.
    """
    print()
    print()
    stars = '*' * max(20, len(text) + 4)
    for _ in range(level):
        print(stars)
    print(f"* {text.center(len(stars) - 4)} *")
    for _ in range(level):
        print(stars)


def run_background_script(script_path: Path):
    """
    Run a Python script using subprocess and handle errors.
    """
    result = subprocess.run([sys.executable, str(script_path)])
    if result.returncode != 0:
        print(f"Failed to run {script_path}: {result.returncode}")
        sys.exit(result.returncode)


def verify_python_version():
    """
    Ensure Python version is 3.11 or newer.
    """
    if sys.version_info < (3, 11):
        print(f"Error: Python 3.11 or newer is required. Current version: {sys.version}")
        sys.exit(1)


def get_project_short_name(project_name: str) -> str:
    """
    Normalize the project name by replacing spaces with underscores and removing special characters.
    """
    return (
        ''.join(c if c.isalnum() or c in ('_', '-') else '_' for c in project_name)
        .strip('_')
        .lower()
    )


def ensure_kitsu_project_short_name(project: dict, access_token: str):
    """
    Ensure the Kitsu project has a short name (code).
    If not, prompt the user to enter one. Returns updated project with shortname set
    """
    if project.get("code"):
        if get_project_short_name(project["code"]) == project["code"]:
            print(f"Kitsu project shortname '{project['code']}' is valid.")
            return project
    print(
        f"Warning: Kitsu project shortname must only contain (alphanumeric, underscores, dashes):"
    )
    print("No valid shortname detected.")

    suggested_short_name = get_project_short_name(project["name"])
    print(f"Suggested short name: {suggested_short_name}")

    while True:
        use_suggested = (
            input(f"Use suggested short name '{suggested_short_name}'? (y/n): ").strip().lower()
        )
        if use_suggested == "y":
            project["code"] = suggested_short_name
            payload = {"code": project["code"]}
            send_put_request(f"/data/projects/{project['id']}", payload, access_token)
            print("Project short name updated successfully.")
            return project
        elif use_suggested == "n":
            print("Aborting setup. Please restart and provide a valid short name.")
            sys.exit(1)
        else:
            print("Invalid input. Please enter 'y' or 'n'.")


def check_version_control():
    print("The Blender Studio Tools project is designed to work with version control software (SVN/GIT-LFS) to manage versioning project files such as Assets & Shots.")
    print("If you are not using version control the Blender Kitsu add-on will create version files on your disk to provide versioning functionality.")
    while True:
        answer = (
            input("Are you using a version control software (SVN/GIT-LFS)? (y/n): ").strip().lower()
        )
        if answer.lower() == "y":
            return True
        elif answer.lower() == "n":
            return False
        else:
            print("Invalid input. Please enter 'y' or 'n'.")


def main():
    verify_python_version()
    parser = argparse.ArgumentParser(
        description="Blender Studio Tools Setup Assistant. This script will help you set up your Blender-Studio-Tools project. Please follow the prompts to setup your project, set your Blender branch or use the arguments below. To learn more see https://projects.blender.org/studio/blender-studio-tools/src/branch/main/scripts/project-tools#readme"
    )
    parser.add_argument("-u", "--url", type=str, help="Kitsu server URL")
    parser.add_argument("-e", "--user", type=str, help="Kitsu username/email")
    parser.add_argument("-p", "--password", type=str, help="Kitsu password")
    parser.add_argument(
        "-r", "--root", type=str, help="Root directory where project folder will be created"
    )
    args = parser.parse_args()

    # Login to Kitsu User to get API Token
    print_header("Blender Studio Tools Setup Assistant", 2)
    print("Welcome to the Blender Studio Tools Setup Assistant!")
    print("This script will help you set up your Blender-Studio-Tools project.")
    print("Please follow the prompts to setup your project, set your Blender branch.")

    print_header("Kitsu Setup", 1)
    input_kitsu_url(args.url)

    user_data = input_kitsu_login(args.user, args.password)
    access_token = user_data.get('access_token')
    if not access_token:
        print("Failed to log in. Please check your credentials.")
        sys.exit(1)

    print_header("Select Kitsu Project", 1)
    projects = kitsu_get_projects(access_token)
    selected_project = select_project(projects)
    print("Selected Project:", selected_project['name'])

    print_header("Set Kitsu Shortname", 1)
    selected_project = ensure_kitsu_project_short_name(selected_project, access_token)

    # Make project path
    print_header("Setup Project Folder", 1)
    print(
        "Enter the path where the project directory will be created. This directory will be named after Kitsu Project."
    )
    project_path = make_project_folder(selected_project["code"], args.root)
    print(f"Project path created at: {project_path}")

    # Check for verson control vs disk version deployment
    print_header("Version Control Software", 1)
    version_control = check_version_control()

    # Populate Folder Structure
    init_folder_structure(
        project_path.as_posix(), Path(__file__).parent.joinpath("folder_structure.json")
    )
    init_folder_structure(
        project_path.joinpath("svn").as_posix(),
        Path(__file__).parent.joinpath("folder_structure_svn.json"),
    )
    init_folder_structure(
        project_path.joinpath("shared").as_posix(),
        Path(__file__).parent.joinpath("folder_structure_shared.json"),
    )

    # Get Blender Branch
    print_header("Select Blender Branch", 1)
    print("Select the Blender branch you want to use for this project.")
    print("Only 4.5+ versions are supported.")
    available_blender_branches = get_available_blender_branches()
    selected_branch_name = input_blender_branch(available_blender_branches)
    print(f"Selected Blender Branch: {selected_branch_name}")
    write_blender_branch(available_blender_branches[selected_branch_name], project_path)

    # Download Blender
    update_blender_script = project_path.joinpath("svn/tools/update_blender.py")
    run_background_script(update_blender_script)

    # Download Blender Studio Extensions
    update_extensions_script = project_path.joinpath("svn/tools/update_extensions.py")
    run_background_script(update_extensions_script)
    # Write project config file
    write_config_file(KITSU_URL, selected_project, project_path, version_control)

    print_header("Mounting Project Folders", 1)

    print(
        f"If you are using SVN or GIT LFS to do version control please make your initial commit of {project_path.joinpath('svn').as_posix()} now."
    )
    print("https://studio.blender.org/tools/td-guide/svn-setup")
    print()
    print(
        f"If you are using Syncthing or other to sync files, please setup your sync of {project_path.joinpath('shared').as_posix()} now."
    )
    print("https://studio.blender.org/tools/td-guide/syncthing-setup")

    print()
    print(
        f"Next step: Ensure the SVN and Shared directories above are available on your artist workstations. Once the directories are setup, you can run deployment assistant on an Artist workstation."
    )
    print(f"{project_path.joinpath('svn/tools/deployment_assistant.py').as_posix()}")
    print(
        "https://projects.blender.org/studio/blender-studio-tools/src/branch/main/scripts/project-tools#readme"
    )
    print_header("Completed! Setup Assistant", 2)


if __name__ == "__main__":
    main()

import sys
import subprocess
import argparse
from pathlib import Path
from typing import Tuple, List, Dict, Any, Union, Optional

from . import vars
from .log import LoggerFactory

logger = LoggerFactory.getLogger()


def exception_handler(func):
    def func_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)

        except ValueError as error:
            logger.info(
                "# Oops. Seems like you gave some wrong input!"
                f"\n# Error: {error}"
                "\n# Program will be cancelled."
            )
            cancel_program()

        except RuntimeError as error:
            logger.info(
                "# Oops. Something went wrong during the execution of the Program!"
                f"\n# Error: {error}"
                "\n# Program will be cancelled."
            )
            cancel_program()

    return func_wrapper


def cancel_program() -> None:
    logger.info("# Exiting blender-purge")
    sys.exit(0)


def get_cmd_list(path: Path) -> Tuple[str]:
    cmd_list: Tuple[str] = (
        vars.BLENDER_PATH,
        path.as_posix(),
        "-b",
        "-P",
        f"{vars.PURGE_PATH}",
    )
    return cmd_list


"""
        "--log",
        "*overrides*",
        "--log",
        "-level 1",
"""


def validate_user_input(user_input, options):
    if user_input.lower() in options:
        return True
    else:
        return False


def prompt_confirm(path_list: List[Path]):
    options = ["yes", "no", "y", "n"]
    list_str = "\n".join([p.as_posix() for p in path_list])
    noun = "files" if len(path_list) > 1 else "file"
    confirm_str = f"# Do you want to purge {len(path_list)} {noun}? ([y]es/[n]o)"
    input_str = "# Files to purge:" + "\n" + list_str + "\n\n" + confirm_str
    while True:
        user_input = input(input_str)
        if validate_user_input(user_input, options):
            if user_input in ["no", "n"]:
                logger.info("\n# Process was canceled.")
                return False
            else:
                return True
        logger.info("\n# Please enter a valid answer!")
        continue


def run_check():
    cmd_list: Tuple[str] = (vars.BLENDER_PATH, "-b", "-P", f"{vars.CHECK_PATH}")
    p = subprocess.Popen(cmd_list)
    return p.wait()


def purge_file(path: Path) -> int:
    # get cmd list
    cmd_list = get_cmd_list(path)
    p = subprocess.Popen(cmd_list, shell=False)
    # stdout, stderr = p.communicate()
    return p.wait()


def is_filepath_valid(path: Path) -> None:

    # check if path is file
    if not path.is_file():
        raise ValueError(f"Not a file: {path.suffix}")

    # check if path is blend file
    if path.suffix != ".blend":
        raise ValueError(f"Not a blend file: {path.suffix}")


@exception_handler
def purge(args: argparse.Namespace) -> int:

    # parse arguments
    path = Path(args.path).absolute()
    confirm = args.confirm
    recursive = args.recursive

    if not path:
        raise ValueError("Please provide a path as first argument")

    if not path.exists():
        raise ValueError(f"Path does not exist: {path.as_posix()}")

    # vars
    files = []

    # collect files to purge
    if path.is_dir():
        if recursive:
            blend_files = [
                f for f in path.glob("**/*") if f.is_file() and f.suffix == ".blend"
            ]
        else:
            blend_files = [
                f for f in path.iterdir() if f.is_file() and f.suffix == ".blend"
            ]
        files.extend(blend_files)
    else:
        is_filepath_valid(path)
        files.append(path)

    # can only happen on folder here
    if not files:
        logger.info("# Found no .blend files to purge")
        cancel_program()

    # sort
    files.sort(key=lambda f: f.name)

    # promp confirm
    if bool(confirm) or path.is_dir():
        if not prompt_confirm(files):
            cancel_program()

    # perform check of correct preference settings
    return_code = run_check()
    if return_code == 1:
        raise RuntimeError(
            "Override auto resync is turned off. Turn it on in the preferences and try again."
        )

    # purge each file two times
    for i in range(vars.PURGE_AMOUNT):
        return_code = purge_file(path)
        if return_code != 0:
            raise RuntimeError("Blender Crashed on file: %s", path.as_posix())

    return 0

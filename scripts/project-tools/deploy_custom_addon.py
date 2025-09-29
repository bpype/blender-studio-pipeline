from pathlib import Path
import hashlib
import shutil


def get_input_addon():
    """
    Validates if the given filepath exists and has a .zip extension.
    Keeps prompting the user until a valid .zip file is provided.

    Returns:
        Path: The validated filepath as a pathlib.Path object.
    """
    while True:
        filepath = input("Enter the path to the .zip file: ").strip()
        path = Path(filepath)
        if not path.exists():
            print(f"Error: The file '{filepath}' does not exist. Please try again.")
            continue
        if not path.suffix == '.zip':
            print(f"Error: The file '{filepath}' is not a .zip file. Please try again.")
            continue
        return path


def generate_sha256_file(zip_path):
    """
    Generates a .sha256 file for the given .zip file.

    Args:
        zip_filepath (str): The path to the .zip file.

    Returns:
        Path: The path to the generated .sha256 file.
    """
    sha256_hash = hashlib.sha256()

    with zip_path.open("rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)

    sha256_file_path = zip_path.with_suffix(zip_path.suffix + ".sha256")
    with sha256_file_path.open("w") as sha256_file:
        sha256_file.write(sha256_hash.hexdigest())

    return sha256_file_path


def main():
    # Validate the zip file
    addon_path = get_input_addon()

    # Define the download folder path
    current_file_folder_path = Path(__file__).parent
    download_folder_path = (
        current_file_folder_path / "../../shared/artifacts/extensions/"
    ).resolve()

    # Copy the zip file to the download folder
    destination_path = download_folder_path / addon_path.name
    shutil.copy(addon_path, destination_path)
    print(f"Copied '{addon_path}' to '{destination_path}'.")

    # Generate the .sha256 file
    sha256_file_path = generate_sha256_file(destination_path)
    print(f"Generated SHA256 file at '{sha256_file_path}'.")
    print(addon_path.name + " deployed to " + str(download_folder_path))
    print("Success!")


if __name__ == "__main__":
    main()

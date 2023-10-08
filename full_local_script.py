"""
This script is used to sort files into folders based on the folderStructure.json file.
It also creates and populates meta.json files for each folder.
"""
import json
import os
import re

META_FILE_NAME = "meta.json"


def load_json(file_path):
    """
    Loads a JSON file.

    file_path: The path to the JSON file.

    Returns: The loaded JSON data.
    """
    with open(file_path, encoding="utf-8") as json_file:
        return json.load(json_file)


def create_folders(folder_structure):
    """
    Creates all folders listed in the folder_structure.json file.

    folder_structure: The folder structure data.
    """
    for folder in folder_structure:
        if folder != "files":
            if not os.path.exists(folder):
                os.makedirs(folder)
                for subfolder in folder_structure[folder]:
                    if subfolder != "files":
                        subfolder_path = os.path.join(folder, subfolder)
                        if not os.path.exists(subfolder_path):
                            os.makedirs(subfolder_path)


def move_files(folder_structure):
    """
    Moves files into folders based on the folder structure data.

    folder_structure: The folder structure data.
    """
    for file in os.listdir():
        for folder, patterns in folder_structure.items():
            if folder != "files":
                if "files" in patterns:
                    for _, regex in patterns["files"].items():
                        if re.match(regex, file):
                            os.rename(file, os.path.join(folder, file))
                for subfolder in patterns:
                    if subfolder != "files" and subfolder in folder_structure[folder]:
                        for _, regex in folder_structure[folder][subfolder][
                            "files"
                        ].items():
                            if re.match(regex, file):
                                os.rename(file, os.path.join(folder, subfolder, file))


def create_meta_json(root_path):
    """
    Creates a meta.json file for each directory in the given path.

    root_path: The path to the directory to create the meta.json files in.
    """

    for root, dirs, files in os.walk(root_path):
        meta = {
            "self": META_FILE_NAME,
            "selfDirName": os.path.basename(root),
            "metaTargets": [],
            "files": {},
            "versionInfo": {},
        }

        for file in files:
            if file.endswith(".hex"):
                match = re.search(r"(\d+)\.(\d+)\.(\d+)\.(\d+)", file)
                if match:
                    version_compact = ".".join(
                        str(int(group)) for group in match.groups()
                    )
                    version_full = match.group(0)

                    meta["versionInfo"] = {
                        "versionCompact": version_compact,
                        "versionFull": version_full,
                        **dict(
                            zip(
                                [
                                    "versionFamily",
                                    "versionMajor",
                                    "versionMinor",
                                    "versionPatch",
                                ],
                                map(int, match.groups()),
                            )
                        ),
                    }
                break

        for directory in dirs:
            target = {
                "targetName": directory,
                "metaInformationFile": f"{directory}/meta.json",
            }
            meta["metaTargets"].append(target)

        for file in files:
            if file != META_FILE_NAME:
                meta["files"][file] = file

        meta_file_path = os.path.join(root, META_FILE_NAME)
        with open(meta_file_path, "w", encoding="utf-8") as meta_file:
            json.dump(meta, meta_file, indent=4)


def get_regex_mappings(folder_structure):
    """
    Extracts the regex mappings from the folder structure data.

    folder_structure: The folder structure data.

    Returns: A dictionary containing the extracted regex mappings.
    """
    regex_mappings = {}

    def extract_recursive(data, path=None):
        if path is None:
            path = []

        for key, value in data.get("files", {}).items():
            regex_mappings.setdefault(key, []).append(value)

        for subfolder, subfolder_data in data.items():
            if subfolder != "files" and isinstance(subfolder_data, dict):
                extract_recursive(subfolder_data, path + [subfolder])

    extract_recursive(folder_structure)
    return regex_mappings


def update_meta_file_keys(root_path, regex_mappings):
    """
    Updates the keys in meta.json files based on the regex mappings.

    root_path: The path to the folder to update the meta.json files in.
    regex_mappings: The extracted data from folderStructure.json.
    """
    for root, _, files in os.walk(root_path):
        for filename in files:
            if filename == META_FILE_NAME:
                meta_file_path = os.path.join(root, filename)
                with open(meta_file_path, "r", encoding="utf-8") as meta_file:
                    meta_data = json.load(meta_file)

                if "files" in meta_data:
                    updated_files = {}
                    for old_key, value in meta_data["files"].items():
                        updated_key = next(
                            (
                                key
                                for key, values in regex_mappings.items()
                                if any(re.match(pattern, old_key) for pattern in values)
                            ),
                            old_key,
                        )
                        updated_files[updated_key] = value

                    meta_data["files"] = updated_files

                    with open(
                        meta_file_path, "w", encoding="utf-8"
                    ) as updated_meta_file:
                        json.dump(meta_data, updated_meta_file, indent=4)


if __name__ == "__main__":
    folder_struc = load_json("folderStructure.json")
    create_folders(folder_struc)
    move_files(folder_struc)
    create_meta_json("C:/Users/pypa/Downloads/sort_test")
    extr_data = get_regex_mappings(folder_struc)
    update_meta_file_keys(".", extr_data)

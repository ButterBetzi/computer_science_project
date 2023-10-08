"""
Module for generating meta.json files.
author: Pascal Puy
"""
import json
import os
import re
from typing import Dict, Tuple

from dateutil import parser

META_TEMPLATE = {
    "self": "meta.json",
    "selfDirName": "",
    "metaTargets": [],
    "files": {},
    "versionInfo": {},
}

BUILD_INFO_TEMPLATE = {
    "buildNode": "",
    "buildId": 0,
    "buildTimestamp": "",
    "buildYear": 0,
    "buildMonth": 0,
    "buildDay": 0,
    "buildHour": 0,
    "buildMinute": 0,
    "buildSecond": 0,
    "versionIar": "",
    "versionPython": "",
    "versionJlink": "",
    "versionControlSystem": {
        "type": "git",
        "repositories": {},
    },
}


class MetaJsonHandler:
    """
    Class for generating meta.json files.
    """

    def __init__(self) -> None:
        self.meta_template = META_TEMPLATE
        self.build_info_template = BUILD_INFO_TEMPLATE

    def _load_json_file(self, file_path: str, template: Dict) -> Dict:
        """
        Loads the JSON file at the specified file_path.
        If the file doesn't exist, creates it with the provided template.
        """
        if not os.path.isfile(file_path):
            with open(file_path, "w", encoding="utf-8") as json_file:
                json.dump(template, json_file, indent=4)
        with open(file_path, "r", encoding="utf-8") as json_file:
            return json.load(json_file)

    def _save_json_file(self, file_path: str, data: Dict) -> None:
        """
        Saves the JSON data to the specified file_path.
        """
        with open(file_path, "w", encoding="utf-8") as json_file:
            json.dump(data, json_file, indent=4)

    def _get_timestamp_from_env(
        self, env_var_name: str
    ) -> Tuple[str, int, int, int, int, int, int]:
        """
        Parses a timestamp from the specified environment variable name.
        Returns a tuple containing ISO timestamp and date/time components.
        """
        timestamp = parser.parse(os.environ.get(env_var_name, ""))
        return (
            timestamp.astimezone().isoformat(),
            timestamp.year,
            timestamp.month,
            timestamp.day,
            timestamp.hour,
            timestamp.minute,
            timestamp.second,
        )

    def _get_repo_name(self, env_var_name: str) -> str:
        """
        Extracts the repository name from the environment variable name.
        Converts it to camelCase.
        """
        repo_name = env_var_name.split("_", 2)[2]
        repo_name = "".join(x.capitalize() or "_" for x in repo_name.split("_"))
        return repo_name[0].lower() + repo_name[1:]

    def update_meta_json(
        self, file_path: str, key: str, value: str, json_path: str
    ) -> None:
        """
        Adds a key-value pair to the JSON file at the specified meta_path.
        If there is no JSON file at the path, it will create one with the meta_template.
        """
        meta_json = self._load_json_file(file_path, self.meta_template)

        if not meta_json["selfDirName"]:
            meta_json["selfDirName"] = os.path.basename(os.path.dirname(file_path))
        meta_json[json_path][key] = value

        self._save_json_file(file_path, meta_json)

    def generate_build_info_file(self, file_path: str) -> None:
        """
        Generates a buildInfo.json file at the specified file_path.
        """
        build_info_json = self._load_json_file(file_path, self.build_info_template)
        build_info_json["buildNode"] = os.environ.get("NODE_NAME", "")
        build_info_json["buildId"] = os.environ.get("BUILD_ID", "")

        (
            build_info_json["buildTimestamp"],
            build_info_json["buildYear"],
            build_info_json["buildMonth"],
            build_info_json["buildDay"],
            build_info_json["buildHour"],
            build_info_json["buildMinute"],
            build_info_json["buildSecond"],
        ) = self._get_timestamp_from_env("BUILD_TIMESTAMP")

        build_info_json["versionIar"] = os.environ.get("IAR_VERSION", "")
        build_info_json["versionPython"] = os.environ.get("PYTHON_VERSION", "")
        build_info_json["versionJlink"] = os.environ.get("JLINK_VERSION", "")

        build_info_json["versionControlSystem"]["repositories"] = {}
        for key, value in os.environ.items():
            if key.startswith("GIT_INFO_"):
                repo_name = self._get_repo_name(key)
                repo_info = json.loads(value)
                build_info_json["versionControlSystem"]["repositories"][
                    repo_name
                ] = repo_info

        self._save_json_file(file_path, build_info_json)

    def create_meta_files_all(self, meta_release_dir: str) -> None:
        """
        Creates a meta.json file in every directory of the specified meta_release_dir.
        Checks for a buildInfo.json file and adds it to the meta.json if it exists.
        Also adds version information to the meta.json if a file with a version is found.
        """
        build_info_path = os.path.join(meta_release_dir, "buildInfo.json")
        self.generate_build_info_file(build_info_path)

        for root, dirs, files in os.walk(meta_release_dir):
            meta_path = os.path.join(root, "meta.json")
            meta_json = self._load_json_file(meta_path, self.meta_template)

            if "meta.json" not in files:
                meta_json["selfDirName"] = os.path.basename(root)
                meta_json["metaTargets"] = [
                    {"metaInformationFile": f"{dir}/meta.json", "targetName": dir}
                    for dir in dirs
                ]

            if "buildInfo.json" in files:
                if "files" not in meta_json:
                    meta_json["files"] = {}
                meta_json["files"]["buildInfo"] = "buildInfo.json"

            for file in files:
                match = re.search(r"(\d+)\.(\d+)\.(\d+)\.(\d+)", file)
                if match:
                    version_compact = ".".join(
                        str(int(group)) for group in match.groups()
                    )
                    version_full = match.group(0)

                    meta_json["versionInfo"] = {
                        "versionCompact": version_compact,
                        "versionFull": version_full,
                        # assign version parts to the matched regex groups
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

            self._save_json_file(meta_path, meta_json)

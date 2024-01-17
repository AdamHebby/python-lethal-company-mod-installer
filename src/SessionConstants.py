from __future__ import annotations
import tempfile

class SessionConstants:
    GITHUB_REPO_URL: str    = "https://github.com/AdamHebby/python-lethal-company-mod-installer/releases"
    GITHUB_LATEST_URL: str  = GITHUB_REPO_URL + "/latest/download/"
    GITHUB_SHASUM_URL: str  = GITHUB_LATEST_URL + "shasum.txt"
    TEMP_TEST_DIR: str      = tempfile.gettempdir() + "/lcmods_test/"
    TEMP_DIR: str           = tempfile.gettempdir() + "/lcmods/"
    TEMP_DIR_CONF: str      = tempfile.gettempdir() + "/lcconf/"
    TEMP_DIR_PROG: str      = tempfile.gettempdir() + "/lcprogress/"
    MOD_DOWNLOAD_URL: str   = ""
    PAGE_DOWNLOAD_URL: str  = ""
    REMOTE_SETTINGS: str    = "https://lcmods.ge3kingit.net.nz/LCMods/settings.yaml"
    USER_AGENT: str         = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    IGNORE_FILES: list[str] = [
        "manifest.json",
        "CHANGELOG.md",
        "README.md",
        "LICENSE",
        "icon.png",
    ]

    LOG_LEVEL_DEBUG: int = 0
    LOG_LEVEL_INFO: int = 1
    LOG_LEVEL_WARNING: int = 2
    LOG_LEVEL_ERROR: int = 3

    LOG_LEVEL: int = LOG_LEVEL_ERROR

    @staticmethod
    def setLogLevel(level: int) -> None:
        SessionConstants.LOG_LEVEL = level

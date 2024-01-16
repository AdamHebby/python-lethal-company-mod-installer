from __future__ import annotations
import hashlib
from hmac import new
import os
import sys

import requests

from src.SessionConstants import SessionConstants
from src.Utils import getCurrentDir, info, success, error, warning

class InstallerManager:
    @staticmethod
    def downloadLatestVersion() -> None:
        Current_Path  = getCurrentDir()
        remoteShaFile = requests.get(SessionConstants.GITHUB_SHASUM_URL).text

        if remoteShaFile == None:
            return

        remoteSha256Sum  = remoteShaFile.split("  ", 1)[0]
        remoteShaExeFile = remoteShaFile.split("  ", 1)[1]
        localSha256Sum   = hashlib.sha256(open(sys.argv[0], "rb").read()).hexdigest()

        if remoteSha256Sum.strip() != localSha256Sum:
            # Download latest exe
            info("Downloading latest version of installer...")
            r = requests.get(SessionConstants.GITHUB_LATEST_URL + remoteShaExeFile, allow_redirects=True)

            newExeName = InstallerManager.renameFileToAvoidCollision(remoteShaExeFile)

            open(os.path.join(Current_Path, newExeName), 'wb').write(r.content)

            success("Launching latest version of installer...")
            try:
                os.startfile(os.path.join(Current_Path, remoteShaExeFile)) # type: ignore
                sys.exit()
            except Exception as e:
                if e.winerror == 1223: # type: ignore
                    success("User cancelled update")
                else:
                    error("Error launching installer: " + str(e))
                    warning(f'Please download the latest installer from {SessionConstants.GITHUB_LATEST_URL + remoteShaExeFile}')
                    input()
        pass

    @staticmethod
    def renameFileToAvoidCollision(exeName: str) -> str:
        Current_Path = getCurrentDir()

        if not os.path.exists(Current_Path + "/" + exeName):
            return exeName

        num = 1
        while True:
            withoutExt = os.path.splitext(exeName)[0]
            newName = f'{withoutExt} ({num}).exe'

            if not os.path.exists(Current_Path + "/" + newName):
                warning(f'File {exeName} already exists, renaming to {newName}')
                return newName

            num += 1

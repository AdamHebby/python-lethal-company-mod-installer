from __future__ import annotations
import shutil
from src.Version import Version
from src.SessionConstants import SessionConstants
from src.Utils import copyTree, findFile, downloadZip, makeDirectory, warning, info
import os, requests, re

class ModSetting:
    author: str
    modName: str
    fullModName: str
    modVersion: Version
    modPathMap: list[str]
    forcePin: str | None = None

    newModVersion: Version | None = None
    updateLog: list = []

    def __init__(
            self,
            fullModName: str,
            modVersion: Version,
            modPathMap: list,
            forcePin: str | None = None
        ):
        self.author      = fullModName.split("/")[0]
        self.modName     = fullModName.split("/")[1]
        self.fullModName = fullModName
        self.modVersion  = modVersion
        self.modPathMap  = modPathMap
        self.forcePin    = forcePin

    def applyNewVersion(self: ModSetting) -> None:
        if self.newModVersion is None:
            return

        self.modVersion = self.newModVersion
        self.newModVersion = None
        self.addUpdateLog("New version set to " + self.modVersion.version)

    def setNewVersion(self: ModSetting, newVersion: Version) -> None:
        self.newModVersion = newVersion

    def setForcePin(self: ModSetting, forcePin: str) -> None:
        self.forcePin = forcePin
        self.addUpdateLog("Force pin set to " + forcePin)

    def addUpdateLog(self: ModSetting, log: str) -> None:
        self.updateLog.append(log)

    def addPathMap(self: ModSetting, pathMapLeft: str, pathMapRight: str) -> None:
        left = pathMapLeft.strip("/").replace('//', '/')
        right = pathMapRight.removeprefix("/").replace('//', '/')

        left = left if left != "" else "/"
        right = right if right != "" else "/"

        pathMap = left + ":" + right

        self.modPathMap.append(pathMap)
        self.addUpdateLog("Added path map " + pathMap)

    def toJSONForSettings(self: ModSetting) -> dict:
        d = {
            "version": self.modVersion.version,
            "pathmap": self.modPathMap,
        }

        if self.forcePin != None:
            d["forcePin"] = self.forcePin

        return d

    def hasDownloadFiles(self: ModSetting) -> bool:
        return (
            os.path.exists(SessionConstants.TEMP_DIR + self.modName) and
            os.path.isdir(SessionConstants.TEMP_DIR + self.modName) and
            len(os.listdir(SessionConstants.TEMP_DIR + self.modName)) > 0
        )

    def download(self: ModSetting) -> None:
        info("Downloading " + str(self))

        downloadZip(self.getDownloadUrl(), SessionConstants.TEMP_DIR + self.modName)

    def downloadNewVersion(self: ModSetting) -> None:
        version = self.modVersion.version if self.newModVersion == None else self.newModVersion.version
        info("Downloading " + self.fullModName + " " + version)

        if os.path.exists(SessionConstants.TEMP_DIR + self.modName):
            print("debug: skipping download of " + self.modName + " - already exists")
            return

        downloadZip(
            SessionConstants.MOD_DOWNLOAD_URL + self.fullModName + "/" + version + "/",
            SessionConstants.TEMP_DIR + self.modName
        )

    def checkForNewVersion(self: ModSetting) -> Version | None:
        pageUrl     = SessionConstants.PAGE_DOWNLOAD_URL + self.fullModName
        downloadUrl = SessionConstants.MOD_DOWNLOAD_URL + self.fullModName
        page        = requests.get(pageUrl, allow_redirects=True, headers={"User-Agent": SessionConstants.USER_AGENT})

        if page.status_code >= 400:
            raise Exception("Error downloading " + pageUrl + " - " + str(page.status_code) + " " + page.reason)

        latestVersion  = re.search(
            r'' + re.escape(downloadUrl) + r'\/((\d+\.?){3,4})\/"',
            page.content.decode("utf-8")
        )

        if latestVersion == None:
            print("NO VERION FOUND FOR " + self.fullModName)
            return None

        latestVersion = Version(str(latestVersion.group(1)))

        if latestVersion.gt(self.modVersion):
            return latestVersion

        return None

    def getDownloadUrl(self: ModSetting) -> str:
        return SessionConstants.MOD_DOWNLOAD_URL + self.fullModName + "/" + self.modVersion.version + "/"

    def verifyThrow(self: ModSetting) -> None:
        if not self.verify():
            raise Exception("Error downloading " + self.modName + " - Incomplete")

    def verify(self: ModSetting) -> bool:
        if not self.hasDownloadFiles():
            warning("Cannot verify " + self.fullModName + " - Incomplete")
            return False

        for pmap in self.modPathMap:
            copyMap  = pmap.split(":")
            copyFrom = SessionConstants.TEMP_DIR + self.modName + "/" + copyMap[0]

            if not os.path.exists(copyFrom) or (os.path.isdir(copyFrom) and len(os.listdir(copyFrom)) == 0):
                warning("Cannot verify " + self.fullModName + " - Missing or empty " + copyFrom)
                return False

        return True

    def copyTo(self: ModSetting, path: str) -> None:
        for pmap in self.modPathMap:
            copyMap  = pmap.split(":")
            copyFrom = SessionConstants.TEMP_DIR + self.modName + "/" + copyMap[0]
            copyTo   = path + "/" + copyMap[1]

            try:
                if copyTo.endswith("/"):
                    makeDirectory(copyTo)

                if not os.path.isdir(copyFrom):
                    shutil.copy(copyFrom, copyTo)
                else:
                    copyTree(copyFrom, copyTo)
            except Exception as e:
                raise Exception("Error copying " + self.modName + " - " + copyFrom + " to " + copyTo + " - " + str(e))

    def findManifest(self: ModSetting) -> str | None:
        return findFile(SessionConstants.TEMP_DIR + self.modName, "manifest.json")

    def __str__(self: ModSetting) -> str:
        version    = f'ForcePin: {self.forcePin}' if self.forcePin != None else self.modVersion.version
        newVersion = f' ( {self.newModVersion.version} )' if self.newModVersion != None else ""

        return f'{self.fullModName} {version}{newVersion}'

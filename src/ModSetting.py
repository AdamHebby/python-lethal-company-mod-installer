from __future__ import annotations
import shutil
from src.Version import Version
from src.SessionConstants import SessionConstants
from src.Utils import copyTree, findFile, downloadZip, loadPotentiallyDodgyJson, makeDirectory, warning, info, yellow
import os, requests, re

class ModSettingManifest:
    path: str
    version: Version
    websiteUrl: str
    description: str
    dependencies: list[str]

    def __init__(self: ModSettingManifest, path: str, version: str | Version, websiteUrl: str, description: str, dependencies: list[str]):
        self.path = path
        self.version = Version(str(version))
        self.websiteUrl = websiteUrl
        self.description = description
        self.dependencies = dependencies

    @staticmethod
    def fromJson(path: str, json: dict) -> ModSettingManifest:
        return ModSettingManifest(
            path,
            json["version_number"],
            json["website_url"],
            json["description"],
            json["dependencies"]
        )

    @staticmethod
    def fromFile(path: str) -> ModSettingManifest:
        manifest = loadPotentiallyDodgyJson(path)

        if manifest == None:
            raise Exception("Error loading manifest.json")

        return ModSettingManifest.fromJson(path, manifest)

class ModSetting:
    author: str
    modName: str
    fullModName: str
    modVersion: Version
    modPathMap: list[str]
    forcePin: str | None = None

    newModVersion: Version | None = None

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

    def setNewVersion(self: ModSetting, newVersion: Version) -> None:
        self.newModVersion = newVersion

    def setForcePin(self: ModSetting, forcePin: str) -> None:
        self.forcePin = forcePin

    def addPathMap(self: ModSetting, pathMapLeft: str, pathMapRight: str) -> None:
        left = pathMapLeft.strip("/").replace('//', '/')
        right = pathMapRight.removeprefix("/").replace('//', '/')

        left = left if left != "" else "/"
        right = right if right != "" else "/"

        pathMap = left + ":" + right

        self.modPathMap.append(pathMap)

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
            warning("Error downloading " + pageUrl + " - " + str(page.status_code) + " " + page.reason)
            return None

        latestVersion  = re.search(
            r'' + re.escape(downloadUrl) + r'\/((\d+\.?){3,4})\/"',
            page.content.decode("utf-8")
        )

        if latestVersion == None:
            print("NO VERSION FOUND FOR " + self.fullModName)
            return None

        latestVersion = Version(str(latestVersion.group(1)))

        if latestVersion.gt(self.modVersion):
            print("NEW VERSION FOUND FOR " + self.fullModName + f" - {self.modVersion} ({self.newModVersion}) -> {latestVersion}")
            return latestVersion

        return None

    def getDownloadUrl(self: ModSetting) -> str:
        if self.forcePin != None:
            return self.forcePin

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

        if self.modDoesNotContainManifest():
            return True

        try:
            manifest = self.getManifest()
            if manifest == None:
                warning("Cannot verify " + self.fullModName + " - Missing manifest.json")
                return False

            if manifest.version != self.modVersion and manifest.version != self.newModVersion and self.forcePin == None:
                warning("Cannot verify " + self.fullModName + " - Invalid version in manifest.json")
                return False

        except Exception as e:
            warning("Cannot verify " + self.fullModName + " - " + str(e))
            return False

        return True

    def modDoesNotContainManifest(self: ModSetting) -> bool:
        return self.findManifest() == None and self.hasDownloadFiles()

    def getManifest(self: ModSetting) -> ModSettingManifest | None:
        manifestPath = self.findManifest()
        if manifestPath == None:
            warning("Cannot find manifest.json for " + self.fullModName)
            return None

        return ModSettingManifest.fromFile(manifestPath)

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
        newVersion = yellow(f' ({self.newModVersion.version})' if self.newModVersion != None else "")

        return f'{self.fullModName} {version}{newVersion}'

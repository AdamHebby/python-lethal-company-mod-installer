from __future__ import annotations
import json
import os, hashlib
from src.SessionConstants import SessionConstants
from src.ModSetting import ModSetting
from src.Utils import getFlatFileList

class ModHashMap:
    modName: str
    modHashes: dict[str, str]

    def __init__(self, modName: str):
        self.modName = modName
        self.modHashes = {}

    def addHash(self, path: str, hash: str) -> None:
        self.modHashes[path] = hash

    def getHash(self, path: str) -> str | None:
        if path in self.modHashes:
            return self.modHashes[path]
        else:
            return None

    def getHashes(self) -> dict[str, str]:
        return self.modHashes

class HashMapper:
    modHashMaps: dict[str, ModHashMap]
    lethalCompanyOutputFolder: str

    def __init__(self, lethalCompanyOutputFolder: str):
        self.modHashMaps = {}
        self.lethalCompanyOutputFolder = lethalCompanyOutputFolder

    def load(self: HashMapper) -> None:
        if not self.checkOutputFolder():
            return

        hashesFilePath = os.path.join(self.lethalCompanyOutputFolder, "hashes.json")
        if not os.path.exists(hashesFilePath):
            return

        jsonObj = json.load(open(hashesFilePath, "r"))

        if jsonObj == None:
            return

        for modName in jsonObj:
            modHashMap = ModHashMap(modName)

            for path in jsonObj[modName]:
                modHashMap.addHash(path, jsonObj[modName][path])

            self.modHashMaps[modName] = modHashMap

    def save(self: HashMapper) -> None:
        if not self.checkOutputFolder():
            return

        hashesFilePath = os.path.join(self.lethalCompanyOutputFolder, "hashes.json")
        jsonObj = {}

        for modName in self.modHashMaps:
            jsonObj[modName] = self.modHashMaps[modName].getHashes()

        json.dump(jsonObj, open(hashesFilePath, "w"), indent=4)

    def clear(self: HashMapper) -> None:
        self.modHashMaps = {}
        self.save()

    def hashModFolder(self: HashMapper, mod: ModSetting) -> None:
        modName = mod.modName

        if not self.checkOutputFolder():
            return

        modPath = os.path.join(SessionConstants.TEMP_DIR, modName)
        if not os.path.exists(modPath):
            return

        files = getFlatFileList(modPath)
        if len(files) == 0:
            return

        modHashMap = ModHashMap(mod.fullModName)
        for file in files:
            if os.path.basename(file) in SessionConstants.IGNORE_FILES:
                continue

            if os.path.isfile(file):
                modHashMap.addHash(
                    file.replace(modPath, ""),
                    hashlib.sha256(open(file, "rb").read()).hexdigest()
                )

        self.modHashMaps[mod.fullModName] = modHashMap

        pass

    def checkModHash(self: HashMapper, mod: ModSetting) -> bool:
        if mod.fullModName not in self.modHashMaps:
            return False

        modHashMap = self.modHashMaps[mod.fullModName]
        hashes     = modHashMap.getHashes()

        for file in hashes:
            filePath = os.path.join(self.lethalCompanyOutputFolder, file)

            if os.path.isfile(filePath):
                if hashes[file] != hashlib.sha256(open(file, "rb").read()).hexdigest():
                    return False

        return True

    def checkOutputFolder(self: HashMapper) -> bool:
        return (
            self.lethalCompanyOutputFolder != None and
            os.path.exists(self.lethalCompanyOutputFolder) and
            os.path.isdir(self.lethalCompanyOutputFolder)
        )

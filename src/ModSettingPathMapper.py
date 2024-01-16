from __future__ import annotations
import os
from src.ModSetting import ModSetting
from src.SessionConstants import SessionConstants

def isFile(path: str) -> bool:
    return os.path.exists(path) and os.path.isfile(path)

def isDir(path: str) -> bool:
    return os.path.exists(path) and os.path.isdir(path)

def isDirFlat(path: str) -> bool:
    for file in os.listdir(path):
        if isDir(path + "/" + file):
            return False

    return True

def joinPaths(a, *p) -> str:
    path = a
    for b in p:
        path = path + os.sep + b

    return path.replace("//", "/")

def findFileExtsRecursive(path: str, ext: str, found: list[str] = []) -> list[str]:
    if not os.path.exists(path):
        return []

    if os.path.isfile(path):
        if path.endswith(ext):
            found.append(path)
        return found

    for file in os.listdir(path):
        findFileExtsRecursive(joinPaths(path, file), ext, found)

    return found

class ModSettingPathMapper:
    # BepInEx actually has a very simple pathmap system and loads magically.
    @staticmethod
    def dumbExecute(mod: ModSetting) -> None:
        if mod.modName == "BepInExPack" or mod.modName == "FakeMod_BepInExPack":
            mod.addPathMap(mod.modName, "/")
            return

        # find all .cfg files in the mod folder and add them to the pathmap for /BepInEx/config/
        modDir = joinPaths(SessionConstants.TEMP_DIR, mod.modName, "/")
        cfgs = findFileExtsRecursive(modDir, ".cfg", [])
        if len(cfgs) > 0:
            for file in cfgs:
                mod.addPathMap(file.removeprefix(modDir), "/BepInEx/config/")

        mod.addPathMap('/', "/BepInEx/plugins/" + mod.modName + "/")

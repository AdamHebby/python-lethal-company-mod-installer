from __future__ import annotations
import json
import os, sys, traceback
import random
import time
from turtle import down

from src.ModSettingPathMapper import ModSettingPathMapper
from src.ModSetting import ModSetting, ModSettingManifest
from src.Settings import Settings
from src.Version import Version
from src.Utils import error, loadPotentiallyDodgyJson, success, cleanTempFiles

Current_Path = str(os.path.dirname(__file__))

class DependencyManager:
    _dependencies: dict[str, dict] = {}
    settings: Settings

    def __init__(self: DependencyManager, settings: Settings) -> None:
        for mod in settings.modSettings:
            self._dependencies[mod.fullModName] = {
                "modName": mod.fullModName,
                "modVersion": mod.modVersion.version,
                "forcePin": mod.forcePin,
            }

    def downloadAllDependencies(self: DependencyManager) -> None:
        success("Downloading ALL dependencies...")
        self.downloadDependenciesRecursively(self._dependencies)

    def downloadDependenciesRecursively(self: DependencyManager, dependencies: dict[str, dict]) -> None:
        for dep in list(dependencies):
            depObj = dependencies[dep]

            mod = ModSetting(dep, Version(depObj["modVersion"]), [], depObj["forcePin"] if "forcePin" in depObj else None)

            if mod.fullModName in self._dependencies and mod.forcePin == None and self._dependencies[mod.fullModName]["forcePin"] == None:
                v = Version(self._dependencies[mod.fullModName]["modVersion"])

                if v > mod.modVersion and mod.hasDownloadFiles() and mod.verify(True):
                    continue

            manifest = None
            if not mod.hasDownloadFiles() or not mod.verify(True):
                mod.download()

            manifest = mod.getManifest()

            if manifest == None:
                continue

            depObj["manifest"] = manifest

            newDeps = self.getManifestDependencies(depObj)
            for d in newDeps:
                self.addDependency(newDeps[d])

            self.downloadDependenciesRecursively(newDeps)

    def getManifestDependencies(self: DependencyManager, dependency: dict) -> dict[str, dict]:
        if "manifest" not in dependency or dependency["manifest"] == None:
            return {}

        return self.listDependenciesInManifest(dependency["manifest"])

    def addDependency(self: DependencyManager, mod: dict) -> None:
        if mod["modName"] in self._dependencies:
            if "forcePin" in self._dependencies[mod["modName"]] and self._dependencies[mod["modName"]]["forcePin"] != None:
                return

            if "forcePin" in mod and mod["forcePin"] != None:
                self._dependencies[mod["modName"]] = mod
                return

            self._dependencies[mod["modName"]]["modVersion"] = Version.max(
                Version(self._dependencies[mod["modName"]]["modVersion"]),
                Version(mod["modVersion"])
            ).version

            return

        self._dependencies[mod["modName"]] = mod

    def listDependenciesInManifest(self: DependencyManager, manifest: ModSettingManifest) -> dict[str, dict]:
        dependencies: dict[str, dict] = {}

        if manifest == None or len(manifest.dependencies) == 0:
            return dependencies

        for dep in manifest.dependencies:
            depParts = dep.split("-")
            author   = depParts[0]
            depName  = depParts[1]
            version  = depParts[2]
            fullName = author + "/" + depName

            dependencies[fullName] = {
                "modName": fullName,
                "modVersion": version,
                "forcePin": None,
                "modDependencies": {},
                "manifest": None
            }

        return dependencies

    def update(self: DependencyManager) -> None:
        downloadedNew = True
        success("Checking for mod updates...")

        while downloadedNew:
            downloadedNew = False

            if downloadedNew:
                success("New mods required, checking new mods for updates...")

            for dep in self._dependencies:
                depObj = self._dependencies[dep]

                mod = ModSetting(dep, Version(depObj["modVersion"]), [], depObj["forcePin"] if "forcePin" in depObj else None)

                latestVersion = mod.checkForNewVersion()

                if latestVersion == None:
                    continue

                mod.setNewVersion(latestVersion)

                mod.downloadNewVersion()
                mod.modPathMap = []
                ModSettingPathMapper.dumbExecute(mod)

                if not mod.verify():
                    error("Failed to verify " + mod.fullModName)
                    continue

                downloadedNew = True

                success("Verified new version: " + str(mod))
                self._dependencies[dep]["modVersion"] = latestVersion.version

            before = self._dependencies.copy()
            self.downloadAllDependencies()

            if before != self._dependencies:
                downloadedNew = True

    def toJSON(self: DependencyManager) -> dict:
        return {
            "dependencies": [self._dependencies[dep] for dep in self._dependencies]
        }

try:
    # settings path is argv[1], ensure param is entered and file exists
    settingsPath = ""
    if len(sys.argv) == 2:
        settingsPath = sys.argv[1]
    else:
        settingsPath = os.path.join(Current_Path, "settings.yaml")

    settings = Settings.loadFromFile(settingsPath)

    dependencyManager = DependencyManager(settings)
    dependencyManager.update()

    for modDependency in dependencyManager._dependencies:
        dep = dependencyManager._dependencies[modDependency]
        mod = ModSetting(
            dep["modName"],
            Version(dep["modVersion"]),
            [],
            dep["forcePin"] if "forcePin" in dep else None
        )

        if not mod.hasDownloadFiles() or not mod.verify():
            mod.download()

        ModSettingPathMapper.dumbExecute(mod)

        mod.verifyThrow()

        settings.setModSetting(mod)

    settings.printDiff()
    settings.saveToFile(settingsPath)

    cleanTempFiles()

    success("Done")

except Exception as e:
    traceback.print_exc()

    cleanTempFiles()

    sys.exit()

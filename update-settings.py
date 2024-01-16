import os, sys, traceback

from src.ModSettingPathMapper import ModSettingPathMapper
from src.ModSetting import ModSetting
from src.Settings import Settings
from src.Version import Version
from src.Utils import error, getCurrentDir, loadPotentiallyDodgyJson, info, success, cleanTempFiles

Current_Path = getCurrentDir()

try:
    # settings path is argv[1], ensure param is entered and file exists
    settingsPath = ""
    if len(sys.argv) == 2:
        settingsPath = sys.argv[1]
    elif not os.path.isfile(sys.argv[1]):
        settingsPath = os.path.join(Current_Path, "settings.yaml")

    settings = Settings.loadFromFile(settingsPath)

    suggests: dict[str, ModSetting] = {}

    for mod in settings.modSettings:
        info("Checking " + str(mod))

        if mod.forcePin != None:
            print("Skipping pinned version " + mod.forcePin)
            continue

        latestVersion  = mod.checkForNewVersion()

        if latestVersion != None:
            success("New version available for " + mod.fullModName + " (" + str(latestVersion) + ")")
            mod.setNewVersion(latestVersion)

        mod.downloadNewVersion()
        mod.modPathMap = []
        ModSettingPathMapper.dumbExecute(mod)
        mod.verifyThrow()
        mod.applyNewVersion()

        settings.setModSetting(mod)

        info("Checking manifest for " + mod.fullModName)
        # find manifest.json within mod folder
        manifestPath = mod.findManifest()
        if manifestPath == None:
            error("Cannot find manifest.json for " + mod.fullModName)
            continue

        try:
            # Use subprocess.run with input and output pipes
            manifest = loadPotentiallyDodgyJson(manifestPath)

            if manifest != None and "dependencies" in manifest:
                for dep in manifest["dependencies"]:
                    depParts = dep.split("-")
                    author   = depParts[0]
                    depName  = depParts[1]
                    version  = depParts[2]
                    fullName = author + "/" + depName

                    existingDependency = settings.getModSetting(fullName)
                    newModDependency   = ModSetting(fullName, Version(version), [])

                    if existingDependency != None and existingDependency.modVersion.lt(newModDependency.modVersion):
                        error(
                            f'Newer version of Dependency {fullName} ({existingDependency.modVersion} -> {newModDependency.modVersion}) ' +
                            f'for {mod.fullModName} found in manifest.json'
                        )
                        continue

                    if fullName in suggests:
                        suggests[fullName].modVersion = Version.max(newModDependency.modVersion, suggests[fullName].modVersion)
                    else:
                        suggests[fullName] = newModDependency

        except KeyError as e:
            error("Error loading manifest.json for " + mod.fullModName)
            error("ERROR:" + e.args[0])

        print("")

    for suggest in suggests:
        newMod = suggests[suggest]

        newMod.download()

        ModSettingPathMapper.dumbExecute(newMod)

        newMod.verifyThrow()

        success("Adding " + newMod.fullModName + " " + str(newMod.modVersion) + " to settings")
        settings.setModSetting(newMod)

    # save settings.yaml
    settings.saveToFile(settingsPath)

    cleanTempFiles()

    success("Done")

except Exception as e:
    traceback.print_exc()

    cleanTempFiles()

    sys.exit()

from __future__ import annotations
import json
import os, sys, tempfile, time, concurrent.futures, hashlib, traceback, winreg
from src.SessionConstants import SessionConstants
from src.InstallerManager import InstallerManager

from src.Settings import Settings
from src.Utils import cleanTempFiles, confirm, copyTree, error, warning, info, success, green, makeDirectory, makeCleanDirectory, downloadZip, getCurrentDir
from src.HashMapper import HashMapper
from src.ModSetting import ModSetting
from src.RegistryKey import RegistryKeyManager

try:
    SessionConstants.setLogLevel(SessionConstants.LOG_LEVEL_DEBUG)
    Current_Path    = getCurrentDir()

    # Define constants
    TEMP_DIR        = tempfile.gettempdir() + "/lcmods/"
    TEMP_DIR_CONF   = tempfile.gettempdir() + "/lcconf/"
    TEMP_DIR_PROG   = tempfile.gettempdir() + "/lcprogress/"
    REMOTE_SETTINGS = "https://lcmods.ge3kingit.net.nz/LCMods/settings.yaml"

    def touchFile(path: str):
        open(path, 'a').close()

    def md5(name: str):
        return hashlib.md5(name.encode()).hexdigest()

    def markProgress(name: str):
        touchFile(TEMP_DIR_PROG + name)

    def hasProgress(name: str):
        return os.path.exists(TEMP_DIR_PROG + name)

    def delProgress(name: str):
        if os.path.exists(TEMP_DIR_PROG + name):
            os.remove(TEMP_DIR_PROG + name)

    def downloadMod(mod: ModSetting) -> None:
        info("Downloading " + str(mod))
        progressHash = md5(mod.getDownloadUrl())  # Decode the bytes object to a string
        delProgress(progressHash)
        downloadZip(mod.getDownloadUrl(), TEMP_DIR + mod.modName)
        markProgress(progressHash)

    # Get install location of Lethal Company
    LethalCompanyOutputFolder = RegistryKeyManager.getValue(
        winreg.HKEY_LOCAL_MACHINE, # type: ignore
        r'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Steam App 1966720',
        "InstallLocation",
        ""
    )

    winDefRealTimeProt = RegistryKeyManager.getValue(
        winreg.HKEY_LOCAL_MACHINE, # type: ignore
        r'SOFTWARE\Microsoft\Windows Defender\Real-Time Protection',
        "DisableRealtimeMonitoring",
        0
    )

    if winDefRealTimeProt == 0:
        error("Windows Defender Real-Time Protection is enabled, you may experience issues with mods or the installer")
        print("Carrying on in 3 seconds...")
        time.sleep(3)

    # exit if Lethal Company is not installed
    if LethalCompanyOutputFolder == "" or not os.path.exists(LethalCompanyOutputFolder):
        error("Lethal Company install folder not found: " + LethalCompanyOutputFolder)
        input()
        sys.exit()

    success("Lethal Company found at " + LethalCompanyOutputFolder)

    InstallerManager.downloadLatestVersion()

    # Get settings
    settings         = Settings.autoload()
    settingsHash     = hashlib.md5(json.dumps(settings.toJSON()).encode('utf-8')).hexdigest()
    settingsHashPath = os.path.normpath(os.path.join(LethalCompanyOutputFolder, ".settingshash"))
    lastSettingsHash = open(settingsHashPath, 'r').read() if os.path.exists(settingsHashPath) else ""

    makeDirectory(TEMP_DIR_PROG)

    hashMapper = HashMapper(LethalCompanyOutputFolder)
    hashMapper.load()

    shouldContinue = False
    canSkipDownload = True
    for mod in settings.modSettings:
        if not hashMapper.checkModHash(mod):
            canSkipDownload = False
            break

    if settingsHash != lastSettingsHash and canSkipDownload:
        warning("Settings have changed since last download")
        canSkipDownload = False

    if canSkipDownload and not hasProgress("isDownloading"):
        if confirm(green("Detected VALID existing mods, would you like to skip download?")):
            success("Skipping download, launching Lethal Company...")
            os.startfile("steam://launch/1966720") # type: ignore
            sys.exit()

    if hasProgress("isDownloading") and os.path.isdir(TEMP_DIR) and len(os.listdir(TEMP_DIR)) > 0:
        canSkipDownload = False
        shouldContinue = confirm(green("Detected stalled download, would you like to attempt to resume?)"))

        # Ensure directories exist
        makeDirectory(TEMP_DIR)
        makeDirectory(TEMP_DIR_CONF)
    else:
        # Ensure directories exist, and are empty
        cleanTempFiles()
        makeCleanDirectory(TEMP_DIR)
        makeCleanDirectory(TEMP_DIR_CONF)
        makeCleanDirectory(TEMP_DIR_PROG)

    # Download and extract Custom Configs
    downloadZip(settings.configZipUrl, TEMP_DIR_CONF)

    hashMapper.clear()

    markProgress("isDownloading")

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        results = []
        for mod in settings.modSettings:
            if shouldContinue and mod.hasDownloadFiles() and mod.verify():
                warning("Skipping previously downloaded " + mod.fullModName)
                continue

            # download and extract
            results.append(executor.submit(downloadMod, mod))

        concurrent.futures.wait(results)

    success("Downloaded all mods, checking files...")

    for mod in settings.modSettings:
        verified = False
        for i in range(5):
            try:
                if mod.verify():
                    verified = True
                    break
                else:
                    error("Cannot verify " + mod.fullModName + ", retrying...")
                    mod.download()

            except Exception as e:
                error("Error downloading + verifying " + mod.fullModName + " - " + str(e))
                info("Retrying in 5 seconds...")
                traceback.print_exc()
                time.sleep(5)

        if not verified:
            error("Error downloading + verifying " + mod.fullModName)
            input()
            sys.exit()

    success("Verified Downloads, copying files...")

    makeDirectory(LethalCompanyOutputFolder + "/BepInEx")
    makeCleanDirectory(LethalCompanyOutputFolder + "/BepInEx/plugins")
    makeDirectory(LethalCompanyOutputFolder + "/BepInEx/patchers")
    makeDirectory(LethalCompanyOutputFolder + "/BepInEx/config")

    # Loop through all configured mods, download ZIP, extract, copy files
    for mod in settings.modSettings:
        info("Copying " + mod.fullModName)

        for i in range(3):
            try:
                if mod.hasDownloadFiles():
                    mod.copyTo(LethalCompanyOutputFolder)
                    break
                else:
                    error("Incomplete download of " + mod.fullModName + ", retrying...")
                    mod.download()
                    mod.verifyThrow()

            except Exception as e:
                error("Error copying " + mod.fullModName + " - " + str(e))
                traceback.print_exc()
                info("Retrying in 5 seconds...")
                time.sleep(5)

    success("All mods copied, cleaning up...")

    hashMapper.clear()
    copyTree(TEMP_DIR_CONF + "/config", LethalCompanyOutputFolder + "/BepInEx/config")
    for mod in settings.modSettings:
        hashMapper.hashModFolder(mod)

    hashMapper.save()

    # Save settings hash
    open(settingsHashPath, 'w').write(settingsHash)

    cleanTempFiles()

    # Launch Lethal Company
    success("Launching Lethal Company...")

    os.startfile("steam://launch/1966720") # type: ignore

except Exception as e:
    traceback.print_exc()
    input()
    sys.exit()

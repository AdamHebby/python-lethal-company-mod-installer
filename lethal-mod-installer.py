import requests, zipfile, io, os, sys, shutil, tempfile, time, queue, yaml, concurrent.futures

# Ensure program is running
if getattr(sys, 'frozen', False):
    Current_Path = os.path.dirname(sys.executable)
else:
    Current_Path = str(os.path.dirname(__file__))

# Make Directory
def makeDirectory(path):
    if not os.path.exists(path):
        os.mkdir(path)

# Empty and remake directory
def makeCleanDirectory(path, deleteIfExist = True):
    if deleteIfExist and os.path.exists(path):
        shutil.rmtree(path)

    makeDirectory(path)

# Download and extract zip file
def download(downloadUrl, path):
    r = requests.get(downloadUrl, headers={"User-Agent": userAgent})
    z = zipfile.ZipFile(io.BytesIO(r.content))
    z.extractall(path)

# Copy directory tree, makes directories if they don't exist
def copyTree(fromPath, toPath):
    makeDirectory(toPath)

    for filename in os.listdir(fromPath):
        if os.path.isdir(fromPath + "/" + filename):
            copyTree(fromPath + "/" + filename, toPath + "/" + filename)
        else:
            shutil.copy(fromPath + "/" + filename, toPath)

try:
    # Get install location of Lethal Company
    LethalCompanyOutputFolder = ""
    if 'nt' in sys.builtin_module_names:
        import winreg
        aReg = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
        aKey = winreg.OpenKey(aReg, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Steam App 1966720')
        LethalCompanyOutputFolder = winreg.QueryValueEx(aKey, "InstallLocation")[0]

    # exit if Lethal Company is not installed
    if LethalCompanyOutputFolder == "" or not os.path.exists(LethalCompanyOutputFolder):
        print("Lethal Company install folder not found: " + LethalCompanyOutputFolder)
        input()
        sys.exit()

    print("Lethal Company found at " + LethalCompanyOutputFolder)

    # Get settings
    settings = yaml.load(open(Current_Path + "/settings.yaml", "r"), Loader=yaml.FullLoader)

    if input("Download latest settings.yaml? (y/n) [n]: ") == "y":
        print("Downloading settings.yaml")
        r = requests.get(settings["settings"]["remoteSettingsUrl"], allow_redirects=True)

        if r.status_code != 200:
            print("Error downloading settings.yaml")
            input()
            sys.exit()

        open(Current_Path + "/settings.yaml", 'wb').write(r.content)
        settings = yaml.load(open(Current_Path + "/settings.yaml", "r"), Loader=yaml.FullLoader)

    # Set variables
    modDownloadUrl = settings["settings"]["modDownloadUrl"]
    userAgent      = settings["settings"]["downloadUserAgent"]
    tempDir        = tempfile.gettempdir() + "/lcmods/"
    tempDirConf    = tempfile.gettempdir() + "/lcconf/"

    # Ensure directories exist
    makeCleanDirectory(tempDir)
    makeCleanDirectory(tempDirConf)
    makeCleanDirectory(LethalCompanyOutputFolder + "/BepInEx")
    makeCleanDirectory(LethalCompanyOutputFolder + "/BepInEx/plugins")
    makeDirectory(LethalCompanyOutputFolder + "/BepInEx/config")

    # Download and extract Custom Configs
    download(settings["settings"]["configZipUrl"], tempDirConf)
    copyTree(tempDirConf + "/config", LethalCompanyOutputFolder + "/BepInEx/config")

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        results = []
        for modName in settings["settings"]["mods"]:
            # vars
            modconfig    = settings["settings"]["mods"][modName]
            version      = modconfig["version"]
            downloadUrl  = modDownloadUrl + modName + "/" + version + "/"
            downloadPath = tempDir + modName.split("/")[1]

            # download and extract
            print("Downloading " + modName + " " + version)
            results.append(executor.submit(download, downloadUrl, downloadPath))

        concurrent.futures.wait(results)

    print("Downloaded all mods, copying files...")

    # Loop through all configured mods, download ZIP, extract, copy files
    for modName in settings["settings"]["mods"]:
        # vars
        modconfig    = settings["settings"]["mods"][modName]
        version      = modconfig["version"]
        downloadUrl  = modDownloadUrl + modName + "/" + version + "/"
        downloadPath = tempDir + modName.split("/")[1]

        # copy files
        for pmap in modconfig["pathmap"]:
            copyMap  = pmap.split(":")
            copyFrom = downloadPath + "/" + copyMap[0]
            copyTo   = LethalCompanyOutputFolder + "/" + copyMap[1]

            if not os.path.isdir(copyFrom):
                shutil.copy(copyFrom, copyTo)
            else:
                copyTree(copyFrom, copyTo)

    if os.path.exists(tempDir):
        shutil.rmtree(tempDir)

    if os.path.exists(tempDirConf):
        shutil.rmtree(tempDirConf)

    # Launch Lethal Company
    print("Launching Lethal Company...")
    os.startfile(LethalCompanyOutputFolder + "/Lethal Company.exe")

except Exception as e:
    print("Error!")
    print(e)
    input()
    sys.exit()

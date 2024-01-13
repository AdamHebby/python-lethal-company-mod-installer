import requests, zipfile, io, os, sys, shutil, tempfile, time, queue, yaml, concurrent.futures, hashlib, colorama

# Ensure program is running
if getattr(sys, 'frozen', False):
    Current_Path = os.path.dirname(sys.executable)
else:
    Current_Path = str(os.path.dirname(__file__))

# Define constants
TEMP_DIR        = tempfile.gettempdir() + "/lcmods/"
TEMP_DIR_CONF   = tempfile.gettempdir() + "/lcconf/"
TEMP_DIR_PROG   = tempfile.gettempdir() + "/lcprogress/"
REMOTE_SETTINGS = "https://lcmods.ge3kingit.net.nz/LCMods/settings.yaml"

def error(msg: str):
    print(colorama.Fore.RED + msg + colorama.Style.RESET_ALL)

def warning(msg: str):
    print(colorama.Fore.YELLOW + msg + colorama.Style.RESET_ALL)

def info(msg: str):
    print(colorama.Fore.CYAN + msg + colorama.Style.RESET_ALL)

def success(msg: str):
    print(colorama.Fore.GREEN + msg + colorama.Style.RESET_ALL)

# Make Directory
def makeDirectory(path: str):
    if not os.path.exists(path):
        os.mkdir(path)

# Empty and remake directory
def makeCleanDirectory(path: str, deleteIfExist: bool = True):
    if deleteIfExist and os.path.exists(path):
        shutil.rmtree(path)

    makeDirectory(path)

# Download and extract zip file
def downloadZip(downloadUrl: str, path: str):
    for i in range(10):
        try:
            r = requests.get(downloadUrl, headers={"User-Agent": userAgent})

            if r.status_code >= 400:
                raise Exception("Error downloading " + downloadUrl + " - " + str(r.status_code) + " " + r.reason)

            if len(r.content) == 0:
                raise Exception("Error downloading " + downloadUrl + " - No content")

            z = zipfile.ZipFile(io.BytesIO(r.content))

            if z.testzip() != None:
                raise Exception("Error extracting " + downloadUrl + " - Testzip Failure at " + z.testzip())

            z.extractall(path)

            if not os.path.exists(path) or not os.path.isdir(path) or len(os.listdir(path)) == 0:
                raise Exception("Error extracting " + downloadUrl + " to " + path + " - Folder is empty or does not exist")

            markProgress(md5(downloadUrl.encode()))

            break
        except Exception as e:
            error("Error downloading " + downloadUrl)
            error(e)
            info("Retrying in 5 seconds...")
            time.sleep(5)

# Copy directory tree, makes directories if they don't exist
def copyTree(fromPath: str, toPath: str):
    makeDirectory(toPath)

    for filename in os.listdir(fromPath):
        if os.path.isdir(fromPath + "/" + filename):
            copyTree(fromPath + "/" + filename, toPath + "/" + filename)
        else:
            shutil.copy(fromPath + "/" + filename, toPath)

def touchFile(path: str):
    open(path, 'a').close()

def md5(name: str):
    return hashlib.md5(name).hexdigest()

def markProgress(name: str):
    touchFile(TEMP_DIR_PROG + name)

def hasProgress(name: str):
    return os.path.exists(TEMP_DIR_PROG + name)

def delProgress(name: str):
    if os.path.exists(TEMP_DIR_PROG + name):
        os.remove(TEMP_DIR_PROG + name)

class ModDownload:
    def __init__(
            self: any,
            fullModName: str,
            modVersion: str,
            modDownloadUrl: str,
            modPathMap: list,
            forcePin: str = None
        ):
        self.author         = fullModName.split("/")[0]
        self.modName        = fullModName.split("/")[1]
        self.fullModName    = fullModName
        self.modVersion     = modVersion
        self.modDownloadUrl = modDownloadUrl
        self.modPathMap     = modPathMap
        self.forcePin       = forcePin

    #
    def fromSettings(settings: dict) -> list:
        mods = []

        modDownloadUrl = settings["settings"]["modDownloadUrl"]
        for modName in settings["settings"]["mods"]:
            # vars
            modconfig    = settings["settings"]["mods"][modName]
            version      = modconfig["version"]
            downloadUrl  = modDownloadUrl + modName + "/" + version + "/"

            mods.append(ModDownload(
                modName,
                version,
                downloadUrl,
                modconfig["pathmap"],
                modconfig["forcePin"] if "forcePin" in modconfig else None
            ))

        return mods

    def getDownloadUrl(self: any):
        return self.forcePin if self.forcePin != None else self.modDownloadUrl

    def getModVersion(self: any):
        return self.forcePin if self.forcePin != None else self.modVersion

    def __str__(self: any) -> str:
        return self.fullModName + " " + self.getModVersion()

    def hasDownloadFiles(self: any) -> bool:
        return (
            os.path.exists(TEMP_DIR + self.modName) and
            os.path.isdir(TEMP_DIR + self.modName) and
            len(os.listdir(TEMP_DIR + self.modName)) > 0
        )

    def isComplete(self: any) -> bool:
        return (
            hasProgress(md5(self.getDownloadUrl().encode())) and
            self.hasDownloadFiles()
        )

    def download(self: any) -> None:
        info("Downloading " + str(self))
        delProgress(md5(self.getDownloadUrl().encode()))

        downloadZip(self.getDownloadUrl(), TEMP_DIR + self.modName)

    def copy(self: any, LethalCompanyOutputFolder: str) -> None:
        for pmap in self.modPathMap:
            copyMap  = pmap.split(":")
            copyFrom = TEMP_DIR + self.modName + "/" + copyMap[0]
            copyTo   = LethalCompanyOutputFolder + "/" + copyMap[1]

            try:
                if copyTo.endswith("/"):
                    makeDirectory(copyTo)

                if not os.path.isdir(copyFrom):
                    shutil.copy(copyFrom, copyTo)
                else:
                    copyTree(copyFrom, copyTo)
            except Exception as e:
                raise Exception("Error copying " + self.modName + " - " + copyFrom + " to " + copyTo + " - " + str(e))

    def verifyThrow(self: any) -> None:
        if not self.verify(False):
            raise Exception("Error downloading " + self.modName + " - Incomplete")

    def verify(self: any) -> bool:
        if not self.isComplete():
            warning("Cannot verify " + self.fullModName + " - Incomplete")
            return False

        for pmap in self.modPathMap:
            copyMap  = pmap.split(":")
            copyFrom = TEMP_DIR + self.modName + "/" + copyMap[0]

            if not os.path.exists(copyFrom) or (os.path.isdir(copyFrom) and len(os.listdir(copyFrom)) == 0):
                warning("Cannot verify " + self.fullModName + " - Missing or empty " + copyFrom)
                return False

        return True

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
        error("Lethal Company install folder not found: " + LethalCompanyOutputFolder)
        input()
        sys.exit()

    success("Lethal Company found at " + LethalCompanyOutputFolder)

    # Get settings
    info("Downloading settings.yaml")
    r = requests.get(REMOTE_SETTINGS, allow_redirects=True)

    if r.status_code != 200:
        error("Error downloading settings.yaml")
        input()
        sys.exit()

    settings = yaml.load(r.content, Loader=yaml.FullLoader)
    # settings = yaml.load(open(os.path.join(Current_Path, "settings.yaml"), "r"), Loader=yaml.FullLoader)

    userAgent = settings["settings"]["downloadUserAgent"]

    makeDirectory(TEMP_DIR_PROG)
    shouldContinue = False

    if hasProgress("isDownloading") and os.path.isdir(TEMP_DIR) and len(os.listdir(TEMP_DIR)) > 0:
        shouldContinue = input("Detected stalled download, would you like to attempt to resume? (y/n)") == "y"

        # Ensure directories exist
        makeDirectory(TEMP_DIR)
        makeDirectory(TEMP_DIR_CONF)
    else:
        # Ensure directories exist, and are empty
        makeCleanDirectory(TEMP_DIR)
        makeCleanDirectory(TEMP_DIR_CONF)
        makeCleanDirectory(TEMP_DIR_PROG)

    # Download and extract Custom Configs
    downloadZip(settings["settings"]["configZipUrl"], TEMP_DIR_CONF)

    markProgress("isDownloading")

    mods = ModDownload.fromSettings(settings)

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        results = []
        for mod in mods:
            if shouldContinue and mod.isComplete():
                warning("Skipping previously downloaded " + mod.fullModName)
                continue

            # download and extract
            results.append(executor.submit(mod.download))

        concurrent.futures.wait(results)

    success("Downloaded all mods, checking files...")

    for mod in mods:
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
    copyTree(TEMP_DIR_CONF + "/config", LethalCompanyOutputFolder + "/BepInEx/config")

    # Loop through all configured mods, download ZIP, extract, copy files
    for mod in mods:
        info("Copying " + mod.fullModName)

        for i in range(3):
            try:
                if mod.isComplete():
                    mod.copy(LethalCompanyOutputFolder)
                    break
                else:
                    error("Incomplete download of " + mod.fullModName + ", retrying...")
                    mod.download()
                    mod.verifyThrow()

            except Exception as e:
                error("Error copying " + mod.fullModName + " - " + str(e))
                info("Retrying in 5 seconds...")
                time.sleep(5)

    success("All mods copied, cleaning up...")
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)

    if os.path.exists(TEMP_DIR_CONF):
        shutil.rmtree(TEMP_DIR_CONF)

    if os.path.exists(TEMP_DIR_PROG):
        shutil.rmtree(TEMP_DIR_PROG)

    # Launch Lethal Company
    success("Launching Lethal Company...")
    os.startfile("steam://launch/1966720")

except Exception as e:
    error("Error!")
    error(e)
    input()
    sys.exit()

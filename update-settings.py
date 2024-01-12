import requests, zipfile, io, os, sys, queue, yaml, re

if getattr(sys, 'frozen', False):
    Current_Path = os.path.dirname(sys.executable)
else:
    Current_Path = str(os.path.dirname(__file__))

try:
    # settings path is argv[1], ensure param is entered and file exists
    settingsPath = ""
    if len(sys.argv) == 2:
        settingsPath = sys.argv[1]
    elif not os.path.isfile(sys.argv[1]):
        settingsPath = os.path.join(Current_Path, "settings.yaml")

    if not os.path.isfile(settingsPath):
        print("settings.yaml not found")
        input()
        exit()

    settings = yaml.load(open(settingsPath, "r"), Loader=yaml.FullLoader)

    # load settings.yaml
    baseUrl   = settings["settings"]["modDownloadUrl"]
    pageUrl   = settings["settings"]["modPageUrl"]
    userAgent = settings["settings"]["downloadUserAgent"]

    for modName in settings["settings"]["mods"]:
        print("Checking " + modName)
        modconfig      = settings["settings"]["mods"][modName]
        page           = requests.get(pageUrl + modName, allow_redirects=True, headers={"User-Agent": userAgent})
        currentVersion = modconfig["version"]
        latestVersion  = re.search(r'' + re.escape(baseUrl + modName) + r'\/(.*?)\/"', page.content.decode("utf-8")).group(1)

        if currentVersion != latestVersion:
            print("Updating " + modName + " from " + currentVersion + " to " + latestVersion)
            currentVersion = latestVersion
            settings["settings"]["mods"][modName]["version"] = latestVersion

    # save settings.yaml
    with open(settingsPath, "w") as f:
        yaml.dump(settings, f)

    print("Done")

except Exception as e:
    print("Error!")
    print(e)
    input()
    exit()

import requests, zipfile, io, os, sys, queue, yaml, re

if getattr(sys, 'frozen', False):
    Current_Path = os.path.dirname(sys.executable)
else:
    Current_Path = str(os.path.dirname(__file__))

try:
    settings = yaml.load(open(Current_Path + "/settings.yaml", "r"), Loader=yaml.FullLoader)

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

    # save settings.yaml
    with open(Current_Path + "/settings.yaml", "w") as f:
        yaml.dump(settings, f)

    print("Done")

except Exception as e:
    print("Error!")
    print(e)
    input()
    exit()

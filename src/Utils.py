from __future__ import annotations
import os, shutil, colorama, requests, zipfile, io, time, subprocess, json
import sys
from src.SessionConstants import SessionConstants

def green(msg: str) -> str:
    return colorama.Fore.GREEN + msg + colorama.Style.RESET_ALL

def red(msg: str) -> str:
    return colorama.Fore.RED + msg + colorama.Style.RESET_ALL

def yellow(msg: str) -> str:
    return colorama.Fore.YELLOW + msg + colorama.Style.RESET_ALL

def cyan(msg: str) -> str:
    return colorama.Fore.CYAN + msg + colorama.Style.RESET_ALL

def debug(msg: str):
    if SessionConstants.LOG_LEVEL <= SessionConstants.LOG_LEVEL_DEBUG:
        print(msg)

def error(msg: str):
    if SessionConstants.LOG_LEVEL <= SessionConstants.LOG_LEVEL_ERROR:
        print(red(msg))

def warning(msg: str):
    if SessionConstants.LOG_LEVEL <= SessionConstants.LOG_LEVEL_WARNING:
        print(yellow(msg))

def info(msg: str):
    if SessionConstants.LOG_LEVEL <= SessionConstants.LOG_LEVEL_INFO:
        print(cyan(msg))

def success(msg: str):
    print(green(msg))

def findFile(path: str, filename: str) -> str | None:
    for root, dirs, files in os.walk(path):
        if filename in files:
            return os.path.join(root, filename)

    return None

# Make Directory
def makeDirectory(path: str):
    if not os.path.exists(path):
        os.mkdir(path)

# Empty and remake directory
def makeCleanDirectory(path: str, deleteIfExist: bool = True):
    if deleteIfExist and os.path.exists(path):
        shutil.rmtree(path)

    makeDirectory(path)

def getFlatFileList(path: str) -> list[str]:
    files = []
    for file in os.walk(path):
        for f in file[2]:
            files.append(os.path.join(file[0], f))

    return files

def confirm(msg: str, default: bool = True) -> bool:
    d = f'([Y]/n)' if default else f'(y/[N])'

    val = input(f'{msg} {d}: ').lower().strip()

    return default if val == "" else val.startswith("y")

def cleanTempFiles():
    if os.path.exists(SessionConstants.TEMP_TEST_DIR):
        shutil.rmtree(SessionConstants.TEMP_TEST_DIR)

    if os.path.exists(SessionConstants.TEMP_DIR):
        shutil.rmtree(SessionConstants.TEMP_DIR)

    if os.path.exists(SessionConstants.TEMP_DIR_CONF):
        shutil.rmtree(SessionConstants.TEMP_DIR_CONF)

    if os.path.exists(SessionConstants.TEMP_DIR_PROG):
        shutil.rmtree(SessionConstants.TEMP_DIR_PROG)

def getCurrentDir() -> str:
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)

    return str(os.path.dirname(__file__))

def copyTree(fromPath: str, toPath: str):
    makeDirectory(toPath)

    for filename in os.listdir(fromPath):
        if os.path.isdir(fromPath + "/" + filename):
            copyTree(fromPath + "/" + filename, toPath + "/" + filename)
        else:
            shutil.copy(fromPath + "/" + filename, toPath)

def downloadZip(downloadUrl: str, path: str):
    for i in range(10):
        try:
            r = requests.get(downloadUrl, headers={"User-Agent": SessionConstants.USER_AGENT})

            if r.status_code >= 400:
                raise Exception("Error downloading " + downloadUrl + " - " + str(r.status_code) + " " + r.reason)

            if len(r.content) == 0:
                raise Exception("Error downloading " + downloadUrl + " - No content")

            z = zipfile.ZipFile(io.BytesIO(r.content))

            zipError = z.testzip()
            if zipError != None:
                raise Exception("Error extracting " + downloadUrl + " - Testzip Failure at " + zipError)

            z.extractall(path)

            if not os.path.exists(path) or not os.path.isdir(path) or len(os.listdir(path)) == 0:
                raise Exception("Error extracting " + downloadUrl + " to " + path + " - Folder is empty or does not exist")

            break
        except Exception as e:
            error("Error downloading " + downloadUrl)
            error(str(e))
            info("Retrying in 5 seconds...")
            time.sleep(5)

def loadPotentiallyDodgyJson(path: str) -> dict | None:
    if getattr(sys, 'frozen', False):
        return json.load(open(path, "r"))

    try:
        result = subprocess.run(
            f"cat {path} | jq",
            shell=True,
            executable="/bin/bash",
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # Check for errors
        if result.returncode == 0:
            with open(path, 'w') as file:
                file.write(result.stdout)
        else:
            error("JSON Error: " + result.stderr)
            return None
    except Exception as e:
        pass

    return json.load(open(path, "r"))

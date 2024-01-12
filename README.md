# Python Lethal Company Mod Installer

Just a simple mod installer for Lethal Company written in Python.

Fully customizable, you can add your own mods to the installer.

EXE files can be built using PyInstaller. There is a bash script for doing this via docker.

It's probably easier for you to use Thunderstore - but if you don't want to use that, you can use this.

## Just here to download the mods?

Head to [the releases page](https://github.com/AdamHebby/python-lethal-company-mod-installer/releases) and download the latest release of `lethal-mod-installer.exe`.

## How to use - Server owner

### Update Settings
```bash
git clone git@github.com:AdamHebby/python-lethal-company-mod-installer.git
cd python-lethal-company-mod-installer
pip install -r requirements.txt
python3 update-settings.py
```

SCP / FTP this settings.yaml file to your server

### Setup / Change settings
The purpose of this is to store the EXE files on a server and give it to your friends so they can install the mods easily.

Edit `data/lethal-mod-installer-versionfile.yaml` and `data/update-settings-versionfile.yaml` to your liking.

Copy `settings.example.yaml` to `settings.yaml` and edit it to your liking.

Our Settings.yaml is currently hard-coded, change this in `lethal-mod-installer.py` if you want to change it.

The purpose of the `configZipUrl` setting is to point it to your remote `config.zip` file. This should contain any custom configs you want to add to the game.

Build the EXE files (use `./buildExe`) or craft your own. Copy this ZIP file to your server and separately upload the `settings.yaml` and make them downloadable.


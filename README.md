# Python Lethal Company Mod Installer

Just a simple mod installer for Lethal Company written in Python.

Fully customizable, you can add your own mods to the installer.

EXE files can be built using PyInstaller. There is a bash script for doing this via docker.

It's probably easier for you to use Thunderstore - but if you don't want to use that, you can use this.

## How to use
The purpose of this is to store the EXE files on a server and give it to your friends so they can install the mods easily.

Edit `data/lethal-mod-installer-versionfile.yaml` and `data/update-settings-versionfile.yaml` to your liking.

Copy `settings.example.yaml` to `settings.yaml` and edit it to your liking.

The purpose of the `remoteSettingsUrl` setting is to point it to your remote `settings.yaml` file, which will allow users to fetch this file from your server without having to manually download it again.

The purpose of the `configZipUrl` setting is to point it to your remote `config.zip` file. This should contain any custom configs you want to add to the game.

Build the EXE files (use ./buildExe) or craft your own. Copy this ZIP file to your server and separately upload the `settings.yaml` and make them downloadable.


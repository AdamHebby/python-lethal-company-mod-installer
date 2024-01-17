from __future__ import annotations

class Version:
    def __init__(self: Version, version: str):
        self.version = version
        self.major   = 0
        self.minor   = 0
        self.patch   = 0
        self.build   = 0

        self.parse()

    def parse(self: Version) -> None:
        version = self.version.split(".")

        if len(version) > 0:
            self.major = int(version[0])

        if len(version) > 1:
            self.minor = int(version[1])

        if len(version) > 2:
            self.patch = int(version[2])

        if len(version) > 3:
            self.build = int(version[3])

    def getFullVersion(self: Version) -> str:
        return str(self.major) + "." + str(self.minor) + "." + str(self.patch) + "." + str(self.build)

    def __str__(self: Version) -> str:
        return self.version

    def gt(self: Version, version) -> bool:
        if self.major > version.major:
            return True

        if self.major == version.major:
            if self.minor > version.minor:
                return True

            if self.minor == version.minor:
                if self.patch > version.patch:
                    return True

                if self.patch == version.patch:
                    if self.build > version.build:
                        return True

        return False

    @staticmethod
    def max(a: Version, b: Version) -> Version:
        return a if a.gt(b) else b

    def lt(self: Version, version) -> bool:
        if self.major < version.major:
            return True

        if self.major == version.major:
            if self.minor < version.minor:
                return True

            if self.minor == version.minor:
                if self.patch < version.patch:
                    return True

                if self.patch == version.patch:
                    if self.build < version.build:
                        return True

        return False

    def __eq__(self: Version, __value: object) -> bool:
        if not isinstance(__value, Version):
            return False

        return self.getFullVersion() == __value.getFullVersion()

    def __ne__(self: Version, __value: object) -> bool:
        return not self.__eq__(__value)

    def __gt__(self: Version, __value: object) -> bool:
        return self.gt(__value)

    def __lt__(self: Version, __value: object) -> bool:
        return self.lt(__value)

    def __ge__(self: Version, __value: object) -> bool:
        return self.gt(__value) or self.__eq__(__value)

    def __le__(self: Version, __value: object) -> bool:
        return self.lt(__value) or self.__eq__(__value)

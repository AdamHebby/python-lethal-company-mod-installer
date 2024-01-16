from __future__ import annotations
import sys

class RegistryKeyManager:
    @staticmethod
    def getValue(reg: str, key: str, value: str, default):
        try:
            if 'nt' in sys.builtin_module_names:
                import winreg
                aReg = winreg.ConnectRegistry(None, reg) # type: ignore
                aKey = winreg.OpenKey(aReg, key) # type: ignore
                return winreg.QueryValueEx(aKey, value)[0] # type: ignore
            else:
                return default

        except Exception:
            return default

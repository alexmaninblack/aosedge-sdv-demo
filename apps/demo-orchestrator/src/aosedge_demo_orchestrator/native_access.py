# SPDX-FileCopyrightText: 2026 maninblack
# SPDX-License-Identifier: MIT

"""Native first-SSH enrollment input. No secret in argv, browser or evidence."""

import ctypes
import subprocess
import sys
from .environment import EnvironmentError

SERVICE = b"io.aosedge.democtl.factory-ssh"
ACCOUNT = b"root"
DIALOG = '''activate
set reply to display dialog "Enter the factory VM root password. Used for first SSH setup of Test and Production." with title "Demo Control — VM access" default answer "" with hidden answer buttons {"Cancel", "Use once", "Save in Keychain"} default button "Use once" cancel button "Cancel" giving up after 180
if gave up of reply then error number -128
return (button returned of reply) & linefeed & (text returned of reply)
'''


class Keychain:
    def __init__(self):
        if sys.platform != "darwin":
            raise EnvironmentError("NATIVE_VM_ACCESS_REQUIRES_MACOS")
        self.api = ctypes.CDLL("/System/Library/Frameworks/Security.framework/Security")
        pointer, uint = ctypes.c_void_p, ctypes.c_uint32
        self.api.SecKeychainFindGenericPassword.argtypes = [pointer, uint, ctypes.c_char_p, uint, ctypes.c_char_p, ctypes.POINTER(uint), ctypes.POINTER(pointer), pointer]
        self.api.SecKeychainFindGenericPassword.restype = ctypes.c_int32
        self.api.SecKeychainAddGenericPassword.argtypes = [pointer, uint, ctypes.c_char_p, uint, ctypes.c_char_p, uint, pointer, pointer]
        self.api.SecKeychainAddGenericPassword.restype = ctypes.c_int32
        self.api.SecKeychainItemFreeContent.argtypes = [pointer, pointer]

    def read(self):
        size, data = ctypes.c_uint32(), ctypes.c_void_p()
        code = self.api.SecKeychainFindGenericPassword(None, len(SERVICE), SERVICE, len(ACCOUNT), ACCOUNT, ctypes.byref(size), ctypes.byref(data), None)
        if code == -25300:  # errSecItemNotFound
            return None
        if code:
            raise EnvironmentError("VM_KEYCHAIN_ACCESS_DENIED")
        try:
            if not 1 <= size.value <= 256:
                raise EnvironmentError("VM_KEYCHAIN_VALUE_INVALID")
            return ctypes.string_at(data, size.value).decode()
        finally:
            self.api.SecKeychainItemFreeContent(None, data)

    def save(self, value):
        raw = value.encode()
        buffer = ctypes.create_string_buffer(raw)
        try:
            code = self.api.SecKeychainAddGenericPassword(None, len(SERVICE), SERVICE, len(ACCOUNT), ACCOUNT, len(raw), buffer, None)
            if code:
                raise EnvironmentError("VM_KEYCHAIN_SAVE_FAILED")
        finally:
            ctypes.memset(buffer, 0, len(buffer))


class NativeVMAccess:
    def __init__(self, progress=None, keychain=None, runner=subprocess.run):
        self.progress = progress or (lambda message: None)
        self.keychain = keychain
        self.runner = runner
        self.value = None

    def __call__(self, role):
        if self.value is not None:
            return self.value
        keychain = self.keychain or Keychain()
        value = keychain.read()
        if value is None:
            self.progress("WAITING_FOR_ACCESS: enter the VM password in the macOS Demo Control dialog (Cancel stops preparation)")
            try:
                answer = self.runner(["/usr/bin/osascript", "-e", DIALOG], capture_output=True, text=True, timeout=185)
            except subprocess.TimeoutExpired:
                raise EnvironmentError("VM_ACCESS_DIALOG_TIMED_OUT") from None
            if answer.returncode:
                raise EnvironmentError("VM_ACCESS_CANCELLED_OR_DIALOG_UNAVAILABLE")
            decision, separator, value = answer.stdout.rstrip("\n").partition("\n")
            if not separator or decision not in ("Use once", "Save in Keychain") or not value or len(value.encode()) > 256 or any(c in value for c in "\r\n\x00"):
                raise EnvironmentError("VM_ACCESS_INPUT_INVALID")
            if decision == "Save in Keychain":
                keychain.save(value)
        self.value = value
        self.progress("VM access available; secret remains in the native process")
        return value

    def clear(self):
        self.value = None

import hashlib
import getpass
import os
import platform
from pathlib import Path

HASH_FILE = os.path.join(Path.home(), ".blacklist_hash")


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def set_password():
    if os.path.exists(HASH_FILE):
        print("[!] There is already a blacklist password set.")
        choice = input("[?] Would you like to change it? (y/n): ").lower()

        if choice != "y":
            print("[i] Password change cancelled.")
            return False

        print("[?] To set a new password, you must first verify the current one.")
        if not verify_password():
            # verify_password handles the "Incorrect password" message
            return False

    # Proceed to create the new password
    pwd = getpass.getpass("[>] Enter NEW blacklist password: ")
    confirm = getpass.getpass("[>] Confirm NEW password: ")

    if pwd != confirm:
        print("[-] Passwords do not match. Change aborted.")
        return False

    if not pwd:
        print("[-] Password cannot be empty.")
        return False

    try:
        with open(HASH_FILE, "w") as f:
            f.write(hash_password(pwd))

        # Set restrictive permissions on Unix/Mac
        if platform.system() != "Windows":
            os.chmod(HASH_FILE, 0o600)

        print("[+] Password updated successfully.")
        return True
    except Exception as e:
        print(f"[-] Failed to save password: {e}")
        return False


def remove_password():
    if not os.path.exists(HASH_FILE):
        print("[!] No password is currently set.")
        return

    print("[?] To remove protection, you must verify the current password.")
    if verify_password():
        try:
            os.remove(HASH_FILE)
            print("[+] Password protection removed. The tool is now unlocked.")
        except Exception as e:
            print(f"[-] Error removing password file: {e}")


def verify_password():
    if not os.path.exists(HASH_FILE):
        print("[!] Warning: No password set. Use --set-password to secure this tool.")
        return True

    trial = getpass.getpass("[>] Enter blacklist password: ")
    with open(HASH_FILE, "r") as f:
        stored_hash = f.read().strip()

    if hash_password(trial) == stored_hash:
        return True
    print("[-] Access Denied: Incorrect password.")
    return False

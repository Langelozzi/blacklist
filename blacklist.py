import platform
import argparse
import os
import shutil
import sys

from modules.password import remove_password, set_password, verify_password

DEFAULT_BLOCKLIST = "blocklist.txt"
DEFAULT_REDIRECT_IP = "127.0.0.1"  # Loopback

WINDOWS_HOST_FILE = r"C:\Windows\System32\drivers\etc\hosts"
UNIX_HOST_FILE = "/etc/hosts"


def is_running_as_root():
    # Windows check: try to open the hosts file in append mode
    if platform.system() == "Windows":
        try:
            with open(WINDOWS_HOST_FILE, "a"):
                pass
            return True
        except PermissionError:
            return False
    # Unix/Linux/Mac check
    return os.geteuid() == 0


def assert_root_user():
    if not is_running_as_root():
        raise PermissionError


def get_hosts_path():
    if platform.system() == "Windows":
        return WINDOWS_HOST_FILE
    else:
        return UNIX_HOST_FILE


def backup_hosts_file():
    hosts_path = get_hosts_path()
    backup_path = f"{hosts_path}.backup"

    if not os.path.exists(backup_path):
        try:
            shutil.copy2(hosts_path, backup_path)
            print(f"[+] Initial backup created at: {backup_path}")
        except Exception as e:
            print(f"[-] Failed to create backup: {e}")
    else:
        # We don't overwrite it because we want to keep the "original" clean state
        pass


def read_blocklist_set(filename):
    if not os.path.exists(filename):
        print(f"[-] Error: File '{filename}' not found.")
        return

    with open(filename, "r") as f:
        websites = {line.strip() for line in f if line.strip()}
        return websites


def get_processed_blocklist(blocklist_set):
    # Add www. version if it doesn't exist in the set yet
    processed_set = set()
    for site in blocklist_set:
        processed_set.add(site)

        has_www_already = site[:4] == "www."
        www_version = f"www.{site}"
        if not has_www_already and www_version not in blocklist_set:
            processed_set.add(www_version)

    return processed_set


def write_blocklist(hosts_path, blocklist, redirect_ip):
    with open(hosts_path, "r+") as file:
        content = file.read()
        print("[>] Blocking sites...")
        for website in blocklist:
            if website not in content:
                file.seek(0, 2)
                file.write(f"{redirect_ip} {website}\n")


def remove_blocklist(hosts_path, blocklist):
    print("[>] Removing blocked sites...")

    with open(hosts_path, "r") as file:
        lines = file.readlines()

    # Keep lines that aren't in our removal set
    new_content = [
        line for line in lines if not any(site in line for site in blocklist)
    ]

    with open(hosts_path, "w") as file:
        file.writelines(new_content)


def get_blocklist(blocklist_filename):
    try:
        blocklist_set = read_blocklist_set(blocklist_filename)
    except PermissionError:
        print("[-] Error: Could not read the blocklist file.")
        return

    return get_processed_blocklist(blocklist_set)


def block_sites(blocklist_filename, redirect_ip):
    hosts_path = get_hosts_path()
    blocklist = get_blocklist(blocklist_filename)
    backup_hosts_file()
    write_blocklist(hosts_path, blocklist, redirect_ip)
    print(f"[+] Successfully blocked sites from '{blocklist_filename}'")


def unblock_sites(blocklist_filename):
    hosts_path = get_hosts_path()
    blocklist = get_blocklist(blocklist_filename)
    backup_hosts_file()
    remove_blocklist(hosts_path, blocklist)
    print(f"[+] Successfully unblocked sites from '{blocklist_filename}'.")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Blacklist: A simple CLI to block/unblock websites via the hosts file."
    )

    # 'nargs="?"' makes it optional; 'default' provides the fallback
    parser.add_argument(
        "file",
        nargs="?",
        default=DEFAULT_BLOCKLIST,
        help=f"Path to the .txt file (default: {DEFAULT_BLOCKLIST})",
    )

    parser.add_argument(
        "-r",
        "--revert",
        action="store_true",
        help="Unblock the domains listed in the file",
    )

    parser.add_argument(
        "-i",
        "--ip-address",
        default=DEFAULT_REDIRECT_IP,
        help=f"The redirect IP address (default: {DEFAULT_REDIRECT_IP})",
    )

    parser.add_argument(
        "--set-password", action="store_true", help="Initialize/Change password"
    )

    parser.add_argument(
        "--remove-password", action="store_true", help="Remove the password completely"
    )

    return parser.parse_args()


def main():
    args = parse_args()

    if args.set_password:
        set_password()
        return

    if args.remove_password:
        remove_password()
        return

    try:
        assert_root_user()

        if not verify_password():
            return

        if args.revert:
            unblock_sites(args.file)
        else:
            block_sites(args.file, args.ip_address)
    except PermissionError:
        print("[-] Error: Insufficient permissions. Run as Admin/Sudo.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[i] Operation cancelled by user. Exiting...")
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)

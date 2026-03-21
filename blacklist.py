import platform
import argparse
import os

DEFAULT_BLOCKLIST = "blocklist.txt"
DEFAULT_REDIRECT_IP = "127.0.0.1"  # Loopback

WINDOWS_HOST_FILE = r"C:\Windows\System32\drivers\etc\hosts"
UNIX_HOST_FILE = "/etc/hosts"


def is_running_as_root():
    return os.geteuid() == 0


def assert_root_user():
    if not is_running_as_root():
        raise PermissionError


def get_hosts_path():
    if platform.system() == "Windows":
        return WINDOWS_HOST_FILE
    else:
        return UNIX_HOST_FILE


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
        print(" >  Blocking domains...")
        for website in blocklist:
            if website not in content:
                file.seek(0, 2)
                file.write(f"{redirect_ip} {website}\n")


def remove_blocklist(hosts_path, blocklist):
    print(" >  Removing blocked domains from hosts file...")

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
    write_blocklist(hosts_path, blocklist, redirect_ip)
    print(f"[+] Successfully blocked domains from '{blocklist_filename}'")


def unblock_sites(blocklist_filename):
    hosts_path = get_hosts_path()
    blocklist = get_blocklist(blocklist_filename)
    remove_blocklist(hosts_path, blocklist)
    print(
        f"[+] Successfully removed domains from '{blocklist_filename}' from the hosts file."
    )


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

    return parser.parse_args()


def main():
    args = parse_args()

    try:
        assert_root_user()
        if args.revert:
            unblock_sites(args.file)
        else:
            block_sites(args.file, args.ip_address)
    except PermissionError:
        print("[-] Error: Insufficient permissions. Run as Admin/Sudo.")


if __name__ == "__main__":
    main()

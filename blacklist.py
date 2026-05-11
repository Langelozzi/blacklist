import os
import sys
import platform
import subprocess
import argparse
import ctypes
from pathlib import Path

from modules.password import remove_password, set_password, verify_password

# Cloudflare for Families (Malware + Adult Content Filter)
IPV4_DNS = ["1.1.1.3", "1.0.0.3"]
IPV6_DNS = ["2606:4700:4700::1113", "2606:4700:4700::1003"]


def is_running_as_root():
    try:
        return (
            os.getuid() == 0
            if platform.system() != "Windows"
            else ctypes.windll.shell32.IsUserAnAdmin()
        )
    except AttributeError:
        return False


def assert_root_user():
    if not is_running_as_root():
        raise PermissionError


def get_all_interfaces():
    """Identifies all relevant hardware interfaces for the current OS."""
    system = platform.system()
    interfaces = []

    if system == "Windows":
        # Get all enabled interfaces that aren't loopback
        cmd = "netsh interface show interface"
        output = subprocess.check_output(cmd, shell=True).decode()
        for line in output.splitlines():
            if "Dedicated" in line:
                # Extracts interface name which starts at index 44 in netsh output
                name = line[44:].strip()
                interfaces.append(name)

    elif system == "Darwin":  # macOS
        cmd = "networksetup -listallnetworkservices"
        output = subprocess.check_output(cmd, shell=True).decode()
        # Filter out asterisks (disabled services) and empty lines
        interfaces = [
            line.strip()
            for line in output.splitlines()
            if line.strip() and "*" not in line and "Network Services" not in line
        ]

    elif system == "Linux":
        # For Linux, we return the active ones for nmcli to modify profiles,
        # but the global config change handles the rest.
        try:
            cmd = "nmcli -t -f NAME connection show"
            output = subprocess.check_output(cmd, shell=True).decode()
            interfaces = [line.strip() for line in output.splitlines() if line.strip()]
        except:
            pass

    return interfaces


def turn_on():
    system = platform.system()
    ifaces = get_all_interfaces()
    print("\n[+] Enabling content filter...\n")

    if system == "Windows":
        for iface in ifaces:
            print(f"  [i] Securing interface: {iface}")
            subprocess.run(
                f'netsh interface ipv4 set dns name="{iface}" source=static addr={IPV4_DNS[0]} primary',
                shell=True,
                capture_output=True
            )
            subprocess.run(
                f'netsh interface ipv4 add dns name="{iface}" addr={IPV4_DNS[1]} index=2',
                shell=True,
                capture_output=True
            )
            subprocess.run(
                f'netsh interface ipv6 set dns name="{iface}" source=static addr={IPV6_DNS[0]}',
                shell=True,
            )
            subprocess.run(
                f'netsh interface ipv6 add dns name="{iface}" addr={IPV6_DNS[1]} index=2',
                shell=True,
            )
        subprocess.run("ipconfig /flushdns", shell=True)

    elif system == "Darwin":
        dns_str = " ".join(IPV4_DNS + IPV6_DNS)
        for iface in ifaces:
            print(f"  [i] Securing interface: {iface}")
            subprocess.run(
                f'sudo networksetup -setdnsservers "{iface}" {dns_str}', shell=True
            )
        subprocess.run("sudo killall -HUP mDNSResponder", shell=True)

    elif system == "Linux":
        # 1. Update all existing connection profiles
        dns_v4 = ",".join(IPV4_DNS)
        dns_v6 = ",".join(IPV6_DNS)
        for iface in ifaces:
            subprocess.run(
                f'nmcli connection modify "{iface}" ipv4.dns "{dns_v4}" ipv4.ignore-auto-dns yes',
                shell=True,
            )
            subprocess.run(
                f'nmcli connection modify "{iface}" ipv6.dns "{dns_v6}" ipv6.ignore-auto-dns yes',
                shell=True,
            )

        # 2. Global override for NEW connections
        config_path = Path("/etc/NetworkManager/conf.d/dns-override.conf")
        content = "[main]\ndns=none\n"
        try:
            with open(config_path, "w") as f:
                f.write(content)
            subprocess.run("systemctl restart NetworkManager", shell=True)
        except Exception as e:
            print(f"[!] Could not write global config: {e}")

    print("\n[+] Content filter status: ON")


def turn_off():
    system = platform.system()
    ifaces = get_all_interfaces()
    print("\n[+] Disabling content filter...")

    if system == "Windows":
        for iface in ifaces:
            subprocess.run(
                f'netsh interface ipv4 set dns name="{iface}" source=dhcp', shell=True
            )
            subprocess.run(
                f'netsh interface ipv6 set dns name="{iface}" source=dhcp', shell=True
            )

    elif system == "Darwin":
        for iface in ifaces:
            subprocess.run(
                f'sudo networksetup -setdnsservers "{iface}" empty', shell=True
            )

    elif system == "Linux":
        # 1. Revert profiles
        for iface in ifaces:
            subprocess.run(
                f'nmcli connection modify "{iface}" ipv4.ignore-auto-dns no ipv6.ignore-auto-dns no',
                shell=True,
            )
            subprocess.run(
                f'nmcli connection modify "{iface}" ipv4.dns "" ipv6.dns ""', shell=True
            )

        # 2. Remove global override
        config_path = Path("/etc/NetworkManager/conf.d/dns-override.conf")
        if config_path.exists():
            config_path.unlink()
            subprocess.run("systemctl restart NetworkManager", shell=True)

    print("\n[+] Content filter status: OFF")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Blacklist: A simple CLI to block/unblock websites via the hosts file."
    )

    parser.add_argument(
        "state",
        nargs="?",
        choices=["on", "off"],
        default=None,
        help="Turn the blacklist 'on' (enable) or 'off' (disable/revert)",
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

    if args.state is None:
        print("[-] Error: Please specify a state ('on' or 'off') or a password command.")
        print("    Usage: blacklist {on,off} | --set-password | --remove-password")
        return

    try:
        assert_root_user()

        if not verify_password():
            return

        if args.state == "on":
            turn_on()
        elif args.state == "off":
            turn_off()

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

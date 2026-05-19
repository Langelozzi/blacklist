import os
import sys
import platform
import subprocess
import argparse
import ctypes
import socket
from pathlib import Path

from modules.password import remove_password, set_password, verify_password

# Cloudflare for Families (Malware + Adult Content Filter)
# -- This blocked all torrent sites and streaming sites too
# IPV4_DNS = ["1.1.1.3", "1.0.0.3"]
# IPV6_DNS = ["2606:4700:4700::1113", "2606:4700:4700::1003"]

# CleanBrowsing (Adult Filter - Allows Streaming + Blocks Malware)
IPV4_DNS = ["185.228.168.168", "185.228.169.168"]
IPV6_DNS = ["2a0d:5600:33:1::", "2a0d:5601:33:1::"]

# Hosts file for allowing select urls
WINDOWS_HOST_FILE = r"C:\Windows\System32\drivers\etc\hosts"
UNIX_HOST_FILE = "/etc/hosts"


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


def run_system_command(command, **kwargs):
    """
    Runs a command while ensuring PyInstaller's bundled libraries
    don't interfere with system utilities. Accepts any standard
    subprocess.run arguments.
    """
    env = os.environ.copy()
    # Remove PyInstaller's library path to use system-native libraries
    env.pop("LD_LIBRARY_PATH", None)

    # Ensure 'env' is included in the final call
    kwargs["env"] = env

    # Use the real subprocess module, not the function name itself
    return subprocess.run(command, **kwargs)


def update_tool():
    """Executes the remote install script based on the current OS."""
    system = platform.system()
    print(f"\n[+] Initiating update for {system}...")

    try:
        if system == "Windows":
            cmd = 'powershell -Command "irm https://raw.githubusercontent.com/Langelozzi/blacklist/main/install.ps1 | iex"'
            # Note: shell=True is important here for Windows to parse the command string correctly
            run_system_command(cmd, shell=True)

        elif system in ["Darwin", "Linux"]:
            cmd = "curl -fsSL https://raw.githubusercontent.com/Langelozzi/blacklist/main/install.sh | sudo bash"
            run_system_command(cmd, shell=True)

        print("\n[+] Update process completed.")
    except Exception as e:
        print(f"\n[-] Update failed: {e}")


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
            run_system_command(
                f'netsh interface ipv4 set dns name="{iface}" source=static addr={IPV4_DNS[0]} primary',
                shell=True,
                capture_output=True,
            )
            run_system_command(
                f'netsh interface ipv4 add dns name="{iface}" addr={IPV4_DNS[1]} index=2',
                shell=True,
                capture_output=True,
            )
            run_system_command(
                f'netsh interface ipv6 set dns name="{iface}" source=static addr={IPV6_DNS[0]}',
                shell=True,
            )
            run_system_command(
                f'netsh interface ipv6 add dns name="{iface}" addr={IPV6_DNS[1]} index=2',
                shell=True,
            )
        run_system_command("ipconfig /flushdns", shell=True)

    elif system == "Darwin":
        dns_str = " ".join(IPV4_DNS + IPV6_DNS)
        for iface in ifaces:
            print(f"  [i] Securing interface: {iface}")
            run_system_command(
                f'sudo networksetup -setdnsservers "{iface}" {dns_str}', shell=True
            )
        run_system_command("sudo killall -HUP mDNSResponder", shell=True)

    elif system == "Linux":
        # 1. Update all existing connection profiles
        dns_v4 = ",".join(IPV4_DNS)
        dns_v6 = ",".join(IPV6_DNS)
        for iface in ifaces:
            run_system_command(
                f'nmcli connection modify "{iface}" ipv4.dns "{dns_v4}" ipv4.ignore-auto-dns yes',
                shell=True,
            )
            run_system_command(
                f'nmcli connection modify "{iface}" ipv6.dns "{dns_v6}" ipv6.ignore-auto-dns yes',
                shell=True,
            )

        # 2. Global override for NEW connections
        config_path = Path("/etc/NetworkManager/conf.d/dns-override.conf")
        content = "[main]\ndns=none\n"
        try:
            with open(config_path, "w") as f:
                f.write(content)
            run_system_command("systemctl restart NetworkManager", shell=True)
        except Exception as e:
            print(f"[!] Could not write global config: {e}")

    print("\n[+] Content filter status: ON")


def turn_off():
    system = platform.system()
    ifaces = get_all_interfaces()
    print("\n[+] Disabling content filter...")

    if system == "Windows":
        for iface in ifaces:
            run_system_command(
                f'netsh interface ipv4 set dns name="{iface}" source=dhcp', shell=True
            )
            run_system_command(
                f'netsh interface ipv6 set dns name="{iface}" source=dhcp', shell=True
            )

    elif system == "Darwin":
        for iface in ifaces:
            run_system_command(
                f'sudo networksetup -setdnsservers "{iface}" empty', shell=True
            )

    elif system == "Linux":
        # 1. Revert profiles
        for iface in ifaces:
            run_system_command(
                f'nmcli connection modify "{iface}" ipv4.ignore-auto-dns no ipv6.ignore-auto-dns no',
                shell=True,
            )
            run_system_command(
                f'nmcli connection modify "{iface}" ipv4.dns "" ipv6.dns ""', shell=True
            )

        # 2. Remove global override
        config_path = Path("/etc/NetworkManager/conf.d/dns-override.conf")
        if config_path.exists():
            config_path.unlink()
            run_system_command("systemctl restart NetworkManager", shell=True)

    print("\n[+] Content filter status: OFF")


def allow_domains(targets):
    """
    Temporarily disables the filter, resolves the specified domains (and their www variants),
    maps them in the hosts file, and re-enables the filter.
    """
    if not targets:
        print("[-] Error: Please specify at least one domain or a file path.")
        return

    domains_to_resolve = set()

    # 1. Parse targets (distinguish between files and raw domains)
    for target in targets:
        path = Path(target)
        if path.is_file():
            try:
                with open(path, "r") as f:
                    for line in f:
                        cleaned = line.strip()
                        if cleaned and not cleaned.startswith("#"):
                            domains_to_resolve.add(cleaned)
            except Exception as e:
                print(f"[-] Failed to read file {target}: {e}")
        else:
            domains_to_resolve.add(target.strip())

    # 2. Automatically inject 'www.' variants if missing
    final_domains = set()
    for domain in domains_to_resolve:
        final_domains.add(domain)
        if not domain.startswith("www.") and len(domain.split(".")) == 2:
            final_domains.add(f"www.{domain}")

    if not final_domains:
        print("[-] No valid domains found to process.")
        return

    # 3. Drop filter temporarily to communicate with clear DNS upstream
    print("[+] Dropping filter temporarily to accurately resolve mappings...")
    turn_off()

    resolved_mappings = {}
    print("[+] Resolving domain IPs...")
    for domain in final_domains:
        try:
            # gethostbyname_ex returns (hostname, aliaslist, ipaddrlist)
            _, _, ip_list = socket.gethostbyname_ex(domain)
            if ip_list:
                resolved_mappings[domain] = ip_list
                print(f"  [i] {domain} -> {', '.join(ip_list)}")
        except socket.gaierror:
            print(
                f"  [!] Failed to resolve: {domain} (Check domain syntax or connection)"
            )

    # Re-enable the filter immediately after resolving
    turn_on()

    if not resolved_mappings:
        print("[-] No domains were successfully resolved. Hosts file left untouched.")
        return

    # 4. Safely update the host configuration file
    hosts_path = WINDOWS_HOST_FILE if platform.system() == "Windows" else UNIX_HOST_FILE

    try:
        # Read current hosts to prevent block corruption or duplicates
        existing_lines = []
        if Path(hosts_path).exists():
            with open(hosts_path, "r") as f:
                existing_lines = f.readlines()

        # Clean existing entries matching our current additions to avoid clutter
        cleaned_lines = [
            line
            for line in existing_lines
            if not any(f" {domain}" in line for domain in resolved_mappings)
        ]

        # Append new resolved blocks
        with open(hosts_path, "w") as f:
            f.writelines(cleaned_lines)
            f.write("\n# --- Blacklist Custom Allow List Start ---\n")
            for domain, ips in resolved_mappings.items():
                for ip in ips:
                    f.write(f"{ip:<16} {domain} # Blacklist-Allow\n")
            f.write("# --- Blacklist Custom Allow List End ---\n")

        print(f"\n[+] Successfully injected entries into {hosts_path}")

        # Flush the system DNS cache to apply rules immediately
        if platform.system() == "Windows":
            run_system_command("ipconfig /flushdns", shell=True)
        elif platform.system() == "Darwin":
            run_system_command("sudo killall -HUP mDNSResponder", shell=True)

    except PermissionError:
        print(
            f"[-] Permission denied writing to {hosts_path}. Ensure the script is run with sudo/Administrator privileges."
        )
    except Exception as e:
        print(f"[-] Failed modifications: {e}")


def disallow_domains(targets):
    """
    Removes specific domains (and their www variants) from the hosts file override.
    If no targets are passed, it clears out ALL custom overrides.
    """
    hosts_path = WINDOWS_HOST_FILE if platform.system() == "Windows" else UNIX_HOST_FILE

    if not Path(hosts_path).exists():
        print("[-] Hosts file not found.")
        return

    domains_to_remove = set()

    # 1. Parse targets if provided
    for target in targets:
        path = Path(target)
        if path.is_file():
            try:
                with open(path, "r") as f:
                    for line in f:
                        cleaned = line.strip()
                        if cleaned and not cleaned.startswith("#"):
                            domains_to_remove.add(cleaned)
            except Exception as e:
                print(f"[-] Failed to read file {target}: {e}")
        else:
            domains_to_remove.add(target.strip())

    # 2. Re-create the matching www. variants to ensure complete cleanup
    final_removal_set = set()
    for domain in domains_to_remove:
        final_removal_set.add(domain)
        if not domain.startswith("www.") and len(domain.split(".")) == 2:
            final_removal_set.add(f"www.{domain}")

    try:
        with open(hosts_path, "r") as f:
            lines = f.readlines()

        cleaned_lines = []
        removed_count = 0

        # 3. Filter out lines
        for line in lines:
            # If the user specified explicit domains to target
            if final_removal_set:
                if "# Blacklist-Allow" in line and any(
                    f" {dom}" in line for dom in final_removal_set
                ):
                    removed_count += 1
                    continue  # Skip this line (removes it)
            else:
                # Nuke EVERYTHING added by this tool if they just run `blacklist disallow`
                if (
                    "# Blacklist-Allow" in line
                    or "--- Blacklist Custom Allow List" in line
                ):
                    removed_count += 1
                    continue

            cleaned_lines += [line]

        # 4. Clean up dangling header/footer blocks if the list is completely empty now
        if not any("# Blacklist-Allow" in line for line in cleaned_lines):
            cleaned_lines = [
                line
                for line in cleaned_lines
                if "--- Blacklist Custom Allow List" not in line
            ]

        # 5. Write changes back
        with open(hosts_path, "w") as f:
            f.writelines(cleaned_lines)

        if final_removal_set:
            print(f"[+] Removed {removed_count} mapping entries for specified domains.")
        else:
            print("[+] Flushed all custom domain allocations from the hosts file.")

        # Flush cache so it applies instantly
        if platform.system() == "Windows":
            run_system_command("ipconfig /flushdns", shell=True)
        elif platform.system() == "Darwin":
            run_system_command("sudo killall -HUP mDNSResponder", shell=True)

    except PermissionError:
        print(
            f"[-] Permission denied writing to {hosts_path}. Run with sudo/Administrator privileges."
        )
    except Exception as e:
        print(f"[-] Modification failed: {e}")


def parse_args(parser):
    parser.add_argument(
        "cmd",
        nargs="?",
        choices=["on", "off", "allow", "disallow"],
        default=None,
        help="Turn the blacklist 'on', 'off', or 'allow', 'disallow' explicit domains",
    )

    # Collects 0 or more domain names or file paths following the command
    parser.add_argument(
        "targets",
        nargs="*",
        default=[],
        help="List of domains or path to a file containing domains to allow or disallow",
    )

    parser.add_argument(
        "--set-password", action="store_true", help="Initialize/Change password"
    )

    parser.add_argument(
        "--remove-password", action="store_true", help="Remove the password completely"
    )

    parser.add_argument(
        "--update", action="store_true", help="Update the tool to the latest version"
    )

    return parser.parse_args()


def main():
    parser = argparse.ArgumentParser(
        description="Blacklist: A CLI tool that allows enabling and disabling adult content filters with a single command."
    )
    args = parse_args(parser)

    if args.set_password:
        set_password()
        return

    if args.remove_password:
        remove_password()
        return

    if args.update:
        update_tool()
        return

    if args.cmd is None:
        parser.print_help()
        return

    try:
        # Enforce administrative access for active mutations
        assert_root_user()

        # Don't need password to turn on
        if args.cmd == "on":
            turn_on()
            return

        if not verify_password():
            return

        if args.cmd == "off":
            turn_off()
        elif args.cmd == "allow":
            allow_domains(args.targets)
        elif args.cmd == "disallow":
            disallow_domains(args.targets)

    except PermissionError:
        print("[-] Error: Insufficient permissions. Run as Admin/Sudo.")
        parser.print_help()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[i] Operation cancelled by user. Exiting...")
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)

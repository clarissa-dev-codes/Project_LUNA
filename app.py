import os
import sys
import platform  # Detects if we are running on Windows or Linux
import subprocess

# MULTI-PLATFORM ENVIRONMENTAL HANDLING
CURRENT_OS = platform.system().lower()  # Returns 'windows' or 'linux'

if CURRENT_OS == 'linux':
    # Clean out leaked Snap paths if launching from a sandboxed tool on Ubuntu
    keys_to_purge = ['LD_PRELOAD', 'GTK_PATH', 'LD_LIBRARY_PATH', 'BASH_FUNC_which%%']
    for key in keys_to_purge:
        os.environ.pop(key, None)
    os.environ['GDK_BACKEND'] = 'x11'

import time
import psutil
import webview
import threading

class LunaAPI:
    def send_to_terminal(self, text):
        print(f"[UI Log]: {text}")
        return "Acknowledged, sir."

    def save_scratchpad(self, content):
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            with open(os.path.join(current_dir, 'scratchpad.txt'), 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception:
            return False

    def load_scratchpad(self):
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            file_path = os.path.join(current_dir, 'scratchpad.txt')
            return open(file_path, 'r', encoding='utf-8').read() if os.path.exists(file_path) else ""
        except Exception:
            return ""

    # ─────────────────────────────────────────────────────────
    # UNIVERSAL CROSS-PLATFORM ACTION MATRIX
    # ─────────────────────────────────────────────────────────
    def execute_ui_command(self, raw_command):
        cmd = raw_command.lower().strip()
        print(f"[OS: {CURRENT_OS.upper()}] Routing action -> {cmd}")

        try:
            # 1. App Launcher Routing
            if "open browser" in cmd or "launch web" in cmd:
                if CURRENT_OS == "windows":
                    # Native Windows command to open default browser
                    os.system("start https://google.com")
                else:
                    # Native Linux command to open default browser
                    subprocess.Popen(["xdg-open", "https://google.com"])
                return {"status": "success", "msg": "Default browser matrix active."}
                
            elif "open code" in cmd or "launch vscode" in cmd:
                if CURRENT_OS == "windows":
                    # Launches VS Code on Windows via shell path
                    subprocess.Popen(["cmd", "/c", "code"], shell=True)
                else:
                    subprocess.Popen(["code"])
                return {"status": "success", "msg": "VS Code workspace opened."}

            # 2. Hardware Control Routing (Universal Linux Audio Update)
            elif "volume up" in cmd:
                if CURRENT_OS == "windows":
                    import ctypes
                    ctypes.windll.user32.keybd_event(0xAF, 0, 0, 0)
                else:
                    # 1. Safely boost the background audio track by 10%
                    subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", "+10%"])
                    # 2. ✨ Pushes a beautiful native floating notification bubble onto your desktop
                    # Arguments: "App Name", "Main Message Text", "--icon=sound-indicator"
                    subprocess.run(["notify-send", "L.U.N.A. Core", "Volume Increased [ +10% ]", "--icon=audio-volume-high", "-h", "string:x-canonical-private-synchronous:volume"])
                return {"status": "success", "msg": "Master speaker matrix boosted."}
                
            elif "volume down" in cmd:
                if CURRENT_OS == "windows":
                    import ctypes
                    ctypes.windll.user32.keybd_event(0xAE, 0, 0, 0)
                else:
                    # 1. Safely attenuate the background audio track by 10%
                    subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", "-10%"])
                    # 2. ✨ Pushes the native floating notification bubble onto your desktop
                    subprocess.run(["notify-send", "L.U.N.A. Core", "Volume Decreased [ -10% ]", "--icon=audio-volume-low", "-h", "string:x-canonical-private-synchronous:volume"])
                return {"status": "success", "msg": "Master speaker matrix attenuated."}

                
            elif "lock system" in cmd or "lock screen" in cmd:
                if CURRENT_OS == "windows":
                    # Native Windows lock function
                    import ctypes
                    ctypes.windll.user32.LockWorkStation()
                else:
                    subprocess.run(["xdg-screensaver", "lock"])
                return {"status": "success", "msg": "Security protocols active. Workstation locked."}

            return {"status": "unknown", "msg": f"Command vector '{raw_command}' not recognized."}

        except Exception as e:
            return {"status": "error", "msg": f"Universal execution failure: {str(e)}"}

def track_hardware_metrics(window):
    time.sleep(2) 
    while True:
        try:
            current_url = window.get_current_url()
            if not current_url or "about:blank" in current_url:
                time.sleep(0.5)
                continue

            cpu = psutil.cpu_percent(interval=None)
            ram = psutil.virtual_memory().percent
            battery_info = psutil.sensors_battery()
            battery = int(battery_info.percent) if battery_info else "100"

            js_code = f"updateHardwareMetrics({cpu}, {ram}, '{battery}');"
            window.evaluate_js(js_code)
        except Exception as e:
            print(f"Metrics tracking error: {e}")
        time.sleep(1)

def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    gui_dir = os.path.join(current_dir, 'gui', 'index.html')
    api = LunaAPI()
    
    window = webview.create_window(
        title="L.U.N.A. Dashboard", 
        url=gui_dir,
        js_api=api,
        width=1200,
        height=800,
        resizable=True,
        background_color='#1d2030'
    )
    
    webview.start(
        func=lambda w: threading.Thread(target=track_hardware_metrics, args=(w,), daemon=True).start(), 
        args=(window,), 
        debug=False
    )

if __name__ == '__main__':
    main()

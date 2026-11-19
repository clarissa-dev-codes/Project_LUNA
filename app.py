import os
import sys
import platform  # Detects if we are running on Windows or Linux
import subprocess
import json #to save everything so that it doesn't go in a temp folder and disappear

# MULTI-PLATFORM ENVIRONMENTAL HANDLING
CURRENT_OS = platform.system().lower()  # Returns 'windows' or 'linux'

if CURRENT_OS == 'linux':
    # Clean out leaked Snap paths if launching from a sandboxed tool on Ubuntu
    keys_to_purge = ['LD_PRELOAD', 'GTK_PATH', 'LD_LIBRARY_PATH', 'BASH_FUNC_which%%']
    os.environ['WEBKIT_DISABLE_COMPOSITING_MODE'] = '1' #prevents webkit from losing GPU surface context for Ubuntu
    for key in keys_to_purge:
        os.environ.pop(key, None)
    os.environ['GDK_BACKEND'] = 'x11'

import time
import psutil
import webview
import threading

# ♥─────────────────────────────────────────────♥
#   Pyintaller resource and save path helpers
# ♥─────────────────────────────────────────────♥
def get_resource_path(relative_path):
    """Finds bundled assets (like the gui folder) inside PyInstaller."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)

def get_app_dir():
    """Finds the permanent folder where the app lives so scratchpad.txt persists."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


class LunaAPI:
    #to save the config.json permantely
    def __init__(self):
        self.config_path = os.path.join(get_app_dir(), 'config.json')
        self.intitialize_default_config()

    def initialize_default_config(self):
        #make if not there (default)
        if not os.path.exists(self.config_path):
            default_config = {
                "user_preferences": {
                    "title": "Ma'am",
                    "theme": "slate-lavender"
                },
                "custom_apps": {
                    "open github": {
                        "windows": "start https://github.com",
                        "linux": "xdg-open https://github.com",
                        "darwin": "open https://github.com"
                    }
                },
                "ai_configuration": {
                    "active_provider": "none",
                    "providers": {
                        "ollama": {
                            "host_url": "http://localhost:11434",
                            "model_name": "llama3.2:3b"
                        },
                        "open_claw": {
                            "endpoint_url": "http://localhost:8000/v1"
                        },
                        "cloud_api": {
                            "api_key": "",
                            "model_name": ""
                        }
                    }
                }
            }
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=4)

    #reads and returns what's in the config file
    def get_config(self):
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading config.json: {e}")
            return {}
        
    #writes the updated stuff to the json file
    def save_config(self, data):
        try: 
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
            return True
        except Exception as e:
                print(f"Error saving config.json: {e}")
                return False

    def send_to_terminal(self, text):
        print(f"[UI Log]: {text}")
        return "Acknowledged, ma'am."

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
    #  UNIVERSAL CROSS-PLATFORM ACTION MATRIX
    # ─────────────────────────────────────────────────────────
    def execute_ui_command(self, raw_command):
        cmd = raw_command.lower().strip()
        config = self.get_config()
        user_title = config.get("user_preferences", {}).get("title", "Ma'am")

        print(f"[OS: {CURRENT_OS.upper()}] Routing action -> {cmd}")

        try:
            if cmd.startswith("call me "):
                new_title = raw_command[8:].strip()
                if not new_title:
                    return {"status": "error", "msg": f"Please specify a name or title, {user_title}."}
                config["user_preferences"]["title"] = new_title
                self.save_config(config)
                return {"status": "success", "msg": f"Preferences updated. I will address you as {new_title} from now on."}
            elif cmd.startswith("set brain "):
                provider = cmd[10:].strip()
                valid_providers = config.get("ai_configuration", {}).get("providers", {}).keys()
                if provider not in valid_providers and provider != "none":
                    return {"status": "error", "msg": f"Unknown provider '{provider}'. Available: {', '.join(valid_providers)}, or none."}
                config["ai_configuration"]["active_provider"] = provider
                self.save_config(config)
                return {"status": "success", "msg": f"AI provider switched to '{provider}', {user_title}."}

            custom_apps = config.get("custom_apps", {})
            if cmd in custom_apps:
                os_cmd = custom_apps[cmd].get(CURRENT_OS)
                if os_cmd:
                    subprocess.Popen(os_cmd, shell=True)
                    return {"status": "success", "msg": f"Executing custom shortcut '{cmd}', {user_title}."}
                return {"status": "error", "msg": f"No command mapped for {CURRENT_OS} under '{cmd}'."}

            if "open browser" in cmd or "launch web" in cmd:
                if CURRENT_OS == "windows":
                    os.system("start https://google.com")
                elif CURRENT_OS == "darwin":  # macOS
                    subprocess.Popen(["open", "https://google.com"])
                else:  # Linux
                    subprocess.Popen(["xdg-open", "https://google.com"])
                return {"status": "success", "msg": "Default browser matrix active."}
                
            elif "open code" in cmd or "launch vscode" in cmd:
                if CURRENT_OS == "windows":
                    subprocess.Popen(["cmd", "/c", "code"], shell=True)
                elif CURRENT_OS == "darwin":  # macOS
                    # Launches VS Code safely by its macOS application bundle registration name
                    subprocess.Popen(["open", "-a", "Visual Studio Code"])
                else:  # Linux
                    subprocess.Popen(["code"])
                return {"status": "success", "msg": "VS Code workspace opened."}

            # ── 2. HARDWARE CONTROL SUBSYSTEM (Audio Management) ──
            elif "volume up" in cmd:
                if CURRENT_OS == "windows":
                    import ctypes
                    ctypes.windll.user32.keybd_event(0xAF, 0, 0, 0)
                elif CURRENT_OS == "darwin":  # macOS
                    # Uses AppleScript to natively boost output metrics smoothly by ~6% increments
                    subprocess.run(["osascript", "-e", "set volume output volume ((output volume of (get volume settings)) + 6)"])
                else:  # Linux
                    subprocess.run(["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", "10%+"])
                    subprocess.run(["notify-send", "L.U.N.A. Core", "Volume Increased [ +10% ]", "--icon=audio-volume-high", "-h", "string:x-canonical-private-synchronous:volume"])
                return {"status": "success", "msg": "Master speaker matrix boosted."}
                
            elif "volume down" in cmd:
                if CURRENT_OS == "windows":
                    import ctypes
                    ctypes.windll.user32.keybd_event(0xAE, 0, 0, 0)
                elif CURRENT_OS == "darwin":  # macOS
                    subprocess.run(["osascript", "-e", "set volume output volume ((output volume of (get volume settings)) - 6)"])
                else:  # Linux
                    subprocess.run(["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", "10%-"])
                    subprocess.run(["notify-send", "L.U.N.A. Core", "Volume Decreased [ -10% ]", "--icon=audio-volume-low", "-h", "string:x-canonical-private-synchronous:volume"])
                return {"status": "success", "msg": "Master speaker matrix attenuated."}

            elif "unmute volume" in cmd or "unmute" in cmd:
                if CURRENT_OS == "windows":
                    import ctypes
                    ctypes.windll.user32.keybd_event(0xAD, 0, 0, 0)
                    ctypes.windll.user32.keybd_event(0xAD, 0, 0x0002, 0)
                elif CURRENT_OS == "darwin":  # macOS
                    # Deactivates the system output mute configuration layer
                    subprocess.run(["osascript", "-e", "set volume without output muted"])
                else:  # Linux
                    subprocess.run(["wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "toggle"])
                    subprocess.run(["notify-send", "L.U.N.A. Core", "Audio Output Active", "--icon=audio-volume-high", "-h", "string:x-canonical-private-synchronous:volume"])
                return {"status": "success", "msg": "Master speaker unmuted."}   

            elif "mute volume" in cmd or "mute" in cmd:
                if CURRENT_OS == "windows":
                    import ctypes
                    ctypes.windll.user32.keybd_event(0xAD, 0, 0, 0)
                    ctypes.windll.user32.keybd_event(0xAD, 0, 0x0002, 0)
                elif CURRENT_OS == "darwin":  # macOS
                    # Forces the internal core audio mixer configuration output to true mute
                    subprocess.run(["osascript", "-e", "set volume with output muted"])
                else:  # Linux
                    subprocess.run(["wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "1"])
                    subprocess.run(["notify-send", "L.U.N.A. Core", "Audio Output Muted", "--icon=audio-volume-muted", "-h", "string:x-canonical-private-synchronous:volume"])
                return {"status": "success", "msg": "Master speaker muted."}         
                
            # ── 3. WORKSTATION SECURITY SUBSYSTEM ──
            elif "lock system" in cmd or "lock screen" in cmd:
                if CURRENT_OS == "windows":
                    import ctypes
                    ctypes.windll.user32.LockWorkStation()
                elif CURRENT_OS == "darwin":  # macOS
                    # Triggers the official macOS login window framework process to slide into view instantly
                    subprocess.run(["open", "-a", "ScreenSaverEngine"])
                else:  # Linux
                    subprocess.run(["xdg-screensaver", "lock"])
                return {"status": "success", "msg": "Security protocols active. Workstation locked."}

            # ── 4. DIRECTORY AUTOMATION SUBSYSTEM ──

            active_brain = config.get("ai_configuration", {}).get("active_provider", "none")
            if active_brain != "none":
                return {"status": "success", "msg": f"[{active_brain.upper()} Adapter]: Brain routing ready for '{raw_command}', {user_title}."}
            return {"status": "unknown", "msg": f"Command '{raw_command}' not recognized, {user_title}."}

        except Exception as e:
            return {"status": "error", "msg": f"Universal execution failure: {str(e)}"}

def track_hardware_metrics(window):
    time.sleep(2) 
    while True:
        try:
            #makes sure the window still exists before it sends anything
            if not window or window not in webview.windows:
                break

            current_url = window.get_current_url()
            if not current_url or "about:blank" in current_url:
                time.sleep(0.5)
                continue

            cpu = psutil.cpu_percent(interval=None)
            ram = psutil.virtual_memory().percent
            battery_info = psutil.sensors_battery()
            battery = int(battery_info.percent) if battery_info else "100"

            js_code = f"if(window.updateHardwareMetrics) {{ window.updateHardwareMetrics({cpu}, {ram}, '{battery}'); }}"
            window.evaluate_js(js_code)

        except Exception as e:
            #should pause longer if the screen is locked or webkit is temp. suspended
            time.sleep(5)
            print(f"Metrics tracking error: {e}")


        time.sleep(2) #changed to 2s to prevent GTK thread queue congestion during idle

def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    gui_dir = get_resource_path(os.path.join('gui', 'index.html'))
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

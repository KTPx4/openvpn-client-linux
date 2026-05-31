import subprocess
import re
import os
import webbrowser
import json
import time
from PyQt6.QtCore import QObject, pyqtSignal, QThread

class VPNMonitorThread(QThread):
    status_updated = pyqtSignal(str, str) # profile, status (Connected, Disconnected, Reconnecting, Authenticating)
    log_updated = pyqtSignal(str)
    auth_url_found = pyqtSignal(str)
    unexpected_disconnect = pyqtSignal(str)
    stats_updated = pyqtSignal(dict)

    def __init__(self, profile_name, config_arg, engine, attach_only=False):
        super().__init__()
        self.profile_name = profile_name
        self.config_arg = config_arg
        self.engine = engine
        self._is_running = True
        self.attach_only = attach_only

    def run(self):
        try:
            if not self.attach_only:
                self.status_updated.emit(self.profile_name, "Connecting...")
                
                # Khởi động VPN bằng openvpn3
                process = subprocess.Popen(
                    ["openvpn3", "session-start"] + self.config_arg,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1
                )

                # Đọc output để bắt link Auth SSO
                for line in process.stdout:
                    if not self._is_running:
                        process.terminate()
                        break
                    self.log_updated.emit(line.strip())
                    if "URL:" in line or "http" in line:
                        match = re.search(r'(https?://[^\s]+)', line)
                        if match:
                            self.auth_url_found.emit(match.group(1))

                process.wait()
            else:
                # Bỏ qua bước start, báo connected luôn nếu attach
                pass

            # Sau khi process exit hoặc nếu attach_only, session có thể đang chạy
            was_connected = self.attach_only
            while self._is_running:
                # Kiểm tra danh sách session đang chạy
                list_result = subprocess.run(["openvpn3", "sessions-list"], capture_output=True, text=True)
                
                # Nếu profile name còn trong danh sách session
                if self.profile_name in list_result.stdout:
                    if "Client connected" in list_result.stdout or "Connection established" in list_result.stdout:
                        if not was_connected:
                            self.status_updated.emit(self.profile_name, "Connected")
                            was_connected = True
                            
                        # Lấy số liệu thống kê (stats)
                        try:
                            # Cần parse đúng dbus path nếu dùng config-path
                            stat_cmd = ["openvpn3", "session-stats", "--config", self.profile_name, "--json"]
                            stat_result = subprocess.run(stat_cmd, capture_output=True, text=True)
                            
                            # Cắt bỏ phần text rác trước dấu { nếu có
                            stdout = stat_result.stdout
                            json_start = stdout.find('{')
                            if json_start != -1:
                                stats_data = json.loads(stdout[json_start:])
                                self.stats_updated.emit(stats_data)
                        except Exception as e:
                            self.log_updated.emit(f"Stats Error: {e}")
                            
                    elif "awaiting external authentication" in list_result.stdout or "Connection, User authentication" in list_result.stdout:
                        self.status_updated.emit(self.profile_name, "Authenticating...")
                else:
                    # Không tìm thấy session nào của profile này -> VPN đã ngắt
                    break
                    
                time.sleep(1)

        except Exception as e:
            self.log_updated.emit(f"Thread Error: {e}")

        if self._is_running:
            self.status_updated.emit(self.profile_name, "Disconnected (Unexpected)")
            self.unexpected_disconnect.emit(self.profile_name)
        else:
            self.status_updated.emit(self.profile_name, "Disconnected")

    def stop(self):
        self._is_running = False

class VPNEngine(QObject):
    configs_updated = pyqtSignal(list)
    auth_url_requested = pyqtSignal(str)
    vpn_status_changed = pyqtSignal(str, str) # profile, status
    log_message = pyqtSignal(str)
    notify_user = pyqtSignal(str, str) # title, message
    stats_updated = pyqtSignal(dict)

    def __init__(self, config_manager):
        super().__init__()
        self.config = config_manager
        self.active_monitor = None
        self.is_disconnecting_manually = False
        self.profile_map = {}

    def list_configs(self):
        try:
            result = subprocess.run(["openvpn3", "configs-list", "--json"], capture_output=True, text=True)
            self.profile_map = {}
            
            stdout = result.stdout
            json_start = stdout.find('{')
            if json_start != -1:
                json_str = stdout[json_start:]
                try:
                    data = json.loads(json_str)
                    for path, info in data.items():
                        name = info.get("name", "Unknown")
                        current_tstamp = self.profile_map.get(name, {}).get("imported_tstamp", 0)
                        if info.get("imported_tstamp", 0) >= current_tstamp:
                            self.profile_map[name] = {"path": path, "imported_tstamp": info.get("imported_tstamp", 0)}
                except json.JSONDecodeError as e:
                    self.log_message.emit(f"Failed to parse JSON configs: {e}")
            
            configs = list(self.profile_map.keys())
            
            if not configs and "openvpn3: command not found" in result.stderr:
                configs = ["mock-profile-1.ovpn", "mock-profile-2.ovpn"]
                self.log_message.emit("openvpn3 not found, using mock data")
                
            self.configs_updated.emit(configs)
            return configs
        except FileNotFoundError:
            self.log_message.emit("openvpn3 is not installed or not in PATH.")
            self.configs_updated.emit(["mock-profile-1.ovpn"])
            return ["mock-profile-1.ovpn"]

    def sync_sessions(self):
        try:
            result = subprocess.run(["openvpn3", "sessions-list"], capture_output=True, text=True)
            for profile_name in self.profile_map.keys():
                if profile_name in result.stdout:
                    if "Client connected" in result.stdout or "Connection established" in result.stdout:
                        if not self.active_monitor:
                            self.active_monitor = VPNMonitorThread(profile_name, [], self, attach_only=True)
                            self.active_monitor.status_updated.connect(self._on_status_updated)
                            self.active_monitor.log_updated.connect(self.log_message.emit)
                            self.active_monitor.auth_url_found.connect(self._on_auth_url_found)
                            self.active_monitor.stats_updated.connect(self.stats_updated.emit)
                            self.active_monitor.unexpected_disconnect.connect(self.handle_unexpected_disconnect)
                            self.active_monitor.start()
                            self.vpn_status_changed.emit(profile_name, "Connected")
                        break
        except Exception as e:
            self.log_message.emit(f"Sync error: {e}")

    def import_config(self, file_path):
        try:
            result = subprocess.run(["openvpn3", "config-import", "--config", file_path], capture_output=True, text=True)
            self.log_message.emit(result.stdout)
            if result.stderr:
                self.log_message.emit(f"Error: {result.stderr}")
            self.list_configs()
        except Exception as e:
            self.log_message.emit(f"Import failed: {e}")

    def connect(self, profile_name):
        self.is_disconnecting_manually = False
        if self.active_monitor:
            self.disconnect()

        path_info = self.profile_map.get(profile_name)
        if path_info:
            config_arg = ["--config-path", path_info["path"]]
        else:
            config_arg = ["--config", profile_name]

        self.active_monitor = VPNMonitorThread(profile_name, config_arg, self)
        self.active_monitor.status_updated.connect(self._on_status_updated)
        self.active_monitor.log_updated.connect(self.log_message.emit)
        self.active_monitor.auth_url_found.connect(self._on_auth_url_found)
        self.active_monitor.stats_updated.connect(self.stats_updated.emit)
        self.active_monitor.unexpected_disconnect.connect(self.handle_unexpected_disconnect)
        self.active_monitor.start()

    def disconnect(self):
        self.is_disconnecting_manually = True
        if self.active_monitor:
            profile = self.active_monitor.profile_name
            self.active_monitor.stop()
            self.active_monitor.wait()
            self.active_monitor = None
            
            disconnect_cmd = ["openvpn3", "session-manage", "--config", profile, "--disconnect"]
            try:
                subprocess.run(disconnect_cmd, capture_output=True)
            except Exception:
                pass
            
            self.vpn_status_changed.emit(profile, "Disconnected")

    def delete_config(self, profile_name):
        path_info = self.profile_map.get(profile_name)
        if path_info:
            try:
                subprocess.run(["openvpn3", "config-manage", "--path", path_info["path"], "--delete", "--force"], capture_output=True)
                self.list_configs()
            except Exception as e:
                self.log_message.emit(f"Failed to delete config: {e}")

    def _on_status_updated(self, profile, status):
        self.vpn_status_changed.emit(profile, status)
        
    def _on_auth_url_found(self, url):
        self.log_message.emit(f"Auth required. Opening: {url}")
        browser_choice = self.config.get('browser', 'system')
        try:
            if browser_choice == 'system':
                webbrowser.open(url)
            else:
                webbrowser.get(browser_choice).open(url)
        except Exception as e:
            self.log_message.emit(f"Failed to open browser: {e}. Opening with system default.")
            webbrowser.open(url)

    def handle_unexpected_disconnect(self, profile):
        if self.is_disconnecting_manually:
            return
            
        if self.config.get('notify_disconnect', True):
            self.notify_user.emit("VPN Disconnected", f"Connection to {profile} was lost.")
            
        if self.config.get('auto_reconnect', True):
            self.log_message.emit(f"Auto-reconnecting to {profile}...")
            self.connect(profile)

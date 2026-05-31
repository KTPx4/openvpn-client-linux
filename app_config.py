import json
import os
from pathlib import Path

class AppConfig:
    def __init__(self):
        self.config_dir = Path.home() / '.config' / 'OpenVPNClient'
        self.config_file = self.config_dir / 'settings.json'
        self.settings = {
            'browser': 'system', # system, google-chrome, firefox, brave-browser, edge
            'auto_reconnect': True,
            'notify_disconnect': True,
            'last_profile': None,
            'favorites': [],
            'custom_names': {}
        }
        self.load()

    def load(self):
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.settings.update(data)
            except Exception as e:
                print(f"Error loading config: {e}")

    def save(self):
        self.config_dir.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

    def get(self, key, default=None):
        return self.settings.get(key, default)

    def set(self, key, value):
        self.settings[key] = value
        self.save()

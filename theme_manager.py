import json
import os
from pathlib import Path
import shutil

DEFAULT_THEMES = [
    {
        "id": "pink_dark",
        "name": "Pink Dark",
        "is_builtin": True,
        "colors": {
            "bg_main": "#110b11",
            "bg_card": "#261720",
            "bg_card_hover": "#331f2b",
            "text_main": "#fdf2f8",
            "text_dim": "#9ca3af",
            "accent1": "#d63384",
            "accent2": "#f472b6",
            "accent_hover1": "#be185d",
            "accent_hover2": "#ec4899",
            "border": "#3d2434",
            "success": "#4ade80",
            "warning": "#fbbf24",
            "danger": "#ff4b4b",
            "input_bg": "#0b0709",
            "fav_active": "#f59e0b",
            "fav_inactive": "#a894a0",
            "scrollbar_bg": "#110b11",
            "scrollbar_handle": "#3d2434"
        }
    },
    {
        "id": "sky_blue_light",
        "name": "Sky Blue Light",
        "is_builtin": True,
        "colors": {
            "bg_main": "#f0f8ff",
            "bg_card": "#ffffff",
            "bg_card_hover": "#e6f2ff",
            "text_main": "#1e293b",
            "text_dim": "#64748b",
            "accent1": "#0ea5e9",
            "accent2": "#38bdf8",
            "accent_hover1": "#0284c7",
            "accent_hover2": "#0ea5e9",
            "border": "#cbd5e1",
            "success": "#22c55e",
            "warning": "#eab308",
            "danger": "#ef4444",
            "input_bg": "#ffffff",
            "fav_active": "#eab308",
            "fav_inactive": "#94a3b8",
            "scrollbar_bg": "#f0f8ff",
            "scrollbar_handle": "#cbd5e1"
        }
    },
    {
        "id": "blue_light",
        "name": "Blue Light",
        "is_builtin": True,
        "colors": {
            "bg_main": "#f8fafc",
            "bg_card": "#ffffff",
            "bg_card_hover": "#f1f5f9",
            "text_main": "#0f172a",
            "text_dim": "#64748b",
            "accent1": "#2563eb",
            "accent2": "#3b82f6",
            "accent_hover1": "#1d4ed8",
            "accent_hover2": "#2563eb",
            "border": "#e2e8f0",
            "success": "#16a34a",
            "warning": "#d97706",
            "danger": "#dc2626",
            "input_bg": "#ffffff",
            "fav_active": "#d97706",
            "fav_inactive": "#94a3b8",
            "scrollbar_bg": "#f8fafc",
            "scrollbar_handle": "#e2e8f0"
        }
    },
    {
        "id": "cyan_dark",
        "name": "Cyan Dark",
        "is_builtin": True,
        "colors": {
            "bg_main": "#0f172a",
            "bg_card": "#1e293b",
            "bg_card_hover": "#334155",
            "text_main": "#f8fafc",
            "text_dim": "#94a3b8",
            "accent1": "#06b6d4",
            "accent2": "#22d3ee",
            "accent_hover1": "#0891b2",
            "accent_hover2": "#06b6d4",
            "border": "#334155",
            "success": "#10b981",
            "warning": "#f59e0b",
            "danger": "#ef4444",
            "input_bg": "#020617",
            "fav_active": "#f59e0b",
            "fav_inactive": "#64748b",
            "scrollbar_bg": "#0f172a",
            "scrollbar_handle": "#334155"
        }
    }
]

class ThemeManager:
    def __init__(self, config_manager):
        self.config = config_manager
        self.themes_dir = Path.home() / '.config' / 'OpenVPNClient' / 'themes'
        self.themes_dir.mkdir(parents=True, exist_ok=True)
        self.themes = {}
        self.load_themes()

    def load_themes(self):
        self.themes = {}
        # Load built-in
        for t in DEFAULT_THEMES:
            self.themes[t["id"]] = t
            
        # Load custom themes
        for file_path in self.themes_dir.glob('*.json'):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if "id" in data and "colors" in data:
                        data["is_builtin"] = False
                        self.themes[data["id"]] = data
            except Exception:
                pass

    def get_all_themes(self):
        return list(self.themes.values())

    def get_current_theme(self):
        current_id = self.config.get('theme', 'pink_dark')
        return self.themes.get(current_id, self.themes['pink_dark'])

    def set_theme(self, theme_id):
        if theme_id in self.themes:
            self.config.set('theme', theme_id)

    def import_theme(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if "id" not in data or "name" not in data or "colors" not in data:
                return False, "Invalid theme format"
            
            if data["id"] in [t["id"] for t in DEFAULT_THEMES]:
                return False, "Cannot overwrite built-in theme"
                
            data["is_builtin"] = False
            dest = self.themes_dir / f"{data['id']}.json"
            
            with open(dest, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
                
            self.load_themes()
            return True, "Theme imported successfully"
        except Exception as e:
            return False, str(e)

    def export_theme(self, theme_id, dest_path):
        if theme_id not in self.themes:
            return False, "Theme not found"
        try:
            with open(dest_path, 'w', encoding='utf-8') as f:
                # Remove is_builtin flag before exporting
                export_data = self.themes[theme_id].copy()
                export_data.pop("is_builtin", None)
                json.dump(export_data, f, indent=4)
            return True, "Theme exported successfully"
        except Exception as e:
            return False, str(e)

    def delete_theme(self, theme_id):
        if theme_id not in self.themes:
            return False, "Theme not found"
        if self.themes[theme_id].get("is_builtin"):
            return False, "Cannot delete built-in theme"
            
        file_path = self.themes_dir / f"{theme_id}.json"
        try:
            if file_path.exists():
                file_path.unlink()
            self.load_themes()
            
            # Revert to default if current theme deleted
            if self.config.get('theme') == theme_id:
                self.set_theme('pink_dark')
                
            return True, "Theme deleted"
        except Exception as e:
            return False, str(e)

import sys
import subprocess
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QComboBox, 
                             QFileDialog, QStackedWidget, QCheckBox, QTextEdit,
                             QFormLayout, QDialog, QScrollArea, QFrame, QInputDialog, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal

class SettingsDialog(QDialog):
    def __init__(self, config_manager, theme_manager, parent=None):
        super().__init__(parent)
        self.config = config_manager
        self.theme_manager = theme_manager
        self.setWindowTitle("Advanced Settings")
        self.setFixedSize(400, 250)
        
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        
        self.browser_combo = QComboBox()
        self.browser_combo.addItems(['system', 'google-chrome', 'firefox', 'brave-browser', 'edge'])
        self.browser_combo.setCurrentText(self.config.get('browser', 'system'))
        
        self.auto_reconnect_cb = QCheckBox("Auto-reconnect on unexpected disconnect")
        self.auto_reconnect_cb.setChecked(self.config.get('auto_reconnect', True))
        
        self.notify_cb = QCheckBox("Notify when VPN disconnected")
        self.notify_cb.setChecked(self.config.get('notify_disconnect', True))
        
        form_layout.addRow("Browser for Auth:", self.browser_combo)
        form_layout.addRow(self.auto_reconnect_cb)
        form_layout.addRow(self.notify_cb)
        
        layout.addLayout(form_layout)
        
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_settings)
        
        c = self.theme_manager.get_current_theme()["colors"]
        save_btn.setStyleSheet(f"background-color: {c['accent1']}; color: white; padding: 8px; border-radius: 4px; font-weight: bold;")
        layout.addWidget(save_btn)

    def save_settings(self):
        self.config.set('browser', self.browser_combo.currentText())
        self.config.set('auto_reconnect', self.auto_reconnect_cb.isChecked())
        self.config.set('notify_disconnect', self.notify_cb.isChecked())
        self.accept()

class ConfigItemWidget(QFrame):
    clicked = pyqtSignal(str)
    delete_requested = pyqtSignal(str)
    favorite_toggled = pyqtSignal(str, bool)
    rename_requested = pyqtSignal(str)

    def __init__(self, profile_name, colors, custom_name=None, is_favorite=False, status="Disconnected"):
        super().__init__()
        self.profile_name = profile_name
        self.custom_name = custom_name
        self.is_favorite = is_favorite
        self.status = status
        self.c = colors
        
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(f"""
            ConfigItemWidget {{
                background-color: {self.c['bg_card']};
                border-radius: 10px;
                border: 1px solid {self.c['border']};
            }}
            ConfigItemWidget:hover {{
                background-color: {self.c['bg_card_hover']};
                border: 1px solid {self.c['accent1']};
            }}
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 12, 10, 12)
        
        # Name and Status
        text_layout = QVBoxLayout()
        display_name = self.custom_name if self.custom_name else self.profile_name.split('/')[-1]
        name_label = QLabel(display_name)
        name_label.setStyleSheet(f"font-weight: bold; font-size: 14px; color: {self.c['text_main']}; border: none; background: transparent;")
        
        self.status_label = QLabel(self.status)
        self.update_status_color()
        
        text_layout.addWidget(name_label)
        text_layout.addWidget(self.status_label)
        
        # Buttons
        self.edit_btn = QPushButton("✎")
        self.edit_btn.setFixedSize(30, 30)
        self.edit_btn.setStyleSheet(f"""
            QPushButton {{ background: transparent; color: {self.c['text_dim']}; border: none; font-size: 16px; }}
            QPushButton:hover {{ color: {self.c['text_main']}; }}
        """)
        self.edit_btn.clicked.connect(lambda: self.rename_requested.emit(self.profile_name))

        self.fav_btn = QPushButton("★" if self.is_favorite else "☆")
        self.fav_btn.setFixedSize(30, 30)
        self.fav_btn.clicked.connect(self.toggle_favorite)
        self.update_fav_btn_style()
        
        self.del_btn = QPushButton("🗑")
        self.del_btn.setFixedSize(30, 30)
        self.del_btn.setStyleSheet(f"""
            QPushButton {{ background: transparent; color: {self.c['text_dim']}; border: none; font-size: 16px; }}
            QPushButton:hover {{ color: {self.c['danger']}; }}
        """)
        self.del_btn.clicked.connect(lambda: self.delete_requested.emit(self.profile_name))
        
        layout.addLayout(text_layout)
        layout.addStretch()
        layout.addWidget(self.edit_btn)
        layout.addWidget(self.fav_btn)
        layout.addWidget(self.del_btn)

    def update_status_color(self):
        if self.status == "Connected":
            self.status_label.setStyleSheet(f"color: {self.c['success']}; font-size: 12px; border: none; background: transparent;")
        elif "Authenticating" in self.status or "Connecting" in self.status:
            self.status_label.setStyleSheet(f"color: {self.c['warning']}; font-size: 12px; border: none; background: transparent;")
        else:
            self.status_label.setStyleSheet(f"color: {self.c['text_dim']}; font-size: 12px; border: none; background: transparent;")

    def set_status(self, status):
        self.status = status
        self.status_label.setText(status)
        self.update_status_color()

    def toggle_favorite(self):
        self.is_favorite = not self.is_favorite
        self.fav_btn.setText("★" if self.is_favorite else "☆")
        self.update_fav_btn_style()
        self.favorite_toggled.emit(self.profile_name, self.is_favorite)

    def update_fav_btn_style(self):
        color = self.c['fav_active'] if self.is_favorite else self.c['fav_inactive']
        self.fav_btn.setStyleSheet(f"""
            QPushButton {{ background: transparent; color: {color}; border: none; font-size: 18px; }}
            QPushButton:hover {{ color: {self.c['fav_active']}; }}
        """)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.profile_name)

class ThemeItemWidget(QFrame):
    select_requested = pyqtSignal(str)
    export_requested = pyqtSignal(str)
    delete_requested = pyqtSignal(str)

    def __init__(self, theme_data, current_theme_id):
        super().__init__()
        self.t = theme_data
        self.is_active = (theme_data["id"] == current_theme_id)
        self.c = theme_data["colors"]
        
        self.setStyleSheet(f"""
            ThemeItemWidget {{
                background-color: {self.c['bg_card']};
                border-radius: 10px;
                border: 2px solid {'#ffffff' if self.is_active else self.c['border']};
            }}
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 15, 10, 15)
        
        name_label = QLabel(self.t["name"] + (" (Active)" if self.is_active else ""))
        name_label.setStyleSheet(f"font-weight: bold; font-size: 14px; color: {self.c['text_main']}; border: none; background: transparent;")
        
        # Color preview
        preview_layout = QHBoxLayout()
        preview_layout.setSpacing(2)
        for color_key in ['bg_main', 'bg_card', 'accent1', 'success']:
            swatch = QFrame()
            swatch.setFixedSize(16, 16)
            swatch.setStyleSheet(f"background-color: {self.c[color_key]}; border-radius: 8px;")
            preview_layout.addWidget(swatch)
            
        text_layout = QVBoxLayout()
        text_layout.addWidget(name_label)
        text_layout.addLayout(preview_layout)
        
        self.select_btn = QPushButton("Apply")
        self.select_btn.setStyleSheet(f"background: {self.c['accent1']}; color: white; padding: 6px 12px; border-radius: 4px; font-weight: bold; border: none;")
        self.select_btn.clicked.connect(lambda: self.select_requested.emit(self.t["id"]))
        
        self.export_btn = QPushButton("Export")
        self.export_btn.setStyleSheet(f"background: transparent; color: {self.c['text_main']}; border: 1px solid {self.c['border']}; border-radius: 4px; padding: 6px;")
        self.export_btn.clicked.connect(lambda: self.export_requested.emit(self.t["id"]))
        
        layout.addLayout(text_layout)
        layout.addStretch()
        layout.addWidget(self.select_btn)
        layout.addWidget(self.export_btn)
        
        if not self.t.get("is_builtin"):
            self.del_btn = QPushButton("🗑")
            self.del_btn.setStyleSheet(f"background: transparent; color: {self.c['danger']}; border: 1px solid {self.c['border']}; border-radius: 4px; padding: 6px;")
            self.del_btn.clicked.connect(lambda: self.delete_requested.emit(self.t["id"]))
            layout.addWidget(self.del_btn)

class MainWindow(QMainWindow):
    def __init__(self, config_manager, engine, theme_manager):
        super().__init__()
        self.config = config_manager
        self.engine = engine
        self.theme_manager = theme_manager
        
        self.current_profile = None
        self.last_bytes_in = 0
        self.last_bytes_out = 0
        
        self.init_ui()
        self.connect_signals()
        
        self.apply_theme()
        
        # Load configs and sync sessions
        self.engine.list_configs()
        self.engine.sync_sessions()

    def init_ui(self):
        app_version = os.environ.get("APP_VERSION", "v0.0.1")
        self.setWindowTitle(f"OpenVPN Client {app_version}")
        self.setFixedSize(420, 680)
        
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        # --- Page 0: List View ---
        list_page = QWidget()
        list_layout = QVBoxLayout(list_page)
        list_layout.setContentsMargins(20, 20, 20, 20)
        list_layout.setSpacing(15)
        
        header_layout = QHBoxLayout()
        self.title_label = QLabel("Profiles")
        self.title_label.setObjectName("TitleLabel")
        
        self.theme_btn = QPushButton("🎨")
        self.theme_btn.setObjectName("ThemeBtn")
        self.theme_btn.setFixedSize(36, 36)
        self.theme_btn.clicked.connect(self.go_to_themes)
        
        self.settings_btn = QPushButton("⚙")
        self.settings_btn.setObjectName("SettingsBtn")
        self.settings_btn.setFixedSize(36, 36)
        self.settings_btn.clicked.connect(self.open_settings)
        
        header_layout.addWidget(self.title_label, 1)
        header_layout.addWidget(self.theme_btn)
        header_layout.addWidget(self.settings_btn)
        
        self.add_btn = QPushButton("+ Import Profile")
        self.add_btn.setObjectName("AddBtn")
        self.add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_btn.clicked.connect(self.import_profile)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        self.configs_container = QWidget()
        self.configs_container.setStyleSheet("background: transparent;")
        self.configs_layout = QVBoxLayout(self.configs_container)
        self.configs_layout.setContentsMargins(0, 0, 0, 0)
        self.configs_layout.setSpacing(10)
        self.configs_layout.addStretch()
        self.scroll_area.setWidget(self.configs_container)
        
        list_layout.addLayout(header_layout)
        list_layout.addWidget(self.add_btn)
        list_layout.addWidget(self.scroll_area)
        
        # --- Footer ---
        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(5, 5, 5, 0)
        self.version_label = QLabel(app_version)
        self.version_label.setObjectName("FooterLabel")
        self.author_label = QLabel("Made with ♥ by Px4")
        self.author_label.setObjectName("FooterLabel")
        self.author_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        footer_layout.addWidget(self.version_label)
        footer_layout.addStretch()
        footer_layout.addWidget(self.author_label)
        list_layout.addLayout(footer_layout)
        
        # --- Page 1: Detail View ---
        detail_page = QWidget()
        detail_layout = QVBoxLayout(detail_page)
        detail_layout.setContentsMargins(20, 20, 20, 20)
        detail_layout.setSpacing(20)
        
        det_header_layout = QHBoxLayout()
        self.back_btn = QPushButton("← Back")
        self.back_btn.setObjectName("BackBtn")
        self.back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.back_btn.clicked.connect(self.go_back_to_list)
        det_header_layout.addWidget(self.back_btn)
        det_header_layout.addStretch()
        
        self.lbl_detail_name = QLabel("Profile Name")
        self.lbl_detail_name.setObjectName("DetailName")
        self.lbl_detail_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        path_layout = QHBoxLayout()
        self.lbl_detail_path = QLabel("/path/to/profile")
        self.lbl_detail_path.setObjectName("DetailPath")
        self.lbl_detail_path.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.btn_open_folder = QPushButton("📂 Open Folder")
        self.btn_open_folder.setObjectName("FolderBtn")
        self.btn_open_folder.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_open_folder.clicked.connect(self.open_profile_folder)
        
        path_layout.addStretch()
        path_layout.addWidget(self.lbl_detail_path)
        path_layout.addWidget(self.btn_open_folder)
        path_layout.addStretch()
        
        self.lbl_detail_status = QLabel("Connecting...")
        self.lbl_detail_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.toggle_btn = QPushButton("Disconnect")
        self.toggle_btn.setObjectName("ToggleBtn")
        self.toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_btn.clicked.connect(self.toggle_current_connection)
        
        self.stats_card = QFrame()
        self.stats_card.setObjectName("StatsCard")
        stats_layout = QVBoxLayout(self.stats_card)
        stats_layout.setContentsMargins(20, 20, 20, 20)
        stats_layout.setSpacing(15)
        
        self.title_stats = QLabel("Connection Statistics")
        self.title_stats.setObjectName("StatsTitle")
        stats_layout.addWidget(self.title_stats)
        
        speed_layout = QHBoxLayout()
        dl_layout = QVBoxLayout()
        self.lbl_speed_in = QLabel("0.0 KB/s")
        self.lbl_speed_in.setObjectName("SpeedIn")
        dl_layout.addWidget(QLabel("↓ Download"))
        dl_layout.addWidget(self.lbl_speed_in)
        
        ul_layout = QVBoxLayout()
        self.lbl_speed_out = QLabel("0.0 KB/s")
        self.lbl_speed_out.setObjectName("SpeedOut")
        ul_layout.addWidget(QLabel("↑ Upload"))
        ul_layout.addWidget(self.lbl_speed_out)
        
        speed_layout.addLayout(dl_layout)
        speed_layout.addLayout(ul_layout)
        stats_layout.addLayout(speed_layout)
        
        total_layout = QHBoxLayout()
        self.lbl_total_in = QLabel("0.00 MB")
        self.lbl_total_out = QLabel("0.00 MB")
        self.lbl_total_in.setObjectName("TotalTxt")
        self.lbl_total_out.setObjectName("TotalTxt")
        
        t_dl_layout = QVBoxLayout()
        t_dl_layout.addWidget(QLabel("Total DL:"))
        t_dl_layout.addWidget(self.lbl_total_in)
        
        t_ul_layout = QVBoxLayout()
        t_ul_layout.addWidget(QLabel("Total UL:"))
        t_ul_layout.addWidget(self.lbl_total_out)
        
        total_layout.addLayout(t_dl_layout)
        total_layout.addLayout(t_ul_layout)
        stats_layout.addLayout(total_layout)
        
        self.log_box = QTextEdit()
        self.log_box.setObjectName("LogBox")
        self.log_box.setReadOnly(True)
        
        detail_layout.addLayout(det_header_layout)
        detail_layout.addWidget(self.lbl_detail_name)
        detail_layout.addLayout(path_layout)
        detail_layout.addWidget(self.lbl_detail_status)
        detail_layout.addWidget(self.toggle_btn)
        detail_layout.addWidget(self.stats_card)
        detail_layout.addWidget(QLabel("Logs:"))
        detail_layout.addWidget(self.log_box)
        
        # --- Page 2: Theme Management ---
        theme_page = QWidget()
        theme_layout = QVBoxLayout(theme_page)
        theme_layout.setContentsMargins(20, 20, 20, 20)
        theme_layout.setSpacing(15)
        
        th_header_layout = QHBoxLayout()
        self.th_back_btn = QPushButton("← Back")
        self.th_back_btn.setObjectName("BackBtn")
        self.th_back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.th_back_btn.clicked.connect(self.go_back_to_list)
        th_header_layout.addWidget(self.th_back_btn)
        th_header_layout.addStretch()
        
        self.theme_title = QLabel("Themes")
        self.theme_title.setObjectName("TitleLabel")
        
        self.btn_import_theme = QPushButton("Import Theme")
        self.btn_import_theme.setObjectName("FolderBtn")
        self.btn_import_theme.clicked.connect(self.import_theme)
        
        theme_header_top = QHBoxLayout()
        theme_header_top.addWidget(self.theme_title)
        theme_header_top.addStretch()
        theme_header_top.addWidget(self.btn_import_theme)
        
        self.theme_scroll = QScrollArea()
        self.theme_scroll.setWidgetResizable(True)
        self.theme_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        self.themes_container = QWidget()
        self.themes_container.setStyleSheet("background: transparent;")
        self.themes_layout = QVBoxLayout(self.themes_container)
        self.themes_layout.setContentsMargins(0, 0, 0, 0)
        self.themes_layout.setSpacing(10)
        self.themes_layout.addStretch()
        self.theme_scroll.setWidget(self.themes_container)
        
        theme_layout.addLayout(th_header_layout)
        theme_layout.addLayout(theme_header_top)
        theme_layout.addWidget(self.theme_scroll)

        self.stacked_widget.addWidget(list_page)
        self.stacked_widget.addWidget(detail_page)
        self.stacked_widget.addWidget(theme_page)

    def apply_theme(self):
        c = self.theme_manager.get_current_theme()["colors"]
        
        qss = f"""
        QMainWindow, QWidget {{ background-color: {c['bg_main']}; color: {c['text_main']}; font-family: 'Segoe UI', Arial, sans-serif; }}
        QScrollBar:vertical {{ background: {c['scrollbar_bg']}; width: 8px; }}
        QScrollBar::handle:vertical {{ background: {c['scrollbar_handle']}; border-radius: 4px; }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
        
        QDialog {{ background-color: {c['bg_main']}; color: {c['text_main']}; }}
        QComboBox {{ background-color: {c['input_bg']}; color: {c['text_main']}; border: 1px solid {c['border']}; padding: 4px; border-radius: 4px; }}
        QCheckBox {{ color: {c['text_main']}; }}
        
        QLabel#TitleLabel {{ font-size: 24px; font-weight: bold; color: {c['text_main']}; }}
        QLabel#DetailName {{ font-size: 18px; font-weight: bold; color: {c['text_main']}; }}
        QLabel#DetailPath {{ font-size: 11px; color: {c['text_dim']}; }}
        QLabel#StatsTitle {{ font-weight: bold; font-size: 14px; color: {c['accent2']}; border: none; }}
        QLabel#SpeedIn {{ font-size: 20px; font-weight: bold; color: {c['success']}; border: none; }}
        QLabel#SpeedOut {{ font-size: 20px; font-weight: bold; color: {c['accent2']}; border: none; }}
        QLabel#TotalTxt {{ color: {c['text_dim']}; font-size: 12px; border: none; }}
        QLabel#FooterLabel {{ color: {c['text_dim']}; font-size: 11px; border: none; font-weight: 500; letter-spacing: 0.5px; }}
        
        QPushButton#AddBtn {{ 
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {c['accent1']}, stop:1 {c['accent2']});
            color: white; font-weight: bold; border-radius: 8px; padding: 12px; font-size: 14px; border: none;
        }}
        QPushButton#AddBtn:hover {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {c['accent_hover1']}, stop:1 {c['accent_hover2']}); }}
        
        QPushButton#BackBtn {{ background: transparent; color: {c['accent1']}; font-size: 16px; font-weight: bold; border: none; text-align: left; }}
        QPushButton#BackBtn:hover {{ color: {c['accent2']}; }}
        
        QPushButton#SettingsBtn, QPushButton#ThemeBtn {{ background-color: {c['bg_card']}; border: 1px solid {c['border']}; border-radius: 18px; color: {c['accent1']}; font-size: 18px; }}
        QPushButton#SettingsBtn:hover, QPushButton#ThemeBtn:hover {{ background-color: {c['bg_card_hover']}; border: 1px solid {c['accent1']}; }}
        
        QPushButton#FolderBtn {{ background: {c['bg_card']}; color: {c['accent1']}; border-radius: 4px; padding: 4px 8px; font-size: 11px; border: 1px solid {c['border']}; }}
        QPushButton#FolderBtn:hover {{ background: {c['bg_card_hover']}; color: {c['text_main']}; border-color: {c['accent1']}; }}
        
        QFrame#StatsCard {{ background-color: {c['bg_card']}; border-radius: 12px; border: 1px solid {c['border']}; }}
        QTextEdit#LogBox {{ background-color: {c['input_bg']}; color: {c['text_dim']}; border: 1px solid {c['border']}; border-radius: 8px; font-family: monospace; font-size: 11px; }}
        """
        self.setStyleSheet(qss)
        
        # Refresh current active view components
        self.engine.list_configs()
        if self.stacked_widget.currentIndex() == 2:
            self.populate_themes()
        
        if self.current_profile:
            # Re-apply status button colors via update_status
            status = self.lbl_detail_status.text()
            self.update_status(self.current_profile, status)

    def connect_signals(self):
        self.engine.configs_updated.connect(self.populate_configs)
        self.engine.vpn_status_changed.connect(self.update_status)
        self.engine.log_message.connect(self.append_log)
        self.engine.notify_user.connect(self.show_notification)
        self.engine.stats_updated.connect(self.update_stats)

    def import_profile(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select OpenVPN Config", "", "OpenVPN Configs (*.ovpn *.conf);;All Files (*)")
        if file_path:
            self.engine.import_config(file_path)

    def populate_configs(self, profiles):
        while self.configs_layout.count() > 1:
            item = self.configs_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        favorites = self.config.get('favorites', [])
        custom_names = self.config.get('custom_names', {})
        colors = self.theme_manager.get_current_theme()["colors"]
        
        sorted_profiles = sorted(profiles, key=lambda x: (0 if x in favorites else 1, x))
        
        for p in sorted_profiles:
            is_fav = p in favorites
            cname = custom_names.get(p)
            status = "Connected" if getattr(self.engine, 'active_monitor', None) and self.engine.active_monitor.profile_name == p else "Disconnected"
            widget = ConfigItemWidget(p, colors, cname, is_fav, status)
            widget.clicked.connect(self.on_profile_clicked)
            widget.delete_requested.connect(self.on_delete_requested)
            widget.favorite_toggled.connect(self.on_favorite_toggled)
            widget.rename_requested.connect(self.on_rename_requested)
            self.configs_layout.insertWidget(self.configs_layout.count() - 1, widget)

    # --- Theme Page Logic ---
    def go_to_themes(self):
        self.populate_themes()
        self.stacked_widget.setCurrentIndex(2)

    def populate_themes(self):
        while self.themes_layout.count() > 1:
            item = self.themes_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        themes = self.theme_manager.get_all_themes()
        curr_id = self.theme_manager.get_current_theme()["id"]
        
        for t in themes:
            widget = ThemeItemWidget(t, curr_id)
            widget.select_requested.connect(self.on_theme_select)
            widget.export_requested.connect(self.on_theme_export)
            widget.delete_requested.connect(self.on_theme_delete)
            self.themes_layout.insertWidget(self.themes_layout.count() - 1, widget)

    def on_theme_select(self, theme_id):
        self.theme_manager.set_theme(theme_id)
        self.apply_theme()

    def on_theme_export(self, theme_id):
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Theme", f"{theme_id}.json", "JSON Files (*.json)")
        if file_path:
            ok, msg = self.theme_manager.export_theme(theme_id, file_path)
            if not ok:
                QMessageBox.warning(self, "Export Failed", msg)
            else:
                QMessageBox.information(self, "Export Success", msg)

    def on_theme_delete(self, theme_id):
        ok, msg = self.theme_manager.delete_theme(theme_id)
        if not ok:
            QMessageBox.warning(self, "Delete Failed", msg)
        else:
            self.populate_themes()
            self.apply_theme()

    def import_theme(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Import Theme", "", "JSON Files (*.json)")
        if file_path:
            ok, msg = self.theme_manager.import_theme(file_path)
            if not ok:
                QMessageBox.warning(self, "Import Failed", msg)
            else:
                QMessageBox.information(self, "Import Success", msg)
                self.populate_themes()

    # --- Profile Actions ---
    def on_profile_clicked(self, profile):
        self.current_profile = profile
        custom_names = self.config.get('custom_names', {})
        display_name = custom_names.get(profile) if custom_names.get(profile) else profile.split('/')[-1]
        self.lbl_detail_name.setText(display_name)
        self.lbl_detail_path.setText(profile)
        
        is_active = False
        if getattr(self.engine, 'active_monitor', None):
            if self.engine.active_monitor.profile_name == profile:
                is_active = True
            else:
                self.engine.disconnect()
                
        if not is_active:
            self.log_box.clear()
            self.last_bytes_in = 0
            self.last_bytes_out = 0
            self.engine.connect(profile)
            self.update_status(profile, "Connecting...")
            
        self.stacked_widget.setCurrentIndex(1)

    def go_back_to_list(self):
        self.stacked_widget.setCurrentIndex(0)
        self.engine.list_configs()

    def toggle_current_connection(self):
        if not self.current_profile: return
        if self.toggle_btn.text() == "Disconnect" or self.toggle_btn.text() == "Cancel":
            self.engine.disconnect()
        else:
            self.engine.connect(self.current_profile)

    def on_delete_requested(self, profile):
        self.engine.delete_config(profile)

    def on_favorite_toggled(self, profile, is_favorite):
        favs = self.config.get('favorites', [])
        if is_favorite and profile not in favs:
            favs.append(profile)
        elif not is_favorite and profile in favs:
            favs.remove(profile)
        self.config.set('favorites', favs)
        self.engine.list_configs()

    def on_rename_requested(self, profile):
        custom_names = self.config.get('custom_names', {})
        current_name = custom_names.get(profile, profile.split('/')[-1])
        
        new_name, ok = QInputDialog.getText(self, "Rename VPN", "Enter a friendly name for this profile:", text=current_name)
        if ok and new_name.strip():
            custom_names[profile] = new_name.strip()
            self.config.set('custom_names', custom_names)
            self.engine.list_configs()

    def open_profile_folder(self):
        if self.current_profile and os.path.exists(self.current_profile):
            folder = os.path.dirname(self.current_profile)
            import shutil
            managers = ['cosmic-files', 'nautilus', 'nemo', 'thunar', 'pcmanfm', 'dolphin']
            for manager in managers:
                if shutil.which(manager):
                    try:
                        subprocess.Popen([manager, folder])
                        return
                    except Exception:
                        pass
            try:
                subprocess.Popen(['xdg-open', folder])
            except Exception:
                pass

    def update_status(self, profile, status):
        if self.current_profile == profile:
            self.lbl_detail_status.setText(status)
            c = self.theme_manager.get_current_theme()["colors"]
            
            if status == "Connected":
                self.lbl_detail_status.setStyleSheet(f"color: {c['success']}; font-size: 14px; margin-bottom: 10px; margin-top: 5px;")
                self.toggle_btn.setText("Disconnect")
                self.toggle_btn.setStyleSheet(f"""
                    QPushButton {{ background-color: {c['bg_card_hover']}; color: {c['accent2']}; font-weight: bold; border-radius: 8px; padding: 12px; font-size: 14px; border: 1px solid {c['accent1']};}}
                    QPushButton:hover {{ background-color: {c['accent1']}; color: white; }}
                """)
                self.stats_card.setVisible(True)
            elif "Disconnected" in status:
                self.lbl_detail_status.setStyleSheet(f"color: {c['text_dim']}; font-size: 14px; margin-bottom: 10px; margin-top: 5px;")
                self.toggle_btn.setText("Connect")
                self.toggle_btn.setStyleSheet(f"""
                    QPushButton {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {c['accent1']}, stop:1 {c['accent2']}); color: white; font-weight: bold; border-radius: 8px; padding: 12px; font-size: 14px; border: none;}}
                    QPushButton:hover {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {c['accent_hover1']}, stop:1 {c['accent_hover2']}); }}
                """)
                self.stats_card.setVisible(False)
            elif "Authenticating" in status or "Connecting" in status:
                self.lbl_detail_status.setStyleSheet(f"color: {c['warning']}; font-size: 14px; margin-bottom: 10px; margin-top: 5px;")
                self.toggle_btn.setText("Cancel")
                self.toggle_btn.setStyleSheet(f"""
                    QPushButton {{ background-color: {c['bg_card_hover']}; color: {c['accent2']}; font-weight: bold; border-radius: 8px; padding: 12px; font-size: 14px; border: 1px solid {c['accent1']};}}
                    QPushButton:hover {{ background-color: {c['accent1']}; color: white; }}
                """)
                self.stats_card.setVisible(False)

        for i in range(self.configs_layout.count()):
            item = self.configs_layout.itemAt(i)
            if item.widget() and isinstance(item.widget(), ConfigItemWidget):
                if item.widget().profile_name == profile:
                    item.widget().set_status(status)

    def update_stats(self, stats):
        bytes_in = stats.get("BYTES_IN", 0)
        bytes_out = stats.get("BYTES_OUT", 0)
        
        speed_in = max(0, bytes_in - self.last_bytes_in) / 1024
        speed_out = max(0, bytes_out - self.last_bytes_out) / 1024
        
        self.lbl_speed_in.setText(f"{speed_in:.1f} KB/s")
        self.lbl_speed_out.setText(f"{speed_out:.1f} KB/s")
        self.lbl_total_in.setText(f"{bytes_in / (1024*1024):.2f} MB")
        self.lbl_total_out.setText(f"{bytes_out / (1024*1024):.2f} MB")
        
        self.last_bytes_in = bytes_in
        self.last_bytes_out = bytes_out

    def append_log(self, msg):
        self.log_box.append(msg)
        scrollbar = self.log_box.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def open_settings(self):
        dialog = SettingsDialog(self.config, self.theme_manager, self)
        dialog.exec()

    def show_notification(self, title, message):
        try:
            subprocess.Popen(['notify-send', title, message, '-a', 'OpenVPN Client'])
        except Exception:
            pass

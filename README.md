# OpenVPN 3 Client GUI

A modern graphical user interface for OpenVPN 3 on Linux, designed to provide a user experience similar to OpenVPN Connect on Windows and macOS.

## Features

### Core Functionality

* Modern and responsive user interface.
* Dark theme support.
* Import and manage `.ovpn` configuration profiles.
* View all available VPN profiles.
* Connect and disconnect VPN profiles with a single click.
* Real-time connection status monitoring.

### Advanced Features

* Automatic detection of OpenVPN 3 authentication URLs (SSO/Auth URL).
* Open authentication pages using your preferred web browser.
* Desktop notifications when the VPN connection is unexpectedly disconnected.
* Automatic reconnection after network interruptions or unexpected disconnects.
* Smart reconnect logic that does **not** reconnect when the user manually disconnects.
* Configurable browser selection for SSO authentication:

  * System Default Browser
  * Google Chrome
  * Mozilla Firefox
  * Brave Browser
  * Microsoft Edge

## System Requirements

### Supported Operating Systems

* Debian-based Linux distributions
* Ubuntu and Ubuntu-based distributions

### Required Packages

* OpenVPN 3
* Python 3
* `libnotify-bin` (for desktop notifications)

## Development Setup

Modern Linux distributions such as Debian 12 and Ubuntu 24.04 implement PEP 668 protections, which require Python packages to be installed inside a virtual environment.

### 1. Install Required System Packages

```bash
sudo apt update
sudo apt install python3-pip python3-venv libnotify-bin -y
```

### 2. Create a Virtual Environment

```bash
python3 -m venv venv
```

### 3. Activate the Virtual Environment

Run this command every time you open a new terminal session:

```bash
source venv/bin/activate
```

### 4. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 5. Launch the Application

```bash
python main.py
```

---

# Building a Debian Package (.deb)

The project includes a `build_deb.sh` script that packages the entire application, including all Python dependencies, into a standalone Debian package using PyInstaller.

### 1. Activate the Virtual Environment

```bash
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Build the Package

```bash
./build_deb.sh
```

### Build Process Overview

The build script automatically performs the following tasks:

* Compiles the Python application into standalone executables using PyInstaller.
* Creates a standard Debian package structure.
* Installs application files under `/opt/openvpnclient`.
* Generates a desktop launcher entry under `/usr/share/applications`.
* Packages everything into a distributable Debian package.

Generated output:

```text
openvpnclient_<version>_amd64.deb
```

### 4. Install the Package

```bash
sudo dpkg -i openvpnclient_1.0.0_amd64.deb
```

If dependency issues occur, run:

```bash
sudo apt-get install -f
```

### 5. Launch the Application

After installation, open your system's Application Menu and search for:

```text
OpenVPN Client
```

---

## Notes

* OpenVPN 3 must be installed and functioning correctly before using this application.
* Desktop notifications require the `libnotify-bin` package.
* Auto-reconnect is only triggered for unexpected disconnects and network interruptions.
* Manual disconnections initiated by the user will not trigger automatic reconnection.

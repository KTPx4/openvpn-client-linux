#!/bin/bash
set -e

APP_NAME="openvpnclient"
VERSION="1.0.0"
ARCH="amd64"
DEB_DIR="build_deb"
INSTALL_DIR="/opt/$APP_NAME"

echo "Building executable with PyInstaller..."
# We use --windowed so it doesn't open a terminal when launching from desktop
# We create a directory bundle rather than single file, it's faster to start
pyinstaller --noconfirm --windowed --name "$APP_NAME" main.py

echo "Preparing deb package structure..."
rm -rf "$DEB_DIR"
mkdir -p "$DEB_DIR/DEBIAN"
mkdir -p "$DEB_DIR/$INSTALL_DIR"
mkdir -p "$DEB_DIR/usr/share/applications"
mkdir -p "$DEB_DIR/usr/share/icons/hicolor/256x256/apps"

# Copy pyinstaller output
cp -r dist/"$APP_NAME"/* "$DEB_DIR/$INSTALL_DIR/"

# Create control file
cat <<EOF > "$DEB_DIR/DEBIAN/control"
Package: $APP_NAME
Version: $VERSION
Section: utils
Priority: optional
Architecture: $ARCH
Depends: openvpn3, libnotify-bin
Maintainer: Your Name <your.email@example.com>
Description: OpenVPN 3 Client GUI
 A modern graphical user interface for OpenVPN 3 Linux client.
 Supports profile importing, auto-reconnect, and browser authentication.
EOF

# Create desktop file
cat <<EOF > "$DEB_DIR/usr/share/applications/$APP_NAME.desktop"
[Desktop Entry]
Name=OpenVPN Client
Comment=OpenVPN 3 Client GUI
Exec=$INSTALL_DIR/$APP_NAME
Icon=$APP_NAME
Terminal=false
Type=Application
Categories=Network;Utility;
EOF

# Optional: Add a dummy icon (or real icon if you have one)
# We will just rely on the fallback system icon for now if not provided,
# but let's touch a dummy file so it doesn't fail if we ever add an icon script.

echo "Building the .deb package..."
dpkg-deb --build "$DEB_DIR" "${APP_NAME}_${VERSION}_${ARCH}.deb"

echo "Done! The package ${APP_NAME}_${VERSION}_${ARCH}.deb is ready."

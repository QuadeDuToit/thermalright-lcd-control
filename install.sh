#!/bin/bash
# SPDX-License-Identifier: Apache-2.0
# Installation script for thermalright-lcd-control (source-based fork)

set -e

# Application name and paths
APP_NAME="thermalright-lcd-control"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# System directories (requires root)
INSTALL_DIR="/usr/share/$APP_NAME"
BIN_DIR="/usr/local/bin"
SYSTEMD_DIR="/etc/systemd/system"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check for root
if [[ $EUID -ne 0 ]]; then
   log_error "This script must be run with sudo"
   exit 1
fi

# Get actual user info
ACTUAL_USER="${SUDO_USER:-$USER}"
ACTUAL_HOME=$(getent passwd "$ACTUAL_USER" | cut -d: -f6)
ACTUAL_UID=$(id -u "$ACTUAL_USER")
ACTUAL_GID=$(id -g "$ACTUAL_USER")

log_info "Installing $APP_NAME for user: $ACTUAL_USER"
log_info "User home: $ACTUAL_HOME"

# Check dependencies
log_info "Checking dependencies..."

if ! command -v python3 &> /dev/null; then
    log_error "python3 is not installed"
    exit 1
fi

if ! command -v pip3 &> /dev/null; then
    log_error "pip3 is not installed"
    exit 1
fi

# Check hidapi
HIDAPI_FOUND=false
if [ -f "/usr/include/hidapi/hidapi.h" ] || [ -f "/usr/local/include/hidapi/hidapi.h" ]; then
    HIDAPI_FOUND=true
fi
if command -v pkg-config &> /dev/null; then
    if pkg-config --exists hidapi-libusb || pkg-config --exists hidapi-hidraw; then
        HIDAPI_FOUND=true
    fi
fi

if [ "$HIDAPI_FOUND" = false ]; then
    log_error "hidapi library not found"
    log_info "Install with: sudo dnf install hidapi-devel"
    exit 1
fi

log_info "Dependencies OK"

# Stop existing service
if systemctl is-active --quiet "$APP_NAME.service"; then
    log_info "Stopping existing service..."
    systemctl stop "$APP_NAME.service"
fi

# Create installation directory
log_info "Installing to $INSTALL_DIR..."
mkdir -p "$INSTALL_DIR"

# Copy source files
cp -r "$SCRIPT_DIR/thermalright_lcd_control" "$INSTALL_DIR/"
cp -r "$SCRIPT_DIR/resources" "$INSTALL_DIR/"
cp "$SCRIPT_DIR/pyproject.toml" "$INSTALL_DIR/"
cp "$SCRIPT_DIR/README.md" "$INSTALL_DIR/" 2>/dev/null || true
cp "$SCRIPT_DIR/LICENSE" "$INSTALL_DIR/" 2>/dev/null || true

# Make config directory writable by user
if [ -n "$SUDO_USER" ]; then
    chown -R "$SUDO_USER:$SUDO_USER" "$INSTALL_DIR/resources/config"
    chown -R "$SUDO_USER:$SUDO_USER" "$INSTALL_DIR/resources/themes/presets"
fi

# Install Python dependencies for root (service)
log_info "Installing Python dependencies for service (root)..."
pip3 install PySide6 hid psutil opencv-python pyusb pillow pyyaml --break-system-packages 2>/dev/null || \
pip3 install PySide6 hid psutil opencv-python pyusb pillow pyyaml

# Install Python dependencies for the user who invoked sudo (GUI)
if [ -n "$SUDO_USER" ]; then
    log_info "Installing Python dependencies for GUI user ($SUDO_USER)..."
    sudo -u "$SUDO_USER" pip3 install PySide6 hid psutil opencv-python pyusb pillow pyyaml --break-system-packages 2>/dev/null || \
    sudo -u "$SUDO_USER" pip3 install PySide6 hid psutil opencv-python pyusb pillow pyyaml
fi

# Install Python package system-wide
log_info "Installing Python package..."
cd "$INSTALL_DIR"
pip3 install -e . --break-system-packages 2>/dev/null || pip3 install -e .

# Create wrapper scripts
log_info "Creating launcher scripts..."

# GUI launcher - runs as user, configs writable by user's group
cat > "$BIN_DIR/$APP_NAME" <<EOF
#!/bin/bash
cd "/usr/share/thermalright-lcd-control"
exec python3 -m thermalright_lcd_control.main_gui --config "/usr/share/thermalright-lcd-control/resources/gui_config.yaml" "\$@"
EOF
chmod 755 "$BIN_DIR/$APP_NAME"

# Service script
cat > "$BIN_DIR/${APP_NAME}-service" <<'EOF'
#!/bin/bash
exec python3 -m thermalright_lcd_control.service "$@"
EOF
chmod 755 "$BIN_DIR/${APP_NAME}-service"

# Create systemd service
log_info "Creating systemd service..."
cat > "$SYSTEMD_DIR/$APP_NAME.service" <<EOF
[Unit]
Description=Thermalright LCD Control Service
After=network.target

[Service]
Type=simple
User=root
ExecStart=$BIN_DIR/${APP_NAME}-service --config $INSTALL_DIR/resources/config
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Create desktop entry
log_info "Creating desktop entry..."
DESKTOP_DIR="$ACTUAL_HOME/.local/share/applications"
mkdir -p "$DESKTOP_DIR"

cat > "$DESKTOP_DIR/$APP_NAME.desktop" <<EOF
[Desktop Entry]
Version=1.3.1
Type=Application
Name=Thermalright LCD Control
Comment=Control Thermalright LCD displays
Exec=$BIN_DIR/$APP_NAME
Icon=$INSTALL_DIR/resources/256x256/icon.png
Terminal=false
Categories=Utility;System;
EOF

chown "$ACTUAL_UID:$ACTUAL_GID" "$DESKTOP_DIR/$APP_NAME.desktop"
chmod 644 "$DESKTOP_DIR/$APP_NAME.desktop"

# Create polkit rules for passwordless operations
log_info "Creating polkit rules for passwordless operations..."
cat > "/etc/polkit-1/rules.d/50-thermalright-lcd-control.rules" <<EOF
// Allow wheel group to restart thermalright-lcd-control service without password
polkit.addRule(function(action, subject) {
    if (action.id == "org.freedesktop.systemd1.manage-units" &&
        action.lookup("unit") == "thermalright-lcd-control.service" &&
        subject.isInGroup("wheel")) {
        return polkit.Result.YES;
    }
});

// Allow wheel group to copy/create files in /usr/share/thermalright-lcd-control without password
polkit.addRule(function(action, subject) {
    if ((action.id == "org.freedesktop.policykit.exec") &&
        subject.isInGroup("wheel")) {
        var program = action.lookup("program");
        var cmdline = action.lookup("command_line");
        
        // Allow cp and mkdir commands for thermalright-lcd-control directories
        if ((program == "/usr/bin/cp" || program == "/usr/bin/mkdir") &&
            cmdline && cmdline.indexOf("/usr/share/thermalright-lcd-control") !== -1) {
            return polkit.Result.YES;
        }
    }
});
EOF

chmod 644 "/etc/polkit-1/rules.d/50-thermalright-lcd-control.rules"

# Initialize device
log_info "Initializing device..."
python3 -m thermalright_lcd_control.device_init --config "$INSTALL_DIR/resources/config" || {
    log_warn "Device initialization failed - device may not be connected"
}

# Enable and start service
log_info "Enabling service..."
systemctl daemon-reload
systemctl enable "$APP_NAME.service"
systemctl start "$APP_NAME.service"

log_info ""
log_info "═══════════════════════════════════════════════"
log_info "✅ Installation completed successfully!"
log_info "═══════════════════════════════════════════════"
log_info ""
log_info "Installation details:"
log_info "  • Application: $INSTALL_DIR"
log_info "  • Command: $APP_NAME"
log_info "  • Service: $APP_NAME.service"
log_info "  • Config: $INSTALL_DIR/resources/config"
log_info ""
log_info "Usage:"
log_info "  • Start GUI: $APP_NAME"
log_info "  • Service status: sudo systemctl status $APP_NAME"
log_info "  • Service logs: sudo journalctl -u $APP_NAME -f"
log_info "  • Restart service: sudo systemctl restart $APP_NAME"
log_info ""
log_info "Rotation feature available in GUI!"
log_info ""

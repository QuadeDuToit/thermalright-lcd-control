#!/bin/bash
# Quick script to reset the LCD USB device and clean up trigger files

echo "=== Thermalright LCD Reset & Cleanup ==="
echo

# 1. Stop the service
echo "1. Stopping service..."
sudo systemctl stop thermalright-lcd-control 2>/dev/null
sleep 1

# 2. Kill any stray processes
echo "2. Checking for stray processes..."
PIDS=$(ps aux | grep thermalright-lcd-service | grep -v grep | awk '{print $2}')
if [ -n "$PIDS" ]; then
    echo "   Found processes: $PIDS"
    sudo kill -9 $PIDS 2>/dev/null
    sleep 1
else
    echo "   No stray processes found"
fi

# 3. Reset USB device
echo "3. Resetting USB device..."
# Find the Thermalright LCD device (VID:0x87ad)
USB_DEV=$(lsusb | grep "87ad:" | sed 's/Bus \([0-9]*\) Device \([0-9]*\).*/\/dev\/bus\/usb\/\1\/\2/')
if [ -n "$USB_DEV" ]; then
    echo "   Found device: $USB_DEV"
    # Use usbreset or unbind/bind to reset
    if command -v usbreset &> /dev/null; then
        sudo usbreset "$USB_DEV"
    else
        echo "   Attempting unbind/bind..."
        BUS=$(echo $USB_DEV | cut -d'/' -f5)
        DEV=$(echo $USB_DEV | cut -d'/' -f6)
        BIND_PATH=$(find /sys/bus/usb/devices -name "$BUS-*" -type l 2>/dev/null | head -1)
        if [ -n "$BIND_PATH" ]; then
            DRIVER=$(basename $(readlink "$BIND_PATH/driver" 2>/dev/null) 2>/dev/null)
            if [ -n "$DRIVER" ]; then
                sudo sh -c "echo '$BUS-*' > /sys/bus/usb/drivers/$DRIVER/unbind" 2>/dev/null
                sleep 0.5
                sudo sh -c "echo '$BUS-*' > /sys/bus/usb/drivers/$DRIVER/bind" 2>/dev/null
            fi
        fi
    fi
    sleep 1
else
    echo "   Device not found (maybe not connected?)"
fi

# 4. Clean up trigger files
echo "4. Cleaning up trigger files..."
if [ -d "/tmp/thermalright-lcd-triggers" ]; then
    COUNT=$(ls /tmp/thermalright-lcd-triggers/*.trigger 2>/dev/null | wc -l)
    if [ $COUNT -gt 0 ]; then
        sudo rm /tmp/thermalright-lcd-triggers/*.trigger
        echo "   Removed $COUNT old trigger files"
    else
        echo "   No trigger files to clean"
    fi
else
    echo "   Trigger directory doesn't exist yet"
fi

echo
echo "=== Done! ==="
echo
echo "Now try starting the service:"
echo "  sudo systemctl start thermalright-lcd-control"
echo
echo "Or run manually to see errors:"
echo "  sudo thermalright-lcd-service --config /usr/share/thermalright-lcd-control/resources/config"

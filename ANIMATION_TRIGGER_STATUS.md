# Animation Trigger System - Status & Troubleshooting

## ✅ What's Working

1. **Animation trigger CLI** (`thermalright-lcd-trigger`) is installed
2. **Service integration** - Animation monitoring code is in place
3. **GUI fix** - Lazy initialization prevents errors when device not connected

## ⚠️ Current Issues

### Issue #1: Service Not Running
**Problem:** The LCD service must be running for animations to play.

**Check if service is running:**
```bash
ps aux | grep thermalright-lcd-service
```

**Start the service manually (for testing):**
```bash
sudo /var/data/python/bin/thermalright-lcd-service
```

**Or set up systemd service** (recommended for permanent use):
```bash
sudo systemctl start thermalright-lcd-control
sudo systemctl enable thermalright-lcd-control  # Auto-start on boot
```

### Issue #2: HID Library Missing (GUI only)
**Problem:** GUI can't launch due to missing libhidapi library.

**Fix (Fedora/RHEL):**
```bash
sudo dnf install hidapi
```

**Fix (Debian/Ubuntu):**
```bash
sudo apt install libhidapi-hidraw0 libhidapi-libusb0
```

This is only needed if you want to run the GUI. The service and trigger command work independently.

## 🧪 Testing Animation Triggers

### 1. Start the service first:
```bash
sudo /var/data/python/bin/thermalright-lcd-service
```

### 2. In another terminal, trigger an animation:
```bash
/var/data/python/bin/thermalright-lcd-trigger --play-animation /path/to/video.mp4
```

### 3. Check service logs:
Look for messages like:
- `Animation trigger system initialized`
- `Playing triggered animation: /path/to/video.mp4`
- `Animation finished: /path/to/video.mp4`

## 📁 How It Works

1. **Trigger Command** creates a file in `/tmp/thermalright-lcd-triggers/`
2. **Service** monitors this directory (checks every 0.5 seconds)
3. **Service** plays the animation when detected
4. **Service** returns to normal display after animation completes

## 🎬 Git Hooks Setup

Once the service is running properly, install git hooks:

```bash
# 1. Create animations directory
sudo mkdir -p /usr/share/thermalright-lcd-control/animations

# 2. Add your animation files (480x480 recommended)
sudo cp my-pull-animation.mp4 /usr/share/thermalright-lcd-control/animations/git-pull.mp4
sudo cp my-push-animation.mp4 /usr/share/thermalright-lcd-control/animations/git-push.mp4

# 3. Install hooks in your git repo
cd /path/to/your/repo
cp ~/.local/share/thermalright-lcd-control/resources/git-hooks/post-merge .git/hooks/
cp ~/.local/share/thermalright-lcd-control/resources/git-hooks/pre-push .git/hooks/
chmod +x .git/hooks/post-merge .git/hooks/pre-push

# 4. Edit hooks to use full path
sed -i 's|thermalright-lcd-trigger|/var/data/python/bin/thermalright-lcd-trigger|' .git/hooks/post-merge
sed -i 's|thermalright-lcd-trigger|/var/data/python/bin/thermalright-lcd-trigger|' .git/hooks/pre-push
```

## 🔍 Debugging Checklist

- [ ] LCD device connected and recognized (`lsusb | grep 87ad`)
- [ ] Service is running (`ps aux | grep thermalright-lcd-service`)
- [ ] Animation file exists and is readable
- [ ] Animation format is supported (MP4, AVI, MKV, MOV, WebM, GIF)
- [ ] Trigger directory exists (`/tmp/thermalright-lcd-triggers/`)
- [ ] Service has permissions to read animation file (runs as root)

## 📝 Next Steps

1. **Start the service** to enable animation playback
2. **Test manually** with a simple video file
3. **Install git hooks** once working
4. **Create custom animations** optimized for your LCD (480x480)

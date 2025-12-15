# Git Hooks for LCD Animations

Play animations automatically when you do git operations!

## Installation

1. **Copy hooks to your repository:**
   ```bash
   cp resources/git-hooks/post-merge .git/hooks/
   cp resources/git-hooks/pre-push .git/hooks/
   chmod +x .git/hooks/post-merge .git/hooks/pre-push
   ```

2. **Create animations directory:**
   ```bash
   sudo mkdir -p /usr/share/thermalright-lcd-control/animations
   ```

3. **Add your animation files:**
   - `git-pull.mp4` - Plays when you do `git pull`
   - `git-push.mp4` - Plays when you do `git push`

   Supported formats: MP4, AVI, MKV, MOV, WebM, GIF

## Manual Testing

Test the animation trigger without git:

```bash
thermalright-lcd-trigger --play-animation /path/to/your/video.mp4
```

## Creating Animations

### Recommended Settings:
- **Resolution:** 480x480 (or will be scaled)
- **Duration:** 2-5 seconds (short and sweet)
- **Format:** MP4 with H.264 codec
- **FPS:** 24-30 fps

### Example with FFmpeg:

Convert any video to LCD-friendly format:
```bash
ffmpeg -i input.mp4 -vf "scale=480:480:force_original_aspect_ratio=decrease,pad=480:480:(ow-iw)/2:(oh-ih)/2" -r 30 -t 3 -c:v libx264 git-pull.mp4
```

Create from images:
```bash
ffmpeg -framerate 30 -i frame_%03d.png -vf "scale=480:480" -t 3 -c:v libx264 git-push.mp4
```

## Customization

Edit the hook files to:
- Change animation paths
- Add conditions (only trigger for certain branches)
- Play different animations based on context

Example - only play on main branch:
```bash
BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$BRANCH" = "main" ] && [ -f "$ANIMATION" ]; then
    thermalright-lcd-trigger --play-animation "$ANIMATION" &
fi
```

## Troubleshooting

**Animation doesn't play:**
- Check the service is running: `systemctl status thermalright-lcd-control`
- Verify file exists and is readable
- Test manually with `thermalright-lcd-trigger --play-animation <file>`
- Check file format is supported

**Hook not executing:**
- Ensure hook file is executable: `chmod +x .git/hooks/post-merge`
- Check file is in correct location (inside `.git/hooks/`)
- Verify shebang line is correct: `#!/bin/sh`

**Animation cut off/slow:**
- Keep animations short (2-5 seconds)
- Reduce FPS if needed (24-30 is good)
- Service processes animations sequentially

#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Rejeb Ben Rejeb

"""CLI tool to trigger animations on the LCD display"""

import argparse
import sys
import os
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="ThermalRight LCD Control - Animation Trigger"
    )
    parser.add_argument(
        '--play-animation',
        metavar='PATH',
        help='Play an animation file (video/GIF) on the LCD display'
    )
    
    args = parser.parse_args()
    
    if args.play_animation:
        animation_path = Path(args.play_animation).resolve()
        
        if not animation_path.exists():
            print(f"Error: Animation file not found: {animation_path}", file=sys.stderr)
            return 1
        
        # Check file extension
        valid_extensions = {'.mp4', '.avi', '.mkv', '.mov', '.webm', '.gif'}
        if animation_path.suffix.lower() not in valid_extensions:
            print(f"Warning: File extension {animation_path.suffix} may not be supported", file=sys.stderr)
            print(f"Supported formats: {', '.join(valid_extensions)}", file=sys.stderr)
        
        # Trigger the animation
        from thermalright_lcd_control.device_controller.animation_trigger import AnimationTrigger
        
        try:
            AnimationTrigger.trigger_animation(str(animation_path))
            print(f"✓ Animation queued: {animation_path.name}")
            print(f"  The animation will play on your LCD display shortly.")
            return 0
        except Exception as e:
            print(f"Error triggering animation: {e}", file=sys.stderr)
            return 1
    
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())

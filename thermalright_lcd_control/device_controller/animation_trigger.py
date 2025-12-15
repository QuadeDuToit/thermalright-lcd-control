# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Rejeb Ben Rejeb

"""Animation trigger system for playing animations on demand"""

import os
import time
from pathlib import Path
from threading import Thread, Lock
from ..common.logging_config import get_service_logger


class AnimationTrigger:
    """Monitors for animation trigger requests and queues them for playback"""
    
    TRIGGER_DIR = "/tmp/thermalright-lcd-triggers"
    
    def __init__(self):
        self.logger = get_service_logger()
        self.animation_queue = []
        self.queue_lock = Lock()
        self.monitoring = False
        self.monitor_thread = None
        
        # Ensure trigger directory exists
        os.makedirs(self.TRIGGER_DIR, exist_ok=True)
        
        # Clean up any old trigger files
        self._cleanup_triggers()
    
    def start_monitoring(self):
        """Start monitoring for trigger files"""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.monitor_thread = Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        self.logger.info("Animation trigger monitoring started")
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)
    
    def _monitor_loop(self):
        """Monitor loop that checks for trigger files"""
        while self.monitoring:
            try:
                # Check for trigger files
                trigger_files = list(Path(self.TRIGGER_DIR).glob("*.trigger"))
                
                for trigger_file in trigger_files:
                    try:
                        # Read animation path from trigger file
                        with open(trigger_file, 'r') as f:
                            animation_path = f.read().strip()
                        
                        if animation_path and os.path.exists(animation_path):
                            # Add to queue
                            with self.queue_lock:
                                self.animation_queue.append(animation_path)
                            self.logger.info(f"Queued animation: {animation_path}")
                        
                        # Delete trigger file
                        trigger_file.unlink()
                    
                    except Exception as e:
                        self.logger.error(f"Error processing trigger file {trigger_file}: {e}")
                        try:
                            trigger_file.unlink()
                        except:
                            pass
                
                # Sleep before next check
                time.sleep(0.5)
            
            except Exception as e:
                self.logger.error(f"Error in animation trigger monitor: {e}")
                time.sleep(1.0)
    
    def has_pending_animation(self):
        """Check if there's a pending animation in the queue"""
        with self.queue_lock:
            return len(self.animation_queue) > 0
    
    def get_next_animation(self):
        """Get the next animation from the queue"""
        with self.queue_lock:
            if self.animation_queue:
                return self.animation_queue.pop(0)
        return None
    
    def _cleanup_triggers(self):
        """Clean up old trigger files"""
        try:
            for trigger_file in Path(self.TRIGGER_DIR).glob("*.trigger"):
                trigger_file.unlink()
        except Exception as e:
            self.logger.warning(f"Error cleaning up trigger files: {e}")
    
    @staticmethod
    def trigger_animation(animation_path: str):
        """Static method to trigger an animation (called by CLI)"""
        trigger_dir = Path(AnimationTrigger.TRIGGER_DIR)
        trigger_dir.mkdir(parents=True, exist_ok=True)
        
        # Create unique trigger file
        trigger_file = trigger_dir / f"anim_{int(time.time() * 1000)}.trigger"
        
        with open(trigger_file, 'w') as f:
            f.write(animation_path)
        
        return True

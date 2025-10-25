# Changelog

## [1.3.1] - 2024-10-25 - Rotation Feature Fork

### Added
- **Display Rotation Support**: Full 360° rotation control (0°, 90°, 180°, 270°)
- **GUI Rotation Controls**: 
  - Rotation dropdown menu in main GUI
  - "Quick Flip" button for instant normal/upside-down toggle
  - Auto-loading of current rotation setting
- **Command Line Tools**:
  - `lcd-flip`: Simple toggle script
  - `lcd-rotate`: Advanced rotation control with multiple options
  - `lcd-rotation-gui`: Standalone rotation GUI
- **Configuration Support**: 
  - `rotation` parameter in YAML config files
  - Persistent rotation settings across restarts
- **Device Compatibility**: 
  - Enhanced USB device classes for rotation support
  - Tested with Thermalright Frozen Vision 360 ARGB (VID:87AD, PID:70DB)

### Changed
- **Rendering Pipeline**: Added PIL image rotation in frame processing
- **GUI Layout**: Added "Display Rotation" section to controls panel
- **Service Integration**: Automatic service restart when rotation changes

### Technical Implementation
- Modified `display_device.py` base class for rotation support
- Updated `usb_devices.py` device-specific classes 
- Enhanced `controls_manager.py` GUI with rotation controls
- Added rotation logic to frame rendering pipeline before encoding

### Compatibility
- Fully backward compatible with original thermalright-lcd-control
- All existing features and configurations remain unchanged
- No breaking changes to API or configuration format

---

## Original Changelog

Changelog for releases prior to rotation feature fork can be found in the upstream repository: https://github.com/rejeb/thermalright-lcd-control
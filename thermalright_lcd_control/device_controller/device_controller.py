# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Rejeb Ben Rejeb
from .display.device_loader import DeviceLoader
from ..common.logging_config import get_service_logger


def run_service(config_dir: str):
    logger = get_service_logger()
    logger.info("Device controller service started")

    try:
        loader = DeviceLoader(config_dir)
        device = loader.load_device()
        if device is None:
            logger.error(f"No device found", exc_info=True)
            exit(1)
        logger.info("Device loaded successfully, resetting...")
        device.reset()
        logger.info("Device reset complete, starting main loop...")
        device.run()
    except KeyboardInterrupt:
        logger.info("Device controller service stopped by user")
    except Exception as e:
        logger.error(f"Device controller service error: {e}", exc_info=True)
        raise

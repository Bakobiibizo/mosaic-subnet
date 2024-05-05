from mosaic_subnet.base.config import MosaicBaseSettings
from typing import List


class GatewaySettings(MosaicBaseSettings):
    """Configuration settings for the basic Gateway."""

    host: str = "0.0.0.0"
    port: int = 8080

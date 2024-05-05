from mosaic_subnet.base.config import MosaicBaseSettings


class MinerSettings(MosaicBaseSettings):
    """Configuration settings for the basic Miner."""

    host: str = "0.0.0.0"
    port: int = 8888
    model: str = "Lykon/dreamshaper-xl-v2-turbo"

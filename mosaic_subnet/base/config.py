from pydantic_settings import BaseSettings
from typing import List


class MosaicBaseSettings(BaseSettings):
    """Configuration of the base settings of the Mosaic Subnet."""

    use_testnet: bool = False
    call_timeout: int = 60
    module_path: str
    key_name: str


class AccessControl(BaseSettings):
    """Whitelist and blacklist model for future use."""

    whitelist: List[str] = []
    blacklist: List[str] = []


class Config:
    """Environment configuration settings for this library"""

    env_prefix = "MOSAIC"
    env_file = "env/config.env"
    extra = "ignore"

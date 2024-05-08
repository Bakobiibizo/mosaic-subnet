from pydantic_settings import BaseSettings
from pydantic import BaseModel
from typing import List, Optional


class BaseMosaic(BaseSettings):
    """Configuration of the base settings of the Mosaic Subnet."""

    module_path: str = "agent.ArtificialMiner"
    key_name: str = "agent.ArtificialMiner"
    host: str = "0.0.0.0"
    port: int = 50051
    use_testnet: bool = False
    call_timeout: int = 60


class AccessControl(BaseSettings):
    """Whitelist and blacklist model for future use."""

    whitelist: List[str] = []
    blacklist: List[str] = []


class Config:
    """Environment configuration settings for this library"""

    env_prefix = "MOSAIC"
    env_file = "env/config.env"
    extra = "ignore"


class SampleInput(BaseModel):
    """Model for sample input."""

    prompt: str
    negative_prompt: str = ""
    steps: int = 10
    seed: Optional[int] = None

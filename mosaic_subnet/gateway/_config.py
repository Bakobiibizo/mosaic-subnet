import re
from mosaic_subnet.base.base import ModuleSettings
from communex._common import get_node_url
from communex.compat.key import Ss58Address
from typing import Optional


class GatewaySettings(ModuleSettings):
    """Configuration settings for the Gateway."""

    module_path: str = "gateway.Gateway"
    key_name: str = "gateway.Gateway"
    host: str = "0.0.0.0"
    port: int = 8080
    use_testnet: bool = False
    call_timeout: int = 60
    ss58_address: Optional[Ss58Address] = None
    IP_REGEX: re.Pattern[str] = re.compile(
        pattern=r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+"
    )

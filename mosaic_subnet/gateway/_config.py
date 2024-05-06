from ..base.config import MosaicBaseSettings
from communex._common import get_node_url
from communex.compat.key import Ss58Address, local_key_addresses
from typing import Optional


class GatewaySettings(MosaicBaseSettings):
    """Configuration settings for the basic Gateway."""

    host: Optional[str] = "0.0.0.0"
    port: Optional[int] = 8080
    module_path: Optional[str] = "agent.ArtificialGateway"
    key_name: Optional[str] = "agent.ArtificialGateway"

    def get_ss58_address(self, key_name: str):
        local_keys = local_key_addresses()
        if not key_name:
            raise ValueError("No key_name provided")
        return local_keys[key_name]

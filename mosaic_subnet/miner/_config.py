from communex.compat.key import local_key_addresses
from mosaic_subnet.base.base import ModuleSettings


class MinerSettings(ModuleSettings):
    """Configuration settings for the basic Miner."""

    key_name: str = "agent.ArtificialMiner"
    module_path: str = "agent.ArtificialMiner"
    host: str = "0.0.0.0"
    port: int = 8888
    use_testnet: bool = False
    model: str = "Lykon/dreamshaper-xl-v2-turbo"

    def get_ss58_address(self, key_name: str):
        local_keys = local_key_addresses()
        return local_keys[key_name]

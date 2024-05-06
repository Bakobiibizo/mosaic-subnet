from pydantic_settings import BaseSettings
from communex.compat.key import local_key_addresses


class MinerSettings(BaseSettings):
    """Configuration settings for the basic Miner."""

    host: str = "0.0.0.0"
    port: int = 8888
    model: str = "Lykon/dreamshaper-xl-v2-turbo"
    module_path: str = "agent.ArtificialMiner"
    key_name: str = "agent.ArtificialMiner"
    use_testnet: bool = False

    def get_ss58_address(self, key_name: str):
        local_keys = local_key_addresses()
        return local_keys[key_name]

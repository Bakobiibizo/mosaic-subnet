from mosaic_subnet.base._config import MosaicBaseSettings
from communex.compat.key import local_key_addresses


class ValidatorSettings(MosaicBaseSettings):
    iteration_interval: int = 60
    host: str = "0.0.0.0"
    port: int = 9090
    module_path: str = "validator.Validator"
    key_name: str = "module"

    def get_ss58_address(self, key_name: str):
        addresses = local_key_addresses()
        return addresses[key_name]

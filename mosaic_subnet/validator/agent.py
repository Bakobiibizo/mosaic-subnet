from ..validator import Validator
from ..validator.model import CLIP
from ..validator._config import ValidatorSettings
from communex.compat.key import Keypair

config = ValidatorSettings(
    host="66.226.79.190",
    port=50050,
    module_path="agent.ArtificialValidator",
    key_name="agent.ArtificialValidator",
    use_testnet=False,
)
ss58_address = config.get_ss58_address(config.key_name)

ArtificialValidator = Validator(key=Keypair(ss58_address=ss58_address), config=config)

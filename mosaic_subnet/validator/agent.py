from mosaic_subnet.validator.validator import Validator
from mosaic_subnet.validator._config import ValidatorSettings

settings = ValidatorSettings(
    key_name="agent.ArtificialValidator",
    module_path="validator.ArtificialValidator",
    host="0.0.0.0",
    port=7777,
    iteration_interval=60,
    use_testnet=True,
)


AritificialValidator = Validator(**settings.model_dump())

from mosaic_subnet.gateway.gateway import Gateway
from mosaic_subnet.gateway._config import GatewaySettings
from communex.compat.key import Keypair

settings = GatewaySettings(
    host="0.0.0.0",
    port=8080,
    module_path="agent.ArtificialGateway",
    key_name="agent.ArtificialGateway",
    use_testnet=False,
)
ss58_address = settings.get_ss58_address(str(settings.key_name))

ArtificialGateway = Gateway(key=Keypair(ss58_address=ss58_address), config=settings)

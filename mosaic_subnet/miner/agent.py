from dotenv import load_dotenv
from ._config import MinerSettings
from ..miner import Miner

load_dotenv()

config1 = MinerSettings(
    host="66.226.79.190",
    port=50051,
    module_path="agent.ArtificialMiner",
    key_name="agent.ArtificialMiner",
    use_testnet=False,
)
config2 = MinerSettings(
    host="66.226.79.190",
    port=50052,
    module_path="agent.ArtificialMiner_1",
    key_name="agent.ArtificialMiner_1",
    use_testnet=False,
)
config3 = MinerSettings(
    host="66.226.79.190",
    module_path="agent.ArtificialMiner_2",
    key_name="agent.ArtificialMiner_2",
    port=50053,
    use_testnet=False,
)

ArtificialMiner = Miner(**config1.model_dump())

ArtificialMiner_1 = Miner(**config2.model_dump())

ArtificialMiner_2 = Miner(**config3.model_dump())

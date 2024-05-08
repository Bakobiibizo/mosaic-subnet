from dotenv import load_dotenv
from mosaic_subnet.miner._config import MinerSettings
from mosaic_subnet.miner.miner import Miner

load_dotenv()

launch = {}
for i in range(1):
    config = MinerSettings(
        key_name=f"agent.ArtificialMiner_{i+1}",
        module_path=f"agent.ArtificialMiner_{i+1}",
        host="0.0.0.0",
        port=8888,
        use_testnet=False,
        model="Lykon/dreamshaper-xl-v2-turbo",
    )
    launch[f"config{i}"] = config

ArtificialMiner_1 = Miner(launch["config0"])

# ArtificialMiner_1 = Miner(launch["config2"])
#
# ArtificialMiner_2 = Miner(launch["config3"])

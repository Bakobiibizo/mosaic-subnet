from fastapi import FastAPI
import uvicorn
from loguru import logger
from typing import Optional

from communex.client import CommuneClient
from substrateinterface import Keypair
from communex.compat.key import classic_load_key
from communex._common import get_node_url
from communex.module.server import ModuleServer

from mosaic_subnet.miner.model import DiffUsers
from mosaic_subnet.miner._config import MinerSettings
from mosaic_subnet.base.utils import get_netuid


class Miner(DiffUsers):
    """Basic miner that generates images using the Huggingface Diffusers library."""

    def __init__(self, key: Keypair, config: Optional[MinerSettings] = None) -> None:
        """
        Initializes the Miner object with the provided key and configuration settings.

        Parameters:
            key (Keypair): The keypair used for the Miner.
            config (Optional[MinerSettings], optional): Configuration settings for the Miner. Defaults to None.

        Returns:
            None
        """
        super().__init__()
        self.settings: MinerSettings = config or MinerSettings()
        self.key: Keypair = key
        self.c_client = CommuneClient(
            url=get_node_url(use_testnet=self.settings.use_testnet)
        )
        self.netuid: int = get_netuid(client=self.c_client)

    def serve(self) -> None:
        """
        Starts the server and runs the FastAPI app.

        This function initializes a `ModuleServer` object with the current module, key, and a subnets whitelist
        containing the `netuid` attribute. It then retrieves the FastAPI app from the server and runs it using
        `uvicorn.run()`.

        Parameters:
            None

        Returns:
            None
        """
        server = ModuleServer(
            module=self, key=self.key, subnets_whitelist=[self.netuid]
        )
        app: FastAPI = server.get_fastapi_app()
        uvicorn.run(app=app, host=str(self.settings.host), port=int(self.settings.port))


if __name__ == "__main__":
    configuration = MinerSettings(
        host="0.0.0.0",
        port=7777,
        use_testnet=True,
    )
    Miner(key=classic_load_key(name="mosaic-miner0"), config=configuration).serve()

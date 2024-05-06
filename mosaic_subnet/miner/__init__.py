from fastapi import FastAPI
import uvicorn
from loguru import logger
from typing import Optional
import importlib
from importlib.util import module_for_loader
from communex.client import CommuneClient
from substrateinterface import Keypair
from communex.compat.key import classic_load_key
from communex._common import get_node_url
from communex.module.server import ModuleServer, Module

from ..miner.model import DiffUsers
from ..miner._config import MinerSettings
from ..base.utils import get_netuid


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
        self.module: Module = self.dynamic_import()
        self.c_client = CommuneClient(
            url=get_node_url(use_testnet=self.settings.use_testnet)
        )
        self.netuid: int = get_netuid(client=self.c_client)

    def dynamic_import(self) -> Module:
        try:
            module_name, class_name = self.settings.module_path.rsplit(
                sep=".", maxsplit=1
            )
            module: module_for_loader.ModuleType = importlib.import_module(
                name=f"mosaic_subnet/{module_name}"
            )
            module_class: Module = getattr(module, class_name)
        except (ImportError, AttributeError) as e:
            logger.error(e)
        except Exception as e:
            logger.error(e)
        return module_class

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
            module=self.module or self,
            key=self.key,
            subnets_whitelist=[self.netuid],
        )
        app: FastAPI = server.get_fastapi_app()
        uvicorn.run(app=app, host=str(self.settings.host), port=int(self.settings.port))


if __name__ == "__main__":
    configuration = MinerSettings(
        host="0.0.0.0",
        port=7777,
        use_testnet=True,
        key_name="module",
        module_path="miner.Miner",
    )
    Miner(
        key=classic_load_key(name=configuration.key_name), config=configuration
    ).serve()

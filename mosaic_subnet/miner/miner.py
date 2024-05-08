from fastapi import FastAPI
import uvicorn
from communex.client import CommuneClient
from substrateinterface import Keypair
from communex._common import get_node_url
from communex.module.server import ModuleServer, endpoint
from communex.compat.key import Keypair
from mosaic_subnet.base.base import BaseValidator
from mosaic_subnet.miner.diffusers_module import DiffusersModule
from mosaic_subnet.miner._config import MinerSettings, ModuleSettings


class Miner(BaseValidator, DiffusersModule):
    """Basic miner that generates images using the Huggingface Diffusers library."""

    art_model_name: str = "Lykon/dreamshaper-xl-v2-turbo"
    _Module__endpoints: ModuleServer

    def __init__(
        self,
        config=MinerSettings(
            key_name="miner.Miner",
            module_path="miner.Miner",
            host="0.0.0.0",
            port=8888,
            use_testnet=True,
            model="Lykon/dreamshaper-xl-v2-turbo",
        ),
    ) -> None:
        """
        Initializes the Miner object with the provided key and configuration settings.

        Parameters:
            key (Keypair): The keypair used for the Miner.
            config (Optional[MinerSettings], optional): Configuration settings for the Miner. Defaults to None.

        Returns:
            None
        """
        settings = ModuleSettings(
            key_name=config.key_name,
            module_path=config.module_path,
            host=config.host,
            port=config.port,
            use_testnet=config.use_testnet,
        )
        super().__init__(
            settings=settings,
        )
        self._Module__endpoints
        self.settings: MinerSettings = config or MinerSettings()

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
            module=self.dynamic_import() or self,
            key=Keypair(self.settings.get_ss58_address(self.settings.key_name)),
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
    Miner(config=configuration).serve()

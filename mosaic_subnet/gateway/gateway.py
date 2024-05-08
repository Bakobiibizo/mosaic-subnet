import time
import threading
import uvicorn
import random
import importlib
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from substrateinterface import Keypair
from loguru import logger
from typing import Optional

from communex.types import Ss58Address
from communex.client import CommuneClient
from communex._common import get_node_url

from mosaic_subnet.base.base import BaseValidator
from mosaic_subnet.base._config import SampleInput
from mosaic_subnet.gateway._config import GatewaySettings


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MOSAIC_MODULE_KEY = "5DofQSnXnWjF1VUzYVzTQV658GeBExrVFEQ5B4k8Tr1LcBzb"
MOSAIC_NETUID = 14

configuration = GatewaySettings()


class Gateway(BaseValidator):
    """Base class for the Gateway Validator/"""

    def __init__(
        self, key: Optional[Keypair], config: Optional[GatewaySettings]
    ) -> None:
        """
        Initializes a new instance of the Gateway class.

        Parameters:
            key (Keypair): The keypair used for the Gateway.
            config (GatewaySettings): The configuration settings for the Gateway. If not provided, default settings will be used.

        Returns:
            None
        """
        super().__init__()
        self.settings = config or GatewaySettings()
        self.c_client = CommuneClient(
            url=get_node_url(use_testnet=self.settings.use_testnet)
        )
        self.key: Keypair = key
        self.netuid = MOSAIC_NETUID
        self.call_timeout: int = self.settings.call_timeout
        self.top_miners = {}
        self.sync()
        self._loop_thread = None
        self.ss58_address = self.settings.get_ss58_address("agent.ArtificialGateway")

    def dynamic_import(self):
        try:
            module_name, class_name = str(self.settings.module_path).rsplit(
                sep=".", maxsplit=1
            )
            module = importlib.import_module(name=f"mosaic_subnet/{module_name}")
            module_class = getattr(module, class_name)
        except Exception as e:
            logger.error(e)
        return module_class

    def sync(self):
        """
        Synchronizes the top miners by fetching the weights of the miners and selecting the top 16.

        This function logs a message using the logger with the information "fetch top miners".
        It then calls the `get_top_weights_miners` method to fetch the weights of the miners.
        The `get_top_weights_miners` method takes an integer parameter `k` which specifies the number of top miners to select.
        The function assigns the result of `get_top_weights_miners(16)` to the `top_miners` attribute.

        Parameters:
            self (Gateway): The instance of the Gateway class.

        Returns:
            None
        """
        logger.info("fetch top miners")
        self.top_miners = self.get_top_weights_miners(16)

    def sync_loop(self):
        """
        Continuously synchronizes the top miners by periodically fetching the weights of the miners and selecting the top 16.

        This function runs in a loop, sleeping for 300 seconds (5 minutes) between each synchronization.
        It calls the `sync` method to fetch the weights of the miners and select the top 16.

        Parameters:
            self (Gateway): The instance of the Gateway class.

        Returns:
            None
        """
        while True:
            time.sleep(300)
            self.sync()

    def start_sync_loop(self):
        """
        Starts a synchronization loop in a separate thread.

        This function initializes a new thread and starts the synchronization loop.
        The loop periodically fetches the weights of the miners and selects the top 16.
        The loop runs indefinitely until the program is terminated.

        Parameters:
            self (object): The instance of the class.

        Returns:
            None
        """
        logger.info("start sync loop")
        self._loop_thread = threading.Thread(target=self.sync_loop, daemon=True)
        self._loop_thread.start()

    def get_top_miners(self):
        """
        Returns the top miners selected by the Gateway.

        :return: A dictionary containing the top miners selected by the Gateway. The keys are the module IDs, and the values are tuples containing the IP address and SS58 address of the miner.
        :rtype: dict[int, tuple[list[str], Ss58Address]]
        """
        return self.top_miners


@app.post(
    "/generate",
    responses={200: {"content": {"image/png": {}}}},
    response_class=Response,
)
def generate_image(req: SampleInput):
    """
    Generates an image based on the given request.

    This function is a POST endpoint that generates an image based on the provided request. It takes a `SampleInput` object as input and returns a `Response` object containing the generated image in PNG format.

    Parameters:
        req (SampleInput): The request object containing the input data for generating the image.

    Returns:
        Response: The response object containing the generated image in PNG format.

    Raises:
        None

    """
    config = GatewaySettings()
    gateway = Gateway(key=config.key_name, config=config)  # type: ignore
    miners: dict[int, tuple[list[str], Ss58Address]] = gateway.get_queryable_miners()
    result = b""
    for _ in range(10):
        mid = random.choice(list(miners.keys()))
        module: tuple[list[str], Ss58Address] = miners[mid]
        result = gateway.get_miner_generation(miner_info=module, miner_input=req)
        if result:
            break
    return Response(content=result, media_type="image/png")


if __name__ == "__main__":
    settings = GatewaySettings(
        host="0.0.0.0",
        port=8080,
        use_testnet=True,
        key_name="agent.ArtificialGateway",
        module_path="agent.ArtificialGateway",
    )
    validator = Gateway(key=settings.ss58Address, config=settings)  # type: ignore
    validator.start_sync_loop()
    uvicorn.run(app=app, host=settings.host, port=settings.port)  # type: ignore

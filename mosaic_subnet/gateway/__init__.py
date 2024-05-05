import random
import time
import threading
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from substrateinterface import Keypair
from loguru import logger

from communex.client import CommuneClient
from communex._common import get_node_url
from communex.compat.key import classic_load_key

from mosaic_subnet.base.utils import (
    get_netuid,
)
from mosaic_subnet.base import SampleInput, BaseValidator
from mosaic_subnet.gateway._config import GatewaySettings


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Gateway(BaseValidator):
    """Base class for the Gateway Validator/"""

    def __init__(self, key: Keypair, config: GatewaySettings) -> None:
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
            get_node_url(use_testnet=self.settings.use_testnet)
        )
        self.key = key
        self.netuid = get_netuid(self.c_client)
        self.call_timeout = self.settings.call_timeout
        self.top_miners = {}
        self.sync()
        self._loop_thread = None

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


def get_validator(validator_name="mosaic-validator0") -> Gateway:
    """
    Returns a Gateway object for the validator with the given name.

    Parameters:
        validator_name (str): The name of the validator. Defaults to "mosaic-validator0".

    Returns:
        Gateway: The Gateway object for the validator.
    """
    return Gateway(key=classic_load_key(name=validator_name), config=GatewaySettings())


validator: Gateway = get_validator()


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
    result = b""
    for _ in range(3):
        top_miners = validator.get_top_miners()
        mid = random.choice(list(top_miners.keys()))
        module = top_miners[mid]
        result = validator.get_miner_generation(module, req)
        if result:
            break
    return Response(content=result, media_type="image/png")


if __name__ == "__main__":
    settings = GatewaySettings(
        host="0.0.0.0",
        port=8080,
        use_testnet=True,
    )
    validator = Gateway(key=classic_load_key("mosaic-validator0"), config=settings)
    validator.start_sync_loop()
    uvicorn.run(app=app, host=settings.host, port=settings.port)

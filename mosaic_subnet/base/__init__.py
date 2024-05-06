import asyncio
import base64
from typing import Optional
import heapq
from operator import itemgetter

from loguru import logger

from substrateinterface import Keypair
from communex.client import CommuneClient
from communex.module.client import ModuleClient
from communex._common import get_node_url
from communex.types import Ss58Address
from .utils import get_ip_port
from pydantic import BaseModel


class SampleInput(BaseModel):
    """Model for sample input."""

    prompt: str
    negative_prompt: str = ""
    steps: int = 10
    seed: Optional[int] = None


class BaseValidator:
    """Base validator class to inherit."""

    def __init__(self) -> None:
        """
        Initializes the BaseValidator object with a default call timeout of 60 seconds.
        """
        self.call_timeout = 60
        self.c_client = CommuneClient(url=get_node_url(use_testnet=False))
        self.netuid = 14
        self.key = ""
        self.ss58_address: Ss58Address

    def get_miner_generation(
        self,
        miner_info: tuple[list[str], Ss58Address],
        miner_input: SampleInput,
    ) -> bytes:
        """
        Get the generated image from a miner based on the provided input.

        Args:
            miner_info (tuple[list[str], Ss58Address]): A tuple containing the connection information (module IP and port) and the miner's key.
            input (SampleInput): The input data for generating the image.

        Returns:
            bytes: The generated image as bytes. Returns None if an exception occurs.

        Raises:
            None

        Description:
            This function sends a request to a miner to generate an image based on the provided input. It connects to the miner using the module IP and port, and sends a "sample" request with the input data. The generated image is then decoded from base64 and returned. If an exception occurs during the process, the function logs the error and returns None.
        """
        try:
            connection, miner_key = miner_info
            self.key = Keypair(ss58_address=miner_key)
            self.ss58_address = miner_key
            module_ip, module_port = connection
            logger.debug("call", module_ip, module_port)
            client = ModuleClient(
                host=module_ip,
                port=int(module_port),
                key=Keypair(ss58_address=miner_key),
            )
            result = asyncio.run(
                main=client.call(
                    fn="sample",
                    target_key=miner_key,
                    params=miner_input.model_dump(),
                    timeout=self.call_timeout,
                )
            )
        except ValueError as e:
            logger.error(e)
        return base64.b64decode(result)

    def get_queryable_miners(self) -> dict[int, tuple[list[str], Ss58Address]]:
        """
        Retrieves the queryable miners in the current subnet.

        Returns:
            dict[int, tuple[list[str], Ss58Address]]: A dictionary mapping module IDs to tuples containing the module's
            addresses and the corresponding SS58 address.

        Raises:
            RuntimeError: If the validator key is not registered in the subnet.
        """
        modules_addresses: dict[int, str] = self.c_client.query_map_address(
            netuid=self.netuid
        )
        modules_keys: dict[int, Ss58Address] = self.c_client.query_map_key(
            netuid=self.netuid
        )
        val_ss58 = self.key.ss58_address
        if val_ss58 not in modules_keys.values():
            raise RuntimeError(f"validator key {val_ss58} is not registered in subnet")
        modules_info: dict[int, tuple[list[str], Ss58Address]] = {}

        modules_filtered_address: dict[int, list[str]] = get_ip_port(
            modules_addresses=modules_addresses
        )
        for module_id in modules_keys.keys():
            if module_id == 0:  # skip master
                continue
            if modules_keys[module_id] == val_ss58:  # skip yourself
                continue
            module_addr: list[str] | None = modules_filtered_address.get(
                module_id, None
            )
            if not module_addr:
                continue
            modules_info[module_id] = (module_addr, modules_keys[module_id])
        return modules_info

    def get_top_weights_miners(
        self, k: int
    ) -> dict[int, tuple[list[str], Ss58Address]]:
        """
        Retrieves the top `k` miners with the highest weights in the current subnet.

        Parameters:
            k (int): The number of top miners to retrieve.

        Returns:
            dict[int, tuple[list[str], Ss58Address]]: A dictionary mapping module IDs to tuples containing the module's
            addresses and the corresponding SS58 address.

        Raises:
            RuntimeError: If the validator key is not registered in the subnet.
        """
        modules_weights: dict[int, list[int]] = self.c_client.query_map_weights(
            netuid=self.netuid
        )
        weight_map = {}
        for uid, score in modules_weights.items():
            v = weight_map.get(uid, 0)
            score_total = 0
            for s in score:
                score_total += s[1]
            logger.debug(weight_map)
            weight_map[uid] = v + score_total
        candidates = heapq.nlargest(n=k, iterable=weight_map.items(), key=itemgetter(1))

        modules_addresses: dict[int, str] = self.c_client.query_map_address(
            netuid=self.netuid
        )
        modules_keys: dict[int, Ss58Address] = self.c_client.query_map_key(
            netuid=self.netuid
        )
        val_ss58 = self.key.ss58_address
        if val_ss58 not in modules_keys.values():
            raise RuntimeError(f"validator key {val_ss58} is not registered in subnet")
        modules_info: dict[int, tuple[list[str], Ss58Address]] = {}

        modules_filtered_address: dict[int, list[str]] = get_ip_port(
            modules_addresses=modules_addresses
        )
        for module_id, weight in candidates:
            if modules_keys[module_id] == val_ss58:  # skip yourself
                continue
            module_addr: list[str] | None = modules_filtered_address.get(
                module_id, None
            )
            if not module_addr:
                continue
            modules_info[module_id] = (module_addr, modules_keys[module_id])
        return modules_info

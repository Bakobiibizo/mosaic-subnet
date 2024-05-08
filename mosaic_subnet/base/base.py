import asyncio
import base64
import importlib
import re
from re import Match
from typing import Optional
from pydantic import BaseModel
from substrateinterface import Keypair
from loguru import logger
from communex.client import CommuneClient
from communex.module.client import ModuleClient
from communex._common import get_node_url
from communex.types import Ss58Address
from communex.compat.key import local_key_addresses

from mosaic_subnet.base._config import SampleInput, BaseMosaic

IP_REGEX: re.Pattern[str] = re.compile(
    pattern=r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+"
)


class ModuleSettings(BaseMosaic):
    """Model for module settings."""

    class Config:
        arbitrary_types_allowed = True

    def get_ss58_address(self, key_name: str):
        """
        Retrieves the SS58 address associated with the given key name.

        Parameters:
            key_name (str): The name of the key.

        Returns:
            str: The SS58 address corresponding to the key name.

        Raises:
            ValueError: If the key_name parameter is not provided.
        """
        local_keys = local_key_addresses()
        if not key_name:
            raise ValueError("No key_name provided")
        return local_keys[key_name]


class BaseValidator(BaseModel):
    """Base validator class to inherit."""

    settings: ModuleSettings
    c_client: CommuneClient = CommuneClient(url=get_node_url(use_testnet=False))
    call_timeout: int = 60
    netuid: int = 14

    class Config:
        arbitrary_types_allowed = True
        json_schema_extra = {
            "example": {
                "key_name": "validator.Validator",
                "module_path": "validator.Validator",
                "host": "0.0.0.0",
                "port": 50050,
                "use_testnet": False,
            }
        }

    def __init__(self, settings: ModuleSettings) -> None:
        """
        Initializes the BaseValidator object with a default call timeout of 60 seconds.
        """
        super().__init__(settings=settings.model_dump())
        self.settings = settings

    def dynamic_import(self, module_prefix: str = "mosaic_subnet.miner"):
        module_name, class_name = self.settings.module_path.rsplit(sep=".", maxsplit=1)
        try:
            module = importlib.import_module(name=f"{module_prefix}.{module_name}")
            return getattr(module, class_name)
        except ImportError as e:
            logger.error(f"Module not found: {e}")

    def get_miner_generation(
        self,
        miner_list: tuple[list[str], Ss58Address],
        miner_input: SampleInput,
    ) -> bytes:
        """
        A function to calculate the miner generation based on the provided miner list and input.

        Args:
            self: The instance of the class.
            miner_list: A tuple containing a list of miner connections and an Ss58Address.
            miner_input: The sample input for the miner.

        Returns:
            Bytes: The miner generation calculated based on the input.
        """
        miner_conection, miner_ss58_address = miner_list
        module_host, module_port = miner_conection
        logger.debug("call", module_host, module_port)
        try:
            client = ModuleClient(
                host=module_host,
                port=int(module_port),
                key=Keypair(ss58_address=miner_ss58_address),
            )
            result = asyncio.run(
                main=client.call(
                    fn="sample",
                    target_key=miner_ss58_address,
                    params=miner_input,
                    timeout=self.call_timeout,
                )
            )
        except ValueError as e:
            logger.error(e)
        return base64.b64decode(result)

    def get_queryable_miners(self):
        """
        Retrieves queryable miners and their information based on the netuid and self attributes.

        :return: A dictionary containing the information of queryable miners. The keys are module IDs, and the values are dictionaries
                 with 'netuid', 'ss58_address', 'host', and 'port' information.
        :rtype: dict[int, dict[str, Union[int, str]]]
        """
        try:
            module_addresses = self.c_client.query_map_address(netuid=self.netuid)
            module_keys = self.c_client.query_map_key(netuid=self.netuid)
            if module_addresses:
                module_addresses = dict(module_addresses.items())
            if module_keys:
                modules_keys = dict(module_keys.items())
            module_dict = {}
            modules_filtered_address = self.get_ip_port(
                modules_addresses=module_addresses
            )
            for module_id, ss58_address in modules_keys.items():
                module_info = {}
                if module_id == 0:  # skip master
                    continue
                if ss58_address == self.settings.get_ss58_address(
                    str(self.settings.key_name)
                ):  # skip yourself
                    continue
                if ss58_addr := modules_filtered_address.get(module_id):
                    module_info["netuid"] = module_id
                    module_info["ss58_address"] = ss58_addr
                module_host_address = module_addresses[module_id]
                if module_host_address := modules_filtered_address.get(module_id):
                    if ":" in module_host_address:
                        host, port = module_host_address[module_id].split(":")
                        module_info["host"] = host
                        module_info["port"] = port
                module_dict[module_id] = module_info
            return module_dict
        except RuntimeError as e:
            logger.error(e)

    def score_miner(self, module_info):
        """
        Calculates the score for a miner based on their module information.

        Args:
            module_info (dict): A dictionary containing the module information of the miner.
                It should have the following keys:
                - "netuid" (int): The netuid of the miner.
                - "ss58_address" (str): The ss58 address of the miner.

        Returns:
            dict: A dictionary containing the module information of the miner, including the weight.
                The dictionary has the following structure:
                - "netuid" (int): The netuid of the miner.
                - "weight" (float): The weight of the miner.

        Raises:
            RuntimeError: If the ss58_address of the miner is not registered in the subnet.
        """
        netuid = module_info["netuid"]
        weights_dict = self.c_client.query_map_weights(netuid=netuid)
        ss58_key = module_info["ss58_address"]
        if ss58_key not in weights_dict:
            raise RuntimeError(f"validator key {ss58_key} is not registered in subnet")
        modules_info = {}
        weights = weights_dict[ss58_key]
        if netuid in modules_info:
            modules_info[netuid]["weight"] += weights
        else:
            modules_info[netuid] = {"weight": weights}
        return modules_info

    def get_validate_input(self):
        raise NotImplementedError

    @staticmethod
    def extract_address(string: str) -> re.Match[str] | None:
        """
        Extracts an address from a string.
        """
        return re.search(pattern=IP_REGEX, string=string)

    @staticmethod
    def get_netuid(client: CommuneClient, subnet_name: str = "mosaic") -> int:
        """
        Get the netuid associated with a given subnet name.

        Args:
            client (CommuneClient): The commune client object.
            subnet_name (str, optional): The name of the subnet. Defaults to "mosaic".

        Returns:
            int: The netuid associated with the subnet name.

        Raises:
            ValueError: If the subnet name is not found.
        """
        subnets: dict[int, str] = client.query_map_subnet_names()
        for netuid, name in subnets.items():
            if name == subnet_name:
                logger.info("use netuid:", netuid)
                return netuid
        raise ValueError(f"Subnet {subnet_name} not found")

    @staticmethod
    def get_ip_port(modules_addresses: dict[int, str]) -> dict[int, list[str]]:
        """
        Get the IP addresses and ports from a dictionary of module addresses.

        Args:
            modules_addresses (dict[int, str]): A dictionary mapping module IDs to their addresses.

        Returns:
            dict[int, list[str]]: A dictionary mapping module IDs to a list of IP addresses and ports.

        Raises:
            None

        Examples:
            >>> modules_addresses = {1: "192.168.0.1:8080", 2: "10.0.0.1:9090"}
            >>> get_ip_port(modules_addresses)
            {1: ["192.168.0.1", "8080"], 2: ["10.0.0.1", "9090"]}
        """
        filtered_addr: dict[int, Match[str] | None] = {
            id: BaseValidator.extract_address(string=addr)
            for id, addr in modules_addresses.items()
        }
        ip_port: dict[int, list[str]] = {
            id: x.group(0).split(":")
            for id, x in filtered_addr.items()
            if x is not None
        }
        return ip_port

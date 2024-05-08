import time
import asyncio
import concurrent.futures

from functools import partial
from loguru import logger
from typing import Iterator, Literal, Optional
from substrateinterface import Keypair

from communex.module.module import Module
from communex.client import CommuneClient
from communex._common import get_node_url
from communex.compat.key import classic_load_key

from mosaic_subnet.base.base import ModuleSettings
from mosaic_subnet.base._config import SampleInput
from mosaic_subnet.validator.model import CLIP

from mosaic_subnet.validator.dataset import ValidationDataset
from mosaic_subnet.validator.sigmoid import threshold_sigmoid_reward_distribution
from mosaic_subnet.base.base import BaseValidator

configuration = ModuleSettings(
    key_name="validator.Validator",
    module_path="validator.Validator",
    host="0.0.0.0",
    port=50050,
    call_timeout=60,
    use_testnet=True,
)


class Validator(BaseValidator, Module):
    """Validator class for classification of miner images."""

    def __init__(self, key: Keypair, config) -> None:
        """
        Initializes a new instance of the Validator class.

        Parameters:
            key (Keypair): The keypair used for the Validator.
            config (ValidatorSettings): The configuration settings for the Validator. If not provided, default settings will be used.

        Returns:
            None
        """
        super().__init__(settings=config)
        self.settings = config
        self.key: Keypair = key
        self.module = self.dynamic_import()
        self.c_client = CommuneClient(
            url=get_node_url(use_testnet=self.settings.use_testnet)
        )
        self.netuid = self.get_netuid(client=self.c_client)
        self.dataset = ValidationDataset()
        self.call_timeout: int = 60
        self.iteration_interval: int = 5
        self.module = self.dynamic_import()

    async def validate_step(self) -> None:
        score_dict: dict[int, float] = {}
        modules_info = self.get_queryable_miners()

        validation_input: SampleInput = self.get_validate_input()
        logger.debug("input:", validation_input)
        get_miner_generation = partial(self.get_miner_generation)
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            if not modules_info:
                return
            it: Iterator[bytes] = executor.map(
                get_miner_generation, modules_info.values()
            )
            miner_answers: list[bytes] = [*it]

        for uid, miner_response in zip(modules_info.keys(), miner_answers):
            miner_answer: bytes = miner_response
            if not miner_answer:
                logger.debug(f"Skipping miner {uid} that didn't answer")
                continue
            score: float | Literal[0] = self.calculate_score(miner_answer, input.prompt)
            score_dict[uid] = score

        if not score_dict:
            logger.info("score_dict empty, skip set weights")
            return
        logger.debug("original scores:", score_dict)
        adjusted_to_sigmoid: dict[int, float] = threshold_sigmoid_reward_distribution(
            score_dict=score_dict
        )
        logger.debug("sigmoid scores:", adjusted_to_sigmoid)
        # Create a new dictionary to store the weighted scores
        weighted_scores: dict[int, int] = {}

        # Calculate the sum of all inverted scores
        scores: float | Literal[0] = sum(adjusted_to_sigmoid.values())

        # Iterate over the items in the score_dict
        for uid, score in adjusted_to_sigmoid.items():
            # Calculate the normalized weight as an integer
            weight = int(score * 1000 / scores)

            # Add the weighted score to the new dictionary
            weighted_scores[uid] = weight

        # filter out 0 weights
        weighted_scores = {k: v for k, v in weighted_scores.items() if v != 0}
        logger.debug("weighted scores:", weighted_scores)
        if not weighted_scores:
            logger.info("weighted_scores empty, skip set weights")
            return
        try:
            uids = list(weighted_scores.keys())
            weights = list(weighted_scores.values())
            logger.info("Setting weights for {count} uids", count=len(uids))
            logger.debug(f"Setting weights for the following uids: {uids}")
            self.c_client.vote(
                key=self.key, uids=uids, weights=weights, netuid=self.netuid
            )
        except ValueError as e:
            logger.error(e)

    def get_validate_input(self) -> SampleInput:
        """
        Returns a SampleInput object with a random prompt from the dataset and 2 steps.
        """
        return SampleInput(prompt=self.dataset.random_prompt())

    def calculate_score(self, miner_answer: bytes, prompt: str) -> float:
        return self.module.get_similarity(miner_answer, prompt)

    def validation_loop(self) -> None:
        while True:
            start_time: float = time.time()
            asyncio.run(self.validate_step())
            elapsed: float = time.time() - start_time
            if elapsed < self.iteration_interval:
                sleep_time: float = self.iteration_interval - elapsed
                logger.info(f"Sleeping for {sleep_time}")
                time.sleep(sleep_time)


if __name__ == "__main__":
    settings = MosaicBaseSettings(use_testnet=True)
    Validator(
        key=classic_load_key(name="validator.Validator"), config=settings
    ).validation_loop()

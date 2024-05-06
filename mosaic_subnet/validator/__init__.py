import time
import asyncio
import concurrent.futures

from functools import partial
from loguru import logger
from typing import Iterator, Literal
from substrateinterface import Keypair
import importlib
from importlib.util import module_for_loader

from communex.module.module import Module
from communex.client import CommuneClient
from communex._common import get_node_url
from communex.types import Ss58Address
from communex.compat.key import classic_load_key

from ..validator._config import ValidatorSettings
from ..validator.model import CLIP
from ..base.utils import get_netuid
from ..base import SampleInput, BaseValidator
from ..validator.dataset import ValidationDataset
from ..validator.sigmoid import threshold_sigmoid_reward_distribution


class Validator(BaseValidator, Module):
    """Validator class for classification of miner images."""

    def __init__(self, key: Keypair, config: ValidatorSettings) -> None:
        """
        Initializes a new instance of the Validator class.

        Parameters:
            key (Keypair): The keypair used for the Validator.
            config (ValidatorSettings): The configuration settings for the Validator. If not provided, default settings will be used.

        Returns:
            None
        """
        super().__init__()
        self.settings: ValidatorSettings = config or ValidatorSettings()
        self.key: Keypair = key
        self.module = self.dynamic_import()
        self.c_client = CommuneClient(
            url=get_node_url(use_testnet=self.settings.use_testnet)
        )
        self.netuid = get_netuid(client=self.c_client)
        self.dataset = ValidationDataset()
        self.call_timeout: int = self.settings.call_timeout

    def dynamic_import(self):
        try:
            module_name, class_name = self.settings.module_path.rsplit(
                sep=".", maxsplit=1
            )
            module = importlib.import_module(name=f"mosaic_subnet/{module_name}")
            module_class: Module = getattr(module, class_name)
            return module_class
        except Exception as e:
            logger.error(e)

    def calculate_score(self, img: bytes, prompt: str) -> float | Literal[0]:
        """
        Calculates the score based on the similarity between the input image and a prompt text.

        Parameters:
            img (bytes): The input image as a byte string.
            prompt (str): The prompt text.

        Returns:
            float | Literal[0]: The calculated score representing the similarity, or 0 if an exception occurs.
        """
        try:
            self.model = CLIP()
            return self.model.get_similarity(file=img, prompt=prompt)
        except ValueError:
            return 0

    async def validate_step(self) -> None:
        """
        Validates a step by querying multiple miners and setting weights based on the similarity between their generated images and a prompt text.

        This function performs the following steps:
        1. Retrieves the queryable miners' information.
        2. Retrieves the validation input.
        3. Generates the image generation task for each miner using a partial function.
        4. Executes the image generation tasks concurrently using a ThreadPoolExecutor.
        5. Calculates the similarity score between each miner's generated image and the prompt text for each miner.
        6. Adjusts the similarity scores to a sigmoid distribution.
        7. Calculates the weighted scores based on the adjusted similarity scores.
        8. Sets the weights for each miner using the CommuneClient.

        Parameters:
            None

        Returns:
            None

        Raises:
            ValueError: If there is an error setting the weights.

        """
        score_dict = dict()
        modules_info = self.get_queryable_miners()

        validation_input: SampleInput = self.get_validate_input()
        logger.debug("input:", validation_input)
        get_miner_generation = partial(
            self.get_miner_generation, input=validation_input
        )
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
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
        Returns a SampleInput object with a randomly selected prompt from the dataset and 2 steps.

        :return: A SampleInput object.
        :rtype: SampleInput
        """
        return SampleInput(
            prompt=self.dataset.random_prompt(),
            steps=2,
        )

    def validation_loop(self) -> None:
        """
        Runs a validation loop indefinitely.

        This function continuously runs a validation loop, executing the `validate_step` method asynchronously.
        The loop runs until the program is terminated.

        Parameters:
            self (object): The instance of the class.

        Returns:
            None
        """
        while True:
            start_time: float = time.time()
            asyncio.run(self.validate_step())
            elapsed: float = time.time() - start_time
            if elapsed < self.settings.iteration_interval:
                sleep_time: float = self.settings.iteration_interval - elapsed
                logger.info(f"Sleeping for {sleep_time}")
                time.sleep(sleep_time)


if __name__ == "__main__":
    settings = ValidatorSettings(use_testnet=True)
    Validator(
        key=classic_load_key(name="validator.Validator"), config=settings
    ).validation_loop()

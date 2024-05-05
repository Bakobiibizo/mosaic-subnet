from datasets import load_dataset, Dataset
from random import randint


class ValidationDataset:
    """Dataset loader for the validator."""

    def __init__(self) -> None:
        """
        Initializes the ValidationDataset object.

        This function initializes the ValidationDataset object by loading the dataset using the
        `load_dataset` function from the `datasets` library. The dataset is loaded from the
        "FredZhang7/stable-diffusion-prompts-2.47M" dataset collection.

        Parameters:
            None

        Returns:
            None
        """
        self.dataset = load_dataset("FredZhang7/stable-diffusion-prompts-2.47M")

    def random_prompt(self) -> str:
        """
        Retrieves a random prompt from the dataset.

        Returns:
            str: The randomly selected prompt from the dataset.

        Raises:
            ValueError: If the dataset is not loaded as a dictionary or a Dataset object.
        """
        if isinstance(self.dataset, dict or isinstance(self.dataset, Dataset)):
            index: int = randint(0, len(self.dataset["train"]))
            return self.dataset["train"][index]["text"]
        else:
            raise ValueError("dataset was not loaded as a dict.")


if __name__ == "__main__":
    ValidationDataset()

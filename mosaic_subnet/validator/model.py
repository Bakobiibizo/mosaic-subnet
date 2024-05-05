from io import BytesIO

import torch
import torch.nn as nn
from PIL import Image
from transformers import CLIPProcessor, CLIPModel, BatchEncoding
from transformers import pipeline
from loguru import logger

from communex.module.module import Module
from transformers.pipelines.base import Pipeline


class CLIP(Module, nn.Module):
    """CLIP text encoding model for image classification."""

    def __init__(self, model_name: str = "openai/clip-vit-base-patch32") -> None:
        """
        Initializes the CLIP model with the specified model name.

        Args:
            model_name (str, optional): The name of the model to initialize. Defaults to "openai/clip-vit-base-patch32".

        Returns:
            None
        """
        super().__init__()
        self.model_name: str = model_name
        logger.info(self.model_name)

        self.device = torch.device(
            device="cuda" if torch.cuda.is_available() else "cpu"
        )

        self.model: CLIPModel = CLIPModel.from_pretrained(
            pretrained_model_name_or_path=model_name
        ).to(self.device)  # type: ignore

        self.processor = CLIPProcessor.from_pretrained(
            pretrained_model_name_or_path=model_name
        )
        if isinstance(self.processor, CLIPProcessor):
            self.processor.feature_extractor.do_center_crop = (
                False  # for embedding consistency do not crop.
            )

    def get_similarity(self, file: bytes, prompt: str) -> float:
        """
        Calculates the similarity between a generated image and a prompt text using the CLIP model.

        Args:
            file (bytes): The generated image as a byte string.
            prompt (str): The prompt text.

        Returns:
            float: The similarity score between the generated image and the prompt text.
        """
        generated_image: Image.Image = Image.open(BytesIO(initial_bytes=file))
        if isinstance(self.processor, CLIPProcessor):
            inputs = self.processor(
                text=prompt, images=generated_image, return_tensors="pt", padding=True
            ).to(self.device)
        outputs = self.model(**inputs)
        score = outputs.logits_per_image.sum().tolist() / 100
        return score

    def get_metadata(self) -> dict:
        """
        Returns a dictionary containing the metadata information about the model.

        :return: A dictionary with a single key-value pair, where the key is "model" and the value is the name of the model.
        :rtype: dict
        """
        return {"model": self.model_name}

    def forward(self, model_inputs, **forward_params):
        """
        Forward pass of the model.

        Args:
            model_inputs (dict): Inputs to the model.
            **forward_params: Additional parameters for the forward pass.

        Returns:
            model_outputs: Outputs of the model.

        Raises:
            ValueError: If the framework is not supported.

        This function performs the forward pass of the model. It takes in the model inputs and any additional parameters for the forward pass. It first checks the framework of the model and performs the forward pass accordingly. If the framework is "tf", it sets the "training" parameter of the model inputs to False and calls the private `_forward` method with the model inputs and the forward parameters. If the framework is "pt", it creates an inference context and ensures that the model inputs are on the specified device. It then calls the private `_forward` method with the model inputs and the forward parameters. Finally, it ensures that the model outputs are on the CPU device. If the framework is not supported, it raises a ValueError. The model outputs are then returned.

        Copied from the hugging face transformers library:
        # Copyright 2018 The HuggingFace Inc. team.
        # Licensed under the Apache License, Version 2.0 (the "License");
        # you may not use this file except in compliance with the License.
        # You may obtain a copy of the License at
        #             http://www.apache.org/licenses/LICENSE-2.0

        # Unless required by applicable law or agreed to in writing, software
        # distributed under the License is distributed on an "AS IS" BASIS,
        # WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
        # See the License for the specific language governing permissions and
        # limitations under the License.
        """
        with self.device_placement():
            if self.framework == "tf":
                model_inputs["training"] = False
                model_outputs = self._forward(model_inputs, **forward_params)
            elif self.framework == "pt":
                inference_context = self.get_inference_context()
                with inference_context():
                    model_inputs = self._ensure_tensor_on_device(
                        model_inputs, device=self.device
                    )
                    model_outputs = self._forward(model_inputs, **forward_params)
                    model_outputs = self._ensure_tensor_on_device(
                        model_outputs, device=torch.device("cpu")
                    )
            else:
                raise ValueError(f"Framework {self.framework} is not supported")
        return model_outputs


class NSFWChecker(Module):
    """Encoding model for NSFW classification."""

    def __init__(self) -> None:
        """
        Initializes the NSFWChecker class with the specified model and device.

        This method initializes the NSFWChecker class by setting the model name to "Falconsai/nsfw_image_detection"
        and determining the device to be used for classification based on the availability of a CUDA-enabled GPU.
        The classifier is then initialized using the specified task, model, and device.

        Parameters:
            None

        Returns:
            None
        """
        super().__init__()
        self.model_name = "Falconsai/nsfw_image_detection"
        self.device = torch.device(
            device="cuda" if torch.cuda.is_available() else "cpu"
        )
        self.classifier: Pipeline = pipeline(
            task="image-classification",
            model="Falconsai/nsfw_image_detection",
            device=self.device,
        )

    def check_nsfw(self, file: bytes) -> bool:
        """
        Checks if the given file is NSFW (Not Safe For Work) based on the classification results.

        Parameters:
            file (bytes): The image file in bytes format to be checked.

        Returns:
            bool: True if the image is classified as NSFW with a score higher than 0.8, False otherwise.
        """
        classified_image: Image.Image = Image.open(fp=BytesIO(initial_bytes=file))
        encoding = BatchEncoding(data={"image": classified_image})
        encoding.to(device=self.device)

        if isinstance(self.classifier, Pipeline):
            results = self.classifier.run_single(
                inputs=encoding,
                forward_params={"target": "nsfw"},
                postprocess_params={"threshold": 0.8},
                preprocess_params={"target": "nsfw"},
            )

        if results["label"] == "nsfw" and results["score"] > 0.8:
            return True
        return False


if __name__ == "__main__":
    import httpx

    resp = httpx.get("http://images.cocodataset.org/val2017/000000039769.jpg")
    image = resp.content
    c = CLIP()
    score_cat = c.get_similarity(file=image, prompt="cat")
    score_dog = c.get_similarity(file=image, prompt="dog")
    print(score_cat, score_dog)

    nc = NSFWChecker()
    is_nsfw = nc.check_nsfw(image)
    print(is_nsfw)

from io import BytesIO
from typing import Optional
import base64
from PIL.Image import Image


import torch
from diffusers.pipelines.auto_pipeline import AutoPipelineForText2Image
from diffusers.pipelines.stable_diffusion_xl.pipeline_stable_diffusion_xl import (
    StableDiffusionXLPipeline,
)
from torch import Generator

from communex.module.module import Module, endpoint


class DiffUsers(Module):
    """Implementation of the Diffusers pipeline from the Hugging Face library."""

    def __init__(self, model_name: str = "Lykon/dreamshaper-xl-v2-turbo") -> None:
        """
        Initializes the DiffUsers class with the specified model_name.

        Parameters:
            model_name (str, optional): The name of the model to use. Defaults to "Lykon/dreamshaper-xl-v2-turbo".

        Returns:
            None
        """
        super().__init__()
        self.model_name: str = model_name
        self.device = torch.device(device="cuda")
        self.pipeline: StableDiffusionXLPipeline = (
            AutoPipelineForText2Image.from_pretrained(
                pretrained_model_or_path=model_name,
                torch_dtype=torch.float16,
                variant="fp16",
            ).to(self.device)
        )

    @endpoint
    def sample(
        self,
        prompt: str,
        steps: int = 30,
        negative_prompt: str = "ugly, gross, deformed, unnatural, disfigured, poorly made, blurry",
        seed: Optional[int] = None,
    ) -> str:
        """
        This function samples an image based on the given prompt and negative prompt.

        Parameters:
            prompt (str): The main prompt for generating the image.
            steps (int, optional): The number of inference steps. Defaults to 30.
            negative_prompt (str, optional): The negative prompt for the image. Defaults to a set of negative adjectives.
            seed (Optional[int], optional): The seed for the random number generator. Defaults to None.

        Returns:
            str: The base64 encoded image in PNG format.
        """
        generator = torch.Generator(device=self.device)
        if seed is None:
            seed = generator.seed()
        generator: Generator = generator.manual_seed(seed=seed)
        image: Image = self.pipeline(
            prompt=prompt,
            negative_prompt=negative_prompt,
            num_inference_steps=steps,
            generator=generator,
            guidance_scale=0.0,
        ).images[0]  # type: ignore
        buf = BytesIO()
        image.save(buf, format="png")
        buf.seek(0)
        return base64.b64encode(s=buf.read()).decode()

    @endpoint
    def get_metadata(self) -> dict:
        """
        A function that returns metadata information about the model.

        Returns:
            dict: A dictionary containing the model name.
        """
        return {"model": self.model_name}


if __name__ == "__main__":
    d = DiffUsers()
    out: str = d.sample(prompt="cat, jumping")
    with open("a.png", "wb") as f:
        f.write(out.encode())

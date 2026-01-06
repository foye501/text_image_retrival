import os
from typing import Iterable, List, Optional, Union

import torch
from PIL import Image
from transformers import CLIPModel, CLIPProcessor


class ClipEmbedder:
    def __init__(
        self,
        model_name: str = "openai/clip-vit-large-patch14",
        device: Optional[str] = None,
    ) -> None:
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"

        self.device = device
        self.model_name = model_name
        self.model = CLIPModel.from_pretrained(model_name).to(device)
        self.processor = CLIPProcessor.from_pretrained(model_name)
        self.model.eval()

    def encode_text(self, texts: Iterable[str]) -> List[List[float]]:
        inputs = self.processor(text=list(texts), return_tensors="pt", padding=True)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        with torch.no_grad():
            embeddings = self.model.get_text_features(**inputs)
        embeddings = self._normalize(embeddings)
        return embeddings.cpu().tolist()

    def encode_image(
        self, images: Iterable[Union[str, Image.Image]]
    ) -> List[List[float]]:
        pil_images = [self._load_image(image) for image in images]
        inputs = self.processor(images=pil_images, return_tensors="pt", padding=True)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        with torch.no_grad():
            embeddings = self.model.get_image_features(**inputs)
        embeddings = self._normalize(embeddings)
        return embeddings.cpu().tolist()

    def _load_image(self, image: Union[str, Image.Image]) -> Image.Image:
        if isinstance(image, Image.Image):
            return image
        if isinstance(image, str):
            if not os.path.exists(image):
                raise FileNotFoundError(f"Image path not found: {image}")
            return Image.open(image).convert("RGB")
        raise TypeError("image must be a PIL.Image.Image or file path string")

    @staticmethod
    def _normalize(embeddings: torch.Tensor) -> torch.Tensor:
        return embeddings / embeddings.norm(p=2, dim=-1, keepdim=True)

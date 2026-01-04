from __future__ import annotations

from typing import Any, Dict, List, Optional

import weaviate


class WeaviateStore:
    def __init__(
        self,
        url: str,
        api_key: Optional[str] = None,
        class_name: str = "Streamer",
        timeout_config: tuple[int, int] = (5, 30),
    ) -> None:
        auth = weaviate.AuthApiKey(api_key) if api_key else None
        self.client = weaviate.Client(url=url, auth_client_secret=auth, timeout_config=timeout_config)
        self.class_name = class_name

    def ensure_schema(self) -> None:
        if self.client.schema.exists(self.class_name):
            return

        schema = {
            "class": self.class_name,
            "description": "Streamer image embeddings (CLIP, no vectorizer).",
            "vectorizer": "none",
            "properties": [
                {"name": "streamer_id", "dataType": ["string"]},
                {"name": "image_uri", "dataType": ["string"]},
            ],
        }
        self.client.schema.create_class(schema)

    def add_streamer(self, streamer_id: str, image_uri: str, vector: List[float]) -> str:
        data = {"streamer_id": streamer_id, "image_uri": image_uri}
        return self.client.data_object.create(data_object=data, class_name=self.class_name, vector=vector)

    def query_by_vector(self, vector: List[float], limit: int = 5) -> List[Dict[str, Any]]:
        query = (
            self.client.query.get(self.class_name, ["streamer_id", "image_uri"])
            .with_additional(["distance", "id"])
            .with_near_vector({"vector": vector})
            .with_limit(limit)
        )
        result = query.do()
        return result.get("data", {}).get("Get", {}).get(self.class_name, [])

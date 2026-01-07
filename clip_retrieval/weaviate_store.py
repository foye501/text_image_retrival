from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import weaviate
from weaviate.classes.config import Configure, DataType, Property
from weaviate.classes.query import Filter, MetadataQuery


class WeaviateStore:
    def __init__(
        self,
        url: str,
        api_key: Optional[str] = None,
        class_name: str = "Streamer",
        grpc_port: Optional[int] = None,
    ) -> None:
        parsed = urlparse(url)
        http_host = parsed.hostname or "localhost"
        http_secure = parsed.scheme == "https"
        if parsed.port is not None:
            http_port = parsed.port
        else:
            http_port = 443 if http_secure else 8080

        if grpc_port is None:
            grpc_port = 50052

        auth = weaviate.auth.AuthApiKey(api_key) if api_key else None
        self.client = weaviate.connect_to_custom(
            http_host=http_host,
            http_port=http_port,
            http_secure=http_secure,
            grpc_host=http_host,
            grpc_port=grpc_port,
            grpc_secure=http_secure,
            auth_credentials=auth,
        )
        self.class_name = class_name

    def ensure_schema(self) -> None:
        if self.client.collections.exists(self.class_name):
            return

        self.client.collections.create(
            name=self.class_name,
            description="Streamer image embeddings (CLIP, no vectorizer).",
            vectorizer_config=Configure.Vectorizer.none(),
            properties=[
                Property(name="streamer_id", data_type=DataType.TEXT),
                Property(name="image_uri", data_type=DataType.TEXT),
            ],
        )

    def add_streamer(self, streamer_id: str, image_uri: str, vector: List[float]) -> str:
        self.ensure_schema()
        data = {"streamer_id": streamer_id, "image_uri": image_uri}
        collection = self.client.collections.get(self.class_name)
        return str(collection.data.insert(properties=data, vector=vector))

    def query_by_vector(
        self,
        vector: List[float],
        limit: int = 5,
        streamer_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        self.ensure_schema()
        collection = self.client.collections.get(self.class_name)
        filters = None
        if streamer_id:
            filters = Filter.by_property("streamer_id").equal(streamer_id)
        results = collection.query.near_vector(
            near_vector=vector,
            limit=limit,
            return_properties=["streamer_id", "image_uri"],
            return_metadata=MetadataQuery(distance=True),
            filters=filters,
        )
        items = []
        for obj in results.objects:
            items.append(
                {
                    "streamer_id": obj.properties.get("streamer_id", ""),
                    "image_uri": obj.properties.get("image_uri", ""),
                    "_additional": {
                        "distance": obj.metadata.distance,
                        "id": str(obj.uuid),
                    },
                }
            )
        return items

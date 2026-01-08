# CLIP Retrieval API

Base URL:

```
http://159.135.196.86:12280/
```

## Add Streamer Image

`POST /streamers`

Content-Type: `multipart/form-data`

Fields:

- `streamer_id` (string)
- `image` (file, optional if `s3_key` provided)
- `s3_key` (string, optional if `image` provided)

Response:

```json
{
  "id": "uuid",
  "streamer_id": "streamer_001",
  "image_uri": "data/streamer_images/streamer_001.jpg"
}
```

Example:

```bash
curl -X POST "http://<host>:<port>/streamers" \
  -F "streamer_id=streamer_001" \
  -F "image=@/path/to/streamer_001.jpg"
```

Example (S3):

```bash
curl -X POST "http://<host>:<port>/streamers" \
  -F "streamer_id=streamer_001" \
  -F "s3_key=path/to/streamer_001.jpg"
```

## Delete Streamer Data

`POST /streamers/delete`

Body (at least one required):

```json
{"streamer_id":"streamer_001"}
```

Example:

```bash
curl -X POST "http://<host>:<port>/streamers/delete" \
  -H "Content-Type: application/json" \
  -d '{"s3_key":"path/to/streamer_001.jpg"}'
```

## Search by Text

`POST /search`

Content-Type: `application/json`

Body:

```json
{"text":"a streamer with neon background","limit":3,"streamer_id":"streamer_001"}
```

Response:

```json
[
  {
    "streamer_id": "streamer_001",
    "image_uri": "data/streamer_images/streamer_001.jpg",
    "distance": 0.75,
    "score": 0.25,
    "id": "uuid"
  }
]
```

Example:

```bash
curl -X POST "http://<host>:<port>/search" \
  -H "Content-Type: application/json" \
  -d '{"text":"a streamer with neon background","limit":3,"streamer_id":"streamer_001"}'
```

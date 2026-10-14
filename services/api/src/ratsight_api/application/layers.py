from ratsight_api.domain.layers import LAYER_CATALOG


def list_layers() -> list[dict[str, object]]:
    return [
        {
            "id": layer.layer_id,
            "label": layer.label,
            "available": False,
            "classification": layer.classification,
            "message": layer.message,
        }
        for layer in LAYER_CATALOG
    ]

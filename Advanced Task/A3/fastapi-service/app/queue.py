import json
import os


def _queue_dir() -> str:
    return os.environ.get("QUEUE_DIR", "./queue")


def enqueue(txn: dict) -> str:
    """Write the full transaction JSON to QUEUE_DIR/<transaction_id>.json.

    Returns the path of the written file.
    """
    queue_dir = _queue_dir()
    os.makedirs(queue_dir, exist_ok=True)
    path = os.path.join(queue_dir, f"{txn['transaction_id']}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(txn, f)
    return path

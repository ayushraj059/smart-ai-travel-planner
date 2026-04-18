import json
import os
from .dynamodb import batch_write_places, create_table_if_not_exists
from .config import settings


def load_all_cities() -> dict:
    data_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "data")
    )
    if not os.path.isdir(data_dir):
        data_dir = os.path.abspath(settings.data_dir)

    create_table_if_not_exists()

    results = {}
    for filename in os.listdir(data_dir):
        if not filename.endswith(".json"):
            continue
        filepath = os.path.join(data_dir, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            payload = json.load(f)

        city = payload.get("city", "")
        raw_data = payload.get("data", [])

        # Handle both flat list and nested dict (e.g. {attractions: [...], restaurants: [...]})
        if isinstance(raw_data, dict):
            raw_items = []
            for sub_list in raw_data.values():
                if isinstance(sub_list, list):
                    raw_items.extend(sub_list)
        else:
            raw_items = raw_data if isinstance(raw_data, list) else []

        valid_places = []
        for item in raw_items:
            if not isinstance(item, dict):
                continue
            if not item.get("name") or not item.get("category"):
                continue
            item["city"] = city
            valid_places.append(item)

        if valid_places:
            written = batch_write_places(valid_places)
            results[city] = {"total_in_file": len(raw_items), "written": written}

    return results

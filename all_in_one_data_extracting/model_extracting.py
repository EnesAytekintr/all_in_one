from huggingface_hub import HfApi
import logging, csv, os
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()

logging.getLogger("huggingface_hub").setLevel(logging.ERROR)

FIELDS = [
    "id",
    "author",
    "created_at",
    "last_modified",  
    "downloads",
    "likes",
    "pipeline_tag",
    "library_name",
    "gated",
    "private",
    "license",
    "base_model",
    "language",
    "datasets",
    "tags",
]

EXPAND = [
    "author", "createdAt", "lastModified", "downloads", "likes",
    "pipeline_tag", "library_name", "gated", "private", "tags", "cardData"
]

TOKEN = os.getenv("TOKEN")

api = HfApi(token=TOKEN)

def model_to_record(limit: int | None):
    models_gen = api.list_models(expand=EXPAND, sort="downloads")

    for _ in range(limit):
        try:
            model = next(models_gen)
        except StopIteration:
            break

        card = getattr(model, "card_data", None)

        tags = model.tags or []
        tags_str = ",".join(tags) if isinstance(tags, list) else str(tags)
        
        language = getattr(card, "language", None)
        lang_str = ",".join(language) if isinstance(language, list) else language

        datasets = getattr(card, "datasets", None)
        data_str = ",".join(datasets) if isinstance(datasets, list) else datasets

        yield {
            "id": model.id,
            "author": getattr(model, "author", None),
            "created_at": str(getattr(model, "created_at")),
            "last_modified": str(getattr(model, "last_modified")),
            
            "downloads": getattr(model, "downloads", 0),
            "likes": getattr(model, "likes", 0),
            
            "pipeline_tag": getattr(model, "pipeline_tag", None),
            "library_name": getattr(model, "library_name", None),
            "gated": getattr(model, "gated", "false"),
            "private": getattr(model, "private", False),
            
            "license": getattr(card, "license", None) if card else None,
            "base_model": getattr(card, "base_model", None) if card else None,
            "language": lang_str,
            "datasets": data_str,
            
            "tags": tags_str,
        }

def models_to_csv(csv_path: str, limit: int | None) -> int:
    dir_name = os.path.dirname(csv_path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)

    row_count = 0
    seen: set[str] = set()

    with open(csv_path, "w", encoding="utf-8", newline="") as c, tqdm(
        total=limit,
        unit=" model",
        desc="Fetching & Streaming to CSV",
        dynamic_ncols=True
    ) as bar:
        
        writer = csv.DictWriter(c, extrasaction="ignore", fieldnames=FIELDS)
        writer.writeheader()

        try:
            for record in model_to_record(limit):
                model_id = record.get("id")
                
                if model_id in seen:
                    continue
                
                seen.add(model_id)
                writer.writerow(record)
                row_count += 1
                bar.update(1)

                if row_count % 10_000 == 0:
                    c.flush()

        except Exception:
            print(f"\nProgram stopped. {row_count} model successfully transformed to CSV.")
            raise

    return row_count

def main():
    limit = int(os.getenv("LIMIT", 100000))
    csv_path = os.getenv("CSV_PATH", "all_in_one_data_extracting/model_data/model.csv")

    models_to_csv(csv_path=csv_path, limit=limit)

if __name__ == "__main__":
    main()
from huggingface_hub import HfApi
import logging, json, csv, os
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

def model_to_record(limit:int | None):

    models_gen = api.list_models(expand=EXPAND, sort="downloads")

    for i in range(limit):
        model = next(models_gen)

        card = getattr(model, "card_data", None)

        yield  {
            "id": model.id,
            "author": getattr(model, "author", None),
            "created_at": str(getattr(model, "created_at", None)),
            "last_modified": str(getattr(model, "last_modified", None)),
            
            "downloads": getattr(model, "downloads", 0),
            "likes": getattr(model, "likes", 0),
            
            "pipeline_tag": getattr(model, "pipeline_tag", None),
            "library_name": getattr(model, "library_name", None),
            "gated": getattr(model, "gated", False),
            "private": getattr(model, "private", False),
            
            "license": getattr(card, "license", None) if card else None,
            "base_model": getattr(card, "base_model", None) if card else None,
            "language": getattr(card, "language", None) if card else None,
            "datasets": getattr(card, "datasets", None) if card else None,
            
            "tags": model.tags or [],
            }

def models_to_jsonl(jsonl_path:str | None, limit:int | None) -> int:    
    row_count = 0

    seen: set[str] = set()

    with open(jsonl_path, "w", encoding="utf-8") as f, tqdm(
    total=limit,
    unit=" line",
    unit_scale=False,
    desc="Fetching",
    dynamic_ncols=True
    ) as bar:
        
        try:
            for model in model_to_record(limit):

                if model.get("id") in seen:
                    continue
                
                seen.add(model.get("id"))

                f.write(json.dumps(model, ensure_ascii= False) + "\n")

                if len(seen) % 10_000 == 0:
                    f.flush()

                row_count += 1
                bar.update(1)

        except:
            print(f"\n{row_count} model's metadata successfully processed.")
            os._exit(0)

    return row_count

def jsonl_to_csv(jsonl_path:str | None, csv_path:str | None, limit:int | None) -> int:

    row_count = 0

    with open(jsonl_path, "r", encoding="utf-8") as j, open(csv_path, "w", encoding="utf-8", newline="") as c, tqdm(
    total=limit,
    unit="model",
    desc="Fetching",
    dynamic_ncols=True
    ) as bar:

        try:
            writer = csv.DictWriter(c, extrasaction="ignore", fieldnames= FIELDS)
            writer.writeheader()

            for line in j:

                line = line.strip()

                if not line:
                    continue

                record = json.loads(line)

                if isinstance("tags", dict):
                    record["tags"] = ";".join(record["tags"])

                writer.writerow(record)
                row_count += 1
                bar.update(1)

        except:
            print(f"\n{row_count} model's metadata successfully processed.")
            os._exit(0)

    return row_count


def main():
    limit = int(os.getenv("LIMIT", 100))
    jsonl_path = os.getenv("JSONL_PATH", "HF_models.jsonl")
    csv_path = os.getenv("CSV_PATH", "HF_models.csv")
    models_to_jsonl(jsonl_path= jsonl_path, limit=limit)
    jsonl_to_csv(jsonl_path=jsonl_path, csv_path= csv_path, limit= limit)


if __name__ == "__main__":
    main()
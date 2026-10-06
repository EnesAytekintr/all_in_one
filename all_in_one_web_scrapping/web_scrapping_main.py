import requests, json
import pandas as pd

headers = {"User-Agent": "CoolBot/0.0 (https://example.org/coolbot/; coolbot@example.org)"}

url = "https://huggingface.co/api/models"

params = {"sort": "downloads", "limit": 1000}
"""
total = 0
with open("model_files/models.jsonl", "w", encoding="utf-8") as f:
    
    while url and total < 1_000_000:
        r = requests.get(url, headers=headers, params=params, timeout=30)
        
        models = r.json()

        if not isinstance(models, list):
            raise RuntimeError(f"Unexpected response: {models}")

        for m in models:
            f.write(json.dumps(m, ensure_ascii=False) + "\n")
        total += len(models)

        url = r.links.get("next", {}).get("url")
        params = None
        print(total)
"""
df = pd.read_json("model_files/models.jsonl", lines=True)

if "tags" in df.columns:
    df["tags"] = df["tags"].apply(lambda x: ":".join(x) if isinstance(x, list) else x)

df.to_csv("model_files/models.csv", index= False, chunksize=100000)
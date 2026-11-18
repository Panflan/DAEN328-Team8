import json
from pathlib import Path
from collections import Counter
from transform import transform_batch, COLUMNS

"""
TO TEST THE FILE YOU NEED TO BE IN THE DIRECTORY THEN RUN THE FILE
IT WILL SAVE AS "cleaned_sample.json"
"""




RAW_PATH = Path("data/raw_data.json")
CLEAN_PATH = Path("data/cleaned_sample.json")

SAMPLE_SIZE = 100

def test_sample():
    if not RAW_PATH.exists():
        print(f"File not found: {RAW_PATH.resolve()}")
        return

    stats = Counter()
    batch = []

    with open(RAW_PATH, "r", encoding="utf-8") as file:
        for line in file:
            if not line.strip():
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                stats["invalid_json"] += 1
                continue

            batch.append(record)

            if len(batch) >= SAMPLE_SIZE:
                break
    if not batch:
        print("No valid records found.")
        return

    #transforming the sample
    cleaned_batch = transform_batch(batch, stats)

    #saving records
    CLEAN_PATH.parent.mkdir(parents=True,exist_ok=True)

    with open(CLEAN_PATH,"w", encoding="utf-8") as file:
        for record in cleaned_batch:
            file.write(json.dumps(record) + "\n")

    print("\n=== TRANSFORMATION SUMMARY ===")
    print(f"Rows received: {stats['received']}")
    print(f"Rows cleaned: {stats['cleaned']}")
    print(f"Duplicated removed: {stats['duplicates']}")
    print(f"Invalid IDs: {stats['invalid_id']}")
    print(f"Invalid JSON lines: {stats['invalid_json']}")

    print("\n=== Missing VALUES ===")

    for col in COLUMNS:
        count = stats[f"missing_{col}"]
        print(f"{col}: {count}")

    print("\n=== ORIGINAL RECORD ===")
    print(json.dumps(batch[0], indent=4))

    if cleaned_batch:
        print("\n=== CLEANED RECORD ===")
        print(json.dumps(cleaned_batch[0], indent=4))

    print(f"\nCleaned sample saved to: {CLEAN_PATH}")


if __name__ == "__main__":
    test_sample()
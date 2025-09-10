import json

class Helper:
    @staticmethod
    def write_jsonl(filename, data):
        with open(filename, "w", encoding="utf-8") as f:
            for entry in data:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        print(f"Saved {len(data)} entries to {filename}")

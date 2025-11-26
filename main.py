import json

def analyze_sarif(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        sarif_data = json.load(f)

    print("=== SARIF ANALYSIS ===")

    print(f"Top-level keys: {list(sarif_data.keys())}\n")

    runs = sarif_data.get("runs", [])
    print(f"Number of runs: {len(runs)}")



if __name__ == "__main__":
    analyze_sarif("result.sarif")

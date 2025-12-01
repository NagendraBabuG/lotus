import json

def convertToJson(input_path, output_path):
    with open(input_path, "r", encoding="utf-8") as f:
        codeql_data = json.load(f)

    
    rule_lookup = {}
    for run in codeql_data.get("runs", []):
        for rule in run.get("tool", {}).get("driver", {}).get("rules", []):
            rule_id = rule["id"]
            props = rule.get("properties", {})
            rule_lookup[rule_id] = {
                "shortDescription": rule.get("shortDescription", {}).get("text", ""),
                "fullDescription": rule.get("fullDescription", {}).get("text", ""),
                "severity": rule.get("defaultConfiguration", {}).get("level", "warning"),
                "securitySeverity": props.get("security-severity"),
                "cwe": [tag for tag in props.get("tags", []) if tag.startswith("external/cwe/cwe-")],
                "tags": [tag for tag in props.get("tags", []) if not tag.startswith("external/cwe/")],
                "precision": props.get("precision", "high")
            }

    results = []

    for run in codeql_data.get("runs", []):
        for result in run.get("results", []):
            rule_id = result["ruleId"]
            message = result["message"]["text"]
            location = result["locations"][0]["physicalLocation"]
            file = location["artifactLocation"]["uri"]
            region = location["region"]

            results.append({
                "file": file,
                "line": region["startLine"],
                "column": region["startColumn"],
                "message": message,
                "ruleId": rule_id,
                "rule": rule_lookup.get(rule_id, {})  
            })

    output = {
        "total_results": len(results),
        "results": results
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    convertToJson("codeql_results.sarif", "codeql_results.json")
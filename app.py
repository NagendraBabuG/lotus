import json

def convertFileFormat(input, output):
    with open(input, "r", encoding="utf-8") as f:
        sarif_data = json.load(f)

    res_objs = []

    runs = sarif_data.get("runs", [])
    
    for run in runs:
        results = run.get("results", [])

        for result in results:
            result_obj = {}

            result_obj["ruleId"] = result.get("ruleId")
            result_obj["ruleIndex"] = result.get("ruleIndex")
            result_obj["message"] = result.get("message", {}).get("text")
            result_obj["level"] = result.get("level")
            result_obj["kind"] = result.get("kind")
            result_obj["properties"] = result.get("properties", {})

            locations = result.get("locations", [])

            if locations:
                loc = locations[0]  
                physical = loc.get("physicalLocation", {})
                artifact = physical.get("artifactLocation", {})
                region = physical.get("region", {})

                result_obj["file"] = artifact.get("uri")
                result_obj["startLine"] = region.get("startLine")
                result_obj["startColumn"] = region.get("startColumn")
                result_obj["endLine"] = region.get("endLine")
                result_obj["endColumn"] = region.get("endColumn")
            else:
                result_obj["file"] = None
                result_obj["startLine"] = None
                result_obj["startColumn"] = None
                result_obj["endLine"] = None
                result_obj["endColumn"] = None

            res_objs.append(result_obj)

    res_output = {
        "codeql_results": len(res_objs),
        "results": res_objs
    }

    with open(output, "w", encoding="utf-8") as f:
        json.dump(res_output, f, indent=4)

if __name__ == "__main__":
    convertFileFormat("jav_res.sarif", "jav_results.json")

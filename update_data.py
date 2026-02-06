import requests
import json
import os

URL = "https://api.regolith.rocks"
TOKEN = os.environ.get("REGOLITH_TOKEN")

# SIGNATURE DEFAULTS
VERIFIED_SIGS = {
    "ITYPE": 4000, "CTYPE": 4700, "STYPE": 4720, 
    "PTYPE": 4750, "MTYPE": 4850, "QTYPE": 4870, "ETYPE": 4900
}

# NEW QUERY: Mapping to the discovered fields 'dataName' and 'data'
QUERY = """
query {
  surveyData {
    dataName
    data {
      rockTypes { type prob }
      ores { name prob }
    }
  }
}
"""

def sync():
    if not TOKEN:
        print("!! FAIL: REGOLITH_TOKEN missing !!")
        return

    headers = {"x-api-key": TOKEN.strip(), "Content-Type": "application/json"}
    
    try:
        print("Contacting Regolith API (Targeting dataName path)...")
        response = requests.post(URL, headers=headers, json={"query": QUERY}, timeout=20)
        data = response.json()

        if "errors" in data:
            print(f"API ERROR: {data['errors'][0]['message']}")
            return

        raw_entries = data.get("data", {}).get("surveyData", [])
        if not raw_entries:
            print("!! FAIL: No survey data found !!")
            return

        print(f"SUCCESS: Found {len(raw_entries)} data points. Mapping to repository...")

        ore_data = {}
        rock_data = {}

        for entry in raw_entries:
            name = entry.get("dataName", "UNKNOWN")
            inner_data = entry.get("data", {})
            
            # 1. Process Ores
            ore_data[name] = {
                "ores": {o["name"].capitalize(): o["prob"] for o in inner_data.get("ores", [])}
            }

            # 2. Process Rock Signatures
            is_planet = not any(k in name.upper() for k in ['HALO', 'BELT', 'L1', 'L2', 'L3', 'L4', 'L5'])
            rock_data[name] = {
                "is_planetary": is_planet,
                "signatures": {"GROUND": 4000, "HAND": 3000} if is_planet else {
                    rt["type"].upper(): VERIFIED_SIGS.get(rt["type"].upper() + "TYPE", 4870)
                    for rt in inner_data.get("rockTypes", [])
                }
            }

        with open("ore_locations.json", "w") as f:
            json.dump(ore_data, f, indent=2)
        with open("rock.json", "w") as f:
            json.dump(rock_data, f, indent=2)

        print("Verification: Data successfully mapped from dataName to JSON files.")

    except Exception as e:
        print(f"!! CRITICAL ERROR: {str(e)} !!")

if __name__ == "__main__":
    sync()

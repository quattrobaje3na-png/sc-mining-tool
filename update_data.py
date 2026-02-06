import requests
import json
import os

URL = "https://api.regolith.rocks"
TOKEN = os.environ.get("REGOLITH_TOKEN")

VERIFIED_SIGS = {
    "ITYPE": 4000, "CTYPE": 4700, "STYPE": 4720, 
    "PTYPE": 4750, "MTYPE": 4850, "QTYPE": 4870, "ETYPE": 4900
}

# NEW QUERY: Targeting 'scoutingFind' based on Discovery results
QUERY = """
query {
  scoutingFind {
    dataName
    data
  }
}
"""

def sync():
    if not TOKEN:
        print("!! FAIL: REGOLITH_TOKEN missing !!")
        return

    headers = {"x-api-key": TOKEN.strip(), "Content-Type": "application/json"}
    
    try:
        print("Contacting Regolith API (Targeting scoutingFind)...")
        response = requests.post(URL, headers=headers, json={"query": QUERY}, timeout=20)
        result = response.json()

        if "errors" in result:
            print(f"API ERROR: {result['errors'][0]['message']}")
            return

        raw_entries = result.get("data", {}).get("scoutingFind", [])
        if not raw_entries:
            print("!! FAIL: No data found in scoutingFind !!")
            return

        print(f"SUCCESS: Received {len(raw_entries)} entries. Processing...")

        ore_data = {}
        rock_data = {}

        for entry in raw_entries:
            loc_name = entry.get("dataName", "UNKNOWN")
            content = entry.get("data", {})
            
            # Handle potential stringified JSON in 'data' scalar
            if isinstance(content, str):
                try:
                    content = json.loads(content)
                except:
                    content = {}

            # 1. Process Ores
            ore_list = content.get("ores", [])
            ore_data[loc_name] = {
                "ores": {o["name"].capitalize(): o["prob"] for o in ore_list if "name" in o}
            }

            # 2. Process Rock Signatures
            is_planet = not any(k in loc_name.upper() for k in ['HALO', 'BELT', 'L1', 'L2', 'L3', 'L4', 'L5'])
            rock_types = content.get("rockTypes", [])
            
            rock_data[loc_name] = {
                "is_planetary": is_planet,
                "signatures": {"GROUND": 4000, "HAND": 3000} if is_planet else {
                    rt.get("type", "").upper(): VERIFIED_SIGS.get(rt.get("type", "").upper() + "TYPE", 4870)
                    for rt in rock_types if "type" in rt
                }
            }

        with open("ore_locations.json", "w") as f:
            json.dump(ore_data, f, indent=2)
        with open("rock.json", "w") as f:
            json.dump(rock_data, f, indent=2)

        print(f"VERIFICATION: Successfully updated {len(ore_data)} mining locations.")

    except Exception as e:
        print(f"!! CRITICAL ERROR: {str(e)} !!")

if __name__ == "__main__":
    sync()

import requests
import json
import os

URL = "https://api.regolith.rocks"
TOKEN = os.environ.get("REGOLITH_TOKEN")

VERIFIED_SIGS = {
    "ITYPE": 4000, "CTYPE": 4700, "STYPE": 4720, 
    "PTYPE": 4750, "MTYPE": 4850, "QTYPE": 4870, "ETYPE": 4900
}

# UPDATED QUERY: We remove the brackets {} from 'data' 
# because it's a Scalar JSON object, not a nested GraphQL type.
QUERY = """
query {
  surveyData {
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
        print("Contacting Regolith API (Fetching JSON Object)...")
        response = requests.post(URL, headers=headers, json={"query": QUERY}, timeout=20)
        
        # Check if the server actually liked our request
        if response.status_code != 200:
            print(f"Server Error {response.status_code}: {response.text[:200]}")
            return

        result = response.json()
        if "errors" in result:
            print(f"API ERROR: {result['errors'][0]['message']}")
            return

        raw_entries = result.get("data", {}).get("surveyData", [])
        if not raw_entries:
            print("!! FAIL: No entries found in surveyData !!")
            return

        print(f"SUCCESS: Received {len(raw_entries)} entries. Unpacking JSON...")

        ore_data = {}
        rock_data = {}

        for entry in raw_entries:
            loc_name = entry.get("dataName", "UNKNOWN")
            
            # The 'data' field is now a dictionary we can use directly
            content = entry.get("data", {})
            
            # If the API sends it as a string instead of a dict, we parse it
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

        # Final write to repository files
        with open("ore_locations.json", "w") as f:
            json.dump(ore_data, f, indent=2)
        with open("rock.json", "w") as f:
            json.dump(rock_data, f, indent=2)

        print(f"VERIFICATION: Wrote {len(ore_data)} locations to ore_locations.json and rock.json.")

    except Exception as e:
        print(f"!! CRITICAL ERROR: {str(e)} !!")

if __name__ == "__main__":
    sync()

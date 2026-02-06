import requests
import json
import os

URL = "https://api.regolith.rocks"
TOKEN = os.environ.get("REGOLITH_TOKEN")

# Corrected Signatures from your verified chart
ROCK_SIGNATURES = {
    "ITYPE": 4000, "CTYPE": 4700, "STYPE": 4720, 
    "PTYPE": 4750, "MTYPE": 4850, "QTYPE": 4870, "ETYPE": 4900
}

QUERY = """
query {
  surveyLocations {
    id
    rockTypes { type prob }
    ores { name prob }
  }
}
"""

def verify_file(filename):
    if os.path.exists(filename) and os.path.getsize(filename) > 0:
        print(f"VERIFIED: {filename} written successfully.")
        return True
    print(f"CRITICAL ERROR: {filename} failed verification.")
    return False

def sync():
    if not TOKEN:
        print("MISSING_TOKEN: Check GitHub Secrets for REGOLITH_TOKEN")
        return

    headers = {"x-api-key": TOKEN, "Content-Type": "application/json"}
    payload = {"query": QUERY.replace("\n", " ")}
    
    try:
        response = requests.post(URL, headers=headers, json=payload, timeout=20)
        response.raise_for_status()
        data = response.json()
        raw_locations = data.get("data", {}).get("surveyLocations", [])

        # STAGE 1: Process and Write ore_locations.json
        ore_data = {}
        for loc in raw_locations:
            ore_data[loc["id"]] = {
                "ores": {o["name"].capitalize(): o["prob"] for o in loc.get("ores", [])}
            }
        
        with open("ore_locations.json", "w") as f:
            json.dump(ore_data, f, indent=2)

        # VERIFICATION 1
        if not verify_file("ore_locations.json"):
            return

        # STAGE 2: Process and Write rock.json
        rock_data = {}
        for loc in raw_locations:
            is_ground = not any(k in loc["id"].upper() for k in ['HALO', 'BELT', 'L1', 'L2', 'L3', 'L4', 'L5'])
            
            rock_data[loc["id"]] = {
                "is_planetary": is_ground,
                "signatures": {}
            }
            
            if is_ground:
                rock_data[loc["id"]]["signatures"] = {"GROUND": 4000, "HAND": 3000}
            else:
                for rt in loc.get("rockTypes", []):
                    rtype = rt["type"].upper()
                    lookup = rtype if rtype.endswith("TYPE") else f"{rtype}TYPE"
                    if lookup in ROCK_SIGNATURES:
                        rock_data[loc["id"]]["signatures"][rtype] = ROCK_SIGNATURES[lookup]

        with open("rock.json", "w") as f:
            json.dump(rock_data, f, indent=2)

        # VERIFICATION 2
        verify_file("rock.json")

    except Exception as e:
        print(f"PROCESS_FAILED: {e}")
        exit(1)

if __name__ == "__main__":
    sync()

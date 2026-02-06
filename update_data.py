import requests
import json
import os

URL = "https://api.regolith.rocks"
TOKEN = os.environ.get("REGOLITH_TOKEN")

# YOUR VERIFIED SIGNATURES
VERIFIED_SIGNATURES = {
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

def sync():
    if not TOKEN:
        print("!! CRITICAL: REGOLITH_TOKEN is missing from GitHub Secrets !!")
        return

    headers = {"x-api-key": TOKEN, "Content-Type": "application/json"}
    payload = {"query": QUERY.replace("\n", " ")}
    
    try:
        print("Step 1: Contacting Regolith...")
        response = requests.post(URL, headers=headers, json=payload, timeout=20)
        response.raise_for_status()
        data = response.json()
        
        raw_locations = data.get("data", {}).get("surveyLocations", [])
        
        if not raw_locations:
            print("!! ERROR: API returned zero locations. Check your API Key !!")
            return

        print(f"Step 2: Data received! Processing {len(raw_locations)} locations...")

        master_output = {}
        for loc in raw_locations:
            loc_id = loc["id"]
            # Flag if it's a moon (No L-points or Belts)
            is_ground = not any(k in loc_id.upper() for k in ['HALO', 'BELT', 'RING', 'L1', 'L2', 'L3', 'L4', 'L5'])
            
            master_output[loc_id] = {
                "ores": {o["name"].capitalize(): {"prob": o["prob"]} for o in loc.get("ores", [])},
                "signatures": {},
                "is_planetary": is_ground
            }
            
            # Map the Rock Types
            for rt in loc.get("rockTypes", []):
                rtype = rt["type"].upper()
                lookup = rtype if rtype.endswith("TYPE") else f"{rtype}TYPE"
                
                if is_ground:
                    master_output[loc_id]["signatures"]["GROUND"] = {"sig": 4000}
                    master_output[loc_id]["signatures"]["HAND"] = {"sig": 3000}
                elif lookup in VERIFIED_SIGNATURES:
                    master_output[loc_id]["signatures"][rtype] = {
                        "sig": VERIFIED_SIGNATURES[lookup],
                        "prob": rt["prob"]
                    }

        # Step 3: Hard Write
        with open("ore_locations.json", "w") as f:
            json.dump(master_output, f, indent=2)
            
        print("Step 4: ore_locations.json successfully updated and saved locally!")

    except Exception as e:
        print(f"!! SYNC FAILED: {str(e)} !!")
        exit(1)

if __name__ == "__main__":
    sync()

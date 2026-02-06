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

# The GraphQL Query
QUERY = """
query {
  surveyLocations {
    id
    rockTypes { type prob }
    ores { name prob }
  }
}
"""

def is_planetary(loc_id):
    space_keywords = ['HALO', 'BELT', 'RING', 'L1', 'L2', 'L3', 'L4', 'L5']
    return not any(k in loc_id.upper() for k in space_keywords)

def sync():
    if not TOKEN:
        print("CRITICAL_ERROR: REGOLITH_TOKEN secret is missing from GitHub Settings.")
        return

    headers = {"x-api-key": TOKEN, "Content-Type": "application/json"}
    payload = {"query": QUERY.replace("\n", " ")}
    
    try:
        print("Connecting to Regolith API...")
        response = requests.post(URL, headers=headers, json=payload, timeout=20)
        response.raise_for_status()
        
        data = response.json()
        
        if "errors" in data:
            print(f"API_ERROR: {data['errors'][0]['message']}")
            return

        # Attempt to get locations safely
        raw_locations = data.get("data", {}).get("surveyLocations")
        if not raw_locations:
            print("ERROR: API returned no surveyLocations. Check GraphQL field names.")
            return
            
        print(f"Scrape Successful. Processing {len(raw_locations)} locations...")

        master_output = {}
        for loc in raw_locations:
            loc_id = loc["id"]
            planetary = is_planetary(loc_id)
            
            master_output[loc_id] = {
                "ores": {},
                "signatures": {},
                "is_planetary": planetary
            }
            
            # Map Ores
            for ore in loc.get("ores", []):
                name = ore["name"].capitalize()
                if name == "Quantanium": name = "Quantainium"
                master_output[loc_id]["ores"][name] = {"prob": ore["prob"]}
            
            # Map Rock Types/Signatures
            for rt in loc.get("rockTypes", []):
                rtype_raw = rt["type"].upper()
                lookup = rtype_raw if rtype_raw.endswith("TYPE") else f"{rtype_raw}TYPE"
                
                if planetary:
                    master_output[loc_id]["signatures"]["GROUND"] = {"sig": 4000, "type": "Vehicle/Ship"}
                    master_output[loc_id]["signatures"]["HAND"] = {"sig": 3000, "type": "FPS"}
                elif lookup in VERIFIED_SIGNATURES:
                    master_output[loc_id]["signatures"][rtype_raw] = {
                        "sig": VERIFIED_SIGNATURES[lookup],
                        "prob": rt["prob"]
                    }

        # Final write to file
        with open("ore_locations.json", "w") as f:
            json.dump(master_output, f, indent=2)
            
        print(f"SUCCESS: ore_locations.json rewritten with {len(master_output)} entries.")

    except Exception as e:
        print(f"SYNC FAILED: {str(e)}")
        exit(1)

if __name__ == "__main__":
    sync()

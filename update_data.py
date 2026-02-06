import requests
import json
import os

# 1. Verification of Environment
URL = "https://api.regolith.rocks"
TOKEN = os.environ.get("REGOLITH_TOKEN")

def sync():
    # We create the files early to prove the bot can write to the repo
    print("Pre-seeding files to test write permissions...")
    with open("ore_locations.json", "w") as f: json.dump({"status": "writing_started"}, f)
    with open("rock.json", "w") as f: json.dump({"status": "writing_started"}, f)

    if not TOKEN:
        print("!! FAIL: REGOLITH_TOKEN is not set in GitHub Secrets !!")
        return

    headers = {"x-api-key": TOKEN, "Content-Type": "application/json"}
    query = "query { surveyLocations { id rockTypes { type prob } ores { name prob } } }"
    
    try:
        print("Contacting Regolith API...")
        response = requests.post(URL, headers=headers, json={"query": query}, timeout=20)
        response.raise_for_status()
        data = response.json()
        
        raw_locs = data.get("data", {}).get("surveyLocations", [])
        if not raw_locs:
            print("!! FAIL: API returned no data. Check if your API Key is active !!")
            return

        # STAGE 1: ORES
        ores = {l["id"]: {"ores": {o["name"].capitalize(): o["prob"] for o in l.get("ores", [])}} for l in raw_locs}
        with open("ore_locations.json", "w") as f:
            json.dump(ores, f, indent=2)

        # STAGE 2: ROCKS
        rocks = {}
        for l in raw_locs:
            is_planet = not any(k in l["id"].upper() for k in ['HALO', 'BELT', 'L1', 'L2', 'L3', 'L4', 'L5'])
            rocks[l["id"]] = {
                "is_planetary": is_planet,
                "signatures": {"GROUND": 4000, "HAND": 3000} if is_planet else {
                    rt["type"].upper(): {"prob": rt["prob"]} for rt in l.get("rockTypes", [])
                }
            }
        with open("rock.json", "w") as f:
            json.dump(rocks, f, indent=2)

        print(f"SUCCESS: Captured {len(raw_locs)} locations.")

    except Exception as e:
        print(f"!! CRITICAL ERROR: {str(e)} !!")

if __name__ == "__main__":
    sync()

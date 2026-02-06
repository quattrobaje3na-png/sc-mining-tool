import requests
import json
import os

URL = "https://api.regolith.rocks"
TOKEN = os.environ.get("REGOLITH_TOKEN")

# We'll try both common naming conventions for the Regolith API
QUERIES = [
    "query { surveyLocations { id rockTypes { type prob } ores { name prob } } }",
    "query { locations { id rockTypes { type prob } ores { name prob } } }"
]

def sync():
    if not TOKEN:
        print("!! FAIL: REGOLITH_TOKEN secret is missing !!")
        return

    headers = {"x-api-key": TOKEN, "Content-Type": "application/json"}
    
    for query in QUERIES:
        try:
            print(f"Attempting query: {query[:50]}...")
            response = requests.post(URL, headers=headers, json={"query": query}, timeout=20)
            
            # Print the raw response for debugging if it's not a 200 OK
            if response.status_code != 200:
                print(f"Status {response.status_code}: {response.text[:100]}")
                continue

            data = response.json()
            
            # Look for data in either potential field
            raw_locs = data.get("data", {}).get("surveyLocations") or data.get("data", {}).get("locations")
            
            if raw_locs:
                print(f"SUCCESS: Found {len(raw_locs)} locations!")
                
                # STAGE 1: ORES
                ores = {l["id"]: {"ores": {o["name"].capitalize(): o["prob"] for o in l.get("ores", [])}} for l in raw_locs}
                with open("ore_locations.json", "w") as f:
                    json.dump(ores, f, indent=2)

                # STAGE 2: ROCKS (Simplified logic for now to ensure it writes)
                rocks = {}
                for l in raw_locs:
                    is_planet = not any(k in l["id"].upper() for k in ['HALO', 'BELT', 'L1', 'L2', 'L3', 'L4', 'L5'])
                    rocks[l["id"]] = {
                        "is_planetary": is_planet,
                        "signatures": {"GROUND": 4000, "HAND": 3000} if is_planet else {
                            rt["type"].upper(): 4870 for rt in l.get("rockTypes", []) # Defaulting sigs for test
                        }
                    }
                with open("rock.json", "w") as f:
                    json.dump(rocks, f, indent=2)
                
                return # Exit once we have success

        except Exception as e:
            print(f"Query attempt failed: {str(e)}")

    print("!! ALL ATTEMPTS FAILED: Check your API Key in GitHub Secrets !!")

if __name__ == "__main__":
    sync()

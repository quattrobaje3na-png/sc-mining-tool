import requests
import json
import os

# API Configuration
url = "https://api.regolith.rocks"
# Pulls the token from your GitHub Secrets
api_key = os.environ.get("REGOLITH_TOKEN")

# The GraphQL query to get location data (Adjusted to get survey info)
query = """
query {
  surveyLocations {
    id
    ores {
      name
      prob
    }
  }
}
"""

headers = {
    "x-api-key": api_key,
    "Content-Type": "application/json"
}

def sync():
    if not api_key:
        print("Error: REGOLITH_TOKEN not found in environment.")
        return

    payload = {"query": query.replace("\n", " ")}
    
    try:
        print("Initiating Authenticated Quantum Link...")
        response = requests.post(url, headers=headers, json=payload, timeout=20)
        response.raise_for_status()
        
        data = response.json()
        
        # Format the data to match your tool's ore_locations.json structure
        raw_locations = data.get("data", {}).get("surveyLocations", [])
        processed_data = {}

        for loc in raw_locations:
            loc_id = loc["id"]
            processed_data[loc_id] = {"ores": {}}
            for ore in loc.get("ores", []):
                name = ore["name"].capitalize()
                if name == "Quantanium": name = "Quantainium"
                processed_data[loc_id]["ores"][name] = {"prob": ore["prob"]}

        with open("ore_locations.json", "w") as f:
            json.dump(processed_data, f, indent=2)
            
        print(f"Sync Complete: {len(processed_data)} locations updated via Secure API.")

    except Exception as e:
        print(f"Sync Failed: {e}")
        if response.text:
            print(f"Server Response: {response.text}")
        exit(1)

if __name__ == "__main__":
    sync()

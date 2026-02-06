import requests
import json

# The Regolith export URL
url = "https://regolith.rocks/api/export/survey/locations"

try:
    print("Fetching live data from Regolith...")
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    raw_data = response.json()

    # We only want to save the parts our tool uses to keep the file small
    # This matches the 'ores' structure your scan() function expects
    processed_data = {}
    for loc_id, details in raw_data.items():
        if "ores" in details:
            processed_data[loc_id] = {"ores": details["ores"]}

    with open("ore_locations.json", "w") as f:
        json.dump(processed_data, f, indent=2)
    
    print("Success: ore_locations.json updated.")

except Exception as e:
    print(f"Failed to update data: {e}")
    exit(1) # Signal failure to GitHub Actions
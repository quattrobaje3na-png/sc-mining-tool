import requests
import json

# The Regolith export URL
url = "https://regolith.rocks/api/export/survey/locations"

# NEW: Custom headers to look like a real web browser
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json"
}

try:
    print(f"Fetching live data from: {url}")
    response = requests.get(url, headers=headers, timeout=15)
    
    # Check if the site blocked us
    if response.status_code == 403:
        print("Error: Regolith blocked the request (403 Forbidden).")
        exit(1)
        
    response.raise_for_status()
    
    # Verify we actually got text back
    if not response.text.strip():
        print("Error: Received an empty response from the server.")
        exit(1)

    raw_data = response.json()

    processed_data = {}
    for loc_id, details in raw_data.items():
        if isinstance(details, dict) and "ores" in details:
            processed_data[loc_id] = {"ores": details["ores"]}

    with open("ore_locations.json", "w") as f:
        json.dump(processed_data, f, indent=2)
    
    print(f"Success: Processed {len(processed_data)} locations.")

except json.JSONDecodeError:
    print("Error: Server did not return valid JSON. It might be sending an error page instead.")
    print("Full server response (first 200 chars):", response.text[:200])
    exit(1)
except Exception as e:
    print(f"Failed to update data: {e}")
    exit(1)

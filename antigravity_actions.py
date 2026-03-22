import json
import urllib.request
import urllib.error
import ssl

# Define the hypothetical EdgeOps Antigravity API URL
API_URL = "https://mock-edgeops.rocketride.mock-api/antigravity/v1"

def _print_json(label: str, data: dict):
    print(f"--- {label} ---")
    print(json.dumps(data, indent=2))
    print("-" * (8 + len(label)))

def _make_request(endpoint: str, payload: dict) -> dict:
    url = f"{API_URL}/{endpoint}"
    data = json.dumps(payload).encode('utf-8')
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer YOUR_MOCK_API_KEY'
    }
    
    _print_json(f"REQUEST TO {endpoint}", payload)
    
    req = urllib.request.Request(url, data=data, headers=headers, method='POST')
    
    # Optional context to bypass SSL validation for local development/demos
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    try:
        # Try to hit the actual API (will fail in demo since URL is mock)
        with urllib.request.urlopen(req, context=ctx, timeout=3) as response:
            response_data = json.loads(response.read().decode('utf-8'))
            _print_json(f"SUCCESS RESPONSE FROM {endpoint}", response_data)
            return response_data
            
    except (urllib.error.URLError, json.JSONDecodeError, TimeoutError) as e:
        print(f"\n[!] API Unavailable or Error ({e}). Falling back to MOCK response so the demo continues!")
        return _get_mock_response(endpoint, payload)

def _get_mock_response(endpoint: str, payload: dict) -> dict:
    """Returns a mock response depending on the endpoint."""
    if endpoint == "reroute":
        mock_response = {
            "status": "success",
            "message": "Vehicle successfully rerouted.",
            "vehicle_id": payload.get("vehicle_id"),
            "estimated_time_of_arrival_mins": 5,
            "waypoints_accepted": len(payload.get("new_route_waypoints", []))
        }
    elif endpoint == "rescue":
        mock_response = {
            "status": "success",
            "message": "Human driver rescue vehicle dispatched.",
            "vehicle_id": payload.get("vehicle_id"),
            "passenger_id": payload.get("passenger_id"),
            "rescue_vehicle_eta_mins": 8,
            "rescue_driver": "Sarah O.",
            "target_location": payload.get("location")
        }
    else:
        mock_response = {"status": "error", "message": "Unknown endpoint fallback"}
        
    _print_json(f"MOCK RESPONSE FOR {endpoint}", mock_response)
    return mock_response

def dispatch_reroute(vehicle_id: str, current_lat: float, current_lon: float, new_route_waypoints: list) -> dict:
    """
    Hits the RocketRide Antigravity reroute endpoint and returns a confirmation payload.
    """
    print(f"[*] Dispatching reroute for vehicle {vehicle_id}...")
    payload = {
        "vehicle_id": vehicle_id,
        "current_position": {
            "lat": current_lat,
            "lon": current_lon
        },
        "new_route_waypoints": new_route_waypoints
    }
    return _make_request("reroute", payload)

def dispatch_rescue(vehicle_id: str, passenger_id: str, location_lat: float, location_lon: float) -> dict:
    """
    Dispatches a human driver rescue vehicle to the specified coordinates.
    """
    print(f"[*] Dispatching rescue for passenger {passenger_id} from vehicle {vehicle_id}...")
    payload = {
        "vehicle_id": vehicle_id,
        "passenger_id": passenger_id,
        "location": {
            "lat": location_lat,
            "lon": location_lon
        }
    }
    return _make_request("rescue", payload)

if __name__ == "__main__":
    # Example Demo Usage
    
    # 1. Reroute command
    waypoints = [
        {"lat": 37.7750, "lon": -122.4185},
        {"lat": 37.7751, "lon": -122.4180}
    ]
    dispatch_reroute("av-4092", 37.7749, -122.4194, waypoints)
    
    print("\n" + "="*50 + "\n")
    
    # 2. Rescue command
    dispatch_rescue("av-4092", "psngr-7731", 37.7751, -122.4180)

import os
import time
from mock_bigquery import query_permit
from antigravity_actions import dispatch_reroute

# Gracefully support either the new google-genai or the classic google-generativeai SDK
try:
    from google import genai
    HAS_NEW_GENAI = True
except ImportError:
    HAS_NEW_GENAI = False

try:
    import google.generativeai as genai_classic
    HAS_CLASSIC_GENAI = True
except ImportError:
    HAS_CLASSIC_GENAI = False

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

from passenger_ui_generator import generate_passenger_ui

def handle_incident(gesture_data: dict, vehicle_id: str, location: str) -> dict:
    print(f"\n{'='*60}")
    print(f"🚨 EDGE-OPS ORCHESTRATOR TRIGGERED 🚨")
    print(f"Vehicle: {vehicle_id} | Location: {location}")
    print(f"Incoming Telemetry: {gesture_data}")
    print(f"{'='*60}")

    # 1. VERIFY
    print("\n[1] VERIFYING PERMITS (EdgeOps BigQuery Pipeline)...")
    permit_data = query_permit(location)
    closure_reason = permit_data.get("closure_reason", "No active permits")
    print(f"    -> DB Result: {closure_reason}")

    # 2. DECIDE
    print("\n[2] DECIDING RESOLUTION...")
    gesture = gesture_data.get("gesture_detected", "none")
    
    # If the DB has a valid closure reason
    has_permit = closure_reason != "No active permits"
    
    if has_permit and gesture in ["stop", "detour"]:
        resolution = "reroute"
        print("    -> Decision: REROUTE (Permitted active construction matches gesture)")
    else:
        resolution = "alert_human_operator"
        if not has_permit:
            print("    -> Decision: ALERT HUMAN OPERATOR (Anomaly: Unpermitted closure detected!)")
        else:
            print(f"    -> Decision: ALERT HUMAN OPERATOR (Anomaly: Unknown gesture '{gesture}')")

    # 3. GENERATE UX (Text + Base64 Avatar via Imagen 3)
    print("\n[3] GENERATING PASSENGER UX (Gemini + Imagen 3)...")
    ui_obj = generate_passenger_ui(closure_reason)
    ux_message = ui_obj.get("message", "")
    avatar_b64 = ui_obj.get("image_base64", "")
    print(f"    -> Generated Text: \"{ux_message}\"")
    print(f"    -> Generated Avatar String Length: {len(avatar_b64)} characters")

    # 4. ACT
    print("\n[4] TAKING ACTION...")
    if resolution == "reroute":
        # Mock waypoints logic
        waypoints = [
            {"lat": 37.7750, "lon": -122.4185},
            {"lat": 37.7751, "lon": -122.4180}
        ]
        # In this demo, current lat/lon is mocked based on the location str
        dispatch_reroute(vehicle_id, 37.7749, -122.4194, waypoints)
    elif resolution == "alert_human_operator":
        print(f"    -> [!] Pungent anomaly detected at {location}. Human operator dispatched to AV feed for manual takeover.")

    # 5. LOG
    print("\n[5] LOGGING INCIDENT...")
    incident_report = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "vehicle_id": vehicle_id,
        "location": location,
        "gesture": gesture,
        "permit_data": permit_data,
        "resolution_taken": resolution,
        "ux_message": ux_message
    }
    print("    -> Final Incident Report saved to EdgeOps logs.")
    print(f"{'='*60}\n")
    
    return incident_report

if __name__ == "__main__":
    # Test 1: Permitted Construction Scenario
    test_gesture_1 = {"gesture_detected": "detour", "confidence": 0.92, "description": "Construction worker directing traffic left."}
    handle_incident(test_gesture_1, "av-4092", "995 Market St")
    
    # Test 2: Unpermitted Anomaly Scenario
    test_gesture_2 = {"gesture_detected": "stop", "confidence": 0.95, "description": "Pedestrian standing in the middle of the road holding hand up."}
    handle_incident(test_gesture_2, "av-4092", "California & Battery")

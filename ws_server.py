import asyncio
import websockets
import json
import base64
import os
import io
import time
from PIL import Image

try:
    from google import genai
    from google.genai import types
    HAS_NEW_GENAI = True
except ImportError:
    HAS_NEW_GENAI = False

try:
    import google.generativeai as genai_classic
    HAS_CLASSIC_GENAI = True
except ImportError:
    HAS_CLASSIC_GENAI = False

# Integrating the new EdgeOps orchestration brain directly into the WebSockets layer
from edgeops_orchestrator import handle_incident

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

SYSTEM_PROMPT = """You are an AV dashcam analyzer for autonomous vehicles in San Francisco. 
Analyze each frame. If you detect a human making a Stop, Detour, or Merge hand gesture — 
especially someone in a neon safety vest — respond ONLY with JSON: 
{"gesture_detected": "stop"|"detour"|"merge"|"none", "confidence": 0.0-1.0, "description": str}. 
Otherwise respond with {"gesture_detected": "none", "confidence": 1.0, "description": "clear"}"""

IS_INCIDENT_ACTIVE = False
IS_ANALYZING = False

LAST_ANALYSIS_TIME = 0
DEBOUNCE_SECONDS = 1.0

async def analyze_frame_with_gemini(base64_img_data: str) -> dict:
    global LAST_ANALYSIS_TIME
    now = time.time()
    if now - LAST_ANALYSIS_TIME < DEBOUNCE_SECONDS:
        return {"gesture_detected": "none", "confidence": 1.0, "description": "skipped_due_to_throttle"}
    LAST_ANALYSIS_TIME = now
    
    if "base64," in base64_img_data:
        base64_img_data = base64_img_data.split("base64,")[1]
    
    try:
        image_bytes = base64.b64decode(base64_img_data)
        img = Image.open(io.BytesIO(image_bytes))
        
        if not GEMINI_API_KEY:
            return {"gesture_detected": "none", "confidence": 1.0, "description": "MOCK CLEAR (No API Key)"}
            
        if HAS_NEW_GENAI:
            client = genai.Client(api_key=GEMINI_API_KEY)
            response = await asyncio.to_thread(
                client.models.generate_content,
                model='gemini-2.0-flash',
                contents=[SYSTEM_PROMPT, img],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            raw_text = response.text
        elif HAS_CLASSIC_GENAI:
            genai_classic.configure(api_key=GEMINI_API_KEY)
            model = genai_classic.GenerativeModel('gemini-2.0-flash') 
            response = await asyncio.to_thread(
                model.generate_content,
                [SYSTEM_PROMPT, img],
                generation_config=genai_classic.types.GenerationConfig(
                    response_mime_type="application/json"
                )
            )
            raw_text = response.text
        else:
            return {"gesture_detected": "none", "confidence": 1.0, "description": "MOCK CLEAR (No SDK installed)"}
            
        try:
            return json.loads(raw_text)
        except json.JSONDecodeError:
            return {"gesture_detected": "none", "confidence": 0.0, "description": "JSON parse error"}
            
    except Exception as e:
        print(f"[!] Error calling API: {e}")
        return {"gesture_detected": "none", "confidence": 0.0, "description": f"API Error: {e}"}

async def trigger_orchestration_pipeline(analysis: dict, location: str):
    """Offloads the analysis dict directly to our edgeops_orchestrator pipeline"""
    global IS_INCIDENT_ACTIVE
    if IS_INCIDENT_ACTIVE:
        return
        
    IS_INCIDENT_ACTIVE = True
    vehicle_id = "av-4092"
    
    # Handle the synchronous pipeline in a separate thread so our WebSocket layer remains non-blocking and super fast!
    await asyncio.to_thread(handle_incident, analysis, vehicle_id, location)
        
    # Reset lock so it can fire again after some time during long continuous streams
    asyncio.create_task(reset_incident_lock_after_delay(15))

async def reset_incident_lock_after_delay(delay: int):
    global IS_INCIDENT_ACTIVE
    await asyncio.sleep(delay)
    IS_INCIDENT_ACTIVE = False
    print("[*] Dashboard orchestration lock reset - ready for new incidents.")

async def handle_client(websocket, path):
    global IS_ANALYZING
    print(f"[*] New client connected: {websocket.remote_address}")
    
    try:
        async for message in websocket:
            try:
                payload = json.loads(message)
                event_type = payload.get("event")
                
                # Check for our manual simulator UI
                if event_type == "incident_flag":
                    # Parse location if provided by React, default to "995 Market St"
                    loc = payload.get("location", "995 Market St")
                    dummy_analysis = {
                        "gesture_detected": "detour", 
                        "confidence": 1.0, 
                        "description": "Manual Simulator Flag triggered in React UI"
                    }
                    await trigger_orchestration_pipeline(dummy_analysis, loc)
                    continue
                    
                if event_type == "dashcam_frame":
                    base64_data = payload.get("data")
                    if not base64_data:
                        continue
                        
                    if IS_ANALYZING:
                        continue
                    
                    IS_ANALYZING = True
                    try:
                        analysis = await analyze_frame_with_gemini(base64_data)
                        gesture = analysis.get("gesture_detected", "none")
                        confidence = float(analysis.get("confidence", 0.0))
                        desc = analysis.get("description", "")
                        
                        if gesture != "none" and desc != "skipped_due_to_throttle":
                            print(f"[Gemini Vision] Gesture: {gesture.upper()} | Conf: {confidence:.2f} | {desc}")
                        
                        await websocket.send(json.dumps({
                            "event": "analysis_result",
                            "analysis": analysis
                        }))
                        
                        if gesture != "none" and confidence > 0.85:
                            # Send dynamic frame classification and default location to orchestration
                            await trigger_orchestration_pipeline(analysis, "995 Market St")
                            
                    finally:
                        IS_ANALYZING = False
                        
            except json.JSONDecodeError:
                pass
                
    except websockets.exceptions.ConnectionClosed:
        print(f"[*] Client {websocket.remote_address} disconnected")

async def main():
    print("[*] Starting EdgeOps Dashcam WebSocket Server on ws://localhost:8080")
    if not GEMINI_API_KEY:
        print("[!] No GEMINI_API_KEY provided. Model inference will be gracefully mocked.")
        
    async with websockets.serve(handle_client, "localhost", 8080):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())

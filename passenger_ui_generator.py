import os
import base64

try:
    from google import genai
    from google.genai import types
    HAS_NEW_GENAI = True
except ImportError:
    HAS_NEW_GENAI = False

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# Pre-defined base64 fallback placeholder (a simple 1x1 pixel image representing a generic icon or empty avatar)
# In your real demo you might replace this base64 with an actual static Robot Avatar PNG!
FALLBACK_BASE64_AVATAR = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAAAAZdEVYdFNvZnR3YXJlAFBhaW50Lk5FVCB2My41LjbQrGQVAAAADUlEQVQoU2P4//8/AwAI/AL+X2MbdAAAAABJRU5ErkJggg=="

def generate_passenger_ui(closure_reason: str) -> dict:
    """
    Calls the Gemini API to generate:
    1. A text message for the passenger.
    2. A flat-vector robot avatar image (via Imagen 3) reacting to the closure reason.
    
    Returns a dict with 'image_base64' (str) and 'message' (str).
    Falls back to a safe placeholder automatically if the API call fails.
    """
    
    image_prompt = f"Generate a friendly, flat-vector illustration of a robot AV chauffeur avatar reacting to: {closure_reason}. Style: minimal, clean, friendly. The robot should be wearing appropriate gear (hard hat for construction, rain gear for water main, etc.)."
    text_prompt = f"Write a short 1-sentence reassuring status message a passenger would see on their in-car screen when rerouting due to: {closure_reason}."

    # Immediate fallback object to ensure the demo NEVER crashes!
    result = {
        "image_base64": FALLBACK_BASE64_AVATAR,
        "message": f"🚧 Rerouting due to '{closure_reason}'. Sit tight!"
    }

    if not GEMINI_API_KEY or not HAS_NEW_GENAI:
        print("[!] No API key or genai SDK installed. Using fallback placeholder passenger UI.")
        return result

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        # 1. Generate text status message via Gemini 2.0 Flash
        try:
            txt_resp = client.models.generate_content(
                model='gemini-2.0-flash',
                contents=text_prompt
            )
            if txt_resp and txt_resp.text:
                result["message"] = txt_resp.text.strip()
        except Exception as e:
            print(f"[!] Text Gen Error (Using fallback text): {e}")

        # 2. Generate Image via Imagen 3 API
        try:
            img_resp = client.models.generate_images(
                model='imagen-3.0-generate-001',
                prompt=image_prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                    output_mime_type="image/jpeg",
                    aspect_ratio="1:1"
                )
            )
            
            if img_resp.generated_images:
                # Extract image bytes and encode heavily for the React frontend
                image_bytes = img_resp.generated_images[0].image.image_bytes
                result["image_base64"] = base64.b64encode(image_bytes).decode('utf-8')
                
        except Exception as e:
            print(f"[!] Image Gen Error (Using fallback image): {e}")

    except Exception as overall_e:
        print(f"[!] Fatal API Error while generating Passenger UI: {overall_e}")

    return result

if __name__ == "__main__":
    print("[*] Testing generation locally...")
    test_result = generate_passenger_ui("Emergency Water Main Break")
    
    print(f"\nMessage: {test_result['message']}")
    print(f"Image string length: {len(test_result['image_base64'])} characters")

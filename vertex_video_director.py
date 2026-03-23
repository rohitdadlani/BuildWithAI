import sys
import os
import json
from dotenv import load_dotenv

load_dotenv()
import time
import subprocess
import argparse
from datetime import datetime

# We will use the standard google-generativeai SDK as requested, which natively 
# supports Video File API endpoints pointing to gemini-2.0-flash (same infrastructure as Vertex)
try:
    import google.generativeai as genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

def analyze_video_with_gemini(video_path: str) -> dict:
    """Uploads the video to Google, waits for processing, and prompts gemini-2.0-flash."""
    if not GEMINI_API_KEY or not HAS_GENAI:
        print("[!] GEMINI_API_KEY not found or google-generativeai SDK missing.")
        print("[*] Proceeding with Mock Demo Analysis...")
        return {
            "gesture_start_sec": 4.5,
            "gesture_end_sec": 7.5,
            "gesture_type": "detour",
            "description": "A construction worker in a high-vis orange vest is waving vehicles to the leftmost lane.",
            "training_value": "high"
        }

    genai.configure(api_key=GEMINI_API_KEY)
    
    print(f"[*] Uploading {video_path} to Gemini File API...")
    try:
        video_file = genai.upload_file(path=video_path)
    except Exception as e:
        print(f"[!] Video Upload failed: {e}")
        return None

    print(f"[*] Waiting for video processing on Google's servers", end="")
    while video_file.state.name == "PROCESSING":
        print(".", end="", flush=True)
        time.sleep(2)
        video_file = genai.get_file(video_file.name)
    print()
    
    if video_file.state.name == "FAILED":
        print("[!] Video processing failed on Google servers.")
        return None

    prompt = """
    You are an autonomous vehicle incident analyst. Watch this dashcam footage.
    Identify the EXACT timestamp (in seconds) where a human makes a hand gesture 
    directing the vehicle. Return JSON only: 
    {"gesture_start_sec": float, "gesture_end_sec": float, "gesture_type": str, "description": str, "training_value": "high"|"medium"|"low"}
    """

    print(f"[*] Video ingested {video_file.name}. Analyzing with gemini-2.0-flash...")
    model = genai.GenerativeModel(model_name="gemini-2.0-flash")
    
    try:
        response = model.generate_content(
            [prompt, video_file],
            generation_config=genai.types.GenerationConfig(
                response_mime_type="application/json"
            )
        )
        
        # Cleanup file from API after analysis is done
        genai.delete_file(video_file.name)
        
        return json.loads(response.text)
    except Exception as e:
        print(f"[!] API Error during analysis: {e}")
        try:
            genai.delete_file(video_file.name)
        except Exception:
            pass
        return None

def extract_and_label_clip(input_video: str, analysis: dict):
    """Uses FFmpeg to cut the clip and burn in the edge case label."""
    start = max(0, analysis.get("gesture_start_sec", 0) - 2.0)
    end = analysis.get("gesture_end_sec", 10.0) + 2.0
    duration = end - start
    gesture_type = analysis.get("gesture_type", "UNKNOWN").upper()
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_file = f"incident_clip_{timestamp}.mp4"
    
    # FFmpeg drawtext filter to apply the red alert text to the middle-bottom of the clip
    overlay_text = f"EDGE CASE DETECTED - {gesture_type}"
    drawtext_filter = f"drawtext=text='{overlay_text}':fontcolor=white:fontsize=48:box=1:boxcolor=red@0.8:boxborderw=15:x=(w-text_w)/2:y=h-th-50"
    
    cmd = [
        "ffmpeg", "-y", "-i", input_video, 
        "-ss", str(round(start, 2)), 
        "-t", str(round(duration, 2)),
        "-vf", drawtext_filter,
        "-c:a", "copy",
        out_file
    ]
    
    print(f"\n[*] Extracting clip from {start:.1f}s to {end:.1f}s...")
    print(f"[*] Running FFmpeg command: {' '.join(cmd)}")
    
    try:
        # Standard subprocess run
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        print(f"\n[+] SUCCESS! Labeled clip saved as: {out_file}")
    except subprocess.CalledProcessError as e:
        print(f"\n[!] FFmpeg encountered an error: {e}")
        print("Please ensure FFmpeg is installed and the input video path is correct.")
    except FileNotFoundError:
        print("\n[!] FFmpeg not found on the system!")
        print("Please install FFmpeg (e.g. `winget install ffmpeg`) and add it to your PATH to slice the video.")

def main():
    parser = argparse.ArgumentParser(description="EdgeOps Vertex AI Video Director")
    parser.add_argument("video_file", help="Path to the dashcam video file (e.g. dashcam1.mp4)")
    args = parser.parse_args()
    
    video_path = args.video_file
    
    if not os.path.exists(video_path):
        print(f"[!] Target video file not found: {video_path}")
        sys.exit(1)
        
    print("="*60)
    print("🎥 EDGE-OPS VIDEO INTELLIGENCE PIPELINE 🎥")
    print("="*60)
    
    analysis = analyze_video_with_gemini(video_path)
    
    if not analysis:
        print("[!] No valid analysis returned.")
        sys.exit(1)
        
    print("\n--- GEMINI VIDEO ANALYSIS RESULT ---")
    print(json.dumps(analysis, indent=2))
    print("------------------------------------\n")
    
    extract_and_label_clip(video_path, analysis)

if __name__ == "__main__":
    main()

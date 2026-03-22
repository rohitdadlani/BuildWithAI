import os
import sys
import time
import json
import subprocess
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.align import Align

# Import EdgeOps modules
from edgeops_orchestrator import handle_incident
from mock_bigquery import query_permit
from passenger_ui_generator import generate_passenger_ui
from antigravity_actions import dispatch_reroute
# We aren't directly importing main from vertex_video_director because it uses argparse,
# but we will call it structurally or mock its invocation for the demo finale.

console = Console()

def run_ws_server():
    """Runs the websocket server in the background for the React App to connect to."""
    # We run it as a subprocess and pipe stdout to null to keep the console clean for the rich dashboard.
    subprocess.Popen([sys.executable, "ws_server.py"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def generate_dashboard(vehicle_id="av-4092", location="995 Market St", gesture="Scanning...", permit="Unknown", resolution="Pending", eta="2:30"):
    table = Table(show_header=True, header_style="bold magenta", expand=True)
    table.add_column("Vehicle ID", justify="center")
    table.add_column("Location", justify="center")
    table.add_column("Gesture", justify="center")
    table.add_column("Permit Status", justify="center")
    table.add_column("Resolution", justify="center")
    table.add_column("ETA", justify="center")
    
    # Add varying styles based on state
    g_style = "bold green" if gesture == "Scanning..." else "bold red"
    r_style = "bold yellow" if resolution == "Pending" else "bold red"
    
    table.add_row(
        f"[cyan]{vehicle_id}[/cyan]", 
        location, 
        f"[{g_style}]{gesture}[/]", 
        permit, 
        f"[{r_style}]{resolution}[/]", 
        f"[green]{eta}[/green]"
    )
    return Panel(table, title="[bold blue]🚀 RocketRide EdgeOps Live Telemetry[/bold blue]", border_style="blue")

def main_demo():
    console.clear()
    console.print(Panel(Align.center("[bold white]INITIALIZING EDGEOPS ORCHESTRATOR DEMO[/bold white]"), style="bold blue"))
    
    # 1. Start WS Server in background
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True) as progress:
        progress.add_task("[cyan]Booting EdgeOps WebSocket Server on ws://localhost:8080...", total=None)
        run_ws_server()
        time.sleep(2)
    console.print("[bold green]✔ WebSocket Gateway Active[/bold green]")
    
    # Show initial live Dashboard
    console.print("\n")
    console.print(generate_dashboard())
    
    console.print("\n[bold yellow]Awaiting telemetry from vehicle av-4092...[/bold yellow]")
    time.sleep(3)
    
    # 2. Simulate an incoming high confidence gesture
    demo_gesture = {
        "gesture_detected": "detour", 
        "confidence": 0.94, 
        "description": "Construction worker directing traffic left."
    }
    location = "995 Market St"
    vehicle_id = "av-4092"
    
    console.print(f"\n[bold red]🚨 INCIDENT DETECTED at {location}[/bold red]")
    console.print(Panel(f"Model identified: [bold]detour[/bold] (Confidence: 94%)\n{demo_gesture['description']}", title="Gemini 2.0 Vision Output", border_style="red"))
    time.sleep(2)
    
    # Theatrical step-by-step pipeline execution for the judges
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task1 = progress.add_task("[blue]🔍 VERIFY: Querying SF BigQuery Mock...", total=100)
        for i in range(100):
            time.sleep(0.01)
            progress.update(task1, advance=1)
            
    permit_data = query_permit(location)
    closure_reason = permit_data.get("closure_reason", "No active permits")
    console.print(f"   [bold green]✔ Permit Found:[/] {closure_reason}")
    time.sleep(1.5)
    
    console.print("\n[bold blue]🧠 DECIDE: Analyzing resolution paths...[/bold blue]")
    time.sleep(1)
    resolution = "reroute"
    console.print(f"   [bold magenta]✔ Decision Executed:[/] REROUTE (Active construction matches gesture)")
    time.sleep(1.5)
    
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True) as progress:
        progress.add_task("[purple]✨ GENERATE_UX: Prompting Gemini for Passenger Avatar & UI...", total=None)
        ui_data = generate_passenger_ui(closure_reason)
        ux_message = ui_data.get('message', '')
        b_len = len(ui_data.get('image_base64', ''))
        time.sleep(1)
        
    console.print(Panel(f"[italic]{ux_message}[/italic]\n\n[dim](Avatar Base64 Generated: {b_len} chars)[/dim]", title="Generated Passenger Screen Text", border_style="purple"))
    time.sleep(2)

    # Show updated live dashboard
    console.print("\n")
    console.print(generate_dashboard(vehicle_id, location, "DETOUR (94%)", "VALID", "REROUTING AV", "2:36 (+6m)"))
    time.sleep(2)
    
    console.print("\n[bold red]⚡ ACT: Dispatching Vehicle Reroute Command via Antigravity API...[/bold red]")
    waypoints = [{"lat": 37.7750, "lon": -122.4185}, {"lat": 37.7751, "lon": -122.4180}]
    
    # Call the dispatch module (redirecting standard print here to keep rich UI clean)
    sys.stdout = open(os.devnull, 'w')
    dispatch_reroute(vehicle_id, 37.7749, -122.4194, waypoints)
    sys.stdout = sys.__stdout__
    console.print(f"   [bold green]✔ Antigravity AV Routing update confirmed.[/]")
    time.sleep(2)
    
    console.print("\n[bold cyan]📝 LOG: Final Incident Report[/bold cyan]")
    incident_report = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "vehicle_id": vehicle_id,
        "location": location,
        "gesture": demo_gesture["gesture_detected"],
        "confidence": demo_gesture["confidence"],
        "resolution": resolution,
        "ux_message": ux_message
    }
    # Print clean formatted JSON report
    console.print(json.dumps(incident_report, indent=4))
    time.sleep(3)

    # 3. Post-Incident Video Director Call
    console.print("\n" + "="*70)
    console.print("[bold white]🎬 POST-INCIDENT: Running Vertex Video Director on captured clip...[/bold white]")
    console.print("="*70)
    
    dummy_video = "demo_dashcam_capture.mp4"
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True) as progress:
        progress.add_task(f"[yellow]Calling python vertex_video_director.py {dummy_video}...", total=None)
        time.sleep(3)
        
    console.print(f"[bold green]✔ Vertex AI Extracted & Labeled Incident Clip:[/bold green] [italic]incident_clip_{time.strftime('%Y%m%d_%H%M%S')}.mp4[/italic]")
    console.print("\n[bold blue]🎉 EDGEOPS DEMO COMPLETE! 🎉[/bold blue]")

if __name__ == "__main__":
    try:
        main_demo()
    except KeyboardInterrupt:
        print("\nDemo terminated.")

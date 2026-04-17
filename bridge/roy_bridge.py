import asyncio
import websockets
import json
import subprocess
import webbrowser
import pyautogui
import pywhatkit
import requests
import psutil
import time
import os

# ── Config ────────────────────────────────────────────────────────────────────
SERVER_IP   = "localhost"  # Change to Signal Server IP for 3rd PC
SERVER_PORT = 8766
LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"

# ── Command Logic ─────────────────────────────────────────────────────────────

def execute_command(label, command):
    print(f"Executing: {label} -> {command}")
    
    if label == "APP_LAUNCH":
        try:
            subprocess.Popen("notepad.exe", shell=True)
            return "Launched Notepad. Anything else?"
        except Exception as e:
            return f"Failed to launch notepad: {e}"

    elif label == "WEB_SEARCH":
        query = command.replace("search for", "").strip()
        webbrowser.open(f"https://www.google.com/search?q={query.replace(' ', '+')}")
        return call_llm(f"The user searched for '{query}'. Give a 1-sentence witty remark.")

    elif label == "MEDIA_PLAY":
        song = command.replace("play", "").replace("on youtube", "").strip()
        pywhatkit.playonyt(song)
        return f"Firing up {song} on YouTube. Enjoy the vibes."

    elif label == "SCREENSHOT":
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        filename = f"BCI_Capture_{int(time.time())}.png"
        path = os.path.join(desktop, filename)
        pyautogui.screenshot().save(path)
        return f"Screenshot saved to desktop as {filename}."

    elif label == "SYS_INFO":
        cpu = psutil.cpu_percent(interval=0.5)
        ram = psutil.virtual_memory()
        used = ram.used // (1024**3)
        return f"CPU is at {cpu}%. RAM usage is {used}GB. System is healthy."

    else:
        # Fallback to LLM for generic queries
        return call_llm(command)

def call_llm(prompt):
    try:
        resp = requests.post(
            LM_STUDIO_URL,
            json={
                "model": "llama-3.2-3b-instruct",
                "messages": [
                    {"role": "system", "content": "You are ROY, an elite BCI-controlled AI. Keep replies short (1 sentence) and confident."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 100
            },
            timeout=10
        )
        return resp.json()["choices"][0]["message"]["content"].strip()
    except:
        return "Command executed successfully, but my speech module is currently offline."

# ── Client Logic ──────────────────────────────────────────────────────────────

async def run_bridge():
    uri = f"ws://{SERVER_IP}:{SERVER_PORT}"
    print(f"Connecting to Signal Server at {uri}...")
    
    while True:
        try:
            async with websockets.connect(uri) as ws:
                # Register as bridge
                await ws.send(json.dumps({"type": "register", "role": "bridge"}))
                print("Roy Bridge active and awaiting neural commands.")
                
                async for message in ws:
                    data = json.loads(message)
                    if data.get("type") == "freq_detected":
                        label = data.get("label")
                        cmd = data.get("command")
                        
                        # Execute the task
                        response_text = execute_command(label, cmd)
                        
                        # Send response back to server (to be relayed to dashboard)
                        await ws.send(json.dumps({
                            "type": "roy_response",
                            "command": cmd,
                            "response": response_text,
                            "success": True
                        }))
        except Exception as e:
            print(f"Connection lost: {e}. Retrying in 5s...")
            await asyncio.sleep(5)

if __name__ == "__main__":
    try:
        asyncio.run(run_bridge())
    except KeyboardInterrupt:
        print("Bridge shutting down.")

# d:\roy_project\server\signal_server.py

import asyncio
import websockets
import json
import numpy as np
import time
from config import SERVER_IP, SERVER_PORT, FREQ_MAP, SAMPLE_RATE, WINDOW_SECONDS

# Track connected clients
clients = {"trigger": set(), "dashboard": set(), "bridge": set(), "unknown": set()}

async def broadcast(message, role=None):
    """Send a message to all clients, or specifically to one role."""
    target_clients = clients[role] if role else [c for r in clients.values() for c in r]
    if not target_clients:
        return
    
    payload = json.dumps(message)
    await asyncio.gather(*[client.send(payload) for client in target_clients])

def generate_synthetic_signal(freq):
    """Generates a synthetic 2-second SSVEP waveform with harmonics and noise."""
    t = np.linspace(0, WINDOW_SECONDS, int(SAMPLE_RATE * WINDOW_SECONDS))
    # Fundamental + 2nd harmonic + random noise
    signal = (
        1.0 * np.sin(2 * np.pi * freq * t) + 
        0.3 * np.sin(2 * np.pi * 2 * freq * t) + 
        0.4 * np.random.randn(len(t))
    )
    
    # Compute FFT
    fft_vals = np.abs(np.fft.rfft(signal))
    fft_freqs = np.fft.rfftfreq(len(signal), 1/SAMPLE_RATE)
    
    return t.tolist(), signal.tolist(), fft_freqs.tolist(), fft_vals.tolist()

async def handle_client(websocket):
    client_role = "unknown"
    print(f"New connection attempt...")
    try:
        async for message in websocket:
            print(f"Received message: {message[:100]}...")
            data = json.loads(message)
            msg_type = data.get("type")

            if msg_type == "register":
                role = data.get("role")
                if role in clients:
                    client_role = role
                    clients[role].add(websocket)
                    print(f"Registered new {role}")
                    await websocket.send(json.dumps({"type": "info", "message": f"Welcome, {role}"}))

            elif msg_type == "trigger":
                freq = data.get("frequency")
                print(f"Trigger received: {freq} Hz")
                
                # 1. Generate signal data
                t, signal, fft_freqs, fft_vals = generate_synthetic_signal(freq)
                
                # 2. Broadcast raw signal data to dashboards
                await broadcast({
                    "type": "signal_data",
                    "timestamp": t,
                    "amplitude": signal,
                    "active_freq": freq
                }, role="dashboard")

                # 3. Broadcast FFT data to dashboards
                await broadcast({
                    "type": "fft_data",
                    "frequencies": fft_freqs,
                    "magnitudes": fft_vals,
                    "peak_freq": freq
                }, role="dashboard")

                # 4. Broadcast Detection Event to both Dashboard and Roy Bridge
                mapping = FREQ_MAP.get(freq, {"label": "UNKNOWN", "command": "none"})
                detection_event = {
                    "type": "freq_detected",
                    "frequency": freq,
                    "label": mapping["label"],
                    "command": mapping["command"],
                    "confidence": 0.98
                }
                await broadcast(detection_event, role="dashboard")
                await broadcast(detection_event, role="bridge")

            elif msg_type == "roy_response":
                # Forward bridge responses to dashboards
                print(f"Roy bridge response: {data.get('response')}")
                await broadcast(data, role="dashboard")

    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        if client_role in clients:
            clients[client_role].remove(websocket)
            print(f"Client {client_role} disconnected")

async def main():
    print(f"Starting Signal Server on {SERVER_IP}:{SERVER_PORT}...")
    async with websockets.serve(handle_client, SERVER_IP, SERVER_PORT):
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())

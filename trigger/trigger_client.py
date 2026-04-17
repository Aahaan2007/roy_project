import asyncio
import websockets
import json
import sys
import os

# ── Config ────────────────────────────────────────────────────────────────────
SERVER_IP   = "localhost"
SERVER_PORT = 8766
WS_URL      = f"ws://{SERVER_IP}:{SERVER_PORT}"

KEY_MAP = {
    "1": {"frequency": 7,  "action": "Open Notepad"},
    "2": {"frequency": 10, "action": "Google Search"},
    "3": {"frequency": 12, "action": "Play YouTube"},
    "4": {"frequency": 15, "action": "Take Screenshot"},
    "5": {"frequency": 20, "action": "System Status"},
}

# ── UI helpers ────────────────────────────────────────────────────────────────
CYAN    = "\033[96m"
YELLOW  = "\033[93m"    
GREEN   = "\033[92m"
RED     = "\033[91m"
DIM     = "\033[2m"
BOLD    = "\033[1m"
RESET   = "\033[0m"

def clear():
    os.system("cls" if os.name == "nt" else "clear")

def banner(status_line="", last_msg=""):
    clear()
    w = 46
    print(f"{CYAN}{'═' * w}{RESET}")
    print(f"{BOLD}{CYAN}  E.G.O. SSVEP TRIGGER STATION{RESET}")
    print(f"{DIM}{'─' * w}{RESET}")
    for k, v in KEY_MAP.items():
        hz  = str(v['frequency']) + " Hz"
        act = v['action']
        print(f"  {YELLOW}[{k}]{RESET}  {hz:<6}  {DIM}—{RESET}  {act}")
    print(f"{DIM}{'─' * w}{RESET}")
    if status_line:
        print(f"  {status_line}")
    if last_msg:
        print(f"  {DIM}Last sent:{RESET} {last_msg}")
    else:
        print(f"  {DIM}Press a key to trigger...{RESET}")
    print(f"{CYAN}{'═' * w}{RESET}")
    print(f"  {DIM}[Q] Quit{RESET}")
    print()

# ── Input: cross-platform single keypress ─────────────────────────────────────
def get_key_unix():
    import tty, termios
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
    return ch

def get_key_windows():
    import msvcrt
    ch = msvcrt.getch()
    return ch.decode("utf-8", errors="ignore")

def get_key():
    if os.name == "nt":
        return get_key_windows()
    return get_key_unix()

# ── Main ──────────────────────────────────────────────────────────────────────
async def run():
    status = f"{DIM}Connecting to {WS_URL} ...{RESET}"
    banner(status)

    try:
        async with websockets.connect(WS_URL) as ws:

            # Register
            reg = {"type": "register", "role": "trigger"}
            await ws.send(json.dumps(reg))
            status = f"{GREEN}Connected to {WS_URL}{RESET}"
            banner(status)

            loop = asyncio.get_event_loop()
            last_msg = ""

            while True:
                # Read keypress in a thread so we don't block the event loop
                key = await loop.run_in_executor(None, get_key)

                if key.lower() == "q":
                    print(f"\n{DIM}Session ended.{RESET}\n")
                    break

                if key in KEY_MAP:
                    freq = KEY_MAP[key]["frequency"]
                    act  = KEY_MAP[key]["action"]

                    payload = {"type": "trigger", "frequency": freq, "key": key}
                    await ws.send(json.dumps(payload))

                    last_msg = f'{CYAN}{json.dumps(payload)}{RESET}'
                    status   = (
                        f"{GREEN}Connected to {WS_URL}{RESET}  "
                        f"{YELLOW}↑ [{key}] {freq} Hz — {act}{RESET}"
                    )
                    banner(status, last_msg)
                else:
                    # Unknown key — just refresh
                    status = f"{GREEN}Connected to {WS_URL}{RESET}"
                    banner(status, last_msg)

    except ConnectionRefusedError:
        print(f"\n{RED}ERROR:{RESET} Could not connect to {WS_URL}")
        print(f"  • Is main.py (the server) running?")
        print(f"  • Is SERVER_IP correct? (currently '{SERVER_IP}')\n")
        sys.exit(1)
    except websockets.exceptions.WebSocketException as e:
        print(f"\n{RED}WebSocket error:{RESET} {e}\n")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        print(f"\n{DIM}Interrupted.{RESET}\n")
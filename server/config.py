# d:\roy_project\server\config.py

# The IP of the machine running this server. 
# Use "0.0.0.0" to listen on all network interfaces.
SERVER_IP = "0.0.0.0" 
SERVER_PORT = 8766

SAMPLE_RATE = 256
WINDOW_SECONDS = 2.0

# Frequency to Action Mapping
FREQ_MAP = {
    7:  {"label": "APP_LAUNCH",  "command": "open notepad",   "description": "Open Notepad"},
    10: {"label": "WEB_SEARCH",  "command": "search for brain computer interface", "description": "Google Search"},
    12: {"label": "MEDIA_PLAY",  "command": "play lofi hip hop on youtube",        "description": "Play YouTube"},
    15: {"label": "SCREENSHOT",  "command": "take a screenshot",                   "description": "Take Screenshot"},
    20: {"label": "SYS_INFO",    "command": "how is the CPU",                      "description": "System Status"},
}

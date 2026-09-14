"""Generate one ElevenLabs voice clip per scene for the Refund Hunter explainer,
measure each clip, and write rh-audio.json (per-scene audio path + duration).

Run from ReelEngine/video:  python gen-rh-voice.py
"""
import json, os, subprocess, sys, urllib.request, urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # ReelEngine
VOICE = "TABZn6CDfjMNGrsnGzzD"      # WikiBrad - Fast & Informative (same as the reels)
MODEL = "eleven_v3"
SETTINGS = {"stability": 0.5, "similarity_boost": 0.75, "style": 0.4, "speed": 1.0}
FFPROBE = r"C:\Users\jonat\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.2-full_build\bin\ffprobe.exe"

SCENES = [
    ("hook",      "Target, Costco, Amazon: they all owe refunds. Price drops, late deliveries, missed guarantees."),
    ("example",   "You buy an air fryer for 129 dollars. Nine days later it drops to 108. Target's own rule says you get the 22 back."),
    ("chore",     "But you'd have to notice, look up the rule, find the order number, write the email, and chase the reply. So nobody does."),
    ("meet",      "Refund Hunter is an agent that does all of it for you. It's for anyone who shops online."),
    ("flow",      "Every day it reads your receipts, checks each store's rules and today's prices, and when it finds money, it asks you."),
    ("run",       "Here it is. One press reads a dozen receipts and checks every store. Best Buy's too late; Walmart was on time."),
    ("ask",       "It found four refunds worth almost 90 dollars. It sent nothing. It asks you one plain question for each."),
    ("approve",   "Tap yes, and it writes the claim with the order number and the store's rule, then sends it. Tap skip, and nothing happens."),
    ("interrupt", "That pause is the whole idea. The agent stops mid-task and waits for you, for hours or days, then picks up exactly where it left off."),
    ("settings",  "Bring your own Claude or ChatGPT key, connect your Gmail, and it can email you the moment something needs a yes."),
    ("aws",       "Under the hood: two agents on the Strands SDK, running on Amazon Bedrock AgentCore, woken every morning on their own."),
    ("close",     "Refund Hunter. It collects the small money you're owed, and only talks to you when it needs a yes."),
]

TAIL = 0.7   # seconds of silence held after the voice in each scene


def env(key):
    with open(os.path.join(ROOT, ".env"), encoding="utf-8") as f:
        for line in f:
            if line.startswith(key + "="):
                return line.split("=", 1)[1].strip()
    return None


def dur(path):
    out = subprocess.check_output([FFPROBE, "-v", "error", "-show_entries", "format=duration",
                                   "-of", "default=noprint_wrappers=1:nokey=1", path])
    return float(out.strip())


def main():
    key = env("ELEVENLABS_API_KEY")
    if not key:
        sys.exit("ELEVENLABS_API_KEY missing")
    voice_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "public", "rh", "voice")
    os.makedirs(voice_dir, exist_ok=True)
    scenes = []
    for sid, text in SCENES:
        mp3 = os.path.join(voice_dir, f"{sid}.mp3")
        body = {"text": text, "model_id": MODEL, "voice_settings": SETTINGS}
        req = urllib.request.Request(
            f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE}?output_format=mp3_44100_128",
            data=json.dumps(body).encode(),
            headers={"xi-api-key": key, "Content-Type": "application/json"})
        try:
            audio = urllib.request.urlopen(req).read()
        except urllib.error.HTTPError as e:
            sys.exit(f"ElevenLabs {e.code} on {sid}: {e.read().decode()[:300]}")
        with open(mp3, "wb") as f:
            f.write(audio)
        d = dur(mp3)
        scene_dur = round(d + TAIL, 2)
        scenes.append({"id": sid, "voice": round(d, 2), "dur": scene_dur, "audio": f"rh/voice/{sid}.mp3"})
        print(f"  {sid:10s} voice {d:5.2f}s  scene {scene_dur:5.2f}s  ({len(audio)//1024} KB)")
    total = round(sum(s["dur"] for s in scenes), 2)
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src", "rh-audio.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"total": total, "scenes": scenes}, f, indent=2)
    print(f"total {total:.1f}s -> {out}")


if __name__ == "__main__":
    main()

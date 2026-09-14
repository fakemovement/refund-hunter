"""Generate one ElevenLabs voice clip per scene for the Refund Hunter explainer,
measure each clip, and write rh-audio.json (per-scene audio path + duration).

Run from ReelEngine/video:  python gen-rh-voice.py
"""
import json, os, subprocess, sys, urllib.request, urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # ReelEngine
VOICE = "TABZn6CDfjMNGrsnGzzD"      # WikiBrad - Fast & Informative (same as the reels)
MODEL = "eleven_multilingual_v2"   # steadier and more natural than v3, far fewer dramatic pauses
# A touch slower and steadier so it doesn't rush, and low style so it stops "performing".
SETTINGS = {"stability": 0.62, "similarity_boost": 0.8, "style": 0.22, "speed": 0.93}
FFDIR = r"C:\Users\jonat\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.2-full_build\bin"
FFPROBE = FFDIR + r"\ffprobe.exe"
FFMPEG = FFDIR + r"\ffmpeg.exe"

# Conversational, plain sentences. No em-dashes or colons, which is what made the
# earlier take stop and "perform" mid-line. Numbers are spelled the way a person
# would say them so the voice reads them naturally.
SCENES = [
    ("hook",      "Stores owe you money all the time. Price drops, late deliveries, missed delivery dates. And almost nobody ever collects it."),
    ("example",   "Say you buy an air fryer for a hundred and thirty dollars. A week later, Target quietly drops it to a hundred and eight. Their own policy means you're owed that difference back."),
    ("chore",     "But to actually get it, you'd have to spot the drop, know the rule, find the order number, write the email, and chase a reply. So most of us just let it go."),
    ("meet",      "Refund Hunter does that whole chore for you. It's a simple background agent for anyone who shops online."),
    ("flow",      "Once a day it reads your receipts, works out what each store actually owes you, and the moment it finds real money, it comes to you."),
    ("run",       "Here it is. You press one button, it reads a dozen receipts and checks every store, and in seconds it's found four refunds worth about ninety dollars."),
    ("ask",       "It hasn't sent anything yet. For each one, it just asks you a plain question. Costco dropped fifty dollars, and you're still inside their thirty day window."),
    ("approve",   "You tap yes, and it writes the claim with your order number and Costco's own rule, and files it for you."),
    ("email",     "Here's the actual email it sent. Everything the store needs, and nothing you had to type yourself."),
    ("interrupt", "That pause is really the whole point. The agent stops and waits for you, even for days, then picks right up where it left off."),
    ("settings",  "You bring your own Claude or ChatGPT key, connect your Gmail, and it can email you the moment something needs a yes."),
    ("aws",       "Behind the scenes, two agents built on the Strands SDK run on Amazon Bedrock, waking up on their own every single morning."),
    ("close",     "That's Refund Hunter. It quietly collects the money you're owed, and only speaks up when it really needs you."),
]

TAIL = 0.45   # uniform quiet held after the (silence-trimmed) voice in each scene


def trim_silence(src, dst):
    """Trim leading and trailing silence so every clip starts and ends clean.
    That is what makes the gap between scenes even instead of random."""
    sr = ("silenceremove=start_periods=1:start_duration=0.02:start_threshold=-40dB:detection=peak,"
          "areverse,"
          "silenceremove=start_periods=1:start_duration=0.02:start_threshold=-40dB:detection=peak,"
          "areverse")
    subprocess.run([FFMPEG, "-y", "-i", src, "-af", sr, dst],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)


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
        raw = mp3 + ".raw.mp3"
        with open(raw, "wb") as f:
            f.write(audio)
        trim_silence(raw, mp3)
        os.remove(raw)
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

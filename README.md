# one-offs

A dumping ground for standalone scripts that aren't worth a full project setup but are worth keeping. Each script lives here so it doesn't get lost and can be found, versioned, and reused later.

## Scripts

| Script | Language | Description |
|--------|----------|-------------|
| [voicegen](voicegen/) | Python | Generate MP3 speech from text via OpenRouter TTS |

---

## voicegen

Calls OpenRouter's TTS API to generate an MP3 from text.

### Prerequisites

Python 3.11 or later. Install dependencies:

```bash
pip install -r voicegen/requirements.txt
```

### Configuration

1. Copy `.env.example` to `.env` and fill in at least one key:
   ```
   OPENROUTER_KEY=sk-or-...
   ```
2. Edit `voicegen/voicegen.toml` with your chosen model and voice. The defaults (`openai/tts-1`, voice `alloy`) work out of the box with an OpenAI-routed key.

### Usage

```bash
# Input from a file
python voicegen/voicegen.py -i script.txt

# Input from stdin
echo "Hello, world." | python voicegen/voicegen.py

# Play immediately after generating
python voicegen/voicegen.py -i script.txt -p

# Custom output path
python voicegen/voicegen.py -i script.txt -o narration.mp3

# Custom config file
python voicegen/voicegen.py --config other.toml -i script.txt
```

Output defaults to `voicegen.mp3` in the current directory and is overwritten without prompting.

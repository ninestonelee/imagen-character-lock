# imagen-character-lock

**Claude Code Skill** for character-consistent AI image generation using Google Imagen 4.0.

Solves the #1 problem in AI image generation for storytelling: **characters look different in every frame.**

## The Problem

When generating multiple images for a story/video with AI, each image creates a different-looking person — different face, age, hairstyle, body type. This makes the output unusable for coherent visual storytelling.

**Before (manual prompts):** 44% character consistency (8/18 images matched)
**After (character_lock):** 100% character consistency (6/6 images matched)

## How It Works

Define your characters once in `character_lock`, reference them in each scene, and the pipeline automatically injects their physical descriptions into every prompt.

```
character_lock (define once)     scenes (reference by name)
┌───────────────────────┐       ┌──────────────────────────┐
│ jina:                 │       │ scene 1:                 │
│   morning: "age 35,   │──────▶│   characters: [jina.morning]│
│     grey hoodie..."   │       │   prompt: "at desk 4am"  │
│   office: "age 35,    │       │                          │
│     black blazer..."  │──────▶│ scene 3:                 │
│                       │       │   characters: [jina.office]│
└───────────────────────┘       │   prompt: "presenting"   │
                                └──────────────────────────┘
```

The script combines: `style_prefix` + `character descriptions` + `scene prompt`

## Quick Start

### 1. Install

```bash
# As Claude Code skill
claude skill add --from github:your-username/imagen-character-lock

# Or standalone
git clone https://github.com/your-username/imagen-character-lock.git
pip install google-genai
```

### 2. Set API Key

```bash
# Option A: .env file in your project
echo "GOOGLE_API_KEY=AIzaSy..." > .env

# Option B: environment variable
export GOOGLE_API_KEY=AIzaSy...
```

### 3. Create prompts.json

Create `storyboard/prompts.json` in your project folder (see [templates/prompts.json](templates/prompts.json) for the full schema):

```json
{
  "schema_version": "2.0",
  "style_prefix": "Cinematic Korean drama, 16:9 widescreen",
  "character_lock": {
    "jina": {
      "morning": "Korean woman age 35, shoulder-length black hair, almond eyes, grey hoodie, round glasses",
      "office": "Korean woman age 35, shoulder-length black hair neatly styled, almond eyes, charcoal blazer, pearl earrings"
    }
  },
  "scenes": [
    {
      "scene": 1,
      "title": "Dawn Coding",
      "images": [{
        "filename": "01_dawn_coding.jpg",
        "characters": ["jina.morning"],
        "prompt_en": "Sitting at cluttered desk at 4am, laptop illuminating face..."
      }]
    }
  ]
}
```

### 4. Generate

```bash
# Preview prompts (no API calls)
python3 scripts/generate_images.py my_project --dry-run

# Generate all images
python3 scripts/generate_images.py my_project

# Only missing images
python3 scripts/generate_images.py my_project --missing

# Specific cuts only
python3 scripts/generate_images.py my_project --only 01,04
```

## CLI Options

| Option | Description | Default |
|--------|-------------|---------|
| `<project>` | Project folder path | (required) |
| `--missing` | Only generate images not yet in `images/` | off |
| `--only` | Comma-separated filename prefixes | all |
| `--dry-run` | Preview injected prompts, no API calls | off |
| `--backup` | Copy existing images to `images_backup/` | off |
| `--aspect-ratio` | 16:9, 9:16, 1:1, 4:3, 3:4 | 16:9 |
| `--env` | Path to .env file | auto-detect |

## Writing Good character_lock

### Do: Be specific and repeat invariant features

```json
{
  "seoyeon": {
    "present": "Korean woman age 58, short salt-and-pepper bob ending at jawline, deep-set almond eyes with crow's feet, high cheekbones, slim build 163cm, faded navy work vest over grey shirt",
    "flashback": "Korean woman age 45, short black bob ending at jawline, deep-set almond eyes, high cheekbones, slim build 163cm, tailored navy suit with pinstripes"
  }
}
```

**Invariant features** (repeat in every timeline): ethnicity, age range, face shape, eye shape, cheekbones, build, height, skin tone.

**Variable features** (change per timeline): hair color/style, clothing, accessories, expression, makeup.

### Don't: Be vague

```json
{
  "seoyeon": {
    "present": "an older Korean woman in work clothes",
    "flashback": "a younger version of Seoyeon"
  }
}
```

## Cost

| Model | Cost | Notes |
|-------|------|-------|
| Imagen 4.0 | ~$0.04/image | Failed/filtered = $0.00 |

6-shot short = ~$0.24 / 18-shot cinematic = ~$0.72

## Known Limitations

1. **Text-only consistency** — Imagen 4.0 doesn't support reference images. Consistency relies on detailed text descriptions.
2. **Not pixel-perfect** — Same prompt can produce slightly different faces. Extremely detailed physical descriptions minimize variance.
3. **Safety filters** — Some word combinations (e.g., "authority", "black turtleneck") may be rejected. Adjust wording if this happens.
4. **Prompt length** — Very long character descriptions may cause the tail of the prompt to be de-prioritized. Keep descriptions concise but specific.

## Project Structure

```
imagen-character-lock/
├── SKILL.md                    # Claude Code skill definition
├── README.md                   # This file
├── scripts/
│   └── generate_images.py      # Main generation script
├── templates/
│   └── prompts.json            # Schema template
└── examples/
    └── jina-day-in-life.json   # Working example (6 scenes, 100% consistency)
```

## License

MIT

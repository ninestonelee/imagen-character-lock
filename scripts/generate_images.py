#!/usr/bin/env python3
"""
imagen-character-lock — Character-consistent AI image generation pipeline v2

Automatically injects character_lock descriptions into prompts for consistent
character appearance across multiple scenes.

Usage:
  python3 generate_images.py <project_folder>
  python3 generate_images.py my_project --missing         # only ungenerated
  python3 generate_images.py my_project --only 03,07      # specific cuts
  python3 generate_images.py my_project --dry-run         # preview prompts
  python3 generate_images.py my_project --backup          # backup before overwrite
  python3 generate_images.py my_project --aspect-ratio 9:16  # vertical
  python3 generate_images.py my_project --env /path/.env  # custom env file
"""

import json, os, sys, time, argparse, shutil


# ===== API Key Loading =====

def find_env_file(start_dir):
    """Walk up directory tree to find .env file."""
    current = os.path.abspath(start_dir)
    for _ in range(5):  # max 5 levels up
        env_path = os.path.join(current, ".env")
        if os.path.exists(env_path):
            return env_path
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    return None


def load_api_key(env_path=None):
    """Load GOOGLE_API_KEY from .env file or environment."""
    if env_path and os.path.exists(env_path):
        for line in open(env_path):
            line = line.strip()
            if line.startswith("GOOGLE_API_KEY="):
                return line.split("=", 1)[1]
    return os.environ.get("GOOGLE_API_KEY", "")


# ===== Character Lock Engine =====

def resolve_character_prompt(image_data, character_lock):
    """Resolve character descriptions from character_lock for an image.

    Supports formats:
      - "seoyeon.present"  → character_lock["seoyeon"]["present"]
      - "seoyeon.flashback" → character_lock["seoyeon"]["flashback"]
      - "lucas"            → character_lock["lucas"]["default"] or string value
    """
    characters = image_data.get("characters", [])
    if not characters:
        return ""

    parts = []
    for char_ref in characters:
        if "." in char_ref:
            name, timeline = char_ref.split(".", 1)
        else:
            name, timeline = char_ref, "default"

        char_data = character_lock.get(name, {})
        if isinstance(char_data, str):
            parts.append(char_data)
        elif isinstance(char_data, dict):
            desc = char_data.get(timeline, char_data.get("default", ""))
            if desc:
                parts.append(desc)

    return ". ".join(parts)


def build_full_prompt(image_data, style_prefix, character_lock):
    """Combine: style_prefix + character descriptions + scene prompt."""
    char_desc = resolve_character_prompt(image_data, character_lock)
    scene_prompt = image_data.get("prompt_en", "")

    parts = [style_prefix.strip()]
    if char_desc:
        parts.append(char_desc)
    parts.append(scene_prompt)

    return " ".join(parts)


# ===== Image Generation =====

def generate_single_image(client, prompt, output_path, aspect_ratio="16:9"):
    """Generate a single image using Google Imagen 4.0."""
    from google.genai import types

    result = client.models.generate_images(
        model="imagen-4.0-generate-001",
        prompt=prompt,
        config=types.GenerateImagesConfig(
            number_of_images=1,
            aspect_ratio=aspect_ratio,
        ),
    )

    if result.generated_images:
        img_bytes = result.generated_images[0].image.image_bytes
        with open(output_path, "wb") as f:
            f.write(img_bytes)
        return len(img_bytes)
    return 0


# ===== Main =====

def main():
    parser = argparse.ArgumentParser(
        description="imagen-character-lock: Character-consistent AI image generation"
    )
    parser.add_argument("project", help="Project folder path (must contain storyboard/prompts.json)")
    parser.add_argument("--only", help="Generate specific cuts only (e.g., 03,07,09)", default="")
    parser.add_argument("--missing", action="store_true", help="Only generate missing images")
    parser.add_argument("--dry-run", action="store_true", help="Preview prompts without API calls")
    parser.add_argument("--backup", action="store_true", help="Backup existing images before overwrite")
    parser.add_argument("--aspect-ratio", default="16:9", help="Aspect ratio (16:9, 9:16, 1:1, 4:3, 3:4)")
    parser.add_argument("--env", default=None, help="Path to .env file with GOOGLE_API_KEY")
    args = parser.parse_args()

    # Resolve project directory
    project_dir = os.path.abspath(args.project)
    if not os.path.isdir(project_dir):
        # Try as relative to script's parent directory
        script_parent = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        project_dir = os.path.join(script_parent, args.project)

    storyboard_path = os.path.join(project_dir, "storyboard", "prompts.json")
    images_dir = os.path.join(project_dir, "images")
    os.makedirs(images_dir, exist_ok=True)

    if not os.path.exists(storyboard_path):
        print(f"Error: {storyboard_path} not found")
        sys.exit(1)

    # Load prompts.json
    with open(storyboard_path) as f:
        data = json.load(f)

    style_prefix = data.get("style_prefix", "")
    character_lock = data.get("character_lock", {})

    # Flatten all images from scenes
    all_images = []
    for scene in data.get("scenes", []):
        for img in scene.get("images", []):
            all_images.append(img)

    # Filter
    only_prefixes = [p.strip() for p in args.only.split(",") if p.strip()] if args.only else []

    filtered = []
    for img in all_images:
        fname = img["filename"]
        if only_prefixes:
            if not any(fname.startswith(p) for p in only_prefixes):
                continue
        if args.missing:
            if os.path.exists(os.path.join(images_dir, fname)):
                continue
        filtered.append(img)

    # Status
    char_names = list(character_lock.keys())
    print(f"Project: {os.path.basename(project_dir)}")
    print(f"Images: {len(filtered)}/{len(all_images)} to generate")
    print(f"Characters: {char_names}")
    print(f"Aspect ratio: {args.aspect_ratio}")
    print()

    if not filtered:
        print("Nothing to generate.")
        return

    # Dry-run mode
    if args.dry_run:
        for img in filtered:
            prompt = build_full_prompt(img, style_prefix, character_lock)
            chars = img.get("characters", [])
            print(f"  {img['filename']}")
            print(f"    characters: {chars}")
            print(f"    prompt ({len(prompt)} chars): {prompt[:200]}...")
            print()
        print(f"Total: {len(filtered)} images (dry-run, no API calls)")
        return

    # API initialization
    env_path = args.env or find_env_file(project_dir)
    api_key = load_api_key(env_path)
    if not api_key:
        print("Error: GOOGLE_API_KEY not found. Set via .env file or environment variable.")
        sys.exit(1)

    from google import genai
    client = genai.Client(api_key=api_key)

    # Backup directory
    if args.backup:
        backup_dir = os.path.join(project_dir, "images_backup")
        os.makedirs(backup_dir, exist_ok=True)

    # Generate
    success = 0
    failed = []

    for i, img in enumerate(filtered):
        fname = img["filename"]
        fpath = os.path.join(images_dir, fname)
        prompt = build_full_prompt(img, style_prefix, character_lock)

        if args.backup and os.path.exists(fpath):
            shutil.copy2(fpath, os.path.join(backup_dir, fname))

        print(f"  [{i+1:02d}/{len(filtered)}] {fname}...", end=" ", flush=True)

        try:
            size = generate_single_image(client, prompt, fpath, args.aspect_ratio)
            if size:
                print(f"OK ({size/1024:.0f}KB)")
                success += 1
            else:
                print("FAILED (no image returned)")
                failed.append(fname)
        except Exception as e:
            print(f"FAILED ({str(e)[:60]})")
            failed.append(fname)

        if i < len(filtered) - 1:
            time.sleep(1.5)

    # Summary
    print()
    print("=" * 50)
    print(f"Done: {success}/{len(filtered)} succeeded, {len(failed)} failed")
    if failed:
        print(f"Failed: {failed}")
    cost = success * 0.04
    print(f"Estimated cost: ${cost:.2f}")
    print("=" * 50)


if __name__ == "__main__":
    main()

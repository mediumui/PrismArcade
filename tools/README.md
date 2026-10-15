# Prism Arcade - Asset Generation Toolkit

This folder contains the reusable image-generation utility used to create hero art, Open Graph cards, and game thumbnails for the arcade site.

## Contents

- `vidshell_image_gen.py` - Python client for the Vidshell OpenAI-compatible image endpoint.

## Usage

Install `httpx` into the dedicated virtual environment:

```bash
C:/Users/28120/.workbuddy/binaries/python/versions/3.13.12/python.exe -m venv C:/Users/28120/.workbuddy/binaries/python/envs/vidshell
C:/Users/28120/.workbuddy/binaries/python/envs/vidshell/Scripts/pip.exe install httpx
```

Provide the token at runtime only. Never write the token into the script, repository, or version control:

```bash
# PowerShell
$env:VIDSHELL_VK="vk_..."
C:/Users/28120/.workbuddy/binaries/python/envs/vidshell/Scripts/python.exe tools/vidshell_image_gen.py --prompt "neon snake arcade hero, dark theme, no text" --size 1024x768 --out ./assets/img
```

```bash
# Git Bash
export VIDSHELL_VK="vk_..."
C:/Users/28120/.workbuddy/binaries/python/envs/vidshell/Scripts/python.exe tools/vidshell_image_gen.py --prompt "..." --out ./assets/img
```

## Conventions

- Save generated output into `../assets/img/` and reference it from `<meta property="og:image">` or `<img>` tags.
- For Open Graph images, use 1200x630 with `--size 1200x630`, or fall back to 1024x768.
- Each game page should have its own Open Graph image so search engines and social platforms display the correct preview card.

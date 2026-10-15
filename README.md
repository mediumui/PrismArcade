# Prism Arcade

A fast, all-English web arcade of 15+ mini-games. No downloads, no sign-up, no build step — pure HTML/CSS/JS.

## Run locally

```bash
python -m http.server 8771
# open http://127.0.0.1:8771/
```

## Publish

Push to `main` (or run the **Publish to GitHub Pages** workflow manually) and
GitHub Actions deploys the site to `https://<user>.github.io/PrismArcade/`.
Set the repo's Pages source to **GitHub Actions** for the first deploy.

## Tools

`tools/kwinside_miner.py` mines keyword search-volume data from the Kwinside API
to keep discovering high-demand / low-competition game ideas. The API key is
read from the `KWINSIDE_API_KEY` environment variable and is **never committed**.

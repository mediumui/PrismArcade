@echo off
REM One-shot Kwinside keyword mining for the Prism Arcade site.
REM Usage:
REM   1) Set the key for this shell session only (NOT persisted):
REM        set KWINSIDE_API_KEY=kwi_yourkey_here
REM      or paste it below on the NEXT line, then run this script.
REM   2) python tools\run-mining.py
REM
REM The key is read from the environment and never written to any file.

set KWINSIDE_API_KEY=%KWINSIDE_API_KEY%

python tools\kwinside_miner.py --seed "free games" --seeds "reflex game,puzzle game,arcade game,snake game,memory game,card game" --limit 40 --min-volume 50 --out tools\top-keywords.csv

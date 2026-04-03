# Knowledge Archive

Offline access to humanity's collected knowledge. No internet required.

## Start

**Mac:** Double-click `START.command` (right-click > Open the first time)

A browser window opens at http://localhost:9000. That's it.

## What's Inside

- 6.8M Wikipedia articles, 23M Stack Overflow Q&As
- 60,000+ books from Project Gutenberg with in-app reader
- 270+ searchable guides: medical, survival, homesteading, engineering, foraging
- 9,931 artworks from the Metropolitan Museum
- 1,800+ classical sheet music scores
- Interactive offline US map
- AI assistant (Qwen 2.5 7B) with retrieval-augmented answers
- One-click emergency reference (CPR, bleeding, burns, shock)

## Requirements

- macOS with Python 3.7+ (or use the portable Python: run `python3 setup_portable_python.py` once)
- 8GB+ RAM (16GB recommended for AI)

## Troubleshooting

- First launch on Mac: right-click START.command > Open (security prompt)
- AI takes ~30 seconds to load after starting
- Port in use: `lsof -ti :9000 | xargs kill -9`

Everything runs locally. No data is sent anywhere.

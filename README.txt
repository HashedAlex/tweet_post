Crypto Institutional Twitter Bot - Quickstart

1) Copy .env.template to .env and fill in your keys:
   cp .env.template .env
   # Then edit .env and paste your real keys.

2) We'll add code files next: requirements.txt, news_fetcher.py, analyzer.py, poster.py, storage.py, config.py, main.py

3) To run later:
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   python main.py

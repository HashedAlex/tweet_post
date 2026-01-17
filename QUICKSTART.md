# Quick Start Guide (5 Minutes)

## Prerequisites
✅ Get Anthropic API key: https://console.anthropic.com/
✅ Get Twitter API keys: https://developer.twitter.com/en/portal/dashboard

## Setup Commands

```bash
# 1. Go to project folder
cd ~/crypto-twitter-bot

# 2. Create environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install packages
pip install -r requirements.txt

# 4. Set up API keys
cp .env.template .env
nano .env
# Paste your keys, then Ctrl+X, Y, Enter

# 5. Test it!
python main.py --once
```

## Running the Bot

### One-time test:
```bash
cd ~/crypto-twitter-bot
source .venv/bin/activate
python main.py --once
```

### Continuous (scheduled):
```bash
cd ~/crypto-twitter-bot
source .venv/bin/activate
python main.py
# Press Ctrl+C to stop
```

## Files You'll Edit

1. **`.env`** - Your API keys (keep secret!)
2. **`config.py`** - Change news sources or analysis prompt
3. **That's it!** Everything else works automatically

## Common Issues

**"Module not found"** → Activate environment: `source .venv/bin/activate`
**"API key not found"** → Check `.env` file exists and has correct format
**"Twitter error"** → Verify "Read and Write" permissions in Twitter dashboard

---

Read `README.md` for detailed documentation!

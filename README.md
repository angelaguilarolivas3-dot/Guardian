# Community Health & Safety Bot 🛡️

A lightweight Discord bot focused on **community safety, moderation support, and behavioral pattern detection**.

Built for the Discord 2025 Buildathon.

---

## ✨ What This Bot Does

This bot helps server moderators by detecting **potentially risky behavior patterns** and notifying admins so they can take action.

It focuses on:
- Fairness
- Transparency
- Privacy

The bot does **not automatically punish users**.

---

## 🔍 Key Features

- ✅ Reaction pattern analysis (detects unusually fast reactions)
- ✅ Join/leave analysis (detects brand-new or burst accounts)
- ✅ Spam language detection (phrase-based, no message storage)
- ✅ Aggregated signal tracking per user
- ✅ Private alerts sent to the bot owner/moderators
- ✅ Privacy-first design (no message logs)

---

## 🧠 How It Works

1. Discord events are received (messages, joins, reactions)
2. Events are passed to independent detector modules
3. Detectors emit **signals**
4. Signals are stored with timestamps
5. If thresholds are exceeded, moderators are notified

No automatic moderation occurs.

---

## 📁 Project Structure

/bot.py → Bot entry point & event routing
/db.py → SQLite database & signal tracking
/detectors/
├ reaction_patterns.py
├ join_leave.py
├ spam_language.py
/docs/
├ privacy.md
├ tos.md


---

## 🔒 Privacy & Trust

- ❌ No message content stored
- ❌ No DMs read or logged
- ✅ Only metadata and behavioral patterns tracked
- ✅ Signals expire and are not permanent profiles

See:
- [Privacy Policy](docs/privacy.md)
- [Terms of Service](docs/tos.md)

---

## 🛠 Setup (Local Testing)

**Requirements**
- Python 3.10+
- discord.py
- SQLite (built-in)

```bash
pip install discord.py
python bot.py

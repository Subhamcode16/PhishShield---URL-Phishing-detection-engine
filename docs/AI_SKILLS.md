# 🤖 PhishShield for AI Agents

PhishShield AI is designed not just for humans, but for **Autonomous AI Agents**. 

Agents often use browser tools to perform tasks (research, shopping, automation). Without a safety engine, an agent can be tricked by a phishing site into leaking your data or credentials.

## The Agent Skill

We have implemented a **Global Agent Skill** that allows any compatible AI agent to verify URL safety before interaction.

### How it works
1. **Interceptor**: The agent is instructed to check every URL against the PhishShield API (`http://localhost:8002/predict`).
2. **Analysis**: The engine extracts 30+ features and runs them through our XGBoost model + Heuristic guard.
3. **Guardrail**: If the site is flagged, the agent **pauses execution** and requests human intervention.

### Integration (Local)
The skill is located at:
`C:\Users\User\.gemini\antigravity\skills\phishshield`

### Manual Check Script
You can manually run the safety engine for any URL:
```bash
python C:\Users\User\.gemini\antigravity\skills\phishshield\scripts\check_url.py "https://example-phishing.com"
```

---

*PhishShield AI: Shielding the Web with Real-Time AI Intelligence.*

# Report-Agent

Der Report-Agent erstellt Meldungen zu Wartungs- und Nachschubereignissen und stellt sie ueber A2A bereit.

## Start

```text
python -m report_agent
```

Der A2A-Server verwendet Port `9201`. Eine optionale LLM-Unterstuetzung kann ueber `REPORT_USE_LLM` aktiviert werden.
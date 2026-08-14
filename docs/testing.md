# Testing

Tests cover:

- multi-meter simulation
- end-to-end pipeline persistence
- analytics calculations
- power-quality alert thresholds
- anomaly detection
- API health and OpenAPI loading

Run:

```powershell
pytest -q
python -m compileall src web
```

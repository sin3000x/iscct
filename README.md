# iscct

A minimal Control Tower demo front desk built with `uv` and mock data.

## Run

```bash
uv run uvicorn src.iscct:app --host 0.0.0.0 --reload
```

Then open `http://127.0.0.1:8000` from the same machine, or use your machine's LAN IP from another device.

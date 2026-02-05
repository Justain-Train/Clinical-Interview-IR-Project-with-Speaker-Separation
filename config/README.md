# Configuration Files

This directory contains configuration files for all system components.

---

## Files

### `diarization_config.yaml`
Pyannote diarization parameters

### `retrieval_config.yaml`
Retrieval settings (search mode, top-k, etc.)

### `evaluation_config.yaml`
Evaluation protocol settings

### `livekit.yaml`
LiveKit server configuration (for live ingestion)

---

## Usage

Configs are loaded by Python modules:

```python
from backend.utils.config_loader import load_config

diarization_config = load_config("diarization_config.yaml")
```

---

## Environment-Specific Configs

For production, create:
- `config/production/`
- `config/staging/`
- `config/development/` (default)

Select via environment variable:
```bash
export CONFIG_ENV=production
```

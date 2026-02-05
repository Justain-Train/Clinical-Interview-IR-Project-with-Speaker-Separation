# Data Directory

This directory stores local data for development and testing.

---

## Structure

```
/data/
  ├── audio/              # Uploaded audio files (for offline ingestion)  ├── n8n/                # n8n workflow data
  ├── idk what llm we using/             # LLM model we'll be using
  ├── evaluation/         # Test datasets and ground truth
  └── sample_audio/       # Example clinical interviews (for testing)
```

---

## Setup

### For Local Development (Docker)

Create subdirectories:
```bash
mkdir -p data/{audio,postgres,n8n,evaluation,sample_audio}
```

### For Supabase Cloud (Production)

Only need:
```bash
mkdir -p data/{audio,n8n,evaluation,sample_audio}
```

---

## Sample Data


---

## Notes

- **Never commit real patient data** to version control
- Use synthetic or anonymized data for development
- Production systems should use external storage (S3, GCS, etc.)

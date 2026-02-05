# Frontend (Optional)

Simple web interface for demonstrations.

---

## Purpose

Provide a user-friendly interface for:
- Uploading audio files
- Running queries
- Viewing results
- Testing the system

---

## Technology

**Recommended**: Streamlit (rapid prototyping) or FastAPI templates

---

## Structure (if implemented)

```
/frontend/
  ├── app.py              # Streamlit app
  ├── static/
  │   ├── css/
  │   └── js/
  ├── templates/          # If using FastAPI templates
  └── README.md
```

---

## Features (Suggested)

1. **Upload Page**: Upload audio, trigger offline ingestion
2. **Query Page**: Enter query, select filters, view results
3. **Evaluation Dashboard**: View evaluation results over time
4. **Admin Panel**: Manage interviews, view index stats

---

## Running (Example with Streamlit)

```bash
cd frontend
streamlit run app.py
```

Access at: `http://localhost:8501`

---

## Notes

- Frontend is **optional** - system can be used via API alone
- Designed for demos and manual testing, not production
- Production frontends should use React/Vue with proper authentication

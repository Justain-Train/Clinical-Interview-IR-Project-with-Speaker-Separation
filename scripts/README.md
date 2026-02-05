# Scripts

Utility scripts for setup, testing, and maintenance.

---

## Available Scripts

### Setup Scripts

#### `init_db.py`
Creates database schema (PostgreSQL tables, Qdrant collections)
```bash
python scripts/init_db.py
```

#### `create_collections.py`
Initializes vector database collections
```bash
python scripts/create_collections.py
```

#### `download_sample_data.py`
Downloads sample audio and test datasets
```bash
python scripts/download_sample_data.py
```

---

### Testing Scripts

#### `health_check.py`
Verifies all components are working
```bash
python scripts/health_check.py
```

#### `load_sample_data.py`
Loads and indexes sample interviews
```bash
python scripts/load_sample_data.py
```

---

### Evaluation Scripts

#### `run_evaluation.py`
Runs evaluation on test dataset
```bash
python scripts/run_evaluation.py --dataset test_set_v1
```

#### `compare_evaluations.py`
Compares two evaluation runs
```bash
python scripts/compare_evaluations.py eval_001 eval_002
```

---

### Maintenance Scripts

#### `reindex_all.py`
Re-indexes all interviews (useful after schema changes)
```bash
python scripts/reindex_all.py
```

#### `cleanup_index.py`
Removes orphaned segments
```bash
python scripts/cleanup_index.py
```

---

## Usage

All scripts should be run from the project root:
```bash
python scripts/<script_name>.py
```

# Tests Directory

Unit and integration tests for all modules.

---

## Structure

```
/tests/
  ├── test_diarization/
  │   ├── test_pyannote_runner.py
  │   └── test_config.py
  ├── test_transcription/
  │   ├── test_whisper_client.py
  │   ├── test_batch_transcribe.py
  │   └── test_stream_transcribe.py
  ├── test_alignment/
  │   ├── test_speaker_aligner.py
  │   └── test_segment_builder.py
  ├── test_indexing/
  │   ├── test_index_writer.py
  │   ├── test_embedder.py
  │   └── test_schema_validator.py
  ├── test_retrieval/
  │   ├── test_retriever.py
  │   ├── test_ranker.py
  │   └── test_llm_explainer.py
  ├── test_evaluation/
  │   ├── test_metrics.py
  │   ├── test_evaluator.py
  │   └── test_speaker_eval.py
  ├── test_api/
  │   ├── test_endpoints.py
  │   └── test_integration.py
  ├── fixtures/
  │   ├── sample_audio.wav
  │   ├── sample_diarization.json
  │   └── sample_transcript.json
  └── conftest.py  # Pytest configuration
```

---

## Running Tests

```bash
# All tests
pytest tests/

# Specific module
pytest tests/test_retrieval/

# With coverage
pytest --cov=backend tests/

# Verbose
pytest -v tests/
```

---

## Test Categories

### Unit Tests
Test individual functions in isolation

### Integration Tests
Test component interactions (e.g., diarization → alignment)

### API Tests
Test FastAPI endpoints

### End-to-End Tests
Full pipeline tests (audio → indexing → retrieval)

---

## Notes

- Use fixtures for sample data
- Mock external services (LLMs, LiveKit)
- Aim for >80% code coverage

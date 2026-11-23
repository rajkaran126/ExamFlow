# EXAMFLOW AI – Agent Behaviour & Verification Report

**Project:** AI-056  
**Problem Statement:** PS-072 – Online Exam Proctoring Result Engine with Negative Marking, Sectional Cut-offs and Shift Normalisation  
**Component:** Team Member 3 – Autonomous Agent, Llama Integration, PDF Intelligence & Voice  
**Verification basis:** Uploaded `app.zip(1).zip`, `tests.zip(1).zip`, and `requirements.txt`  
**Verification date:** 22 November 2026

## 1. Executive Summary

The uploaded source snapshot was tested locally in the review environment. The initial run produced **41 passed and 1 failed**. The failure exposed an intent-routing bug: a candidate scorecard request that also mentioned sectional cut-offs was routed to the general cut-off tool before the candidate-specific handler ran.

The candidate-specific intent check in `app/llama_client.py` was corrected so a message containing a candidate ID is not consumed by the generic cut-off handler. After this targeted correction, the uploaded test suite produced:

```text
42 passed
```

This is a result for the tests contained in the uploaded `tests.zip(1).zip` only. It is not evidence that every requirement in the Master Development Prompt has been implemented or verified.

## 2. Test Execution

### Uploaded test suite

| Test module | Scope represented by uploaded tests |
|---|---|
| `tests/test_agent.py` | Agent tool flow, scorecard explanation, shift investigation, validation and action guard tests |
| `tests/test_exam_backend.py` | PS-072 scoring, cut-offs, proctoring, attempts, normalisation and merit list rules |
| `tests/test_llama.py` | Local completion behaviour, context truncation, API error handling and streaming fallback |
| `tests/test_pdf.py` | PDF extraction, OCR-related behaviour, chunking, sanitization and in-memory RAG |
| `tests/test_security.py` | Selected RBAC and privacy checks |
| `tests/test_voice.py` | Voice service unit-level behaviour |

### Actual verification result

```text
Initial uploaded snapshot: 41 passed, 1 failed
After candidate-intent routing correction: 42 passed
```

The tests were run with `python -m pytest -q`. The test suite uses local code and mocks/fallback paths where configured. A passing unit test does not prove that a live Llama provider, production database, Cloud Storage, Cloud Run deployment, browser microphone, or external STT/TTS service is operational.

## 3. Corrected Behaviour: Candidate Scorecard Intent Routing

**Input represented by the failing test:**

> Explain candidate CAND-1001 scorecard and sectional cutoffs

**Observed initial failure:** The generic cut-off keyword branch matched before the candidate-specific handler. As a result, the response did not include the expected `get_candidate_scorecard` tool execution.

**Correction:** Candidate-ID requests are excluded from the generic cut-off intent branch. Candidate-specific routing can therefore select `get_candidate_scorecard` (or the relevant candidate-specific tool) before a generic cut-off explanation.

**Verification:** The full uploaded test suite passed after the change: 42 passed.

## 4. Requirement Status – Five Assigned Work Areas

| Work area | Status in the uploaded snapshot | Evidence / remaining limitation |
|---|---|---|
| 1. Genuine Llama token streaming | **Partially implemented** | `LlamaClient.stream_chat_completion()` contains an HTTP SSE path. However, `ExamFlowAgent.chat_stream()` calls the completed `process_turn()` and then splits the final reply by spaces. The agent-facing stream is therefore not genuine end-to-end token streaming. The streaming unit test can pass through the local fallback and does not establish a live provider stream. |
| 2. RAG persistence readiness | **Not complete in this ZIP** | The uploaded `app/retrieval/vector_store.py` is an in-memory TF-IDF-style store. The ZIP does not contain `app/retrieval/storage.py` or a separate embedding-provider module. There is no evidence of persistent PostgreSQL/pgvector reads/writes or owner/session-scoped database queries in this snapshot. |
| 3. Document-aware chat and PDF workflow | **Partially implemented** | The snapshot includes PDF extraction, OCR service, chunking, sanitization, an in-memory vector store and page-aware retrieval. Retrieval is lexical TF-IDF in this snapshot; semantic embedding retrieval and durable document persistence are not demonstrated. The document search/comparison tools must be treated as in-memory capabilities only. |
| 4. Agent behaviour report and documentation | **Corrected report supplied** | The earlier 25-pass report did not match the uploaded test archive. This report records the actual 42-pass result and explicitly separates unit-test evidence from live integrations and unverified demonstrations. |
| 5. Framework tests and GitHub preparation | **Local test suite verified; GitHub preparation pending** | The uploaded suite passes after the routing correction. Repository branch, remote, contributor permissions and working-tree status were not available in the uploaded ZIP, so no commit or push is claimed. |

## 5. Llama Integration – Evidence and Limitations

The source contains:
- Configurable provider base URL and model identifier.
- API-key based authentication.
- Context truncation.
- Timeout and request error handling in the non-streaming completion path.
- A provider SSE streaming method.
- A deterministic local fallback when no live API key is configured.

Not verified by the uploaded tests:
- Successful authenticated request to the configured live Llama provider.
- Real token arrival timing from a provider SSE connection.
- Provider-specific streaming error/retry behaviour under HTTP 429 and 5xx.
- End-to-end streaming through the FastAPI endpoint and browser UI.

**Important:** A local fallback that emits text fragments is not the same as live Llama token streaming.

## 6. PDF and RAG – Evidence and Limitations

The uploaded code provides PDF extraction/OCR-related modules, chunking, prompt-injection sanitization, page metadata, and an in-memory retrieval path.

The uploaded `vector_store.py` uses lexical token weighting and cosine-style similarity over locally computed TF-IDF vectors. It is not a persistent semantic vector database. The ZIP does not contain the PostgreSQL storage adapter or a live database integration test.

The sanitization logic is a defense-in-depth measure, not a guarantee that all prompt injection attempts are detected. PDF contents remain untrusted input and must never authorize tools or consequential actions.

## 7. Consequential Actions and Security

The uploaded tests cover selected permission and action paths. They do not prove the entire Level 4/Level 5 workflow is connected to a production authorization service, durable audit log, or deployed confirmation UI.

The earlier report's specific preparation IDs, approval tokens, candidate-level findings and claimed version transitions are not reproduced as verified facts here because the uploaded test log does not provide those execution traces.

## 8. Items Not Claimed as Verified

The following are not claimed as complete based on this upload:
- Live Llama API connectivity.
- End-to-end genuine streaming from model provider through API to browser.
- Persistent PostgreSQL/pgvector storage.
- Cross-process document persistence.
- Live Cloud SQL or Cloud Storage integration.
- Production Cloud Run deployment.
- End-to-end browser microphone, STT and TTS playback.
- Production cryptographic approval workflow and audit trail.
- Full compliance with all 19 deliverables in the Master Development Prompt.

## 9. Reproducible Local Test Command

From the project root with the intended virtual environment activated:

```powershell
python -m pytest -q
```

For detailed output:

```powershell
python -m pytest -v
```

## 10. Verification Conclusion

The uploaded test suite passes after one targeted candidate-intent routing correction (**42 passed**). This is a useful local verification milestone, but it does not establish that all advanced architecture, persistence, live provider, voice, deployment or security requirements are complete.

The next engineering work should connect the existing provider SSE method to the actual agent streaming flow, restore/complete the owner- and session-scoped RAG persistence adapter in the current source tree, and add integration tests that exercise those paths without requiring production secrets.

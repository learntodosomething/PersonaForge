# PersonaForge Roadmap

## Phase 1 — Foundation
- Define normalized message and participant schemas.
- Parse Messenger JSON exports.
- Validate malformed or incomplete input.
- Support selecting one speaker.
- Add synthetic test fixtures and parser tests.
- Keep source data local and provide deletion behavior.

## Phase 2 — Style profile
- Analyze message length, vocabulary, punctuation, emoji frequency, and tone.
- Distinguish observed patterns from uncertain inferences.
- Generate an editable persona profile.

## Phase 3 — Retrieval and memory
- Chunk messages or conversation windows.
- Build retrieval over authorized source messages.
- Add relevance filtering and source references.
- Keep retrieved memories separate from the live chat transcript.

## Phase 4 — Chat
- Add a provider-agnostic LLM interface.
- Compose prompts from the style profile and retrieved context.
- Keep AI-generated content clearly identified.
- Add session history and context limits.

## Phase 5 — Web UI
- Upload and validate export files.
- Show import progress and errors.
- Let users select participants and manage personas.
- Add chat, settings, and deletion controls.

## Phase 6 — Evaluation and expansion
- Create synthetic and consented evaluation sets.
- Measure style similarity, relevance, and unsupported claims.
- Consider additional export formats only after the first pipeline is reliable.

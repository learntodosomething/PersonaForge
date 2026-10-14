<div align="center">

# PersonaForge

### Build conversational AI personas from your own conversation archives.

Import message exports, analyze communication patterns, retrieve relevant memories, and chat with an AI persona inspired by a selected speaker.

**Private by design · Modular architecture · Local-first data processing**

[Features](#-planned-features) · [Architecture](#️-architecture) · [Roadmap](#-roadmap) · [Getting Started](#-getting-started)

</div>

---

> **Project status:** Early planning / foundation stage. Features described below are planned and may not yet be implemented.

## Overview

PersonaForge is an experimental application for turning personal conversation archives into configurable AI personas. A user imports an export they are authorized to use, selects a speaker, and creates a persona using that speaker's communication patterns and optionally relevant conversation context.

The goal is not to train a foundation model from scratch. The initial approach is to combine a structured style profile, retrieval-augmented generation (RAG), and an existing language model. Fine-tuning may be explored later if it offers a measurable benefit.

## Planned features

- **Conversation import** — parse supported JSON exports, beginning with Facebook Messenger.
- **Speaker selection** — inspect participants and select the speaker to model.
- **Data cleaning** — normalize timestamps and message content, handle attachments, and remove empty or unsupported records.
- **Style profiling** — summarize vocabulary, sentence length, punctuation, emoji usage, tone, and recurring expressions.
- **Conversation memory** — retrieve relevant, authorized examples from the archive using RAG.
- **Persona chat** — chat with a persona while keeping conversation history separate from source messages.
- **Multiple personas** — create, rename, manage, export, and delete separate persona profiles.
- **Privacy controls** — clear imported data, review what is stored, and avoid sending source messages to external services unless explicitly configured.
- **Evaluation** — test style consistency and response quality against a small set of manually reviewed examples.

## Architecture

The project is intended to use a modular architecture:

```text
PersonaForge/
├── backend/          # API, import pipeline, persona and chat services
├── frontend/         # Web interface
├── tests/            # Automated tests
├── docs/              # Architecture, privacy, and development notes
├── .env.example
├── .gitignore
└── README.md
```

### Proposed technology stack

| Layer | Initial choice | Purpose |
|---|---|---|
| Backend | Python + FastAPI | API and application logic |
| Import pipeline | Python | Parse and normalize conversation exports |
| Data validation | Pydantic | Validate API and internal data models |
| Retrieval | Pluggable vector search | Find relevant conversation examples |
| Language model | Provider abstraction | Support local or hosted models |
| Frontend | React + TypeScript | Interactive web application |
| Testing | pytest + frontend test tooling | Regression and quality checks |

These are proposed defaults, not fixed requirements. Specific model providers, databases, and embedding systems should be selected after the first import prototype is tested.

## Privacy and responsible use

Conversation archives can contain highly sensitive information about multiple people. PersonaForge should be designed around data minimization and user control.

- Only import conversations the user is authorized to process.
- Respect other participants' privacy and obtain consent where appropriate, especially before creating or sharing a persona based on another person.
- Process files locally by default where practical.
- Clearly disclose when an external AI provider receives prompts or retrieved messages.
- Never commit conversation exports, API keys, access tokens, or private model data to Git.
- Provide a way to delete imported conversations, derived profiles, embeddings, and chat history.
- Do not present generated responses as authentic messages from the person being modeled. Make the AI-generated nature of the persona clear.
- Redact sensitive data when appropriate and keep logs free of raw message content by default.

PersonaForge is a software project, not a guarantee that a generated persona accurately represents a real person's beliefs, memories, or intentions.

## Getting Started

The application is not yet implemented. These are the intended first development steps:

1. Clone the repository.
2. Create a Python virtual environment.
3. Implement and test a parser for a small, synthetic Messenger JSON fixture.
4. Add speaker selection and normalized message models.
5. Build the first API endpoints.
6. Add a basic frontend for uploading an export and selecting a speaker.

### Backend environment (planned)

```bash
python -m venv .venv
```

Windows:

```powershell
.venv\Scripts\Activate.ps1
```

macOS / Linux:

```bash
source .venv/bin/activate
```

Once the backend dependency file is added, install dependencies and run the development server according to the setup instructions that will be documented here.

## Roadmap

- [x] **Phase 1 — Foundation:** project structure, schema design, Messenger JSON parser, validation, and test fixtures.
- [x] **Phase 2 — Personality profiling:** analyze style, tone, vocabulary, punctuation, and emoji patterns.
- [ ] **Phase 3 — Memory (RAG):** index authorized messages and retrieve relevant examples for a prompt.
- [ ] **Phase 4 — Persona chat:** implement chat sessions, context management, and model-provider abstraction.
- [ ] **Phase 5 — Web experience:** upload flow, participant selection, persona management, chat UI, and deletion controls.
- [ ] **Phase 6 — Evaluation:** build a repeatable test set for style consistency, relevance, and hallucination checks.
- [ ] **Phase 7 — Expansion:** consider other export formats and platforms after the Messenger pipeline is reliable.
- [ ] **Future research — Fine-tuning:** evaluate whether fine-tuning improves results compared with prompting and RAG.

## Development principles

- Keep import/parsing logic independent from the web framework.
- Use typed, validated internal data models.
- Test with synthetic fixtures; do not use real private conversations in public tests.
- Keep language-model providers behind a small interface.
- Make long-running tasks observable and cancellable.
- Separate source data, derived persona profiles, and generated chat history.
- Document trade-offs and measure improvements before adding complexity.

## Contributing

Contributions and design discussions are welcome. Before opening a pull request, please:

1. Describe the issue or feature.
2. Add or update tests.
3. Avoid including personal conversation data, credentials, or private exports.
4. Update documentation when behavior changes.

A contribution guide and issue templates can be added once the first implementation is in place.

## License

No license has been selected yet. Until a license is added, the repository should not be assumed to grant permission to reuse, distribute, or modify its contents. Choose a license before inviting external contributions.

---

<div align="center">

**PersonaForge** — conversation archives in, configurable AI personas out.


## 📥 How to Export Your Messenger Conversations

PersonaForge uses conversation exports provided by Meta. Follow the steps below to download your Messenger messages in JSON format.

### Step 1 — Open Meta Accounts Center

1. Log in to your Facebook account.
2. Open [Facebook Accounts Center](https://accountscenter.facebook.com/).
3. Navigate to **Your information and permissions**.
4. Select **Export your information** or **Download your information**.

> Meta may change menu names or layouts over time. If you cannot find the option, use the official [Facebook Help Center guide](https://www.facebook.com/help/212802592074644).

### Step 2 — Create an export

1. Select your Facebook account.
2. Choose the option to export or download information to your device.
3. Select the option to customize the information you want to export, if available.
4. Choose **Messages** as the information category.
5. Set the date range to **All time** to include the entire available conversation history.

### Step 3 — Configure the export

Use the following settings:

| Setting | Recommended value |
|---|---|
| Destination | Download to device |
| Information category | Messages |
| Date range | All time |
| Format | JSON |
| Media quality | High, if media is needed |

**Why JSON?** JSON is structured data that software can parse. HTML exports are intended primarily for viewing and are not the recommended format for this workflow.

If you only want to analyze text messages, you may not need to include media files.

### Step 4 — Request and download your archive

1. Confirm your export settings and create the export.
2. Wait while Meta prepares your archive. This may take some time, depending on the amount of data.
3. Return to the export page when the archive is ready.
4. Download the ZIP file.
5. Extract the ZIP file to a folder on your computer.

You may need to re-enter your password or complete an additional security check.

### Step 5 — Locate your Messenger files

Inside the extracted archive, look for a folder related to messages, usually named `messages`.

Conversation files are commonly organized into subfolders, often under a structure similar to:

```text
your-export/
└── messages/
    └── inbox/
        └── conversation_name/
            ├── message_1.json
            ├── message_2.json
            └── ...
```

The exact folder structure and filenames may vary. Some conversations are split across multiple JSON files.

Keep the original archive as a backup. PersonaForge will provide instructions for importing the appropriate files once its import feature is implemented.

### Privacy and security

- Only import conversations you are authorized to use.
- Consider the privacy of everyone included in the conversation, and obtain consent where appropriate before creating or sharing a persona based on another person.
- Keep your downloaded archive private and do not commit it to GitHub.
- Do not upload private conversations to third-party AI services unless you understand and accept how the data will be processed.
- Delete local exports when you no longer need them.

**Note:** Exporting your messages does not guarantee that every historical message or attachment will be available. Availability can depend on the account, conversation, and Meta's current export behavior.

---

**Ready to create your first persona?** Once the import feature is available, you will be able to upload your export, select a conversation participant, and create an AI persona from the available messages.


</div>

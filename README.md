<div align="center">

# 💎 Maison Copy — Luxury AI Description Atelier

### *Where generative intelligence learns the grammar of heritage.*

Structured agent reasoning, a quiet-luxury editorial rulebook, and five bespoke brand registers, composed into one atelier for the world's most exacting product copy.

![Python](https://img.shields.io/badge/Python-3.11%2B-1f1f1f?style=flat-square&logo=python&logoColor=b79a62)
![Streamlit](https://img.shields.io/badge/Streamlit-Interface-1f1f1f?style=flat-square&logo=streamlit&logoColor=b79a62)
![Gemini](https://img.shields.io/badge/Google%20Gemini-GenAI%20SDK-1f1f1f?style=flat-square&logo=googlegemini&logoColor=b79a62)
![Environment](https://img.shields.io/badge/Environment-venv%20isolated-b79a62?style=flat-square)

[The Bottleneck](#the-bottleneck) · [The Architecture](#the-architecture) · [Security](#built-for-commercial-use) · [Tech Stack](#production-tech-stack) · [Installation](#installation) · [Registers](#available-registers)

</div>

<!-- Add a screen recording: ![Maison Copy in action](docs/demo.gif) -->

---

## The Bottleneck

Luxury is a discipline of restraint. General-purpose language models are engines of abundance.

Hand a raw LLM a heritage timepiece or a hand-stitched leather bag, and it reaches for the same worn vocabulary: *luxurious*, *elegant*, *stunning*, *timeless*, *elevate*. The sentences arrive at a uniform pace, the structure is a feature list in disguise, and the brand's history is either ignored or, worse, invented.

For a mass-market listing, that is forgettable. For a maison, it is a liability.

| Where raw LLMs fail | What it looks like | What luxury demands |
|---|---|---|
| **Cheap clichés** | Stock adjectives and exclamation marks | Quiet luxury: confidence without volume |
| **No narrative rhythm** | Flat, uniform sentences | Cadence that moves between the short and the flowing |
| **No sense of heritage** | Generic copy that fits any brand | A distinct register for each house |
| **Fabricated facts** | Invented materials, dates and awards | Absolute fidelity to the supplied brief |

Marketing teams end up rewriting AI output line by line, which erases the time the tool was meant to save.

---

## The Architecture

Maison Copy replaces the single "write me a description" prompt with a **structured, multi-step agent workflow**. Each stage is a separate, live model call that hands a verified artefact to the next, the way a creative studio actually works.

```
                ┌────────────────────┐   ┌────────────────────┐   ┌────────────────────┐   ┌────────────────────┐
 Product brief  │ 1. Deep Asset      │   │ 2. Maison Registry │   │ 3. High-End        │   │ 4. Linguistic      │
 + register  ─▶ │    Analysis        │─▶ │    Mapping         │─▶ │    Narrative       │─▶ │    Polish & Rhythm │─▶ Final copy
 + length       │                    │   │                    │   │    Drafting        │   │                    │
                └────────────────────┘   └────────────────────┘   └────────────────────┘   └────────────────────┘
```

| Stage | What happens |
|---|---|
| **1. Deep Asset Analysis** | The brief is dissected into verified facts and signature elements. Claims the brief does not support are flagged as off-limits before a single sentence is written. |
| **2. Maison Registry Mapping** | The chosen register is translated into a voice direction: tone, sensory imagery, rhythm, and the words that would cheapen this particular piece. |
| **3. High-End Narrative Drafting** | An elite copywriter system prompt composes the draft inside the verified facts and the mapped register. |
| **4. Linguistic Polish & Rhythm** | The draft is refined for cadence and word choice, stripped of clichés and unsupported claims, and streamed live into the final result. |

Every stage is visible in the interface as it runs, so the reasoning is observable rather than hidden behind a spinner.

**Editorial guardrails, enforced at the prompt level**

- **Fact-bound.** Only the details you supply are used. No invented materials, dates, awards or specifications.
- **Banned vocabulary.** Hype words, exclamation marks, emoji and hashtags are excluded by rule.
- **No imitation.** The system describes a register; it never copies a real brand's voice or slogans.
- **Prose only.** No bullet points, no headings: refined, flowing language.

---

## Built for Commercial Use

Maison Copy is engineered with a commercial deployment in mind. Credential handling is secure by default, and the architecture separates the interface from the intelligence layer.

- **Local `.env` key management.** The Gemini API key is read from a local `.env` file. A `.env.example` template is included, and `.env` is git-ignored so credentials never reach version control.
- **Bring your own key.** Each client or team member can plug in their own Gemini API key, either in `.env` or in the sidebar for a single session.
- **Keys stay out of the browser and off disk.** A saved key is shown masked and is never sent to the client. A key typed into the sidebar is held for the session only and is never written to disk. The key is also excluded from logs and tracebacks.
- **Clean separation of concerns.** The API layer (`llm_client.py`) has no UI dependency and exposes validated, immutable configuration, retries with backoff on transient failures, and one typed error with user-safe messages. It is ready to be placed behind a service interface.
- **Safe rendering.** Generated text is rendered as Markdown, never as raw HTML.

> **Data handling note.** Product briefs are sent to the Gemini API for generation. Before processing confidential or unreleased product information, review Google's data-use terms for your API tier.

---

## Production Tech Stack

| Layer | Technology |
|---|---|
| **Core** | Python 3.11+ |
| **Interface** | Streamlit, custom-styled with minimalist typography and signature gold hairline accents |
| **LLM orchestration** | Google GenAI SDK (`google-genai`) with Gemini models, configurable via `GEMINI_MODEL` |
| **Configuration** | `python-dotenv` for local secrets |
| **Environment** | Fully isolated virtual environment (`venv`), with dependencies tracked in `requirements.txt` |

### Project structure

```
maison-copy/
├── app.py              # Streamlit interface, editorial prompts, four-stage agent pipeline
├── llm_client.py       # Gemini API layer: config, client, retries, error handling
├── requirements.txt    # Tracked dependencies
├── .env.example        # Configuration template
├── .gitignore          # Keeps secrets out of version control
└── README.md
```

---

## Installation

**1. Clone the repository**

```bash
git clone https://github.com/<your-username>/maison-copy.git
cd maison-copy
```

**2. Create and activate a virtual environment**

```bash
python -m venv .venv

# macOS / Linux
source .venv/bin/activate

# Windows (PowerShell)
.venv\Scripts\Activate.ps1
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

**4. Add your API key**

Create a `.env` file in the project root (you can copy `.env.example`) and paste your key. Get a free key from [Google AI Studio](https://aistudio.google.com/apikey).

```
GEMINI_API_KEY=your_key
```

**5. Launch the atelier**

```bash
python -m streamlit run app.py
```

The app opens at `http://localhost:8501`. With a saved key, you can compose immediately.

| Variable | Purpose | Required |
|---|---|---|
| `GEMINI_API_KEY` | Your Google Gemini API key | Yes (or paste it in the sidebar) |
| `GEMINI_MODEL` | Override the Gemini model ID | No |

---

## Available Registers

Five editorial registers, each with its own directive behind the scenes. Select the one that matches the house you write for.

| Register | Character | Best suited to |
|---|---|---|
| **Heritage & Authoritative** | The calm, assured voice of a house with a long history. Measured, formal and declarative, with themes of mastery and continuity. | Timeless, classic heritage brands |
| **Timeless & Understated** | Quiet luxury. No emphasis and no display; materials, cut and proportion speak in plain, exact language. | Brands of subtle elegance and restraint |
| **Romantic & Evocative** | Sensory and emotional. Light, scent, memory and anticipation, in flowing, lyrical sentences. | Fine fragrance, high jewellery, hospitality |
| **Modern & Architectural** | Precise and structural. Design described as architecture: geometry, line, proportion and surface. | High horology and design-led objects |
| **Avant-Garde & High-Performance** | Bold, charged and commanding, with kinetic energy built on precision, never hype. Percussive sentences, the vocabulary of motion and engineering, and strict bans on invented performance figures and superlatives. | Elite supercars such as the Lamborghini Revuelto, and disruptive luxury fashion |

---

<div align="center">

**Maison Copy** is conceived and built by **Eugenia Khan**, Founder.
A product at the meeting point of AI engineering and luxury brand craft.

[LinkedIn] www.linkedin.com/in/eugenia-khan-ab5912390 · [GitHub] https://github.com/eugeniakhan

</div>

<sub>Maison Copy is an independent project and is not affiliated with, endorsed by, or sponsored by any brand or product named as an illustration. All trademarks belong to their respective owners.</sub>

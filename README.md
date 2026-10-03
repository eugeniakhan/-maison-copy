<div align="center">

# 💎 Maison Copy

### *Luxury AI Description Atelier*

**Where generative AI learns the language of heritage.**

![Python](https://img.shields.io/badge/Python-3.10%2B-1f1f1f?style=flat-square&logo=python&logoColor=b79a62)
![Streamlit](https://img.shields.io/badge/Streamlit-Web%20App-1f1f1f?style=flat-square&logo=streamlit&logoColor=b79a62)
![LLM](https://img.shields.io/badge/LLM-Prompt%20Engineered-1f1f1f?style=flat-square&logoColor=b79a62)
![Status](https://img.shields.io/badge/Status-Demo%20Ready-b79a62?style=flat-square)

[The Problem](#the-problem) · [The Solution](#the-solution) · [Architecture](#core-architecture--workflow) · [Stack](#technical-stack) · [Getting Started](#getting-started) · [Roadmap](#future-roadmap)

</div>

<!-- Add a short screen recording here: ![Maison Copy demo](docs/demo.gif) -->

---

## The Problem

Luxury is built on restraint. Generic AI writing is built on volume.

Ask a general-purpose chatbot to describe a heritage timepiece or a hand-stitched leather bag, and the result is usually recognisable within a sentence: an exclamation mark, a "stunning," a "must-have," an invitation to "elevate your style." For a mass-market product, that is merely forgettable. For a maison, it is damaging.

Raw, unguided AI tools fail the luxury segment in four consistent ways:

| Failure mode | What it looks like | Why it matters to a maison |
|---|---|---|
| **Cliché and hype** | "Amazing," "perfect," "game-changing," "unique" | Luxury whispers; it never shouts. |
| **Generic register** | Interchangeable copy that could describe any product from any brand | Brand identity is the product. |
| **Feature listing** | Specifications strung together instead of an evocation of ownership | Clients buy a feeling and a story, not a bullet list. |
| **Invented facts** | Fabricated materials, dates, awards or heritage claims | One false claim erodes decades of credibility. |

Brand teams end up rewriting AI output line by line, which erases most of the time the tool was meant to save.

---

## The Solution

**Maison Copy** is a focused writing atelier for premium brands. Instead of asking a general model to "write a product description," it constrains the model with a structured, brand-grade creative brief and a strict editorial rulebook, so the output arrives in the right register from the first draft.

**Value proposition**

- **Elite brand register by default.** Understated, sensory, craftsmanship-led prose in the tradition of the great heritage houses.
- **Fact-bound writing.** The model is instructed to use only the details you supply. No invented materials, certifications, dates or specifications.
- **A banned vocabulary.** Hype words, clichés, exclamation marks, emoji and hashtags are excluded at the prompt level.
- **Hours back for marketing teams.** A client-ready first draft in seconds, so editors refine instead of rewrite.
- **Controlled output.** Choose the tone (timeless, romantic, architectural, heritage) and the length (concise, standard, extended) per product.
- **Minimalist, brand-appropriate interface.** A quiet, typographic UI that fits the world it serves.

**The difference, illustratively**

> **Generic AI:** *"Introducing our stunning, must-have leather bag! Elevate your style with this amazing, timeless piece!"*
>
> **Maison Copy:** *"Cut from full-grain Italian calfskin, the Aurèle Classique is a study in quiet restraint. Its silhouette is soft but certain: structured at the base, yielding at the shoulder, finished with edges burnished to a deep, glowing sheen."*

*(Example shown for a fictional house.)*

---

## Core Architecture & Workflow

Maison Copy is designed around a four-stage creative pipeline that mirrors how a senior copywriter actually works.

```
 Product brief          ┌───────────────┐   ┌───────────────┐   ┌───────────────┐   ┌───────────────┐
 (name, materials, ───▶ │ 1. Analyse    │──▶│ 2. Study      │──▶│ 3. Draft      │──▶│ 4. Refine     │──▶ Final copy
  details, tone,        │ product       │   │ brand voice & │   │ in the maison │   │ language &    │
  length)               │ details       │   │ heritage      │   │ register      │   │ rhythm        │
                        └───────────────┘   └───────────────┘   └───────────────┘   └───────────────┘
```

| Stage | Purpose |
|---|---|
| **1. Analysing product details** | Extract the verifiable facts from the brief: materials, construction, proportions, signature elements. These form the only permitted source material. |
| **2. Studying brand voice & heritage** | Apply the target tone and the editorial voice of a heritage house: understated, sensory, timeless. |
| **3. Drafting in the maison register** | Compose flowing prose that evokes the moment of ownership rather than listing features. |
| **4. Refining language & rhythm** | Polish cadence and word choice, mixing short, rhythmic sentences with longer, flowing ones, and remove anything that breaks the register. |

### Project structure

```
maison-copy/
├── app.py          # Streamlit interface, system prompt, prompt assembly, demo mode
├── llm_client.py   # Modular API layer: config, client creation, error handling
└── README.md
```

### Design principles

- **Separation of concerns.** The API layer (`llm_client.py`) has no UI dependencies, so it is independently testable and reusable.
- **Immutable, validated configuration.** Settings are validated at construction, and secrets are read from the environment, never hardcoded.
- **One exception type for the UI.** All provider errors (authentication, rate limits, timeouts, connectivity) are translated into user-safe messages.
- **Safe rendering.** Generated text is rendered as Markdown, never as raw HTML.

### Current implementation status

> Transparency matters to us, so here is exactly where the project stands.
>
> - **Demo mode (default)** runs with no API key. It simulates the four-stage workflow in the interface and returns pre-written showcase descriptions.
> - **Live mode** sends the structured brief and system prompt to an LLM in a single, tightly constrained generation call.
> - **Promoting each stage to its own chained model call**, with structured intermediate outputs, is the next architectural milestone (see the [Roadmap](#future-roadmap)).

---

## Technical Stack

| Layer | Technology |
|---|---|
| **Language** | Python 3.10+ |
| **Interface** | [Streamlit](https://streamlit.io) with custom CSS (serif display typography, hairline gold accents) |
| **LLM integration** | Anthropic Python SDK with built-in retries, timeouts and typed error handling |
| **Core technique** | Structured prompt engineering: a role-defined system prompt, explicit voice guidelines, a negative vocabulary, fact-grounding constraints and parameterised user briefs |

---

## Getting Started

**Prerequisites:** Python 3.10 or newer.

**1. Clone the repository**

```bash
git clone https://github.com/<your-username>/maison-copy.git
cd maison-copy
```

**2. Create a virtual environment (recommended)**

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
```

**3. Install dependencies**

```bash
pip install streamlit anthropic
```

**4. Run the atelier**

```bash
streamlit run app.py
```

The app opens at `http://localhost:8501` in demo mode. No API key is required.

### Enabling live generation

```bash
export ANTHROPIC_API_KEY="your-key-here"     # Windows (PowerShell): $env:ANTHROPIC_API_KEY="your-key-here"
export DEMO_MODE=0                           # Windows (PowerShell): $env:DEMO_MODE="0"
streamlit run app.py
```

Optionally set `ANTHROPIC_MODEL` to choose a specific model. Keys can also be stored in `.streamlit/secrets.toml`. Never commit API keys to version control.

---

## Future Roadmap

- [ ] **True multi-step agent orchestration.** Promote each pipeline stage to an independent model call with typed intermediate outputs.
- [ ] **Real-time multi-provider integrations**, including Google Gemini, behind a unified provider interface.
- [ ] **AI product photography descriptions.** Upload an image and receive a brand-grade description grounded in what the model can actually see, using multimodal input.
- [ ] **Brand voice profiles.** Save and reuse style guides, lexicons and exemplar copy per maison.
- [ ] **Automated quality gates.** Validate banned vocabulary, word count and fact adherence, with automatic regeneration on failure.
- [ ] **Multilingual and market-aware copy** for international luxury markets.
- [ ] **Catalogue-scale batch generation** from CSV for entire collections.

---

## About

Maison Copy is an independent project by **[Your Name]**, exploring where generative AI and luxury brand identity meet.

Feedback, ideas and collaboration are welcome. Open an issue or reach out via [LinkedIn](https://www.linkedin.com/in/your-profile).

---

<sub>Maison Copy is an independent project and is not affiliated with, endorsed by, or sponsored by any brand referenced as a stylistic benchmark. All trademarks are the property of their respective owners.</sub>

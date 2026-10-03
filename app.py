"""app.py - Streamlit UI for Maison Copy, powered by Google Gemini.

Run:      streamlit run app.py
Requires: pip install -U streamlit google-genai python-dotenv
Key:      saved automatically from a .env file next to this file
          (GEMINI_API_KEY=...), an environment variable, or
          .streamlit/secrets.toml. A key pasted in the sidebar overrides them.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

import streamlit as st

from llm_client import (
    DEFAULT_MODEL,
    LLMConfig,
    LLMError,
    create_client,
    generate_text,
    get_env_api_key,
    stream_text,
)

# --------------------------------------------------------------------------- #
# Prompts
# --------------------------------------------------------------------------- #

# The elite copywriter system prompt. Used for the drafting and refining stages
# (and for the single-call mode), so the brand register is enforced where the
# final copy is actually written.
SYSTEM_PROMPT = """\
You are an elite luxury copywriter with two decades of experience writing for the \
world's most storied maisons in haute couture, fine watchmaking, jewellery and \
leather goods. Your prose has the restraint, authority and quiet confidence of the \
great heritage houses.

VOICE
- Understated, never loud. Luxury whispers; it does not shout.
- Sensory and precise: speak of texture, weight, light, sound, proportion.
- Emphasise craftsmanship, provenance, materials and the hours of human skill behind \
the object. Timelessness over trend.
- Short, rhythmic sentences mixed with the occasional longer, flowing one.
- Evoke a feeling or a moment of ownership rather than listing features.

RULES
- Use ONLY the facts supplied by the user. Never invent materials, certifications, \
dates, heritage claims, awards, prices or technical specifications.
- Do not use clichés or hype words such as "amazing", "stunning", "perfect", \
"must-have", "game-changing", "unique", or exclamation marks. Avoid emoji and \
hashtags.
- Do not imitate or name any real brand, and do not reuse any real brand's slogans.
- Do not use bullet points or headings. Write refined flowing prose only.
- Output the description text only: no preamble, no title, no commentary.
"""

ANALYST_PROMPT = """\
You are a meticulous product analyst for a luxury house. From the brief provided, \
extract only what is explicitly stated. Never infer, embellish or invent.

Return plain text in exactly this layout:
VERIFIED FACTS: the stated facts, one per line, each beginning with "- ".
SIGNATURE ELEMENTS: the two or three most distinctive details to build the \
description around, one per line beginning with "- ".
OFF-LIMITS: claims a copywriter might be tempted to make that the brief does not \
support (for example heritage, awards, origin, precise specifications), one per line \
beginning with "- ". Write "- none noted" if nothing applies.

Be concise: under 120 words in total.
"""

VOICE_PROMPT = """\
You are the creative director of a luxury house. Given a product brief, its verified \
analysis and the requested tone, write a brief voice direction for the copywriter.

Return plain text in exactly this layout:
REGISTER: one sentence describing the voice.
IMAGERY: three or four sensory images or metaphors (light, texture, weight, sound, \
motion, time) that can be grounded in the verified facts.
RHYTHM: one sentence on sentence length and cadence.
AVOID: five words or phrases that would cheapen this particular product.

Follow the register direction exactly, including when it calls for boldness.
Do not add facts. Under 110 words in total.
"""

STEPS = [
    ("1 · Analysing product details…", "1 · Product details analysed"),
    ("2 · Studying brand voice & heritage…", "2 · Brand voice & heritage studied"),
    ("3 · Drafting in the maison register…", "3 · Draft composed"),
    ("4 · Refining language & rhythm…", "4 · Language & rhythm refined"),
]
REFINE_NOTE = "Polishing cadence and removing anything the verified facts do not support."

LENGTH_OPTIONS = {
    "Concise (≈60 words)": 60,
    "Standard (≈120 words)": 120,
    "Extended (≈200 words)": 200,
}

# Each register has a UI hint and a backend directive. Directives describe the voice
# without naming real brands, so the model writes in a register rather than copying
# a trademarked house style.
TONE_PROFILES = {
    "Heritage & Authoritative": {
        "hint": "For timeless, classic heritage houses.",
        "directive": (
            "Write with the calm, assured authority of a house with a long history. Use "
            "measured, formal, declarative sentences. Themes: continuity, mastery, "
            "permanence, objects made to be handed on. Never invent history; refer to "
            "heritage, dates or provenance only where the brief supplies them."
        ),
    },
    "Timeless & Understated": {
        "hint": "Quiet luxury: subtle elegance and restraint.",
        "directive": (
            "Quiet luxury, the most restrained register. No emphasis and no display. Let "
            "materials, texture, cut and proportion speak in plain, exact language. "
            "Favour what is felt over what is seen. There should be no hint of selling."
        ),
    },
    "Romantic & Evocative": {
        "hint": "Sensory and emotional; suited to fragrance, high jewellery and hospitality.",
        "directive": (
            "Sensory and emotional. Lead with feeling and atmosphere: light, scent, skin, "
            "memory, anticipation, the hush of a particular room or hour. Use flowing, "
            "lyrical sentences with a soft cadence. Keep every image grounded in the "
            "supplied facts; never invent notes, gemstones, locations or amenities."
        ),
    },
    "Modern & Architectural": {
        "hint": "Structure, geometry and design; suited to high horology.",
        "directive": (
            "Precise and structural. Describe design as architecture: geometry, line, "
            "proportion, tension, negative space, surface and finish, and the logic of how "
            "the parts relate. Use clean, exact sentences with a cool, confident clarity. "
            "Admire engineering through form rather than jargon."
        ),
    },
    "Avant-Garde & High-Performance": {
        "hint": "Bold and high-octane; suited to elite automotive and disruptive luxury fashion.",
        "directive": (
            "This register overrides the 'whispers' and 'understated' guidance in the VOICE "
            "section. Here the copy is bold, charged and commanding, yet never loud in the "
            "cheap sense. Write with kinetic energy: short, percussive, declarative "
            "sentences, punctuated by one long sentence that accelerates. Draw on the "
            "vocabulary of motion, engineering, sound, force, light on surface and "
            "precision. Treat the object as a statement of intent, chosen deliberately by "
            "its owner. Power must come from exactness and confidence, not volume: no "
            "superlatives, no hype, and no claim to be the fastest, the most powerful or "
            "the first. Never invent performance figures, speeds, power outputs, "
            "materials, production numbers or racing credentials; use only what the brief "
            "supplies. Avoid clichés such as 'beast', 'unleash', 'adrenaline', 'pure "
            "power', 'raw', 'turn heads' and 'break the rules'. For disruptive fashion, "
            "apply the same energy to silhouette, material and attitude: defiant, "
            "deliberate, impeccably made."
        ),
    },
}

TONE_OPTIONS = list(TONE_PROFILES)


def system_prompt_for(tone: str) -> str:
    """The base copywriter prompt plus the directive for the chosen register.

    The RULES section is never overridden, so every register stays fact-bound and
    free of hype words, whatever its energy level.
    """
    return (
        f"{SYSTEM_PROMPT}\n"
        f"REGISTER FOR THIS PIECE: {tone}\n"
        f"{TONE_PROFILES[tone]['directive']}\n"
        "Where this register differs from the VOICE section above, follow this register. "
        "The RULES section always applies in full.\n"
    )


@dataclass(frozen=True)
class Brief:
    brand: str
    product: str
    category: str
    materials: str
    details: str
    audience: str
    tone: str


def brief_facts(brief: Brief) -> str:
    """The supplied facts as labelled lines, skipping empty fields."""
    lines = [
        f"Brand: {brief.brand}" if brief.brand else "",
        f"Product: {brief.product}",
        f"Category: {brief.category}" if brief.category else "",
        f"Materials & craftsmanship: {brief.materials}" if brief.materials else "",
        f"Key details: {brief.details}" if brief.details else "",
        f"Intended clientele: {brief.audience}" if brief.audience else "",
    ]
    return "\n".join(line for line in lines if line)


def build_user_prompt(brief: Brief, words: int) -> str:
    return (
        "Write a luxury product description from the facts below.\n\n"
        f"{brief_facts(brief)}\n\n"
        f"Tone: {brief.tone}.\n"
        f"Length: approximately {words} words."
    )


# --------------------------------------------------------------------------- #
# Agent pipeline (every stage is a real, live model call)
# --------------------------------------------------------------------------- #

RULE = '<div class="lux-rule"></div>'


def run_pipeline(client, config: LLMConfig, brief: Brief, words: int, multi_step: bool) -> dict:
    """Run the agent and render each stage live. Returns data for re-rendering later."""
    user_prompt = build_user_prompt(brief, words)
    system_prompt = system_prompt_for(brief.tone)

    if not multi_step:
        with st.container(key="result"):
            st.markdown(RULE, unsafe_allow_html=True)
            final = st.write_stream(stream_text(client, config, system_prompt, user_prompt))
        return {"steps": [], "final": final.strip()}

    def run_step(index: int, system_prompt: str, prompt: str) -> str:
        running, done = STEPS[index]
        with st.status(running, expanded=True) as status:
            text = generate_text(client, config, system_prompt, prompt)
            st.markdown(text)
            status.update(label=done, state="complete", expanded=False)
        return text

    facts = brief_facts(brief)

    analysis = run_step(0, ANALYST_PROMPT, f"Brief:\n{facts}")
    voice = run_step(
        1,
        VOICE_PROMPT,
        f"Brief:\n{facts}\n\nRequested tone: {brief.tone}\n"
        f"Register direction: {TONE_PROFILES[brief.tone]['directive']}\n\n"
        f"Verified analysis:\n{analysis}",
    )
    draft = run_step(
        2,
        system_prompt,
        f"{user_prompt}\n\nVerified analysis:\n{analysis}\n\nVoice direction:\n{voice}\n\n"
        "Write the description now and respect the OFF-LIMITS list.",
    )

    # Stage 4 streams the final copy into the result container below it.
    step4 = st.container()
    result_slot = st.container(key="result")
    refine_prompt = (
        "Below is a draft description and the verified analysis it must stay faithful to. "
        "Refine the draft: sharpen the rhythm and word choice, remove any cliché, hype word "
        "or claim the analysis does not support, and keep the length at approximately "
        f"{words} words. Keep the {brief.tone} register: do not soften or exaggerate it. "
        "Return only the final description.\n\n"
        f"Verified analysis:\n{analysis}\n\nDraft:\n{draft}"
    )
    with step4:
        running, done = STEPS[3]
        with st.status(running, expanded=True) as status:
            st.caption(REFINE_NOTE)
            with result_slot:
                st.markdown(RULE, unsafe_allow_html=True)
                final = st.write_stream(stream_text(client, config, system_prompt, refine_prompt))
            status.update(label=done, state="complete", expanded=False)

    return {
        "steps": [
            (STEPS[0][1], analysis),
            (STEPS[1][1], voice),
            (STEPS[2][1], draft),
            (STEPS[3][1], REFINE_NOTE),
        ],
        "final": final.strip(),
    }


def render_saved(result: dict) -> None:
    """Re-render a finished run (for example after the download button triggers a rerun)."""
    for label, body in result["steps"]:
        with st.status(label, expanded=False, state="complete"):
            st.markdown(body)
    with st.container(key="result"):
        st.markdown(RULE, unsafe_allow_html=True)
        st.markdown(result["final"])


# --------------------------------------------------------------------------- #
# Configuration helpers
# --------------------------------------------------------------------------- #


def find_saved_key() -> tuple[str, str]:
    """Look for a saved key: .env file or environment first, then Streamlit secrets.

    Returns (key, source), or ("", "") when nothing is configured.
    """
    key = get_env_api_key()  # also loads the .env file next to app.py
    if key:
        return key, ".env file or environment"
    try:
        for name in ("GEMINI_API_KEY", "GOOGLE_API_KEY"):
            value = str(st.secrets.get(name, "")).strip()
            if value:
                return value, "Streamlit secrets"
    except Exception:  # no secrets file present
        pass
    return "", ""


def resolve_api_key(typed_value: str, saved_key: str) -> str:
    """A key typed into the sidebar overrides the saved one."""
    return typed_value.strip() or saved_key


def mask_key(key: str) -> str:
    """Show only the last four characters, enough to recognise the key."""
    return "•" * 8 + (key[-4:] if len(key) >= 12 else "")


# --------------------------------------------------------------------------- #
# UI
# --------------------------------------------------------------------------- #

STYLE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@300;400;500&family=Inter:wght@300;400&display=swap');

#MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"] {visibility: hidden;}
header[data-testid="stHeader"] {background: transparent;}
.block-container {max-width: 760px; padding-top: 4rem;}
html, body, [class*="css"] {font-family: 'Inter', sans-serif; font-weight: 300;}

.lux-title {
    font-family: 'Cormorant Garamond', serif; font-weight: 300;
    font-size: 2.6rem; letter-spacing: 0.28em; text-transform: uppercase;
    text-align: center; margin-bottom: 0.2rem;
}
.lux-sub {
    text-align: center; font-size: 0.75rem; letter-spacing: 0.35em;
    text-transform: uppercase; opacity: 0.55; margin-bottom: 1rem;
}
.lux-rule {width: 48px; height: 1px; background: #b79a62; margin: 1.5rem auto 2.5rem;}

label p {
    font-size: 0.7rem !important; letter-spacing: 0.2em; text-transform: uppercase;
    opacity: 0.7;
}
div.stButton > button {
    width: 100%; border-radius: 0; border: 1px solid #b79a62;
    background: transparent; color: inherit; padding: 0.8rem 0;
    letter-spacing: 0.3em; text-transform: uppercase; font-size: 0.75rem;
    transition: all 0.3s ease;
}
div.stButton > button:hover {background: #b79a62; color: #111; border-color: #b79a62;}
div[data-testid="stVerticalBlockBorderWrapper"] {border-radius: 0;}

/* Agent step expanders */
div[data-testid="stExpander"] details {border-radius: 0; border-color: rgba(183, 154, 98, 0.35);}
div[data-testid="stExpander"] summary p {
    font-size: 0.8rem; letter-spacing: 0.12em; text-transform: none; opacity: 0.85;
}

/* Sidebar */
[data-testid="stSidebar"] {border-right: 1px solid rgba(183, 154, 98, 0.35);}
.lux-side-title {
    font-family: 'Cormorant Garamond', serif; font-weight: 400; font-size: 1.15rem;
    letter-spacing: 0.25em; text-transform: uppercase; margin-bottom: 0.4rem;
}
.lux-side-rule {width: 32px; height: 1px; background: #b79a62; margin: 0.4rem 0 1.4rem;}

.st-key-result p {
    font-family: 'Cormorant Garamond', serif; font-size: 1.35rem;
    line-height: 1.75; font-weight: 400;
}
</style>
"""


def main() -> None:
    st.set_page_config(
        page_title="Maison Copy",
        page_icon="◆",
        layout="centered",
        initial_sidebar_state="expanded",
    )
    st.markdown(STYLE, unsafe_allow_html=True)

    saved_key, saved_source = find_saved_key()

    with st.sidebar:
        st.markdown('<div class="lux-side-title">Atelier Settings</div>', unsafe_allow_html=True)
        st.markdown('<div class="lux-side-rule"></div>', unsafe_allow_html=True)
        api_key_input = st.text_input(
            "Google Gemini API Key",
            type="password",
            placeholder=f"Saved key in use  {mask_key(saved_key)}" if saved_key else "Paste your key",
            help="Leave empty to use the saved key. Paste a key here to override it for this "
            "session; keys typed here are never written to disk.",
        )
        if saved_key:
            st.caption(f"✓ Key loaded from {saved_source}.")
        else:
            st.caption("No saved key found. Paste one above, or add it to a .env file.")
        multi_step = st.toggle(
            "Multi-step agent",
            value=True,
            help="Runs four chained model calls (analyse, voice, draft, refine). "
            "Turn it off for a single faster call that uses less quota.",
        )
        with st.expander("Advanced"):
            model = st.text_input(
                "Model",
                value=os.getenv("GEMINI_MODEL", DEFAULT_MODEL),
                help="If a model is retired, enter a current Gemini model ID here.",
            )
        st.caption("Free key: aistudio.google.com/apikey")

    st.markdown('<div class="lux-title">Maison Copy</div>', unsafe_allow_html=True)
    st.markdown('<div class="lux-sub">Luxury Description Atelier</div>', unsafe_allow_html=True)
    st.markdown(RULE, unsafe_allow_html=True)

    col_a, col_b = st.columns(2)
    brand = col_a.text_input("Brand (optional)", placeholder="e.g. Maison Aurèle")
    product = col_b.text_input("Product name *", placeholder="e.g. Hand-stitched weekender")

    col_c, col_d = st.columns(2)
    category = col_c.text_input("Category", placeholder="e.g. Leather goods")
    audience = col_d.text_input("Clientele (optional)", placeholder="e.g. Discerning travellers")

    materials = st.text_input(
        "Materials & craftsmanship",
        placeholder="e.g. Full-grain Italian calfskin, saddle-stitched by hand",
    )
    details = st.text_area(
        "Key details",
        placeholder="Dimensions, finishes, heritage, signature elements…",
        height=110,
    )

    col_e, col_f = st.columns(2)
    tone = col_e.selectbox("Tone", TONE_OPTIONS)
    length_label = col_f.selectbox("Length", list(LENGTH_OPTIONS), index=1)
    st.caption(TONE_PROFILES[tone]["hint"])

    st.write("")
    if st.button("Compose Description"):
        st.session_state.pop("result", None)
        api_key = resolve_api_key(api_key_input, saved_key)

        if not product.strip():
            st.warning("Please enter a product name.")
        elif not api_key:
            st.warning("No API key found. Paste one in the sidebar or add it to your .env file.")
        else:
            brief = Brief(
                brand=brand.strip(),
                product=product.strip(),
                category=category.strip(),
                materials=materials.strip(),
                details=details.strip(),
                audience=audience.strip(),
                tone=tone,
            )
            try:
                config = LLMConfig(api_key=api_key, model=model.strip() or DEFAULT_MODEL)
                client = create_client(config)
                result = run_pipeline(client, config, brief, LENGTH_OPTIONS[length_label], multi_step)
            except (LLMError, ValueError) as exc:
                st.error(str(exc))
            else:
                st.session_state["result"] = result
                st.download_button("Download as .txt", result["final"], file_name="description.txt")
    elif "result" in st.session_state:
        render_saved(st.session_state["result"])
        st.download_button("Download as .txt", st.session_state["result"]["final"], file_name="description.txt")


if __name__ == "__main__":
    main()
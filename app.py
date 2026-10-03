"""app.py - Streamlit UI for the luxury product description agent.

Run: streamlit run app.py
Requires: pip install streamlit anthropic
Key:     ANTHROPIC_API_KEY as an environment variable or in .streamlit/secrets.toml
"""

from __future__ import annotations

import os
import time
from collections.abc import Iterator
from dataclasses import replace

import streamlit as st

from llm_client import LLMConfig, LLMError, create_client, generate_text

# --------------------------------------------------------------------------- #
# Prompt
# --------------------------------------------------------------------------- #

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

LENGTH_OPTIONS = {
    "Concise (≈60 words)": (60, 300),
    "Standard (≈120 words)": (120, 500),
    "Extended (≈200 words)": (200, 800),
}

TONE_OPTIONS = [
    "Timeless & understated",
    "Romantic & evocative",
    "Modern & architectural",
    "Heritage & authoritative",
]


def build_user_prompt(
    *,
    brand: str,
    product: str,
    category: str,
    materials: str,
    details: str,
    audience: str,
    tone: str,
    words: int,
) -> str:
    """Assemble the user message from the form fields, skipping empty ones."""
    lines = [
        f"Brand: {brand}" if brand else "",
        f"Product: {product}",
        f"Category: {category}" if category else "",
        f"Materials & craftsmanship: {materials}" if materials else "",
        f"Key details: {details}" if details else "",
        f"Intended clientele: {audience}" if audience else "",
    ]
    facts = "\n".join(line for line in lines if line)
    return (
        "Write a luxury product description from the facts below.\n\n"
        f"{facts}\n\n"
        f"Tone: {tone}.\n"
        f"Length: approximately {words} words."
    )


# --------------------------------------------------------------------------- #
# Demo mode (no API key needed)
# --------------------------------------------------------------------------- #

# Demo is ON by default. For real API calls: DEMO_MODE=0 streamlit run app.py
DEMO_MODE = os.getenv("DEMO_MODE", "1") != "0"

DEMO_DEFAULTS = {
    "brand": "Rolex",
    "product": "Vintage Datejust 36, Champagne Dial",
    "category": "Fine watchmaking",
    "audience": "Collectors of vintage timepieces",
    "materials": "Stainless steel and white gold, Jubilee bracelet, automatic movement",
    "details": "36 mm case, fluted bezel, champagne sunburst dial, Cyclops date lens.",
}

DEMO_WATCH = (
    "Some watches announce themselves. This one simply arrives, a quiet presence on the "
    "wrist that has outlasted every fashion around it. The champagne dial catches the light "
    "the way late-afternoon sun settles on old gold, shifting from pale cream to deep honey "
    "with the slightest turn of the hand. Beneath the Cyclops lens, the date waits in its "
    "window with unhurried precision, while the fluted bezel frames the face in a ring of "
    "fine, deliberate light.\n\n"
    "The 36 millimetre case wears the way proportion was once understood: modest, balanced, "
    "entirely at ease beneath a cuff. The Jubilee bracelet drapes with a soft, liquid "
    "movement, each link settling gently against the next. Within, an automatic movement "
    "keeps its patient time, wound by the simple act of living. Decades on, the patina is "
    "not a flaw but a signature. This is a watch made to be worn every day and, in time, "
    "handed on."
)

DEMO_HANDBAG = (
    "Cut from full-grain Italian calfskin, the Aurèle Classique is a study in quiet "
    "restraint. Its silhouette is soft but certain: structured at the base, yielding at the "
    "shoulder, finished with edges burnished to a deep, glowing sheen. Saddle stitches, set "
    "by hand in waxed linen thread, trace each seam with the patient regularity of a "
    "metronome.\n\n"
    "Inside, a suede lining the colour of warm sand hushes the sound of a closing clasp. The "
    "brass hardware, polished and lightly brushed, carries the weight of something made to "
    "last rather than to impress. It holds what a day requires and nothing that it does not. "
    "Carried across a station platform or set down beside a candlelit table, it ages with "
    "grace, deepening with every season into something entirely, quietly yours."
)

DEMO_STEPS = [
    "Analysing product details…",
    "Studying brand voice and heritage…",
    "Drafting in the maison register…",
    "Refining language and rhythm…",
]


def pick_demo(product: str) -> str:
    """Return the pre-written description that matches the product name."""
    if any(k in product.lower() for k in ("bag", "tote", "clutch", "satchel")):
        return DEMO_HANDBAG
    return DEMO_WATCH


def simulate_generation(product: str) -> str:
    """Fake a multi-step generation process, then return the canned text."""
    with st.status("Composing…", expanded=True) as status:
        for step in DEMO_STEPS:
            st.write(step)
            time.sleep(0.9)
        status.update(label="Description ready", state="complete", expanded=False)
    return pick_demo(product)


def typewriter(text: str, delay: float = 0.035) -> Iterator[str]:
    """Yield the text word by word so it appears to be generated live."""
    for word in text.split(" "):
        yield word + " "
        time.sleep(delay)


# --------------------------------------------------------------------------- #
# Infrastructure
# --------------------------------------------------------------------------- #


def load_config() -> LLMConfig:
    """Read the API key from the environment first, then Streamlit secrets."""
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        try:
            api_key = st.secrets.get("ANTHROPIC_API_KEY", "")
        except Exception:  # no secrets file present
            api_key = ""
    return LLMConfig(api_key=api_key, model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5-5"))


@st.cache_resource(show_spinner=False)
def get_client(config: LLMConfig):
    """One shared client per config across reruns and sessions."""
    return create_client(config)


# --------------------------------------------------------------------------- #
# UI
# --------------------------------------------------------------------------- #

STYLE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@300;400;500&family=Inter:wght@300;400&display=swap');

#MainMenu, footer, header {visibility: hidden;}
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
.st-key-result p {
    font-family: 'Cormorant Garamond', serif; font-size: 1.35rem;
    line-height: 1.75; font-weight: 400;
}
</style>
"""


def main() -> None:
    st.set_page_config(page_title="Maison Copy", page_icon="◆", layout="centered")
    st.markdown(STYLE, unsafe_allow_html=True)
    st.markdown('<div class="lux-title">Maison Copy</div>', unsafe_allow_html=True)
    st.markdown('<div class="lux-sub">Luxury Description Atelier</div>', unsafe_allow_html=True)
    st.markdown('<div class="lux-rule"></div>', unsafe_allow_html=True)

    d = DEMO_DEFAULTS if DEMO_MODE else {}

    col_a, col_b = st.columns(2)
    brand = col_a.text_input("Brand (optional)", value=d.get("brand", ""), placeholder="e.g. Maison Aurèle")
    product = col_b.text_input("Product name *", value=d.get("product", ""), placeholder="e.g. Hand-stitched weekender")

    col_c, col_d = st.columns(2)
    category = col_c.text_input("Category", value=d.get("category", ""), placeholder="e.g. Leather goods")
    audience = col_d.text_input("Clientele (optional)", value=d.get("audience", ""), placeholder="e.g. Discerning travellers")

    materials = st.text_input(
        "Materials & craftsmanship",
        value=d.get("materials", ""),
        placeholder="e.g. Full-grain Italian calfskin, saddle-stitched by hand",
    )
    details = st.text_area(
        "Key details",
        value=d.get("details", ""),
        placeholder="Dimensions, finishes, heritage, signature elements…",
        height=110,
    )

    col_e, col_f = st.columns(2)
    tone = col_e.selectbox("Tone", TONE_OPTIONS)
    length_label = col_f.selectbox("Length", list(LENGTH_OPTIONS), index=1)

    st.write("")
    if st.button("Compose Description"):
        if not product.strip():
            st.warning("Please enter a product name.")
        elif DEMO_MODE:
            st.session_state["description"] = simulate_generation(product)
            st.session_state["animate"] = True
        else:
            words, max_tokens = LENGTH_OPTIONS[length_label]
            user_prompt = build_user_prompt(
                brand=brand.strip(),
                product=product.strip(),
                category=category.strip(),
                materials=materials.strip(),
                details=details.strip(),
                audience=audience.strip(),
                tone=tone,
                words=words,
            )
            try:
                config = load_config()
                with st.spinner("Composing…"):
                    st.session_state["description"] = generate_text(
                        get_client(config),
                        replace(config, max_tokens=max_tokens),
                        SYSTEM_PROMPT,
                        user_prompt,
                    )
                st.session_state["animate"] = False
            except (LLMError, ValueError) as exc:
                st.session_state.pop("description", None)
                st.error(str(exc))

    description = st.session_state.get("description")
    if description:
        st.markdown('<div class="lux-rule"></div>', unsafe_allow_html=True)
        with st.container(border=True, key="result"):
            if st.session_state.get("animate"):
                st.write_stream(typewriter(description))
                st.session_state["animate"] = False
            else:
                st.markdown(description)  # rendered as Markdown, never as raw HTML
        st.download_button("Download as .txt", description, file_name="description.txt")


if __name__ == "__main__":
    main()
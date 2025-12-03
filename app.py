import os
import json
from pathlib import Path
from difflib import SequenceMatcher  # needed for best_faq_match
from urllib.parse import quote_plus  # for building search URLs
import streamlit as st

# Optional OpenAI import
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    openai = None
    OPENAI_AVAILABLE = False

# ✅ FIRST and ONLY Streamlit page config call
st.set_page_config(
    page_title="MyCanada – Newcomer AI Assistant",
    page_icon="🍁",
    layout="wide",
)

# =========================================================
# Paths & data loading
# =========================================================

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"


@st.cache_data
def load_json(filename: str):
    path = DATA_DIR / filename
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


faqs = load_json("faqs.json")
cities = load_json("cities.json")
guides = load_json("immigration_guides.json")


# =========================================================
# Helper functions
# =========================================================

def best_faq_match(query: str, threshold: float = 0.55):
    """
    Find the FAQ question with highest similarity to the query.
    Returns (faq_dict or None, similarity_score).
    """
    query = (query or "").strip()
    if not query or not faqs:
        return None, 0.0

    best = None
    best_score = 0.0

    for faq in faqs:
        q_text = faq.get("question", "")
        score = SequenceMatcher(None, query.lower(), q_text.lower()).ratio()
        if score > best_score:
            best_score = score
            best = faq

    if best_score < threshold:
        return None, best_score
    return best, best_score


def list_provinces():
    if not cities:
        return []
    return sorted({c.get("province", "Unknown") for c in cities})


def cities_in_province(province: str):
    return [c for c in cities if c.get("province") == province]


def get_guide_by_topic(topic: str):
    for g in guides:
        if g.get("topic") == topic:
            return g
    return None


def maps_search_url(query: str) -> str:
    """Build a Google Maps search URL."""
    return f"https://www.google.com/maps/search/{quote_plus(query)}"


def google_search_url(query: str) -> str:
    """Generic Google search URL."""
    return f"https://www.google.com/search?q={quote_plus(query)}"


def get_openai_client():
    """Return configured OpenAI client or None if not available."""
    if not OPENAI_AVAILABLE:
        return None

    api_key = None
    # Try Streamlit secrets
    try:
        api_key = st.secrets.get("OPENAI_API_KEY", None)
    except Exception:
        api_key = None

    # Fallback to environment variable
    if not api_key:
        api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        return None

    openai.api_key = api_key
    return openai


def generate_ai_answer(user_question: str, faq: dict | None, lang_code: str):
    """
    Call OpenAI (if available) to generate a tailored answer as
    'MyCanada Newcomer AI Assistant'. Returns (answer, error_message).
    lang_code: "en" or "am"
    """
    client = get_openai_client()
    if client is None:
        return None, (
            "AI is not configured (missing API key or library). "
            "Showing FAQ-based answer only."
        )

    ref_text = ""
    if faq:
        ref_text = (
            f"Closest FAQ (for reference, do not copy blindly):\n"
            f"Q: {faq.get('question', '')}\n"
            f"A: {faq.get('answer', '')}\n"
        )

    system_msg = (
        "You are 'MyCanada Newcomer AI Assistant', a warm, supportive assistant for "
        "people who are new to Canada. You provide practical, concrete guidance about "
        "immigration basics, banking, housing, jobs, community supports, and daily life. "
        "You always remind users to verify legal and immigration details on official "
        "Government of Canada / IRCC sources. Keep answers clear and not too long."
    )

    if lang_code == "am":
        system_msg += (
            " Respond fully in Amharic (አማርኛ), using simple, clear language and short paragraphs. "
            "You may keep bank or website names in English when needed."
        )
    else:
        system_msg += " Respond in clear, simple English."

    user_msg = (
        f"User question:\n{user_question}\n\n"
        f"{ref_text}\n\n"
        "As the MyCanada Newcomer AI Assistant, give a step-by-step answer tailored to this user. "
        "At the end, ask 1–2 short clarifying or follow-up questions to keep the conversation going, "
        "but do NOT answer those follow-up questions yet."
    )

    try:
        # Using ChatCompletion from openai~=0.x
        response = client.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.5,
        )
        answer = response.choices[0].message["content"]
        return answer, None
    except Exception as e:
        return None, f"AI error: {e}"


# =========================================================
# Translation helpers (English <-> Amharic)
# =========================================================

def tr(en: str, am: str) -> str:
    """Simple inline translation helper."""
    lang = st.session_state.get("lang", "en")
    return am if lang == "am" else en


def translate_dynamic(item: dict, key: str) -> str:
    """
    For content coming from JSON, try keys like 'summary_am'.
    Fallback to the base key.
    """
    lang = st.session_state.get("lang", "en")
    if lang == "en":
        return item.get(key, "")
    am_key = f"{key}_am"
    return item.get(am_key, item.get(key, ""))


# =========================================================
# Streamlit UI – theming & layout
# =========================================================

# ---------- Custom CSS: improved contrast, font size, clean layout ----------
st.markdown(
    """
    <style>
    html, body, [class*="css"] {
        font-family: "Segoe UI", -apple-system, BlinkMacSystemFont, "Roboto", sans-serif;
    }

    .stApp {
        background: radial-gradient(circle at 0% 0%, #020617 0%, #020617 40%, #020617 100%);
    }

    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        background: linear-gradient(145deg, #fefce8 0%, #fffbeb 30%, #ecfdf5 65%, #e0f2fe 100%);
        border-radius: 24px;
        box-shadow: 0 22px 60px rgba(15, 23, 42, 0.55);
        margin-top: 1.2rem;
        margin-bottom: 2rem;
        max-width: 1200px;
    }

    /* Centered big title banner */
    .mc-hero {
        border-radius: 24px;
        padding: 1.4rem 1.8rem;
        text-align: center;
        background: radial-gradient(circle at top left, #fb923c 0%, #f97316 20%, #0284c7 85%);
        color: white;
        box-shadow: 0 18px 40px rgba(15, 23, 42, 0.7);
        margin-bottom: 1.0rem;
    }
    .mc-hero h1 {
        margin-bottom: 0.3rem;
        font-size: 2.3rem;
        letter-spacing: 0.03em;
    }
    .mc-hero p {
        margin-top: 0;
        font-size: 1.0rem;
        line-height: 1.5;
        opacity: 0.96;
    }

    /* Small pill tags */
    .mc-pill {
        display: inline-block;
        padding: 0.12rem 0.8rem;
        border-radius: 999px;
        font-size: 0.78rem;
        font-weight: 600;
        background-color: rgba(15, 23, 42, 0.22);
        color: #f9fafb;
        margin: 0 0.18rem;
    }

    /* Sidebar styling - better contrast, larger fonts, cleaner layout */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #020617 0%, #020617 60%, #020617 100%) !important;
        color: #f9fafb !important;
        padding: 1.2rem 1rem !important;
    }
    [data-testid="stSidebar"] * {
        color: #e5e7eb !important;
        font-size: 1.0rem !important;
    }
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: #facc15 !important;
        margin-bottom: 0.4rem !important;
    }
    [data-testid="stSidebar"] label {
        color: #e5e7eb !important;
        font-weight: 500;
    }
    [data-testid="stSidebar"] .element-container {
        padding-bottom: 0.35rem;
    }

    /* Cards */
    .mc-card {
        background-color: rgba(255, 255, 255, 0.9);
        border-radius: 18px;
        padding: 1rem 1.2rem;
        box-shadow: 0 10px 30px rgba(15, 23, 42, 0.18);
        margin-bottom: 0.9rem;
    }

    .mc-muted {
        color: #4b5563;
        font-size: 0.86rem;
    }

    .mc-chip {
        display: inline-flex;
        align-items: center;
        padding: 0.15rem 0.6rem;
        border-radius: 999px;
        background-color: #fee2e2;
        color: #b91c1c;
        font-size: 0.78rem;
        font-weight: 600;
        margin-right: 0.3rem;
        margin-bottom: 0.2rem;
    }

    h2, h3, h4 {
        letter-spacing: 0.01em;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# Sidebar – Language, navigation & filters
# =========================================================

# Language selector
lang_label = st.sidebar.selectbox(
    "Language / ቋንቋ",
    ["English", "Amharic (አማርኛ)"],
)
lang_code = "am" if "Amharic" in lang_label else "en"
st.session_state["lang"] = lang_code

def tr(en: str, am: str) -> str:
    """Re-declare to ensure it picks current lang_code in session."""
    return am if lang_code == "am" else en

st.sidebar.title(tr("MyCanada Controls", "MyCanada መቆጣጠሪያዎች"))

# Page definitions (codes so we can translate labels safely)
PAGE_DEFS = [
    {
        "code": "assistant",
        "icon": "🤖",
        "label_en": "Ask the Newcomer Assistant",
        "label_am": "ከአዲስ መጡ አጋዥ ጠይቅ",
    },
    {
        "code": "cities",
        "icon": "🏙️",
        "label_en": "Explore Cities & Provinces",
        "label_am": "ከተሞችን እና ክፍለ አካባቢዎችን ተመልከት",
    },
    {
        "code": "bank",
        "icon": "🏦",
        "label_en": "Open a Bank Account",
        "label_am": "የባንክ መለያ ክፈት",
    },
    {
        "code": "housing",
        "icon": "🏡",
        "label_en": "Housing Search",
        "label_am": "የቤት መፈለጊያ",
    },
    {
        "code": "employment",
        "icon": "💼",
        "label_en": "Employment Services",
        "label_am": "የስራ አገልግሎቶች",
    },
    {
        "code": "worship",
        "icon": "🛕",
        "label_en": "Places of Worship",
        "label_am": "የመሰገና ቤቶች",
    },
    {
        "code": "food",
        "icon": "🥘",
        "label_en": "Food & Cultural Community Support",
        "label_am": "ምግብ እና የባህል ድጋፍ",
    },
    {
        "code": "guides",
        "icon": "📚",
        "label_en": "Immigration Guides",
        "label_am": "የመግቢያ መመሪያዎች",
    },
    {
        "code": "about",
        "icon": "ℹ️",
        "label_en": "About this App",
        "label_am": "ስለዚህ መተግበሪያ",
    },
]

st.sidebar.subheader(tr("Mode", "ዘዴ"))

page_index = st.sidebar.radio(
    tr("Choose what you want to explore:", "ምን መፈለግ ትፈልጋለህ?"),
    options=list(range(len(PAGE_DEFS))),
    format_func=lambda i: f"{PAGE_DEFS[i]['icon']} "
                          f"{PAGE_DEFS[i]['label_am'] if lang_code == 'am' else PAGE_DEFS[i]['label_en']}",
)
page_code = PAGE_DEFS[page_index]["code"]

st.sidebar.markdown("---")
st.sidebar.subheader(tr("Quick filters (optional)", "ፈጣን ማጣፈጫዎች (በፈቃድ)"))

preferred_region = st.sidebar.multiselect(
    tr("Preferred region(s) in Canada", "በካናዳ ውስጥ የሚመሩት ክልል(ሎች)"),
    options=["Atlantic", "Central", "Prairies", "West Coast", "North"],
    help=tr(
        "Used as soft filters when browsing cities.",
        "ከተሞችን ሲመለከቱ እንደ ቀላል ማጣፈጫ ይጠቀማሉ።",
    ),
)

family_friendly = st.sidebar.checkbox(
    tr(
        "Show cities with strong family/newcomer support",
        "በቤተሰብ እና አዲስ መጡ ድጋፍ ጠንካራ ያሉ ከተሞችን አሳይ",
    ),
    value=False,
)

st.sidebar.markdown("---")
st.sidebar.caption(
    tr(
        "Built with ❤️ by Zalates Analytics as a learning & onboarding assistant for newcomers.",
        "ይህ መተግበሪያ በ Zalates Analytics ለአዲስ መጡ ሰዎች እንደ መማርያና መመሪያ አጋዥ ተገንብቷል።",
    )
)

# =========================================================
# Header / Hero
# =========================================================

st.markdown(
    f"""
    <div class="mc-hero">
        <h1>{tr("MyCanada – Newcomer AI Assistant 🍁", "MyCanada – ለአዲስ መጡ የኤይአይ አጋዥ 🍁")}</h1>
        <p>{tr(
            "Zalates Analytics – AI Data-Cleaning, Integration & Insight Dashboard for newcomers.",
            "Zalates Analytics – ለአዲስ መጡ ሰዎች የመረጃ ማጽዳት፣ ማዋሃድ እና ማብራሪያ ዳሽቦርድ።"
        )}<br>
        {tr(
            "Unify messy information, reduce confusion, and explore warm fall-coloured dashboards for immigration, settlement, and city choices.",
            "የተበታተነ መረጃ ያንዱን ያድርጉ፣ ውርጭነትን አቀንሱ፣ ስለ መግቢያ፣ መቀመጫ እና የከተሞች ምርጫ ቀለማቸው ሞቃት ዳሽቦርዶችን ያስሱ።"
        )}</p>
        <div style="margin-top:0.4rem;">
            <span class="mc-pill">{tr("Immigration basics", "የመግቢያ መሠረታዊ መረጃ")}</span>
            <span class="mc-pill">{tr("City & province explorer", "ከተሞችንና ክልሎችን መመርመሪያ")}</span>
            <span class="mc-pill">{tr("First weeks in Canada", "በካናዳ የመጀመሪያ ሳምንቶች")}</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.caption(
    tr(
        "⚠️ This assistant is for general information only. It does **not** replace legal or immigration advice. Always verify details on official Government of Canada / IRCC websites.",
        "⚠️ ይህ አጋዥ በአጠቃላይ መረጃ ለመርዳት ብቻ ነው። የሕግ ወይም የመግቢያ ምክርን አይተካም። መረጃውን ሁልጊዜ ከመንግስት የካናዳ / IRCC ድህረገፄ ጋር ያረጋግጡ።",
    )
)

# =========================================================
# Page 1 – Ask the assistant (FAQ-style QA with AI)
# =========================================================

if page_code == "assistant":
    if lang_code == "am":
        st.subheader("ከ MyCanada አዲስ መጡ ኤይአይ አጋዥ ጋር ጠይቅ")
        question_label = "ስለ ካናዳ መግባት ወይም መቀመጥ ጥያቄህን እዚህ ጻፍ፦"
        question_ph = "ለምሳሌ፡ የንባብ ፈቃድ እንዴት እጠይቃለሁ? ለ Express Entry የሥራ ስምሪት አስፈላጊ ነው?"
        ask_label = "ከ MyCanada አጋዥ ጠይቅ"
    else:
        st.subheader("Ask the Newcomer Assistant")
        question_label = "Type your question about coming to or settling in Canada:"
        question_ph = (
            "e.g., How do I apply for a study permit? Do I need a job offer for Express Entry?"
        )
        ask_label = "Ask MyCanada Assistant"

    col_q, col_info = st.columns([2, 1.2])

    with col_q:
        user_question = st.text_input(
            question_label,
            placeholder=question_ph,
        )
        ask = st.button(ask_label)

    with col_info:
        if lang_code == "am":
            st.markdown(
                """
                <div class="mc-card">
                    <strong>ጠቃሚ መመሪያዎች</strong>
                    <ul style="padding-left:1.1rem;margin-top:0.4rem;">
                        <li>አንድ ዋና ጥያቄ ብቻ ጠይቅ።</li>
                        <li>ተማሪ፣ ሰራተኛ ወይም እስር ተጠያቂ መሆንህን ግለጽ።</li>
                        <li>ሁልጊዜ ከ IRCC የመንግስት ድህረገፆች ጋር ያረጋግጡ።</li>
                    </ul>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                """
                <div class="mc-card">
                    <strong>Tips for better answers</strong>
                    <ul style="padding-left:1.1rem;margin-top:0.4rem;">
                        <li>Ask one main question at a time.</li>
                        <li>Mention if you are a student, worker, or refugee claimant.</li>
                        <li>Always double-check details on official IRCC sites.</li>
                    </ul>
                </div>
                """,
                unsafe_allow_html=True,
            )

    if ask and user_question.strip():
        faq, score = best_faq_match(user_question)

        # Try AI first
        ai_answer, ai_error = generate_ai_answer(user_question, faq, lang_code)

        if lang_code == "am":
            st.markdown("### 🗣️ ጥያቄህ")
        else:
            st.markdown("### 🗣️ Your question")
        st.write(user_question)

        if lang_code == "am":
            st.markdown("### 🤖 መልስ ከ MyCanada አጋዥ")
        else:
            st.markdown("### 🤖 Assistant answer")

        if ai_answer:
            st.write(ai_answer)
        else:
            # Fallback: FAQ only
            if ai_error:
                st.info(ai_error)
            if faq:
                st.write(faq.get("answer", ""))
                if faq.get("tags"):
                    st.markdown(
                        " ".join(f'<span class="mc-chip">{t}</span>' for t in faq["tags"]),
                        unsafe_allow_html=True,
                    )
            else:
                st.warning(
                    tr(
                        "I could not find a close match in my current FAQ data. Try rephrasing your question or selecting a guide on the **Immigration Guides** page.",
                        "በአሁኑ ያሉ የFAQ መረጃዬ ውስጥ ተመሳሳይ ጥያቄ ማግኘት አልቻልኩም። ጥያቄዎን  занንሱ ወይም በ“የመግቢያ መመሪያዎች” ገጽ ላይ መመሪያ ይምረጡ።",
                    )
                )

        # Transparency: show matched FAQ
        if faq:
            if lang_code == "am":
                st.markdown("### 🔍 በጣም ተመሳሳይ የተገኘው FAQ")
            else:
                st.markdown("### 🔍 Closest matched FAQ (for transparency)")
            with st.expander(tr("Show matched FAQ", "ተመሳሳይ FAQ አሳይ")):
                st.write(f"**Matched question (similarity: {score:.2f})**")
                st.write(faq.get("question", ""))


# =========================================================
# Page 2 – City & Province explorer
# =========================================================

elif page_code == "cities":
    st.subheader(tr("🏙️ Explore Cities & Provinces", "🏙️ ከተሞችን እና ክፍለ አካባቢዎችን ተመልከት"))

    if not cities:
        st.error("No city data available. Please check `data/cities.json`.")
    else:
        provinces = list_provinces()
        col_filters, col_cards = st.columns([1.2, 2.3])

        with col_filters:
            province_choice = st.selectbox(
                tr("Select a province or territory", "ክፍለ አካባቢ ወይም ከተማ ይምረጡ"),
                options=["(all)"] + provinces,
            )

            settlement_focus = st.multiselect(
                tr("What matters most to you?", "ለእርስዎ በጣም የሚነጥቀው ምንድን ነው?"),
                options=[
                    "Affordability",
                    "Jobs & economy",
                    "Public transit",
                    "Student life",
                    "Immigrant services",
                    "Family & schools",
                ],
            )

        with col_cards:
            # Filter logic
            filtered = cities
            if province_choice != "(all)":
                filtered = [c for c in filtered if c.get("province") == province_choice]

            if preferred_region:
                filtered = [
                    c
                    for c in filtered
                    if c.get("region_label") in preferred_region or not c.get("region_label")
                ]

            if family_friendly:
                filtered = [c for c in filtered if c.get("family_friendly", False)]

            st.markdown(
                tr(
                    f"Showing **{len(filtered)}** city(ies) that match your filters.",
                    f"ከማጣፈጫዎችዎ ጋር ተስማሚ **{len(filtered)}** ከተሞችን እያሳየ ነው።",
                )
            )

            if not filtered:
                st.info(
                    tr(
                        "Try removing some filters to see more cities.",
                        "ተጨማሪ ከተሞች ለማየት አንዳንድ ማጣፈጫዎችን ያስወግዱ።",
                    )
                )
            else:
                for city in filtered:
                    name = translate_dynamic(city, "name") or city.get("name")
                    prov = city.get("province")
                    region_label = translate_dynamic(city, "region_label")
                    summary = translate_dynamic(city, "summary")
                    newcomers = translate_dynamic(city, "newcomer_support")
                    key_sectors = city.get("key_sectors", [])
                    cost_level = city.get("cost_of_living", "Unknown")
                    transit = city.get("transit", "Unknown")

                    st.markdown(
                        f"""
                        <div class="mc-card">
                            <h3 style="margin-bottom:0.1rem;">{name}, {prov}</h3>
                            <p class="mc-muted" style="margin-top:0.1rem;">{region_label}</p>
                            <p style="margin-top:0.4rem;">{summary}</p>
                            <p><strong>{tr("Newcomer services:", "የአዲስ መጡ አገልግሎቶች፦")}</strong> {newcomers}</p>
                            <p>
                                <strong>{tr("Cost of living:", "የኑሮ ወጪ፦")}</strong> {cost_level} &nbsp; • &nbsp;
                                <strong>{tr("Transit:", "ትራንስፖርት፦")}</strong> {transit}
                            </p>
                            <p>
                                {"".join(f'<span class="mc-pill">{sec}</span>' for sec in key_sectors)}
                            </p>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

# =========================================================
# Page 3 – Open a Bank Account
# =========================================================

elif page_code == "bank":
    st.subheader(tr("🏦 Open a Bank Account in Canada", "🏦 በካናዳ ውስጥ የባንክ መለያ መክፈት"))

    if lang_code == "am":
        st.markdown(
            """
            ባንክ መለያ መክፈት የክፍያ፣ የደመወዝ መቀበያ እና የክሬዲት ታሪክ ለመጀመር በጣም አስፈላጊ ነው።
            ከታች ዋና እርምጃዎችን በቀላሉ ተከትሉ።
            """
        )
    else:
        st.markdown(
            """
            Opening a bank account early helps you **receive your salary, pay rent, and build credit**.
            Let’s go through the key steps together.
            """
        )

    location = st.text_input(
        tr(
            "Where are you right now? (city or postal code)",
            "አሁን የምትገኙበት ከተማ ወይም ፖስታ ኮድ ያስገቡ፦",
        ),
        placeholder=tr("e.g., Toronto, ON or M5V 2T6", "ለምሳሌ፡ Toronto, ON ወይም M5V 2T6"),
    )

    st.markdown(
        tr(
            "### 1. Key steps to open a basic chequing account",
            "### 1፡ መሰረታዊ የቻክ መለያ ለመክፈት ዋና እርምጃዎች",
        )
    )

    if lang_code == "am":
        st.markdown(
            """
            1. **ባንክ እና የመለያ አይነት ይምረጡ** (የአዲስ መጡ መለያ፣ የተማሪ መለያ ወዘተ)  
            2. **የመለያ ሰነዶችዎን ያዘጋጁ** (ብዙውን ጊዜ 2 መለያ ያስፈልጋል):  
               - ፓስፖርት  
               - የንባብ / የስራ ፈቃድ ወይም የPR ካርድ  
               - የአድራሻ ማረጋገጫ (የኪራይ ስምሪት፣ የመመለሻ ደብዳቤ ወዘተ)  
               - SIN (ካለዎት – መለያ ለመክፈት ግዴታ የለውም ግን ብዙ ጊዜ ይጠየቃል)  
            3. **ቅጽ ሙሉ ወይም በቅድሚያ ቀጠሮ ይያዙ** እና ወደ ቅርብ ቅርንጫፍ ይሂዱ።  
            4. **ከባንክ ባለሙያ ጋር ይወያዩ** – መለያውን ይክፈቱልዎታል እና የዴቢት ካርድ ይሰጡዎታል።  
            5. **ኦንላይን እና ሞባይል ባንክንግ ያበሩ**፣ e-Transfer እና መረጃ መጠንቀቂያዎችን ይቀናብሩ።  
            6. (በፈቃድ) ስለ **ክሬዲት ካርድ፣ ባንክ መታወክ (overdraft) እና የአዲስ መጡ ስፔሻል ፓኬጅ** ይጠይቁ።
            """
        )
    else:
        st.markdown(
            """
            1. **Choose a bank and account type** (e.g., newcomer chequing account, student account).  
            2. **Prepare your documents** (usually 2 pieces of ID):  
               - Passport  
               - Study permit / work permit / PR card  
               - Proof of address (rental agreement, utility bill, official letter)  
               - SIN (if you have it – not required to open an account, but often requested)  
            3. **Book an appointment or walk in** to a branch.  
            4. **Meet with a banking advisor** – they verify your ID, open your account, and give you a debit card.  
            5. **Set up online & mobile banking**, e-Transfers, and alerts.  
            6. (Optional) Ask about **credit card**, **overdraft**, and **newcomer welcome offers**.
            """
        )

    st.markdown(
        tr(
            "### 2. Newcomer banking programs (Big 5 banks)",
            "### 2. ለአዲስ መጡ የባንክ ፕሮግራሞች (Big 5 ባንኮች)",
        )
    )

    if lang_code == "am":
        st.info(
            "ብዙ ታላላቅ ባንኮች ለአዲስ መጡ የሚሰጡ ፓኬጅዎች አሏቸው (ነፃ ክፍያ ያለው መለያ፣ ነጻ ስርዓተ-ገንዘብ ማስተላለፊያ ወዘተ)። ዝርዝሮችን በባንኩ ድህረገፅ ላይ ያረጋግጡ።"
        )
    else:
        st.info(
            "Most major banks have **newcomer packages** with no-fee accounts for 6–12 months, "
            "free international transfers, or cash bonuses. Always check the latest details on their websites."
        )

    bank_links = {
        "RBC – Newcomers to Canada": "https://www.rbc.com/newcomers",
        "TD – New to Canada Banking": "https://www.td.com/ca/en/personal-banking/solutions/new-to-canada",
        "Scotiabank – StartRight® Program": "https://www.scotiabank.com/ca/en/personal/bank/bank-accounts/newcomers.html",
        "CIBC – Newcomer Banking": "https://www.cibc.com/en/personal-banking/newcomers.html",
        "BMO – NewStart® Program": "https://www.bmo.com/main/personal/bank-accounts/newcomers-to-canada",
    }

    for label, url in bank_links.items():
        st.markdown(f"- [{label}]({url})")

    st.markdown(tr("### 3. Find branches near you", "### 3. ቅርብ ያሉ የባንክ ቅርንጫፎችን ያግኙ"))

    if location.strip():
        if lang_code == "am":
            st.success("በእርስዎ አካባቢ ያሉ ባንኮችን ለመፈለግ የ Google Maps አገናኞች፦")
        else:
            st.success("Here are quick links to find branches close to you on Google Maps:")

        banks = ["RBC", "TD Bank", "Scotiabank", "CIBC", "BMO Bank of Montreal"]

        for b in banks:
            query = f"{b} near {location}"
            url = maps_search_url(query)
            st.markdown(f"- [{b} near {location}]({url})")

        st.caption(
            tr(
                "Tip: When you open the map, you’ll see **distance, directions, opening hours, and phone numbers**.",
                "ምክር፦ ካርታውን ሲከፍቱ **ርቀት፣ አቅጣጫ፣ የመክፈቻ ሰዓቶች እና ስልክ ቁጥሮችን** ታያላችሁ።",
            )
        )
    else:
        st.warning(
            tr(
                "Please type your city or postal code above so I can suggest nearby branches.",
                "እባክዎን ከላይ ከተማዎን ወይም ፖስታ ኮድዎን ያስገቡ እና ቅርብ ያሉ ባንኮችን እንዲጠቁምልዎ።",
            )
        )

# =========================================================
# Page 4 – Housing Search
# =========================================================

elif page_code == "housing":
    st.subheader(tr("🏡 Rental Housing for Newcomers", "🏡 ለአዲስ መጡ ሰዎች የኪራይ ቤት መፈለጊያ"))

    if lang_code == "am":
        st.markdown(
            "ለኪራይ ቤት መፈለግ በተለይ በመጀመሪያ ወራቶች እየተባበረ ይሰማል። ከተማ፣ በጀት እና የቤት አይነት መሰረት በመጠቀም እንጀምር።"
        )
    else:
        st.markdown(
            "Let’s explore rental options based on your **city, budget, and type of place**."
        )

    city = st.text_input(
        tr("Preferred city", "የሚመርጡት ከተማ"),
        placeholder=tr("e.g., Ottawa, ON", "ለምሳሌ፡ Ottawa, ON"),
    )
    budget = st.slider(
        tr("Approximate monthly budget (CAD)", "በወር የሚመረጥ በጀት (በዶላር)"),
        min_value=500,
        max_value=4000,
        value=1800,
        step=50,
    )
    accom_type = st.selectbox(
        tr("Type of accommodation", "የቤት አይነት"),
        [
            tr("Any", "ማንኛውም"),
            tr("Room in shared house", "በተካፋይ ቤት ውስጥ ክፍል"),
            tr("Bachelor / studio", "ባችለር / ስቱዲዮ"),
            tr("1-bedroom apartment", "1 መኝታ አፓርታማ"),
            tr("2-bedroom apartment", "2 መኝታ አፓርታማ"),
            tr("Family-size house / townhouse", "ለቤተሰብ አይነት ቤት / ታውንሃውስ"),
        ],
    )

    if city.strip():
        st.markdown(tr("### 1. Search rental listings (trusted platforms)", "### 1. የኪራይ ቤቶች ማግኘት (ታማኝ መስኮቶች)"))

        city_q = city.strip()
        # Use a simple English search phrase for external sites
        accom_search = "Any" if "ማንኛውም" in accom_type else accom_type
        search_phrase = f"rent {accom_search} {city_q}" if "Any" not in accom_search else f"rent apartment {city_q}"

        links = {
            "Rentals.ca": google_search_url(f"site:rentals.ca {search_phrase}"),
            "Kijiji Rentals": google_search_url(f"site:kijiji.ca {search_phrase}"),
            "Facebook Marketplace": "https://www.facebook.com/marketplace/search/?query="
            + quote_plus(search_phrase),
            "PadMapper / Zumper / Others": google_search_url(f"rentals {city_q} apartments"),
        }

        for label, url in links.items():
            st.markdown(f"- [{label} – search for **{city_q}**]({url})")

        st.markdown(tr("### 2. Neighbourhood & rent guidance (approximate)", "### 2. ማህበረሰብ እና የኪራይ መጠን (በግምት)"))

        low = max(400, budget - 400)
        mid_low = max(500, budget - 200)
        mid_high = budget + 200
        high = budget + 500

        if lang_code == "am":
            st.markdown(
                f"""
                እነዚህ የቤት ኪራይ የሚገኙት መጠኖች በብዙ ከተሞች ውስጥ በግምት ናቸው።  
                በእውነቱ መጠኖች በከተማ እና በማዕከል ይለያያሉ፦

                - **በጣም ዝቅተኛ / ተካፋይ አማራጮች**፡ በወር ግምት ~${low}–${mid_low}  
                - **መደበኛ 1-መኝታ**፡ ~${mid_low}–${mid_high}  
                - **ትልቅ የቤተሰብ መኖሪያ**፡ ~${mid_high}–${high}+  

                እነዚህን ቁጥሮች እንደ መጀመሪያ መመሪያ ብቻ ይጠቀሙ።
                """
            )
        else:
            st.markdown(
                f"""
                These are **very rough ranges** you might see in many Canadian cities.  
                Actual prices vary a lot by city and neighbourhood:

                - **Budget / shared options**: ~${low}–${mid_low} / month  
                - **Typical 1-bedroom**: ~${mid_low}–${mid_high} / month  
                - **Larger family units**: ~${mid_high}–${high}+ / month  

                Use these numbers only as a **starting point**, and always confirm with the actual listing.
                """
            )

        st.markdown(tr("### 3. Transit & commute tips", "### 3. የትራንስፖርት እና ስራ መጓጓዣ ምክሮች"))

        if lang_code == "am":
            st.info(
                "የቤት ማስታወቂያን ሲመለከቱ በ Google Maps ላይ ይክፈቱ እና ይመልከቱ፦\n"
                "- ከስራዎ ወይም ትምህርት ቤትዎ ርቀት\n"
                "- ቅርብ ያሉ አውቶቡስ / ሜትሮ መስመሮች\n"
                "- በጅምላ ሰዓት የጉዞ ጊዜ\n"
                "- ወደ ሱፐርማርኬት እና መድሀኒት ቤት የሚሆን መራመድ ርቀት"
            )
        else:
            st.info(
                "When checking a listing, open it in Google Maps and look for:\n"
                "- Distance to your school / workplace\n"
                "- Bus / subway / LRT lines nearby\n"
                "- Travel time during rush hour\n"
                "- Walking distance to grocery stores and pharmacies"
            )
    else:
        st.warning(
            tr(
                "Please enter a city so I can tailor housing search links for you.",
                "እባክዎን ከተማ ያስገቡ እንዲሁም ለእርስዎ ተስማሚ የቤት መፈለጊያ አገናኞችን እንድሰጥዎ።",
            )
        )

# =========================================================
# Page 5 – Employment Services
# =========================================================

elif page_code == "employment":
    st.subheader(tr("💼 Find Jobs & Employment Support", "💼 ስራ እና የስራ ድጋፍ ፈልግ"))

    if lang_code == "am":
        st.markdown("የስራ ፍለጋ እና የአዲስ መጡ የስራ ማስተላለፊያ አገልግሎቶችን እንጀምር።")
    else:
        st.markdown(
            "Let’s search for jobs and newcomer employment services that match your goals."
        )

    job_title = st.text_input(
        tr(
            "What type of job are you looking for?",
            "ምን ዓይነት ስራ እየፈለጉ ነው?",
        ),
        placeholder=tr(
            "e.g., Data analyst, PSW, warehouse worker, cashier",
            "ለምሳሌ፡ Data analyst, PSW, warehouse worker, cashier",
        ),
    )
    job_city = st.text_input(
        tr("Preferred city or region for work", "ስራ ለማግኘት የሚመርጡት ከተማ / ክልል"),
        placeholder=tr("e.g., Toronto, ON or Calgary, AB", "ለምሳሌ፡ Toronto, ON ወይም Calgary, AB"),
    )

    if job_title.strip() and job_city.strip():
        q_job = job_title.strip()
        q_city = job_city.strip()

        st.markdown(tr("### 1. Job postings on trusted Canadian platforms", "### 1. በታማኝ የካናዳ መድረኮች ላይ ስራ ፍለጋ"))

        indeed_url = f"https://ca.indeed.com/jobs?q={quote_plus(q_job)}&l={quote_plus(q_city)}"
        jobbank_url = (
            "https://www.jobbank.gc.ca/jobsearch/jobsearch?"
            f"searchstring={quote_plus(q_job)}&locationstring={quote_plus(q_city)}"
        )
        linkedin_url = (
            "https://www.linkedin.com/jobs/search/?"
            f"keywords={quote_plus(q_job)}&location={quote_plus(q_city)}"
        )

        st.markdown(f"- [Indeed – {q_job} in {q_city}]({indeed_url})")
        st.markdown(f"- [Job Bank – {q_job} in {q_city}]({jobbank_url})")
        st.markdown(f"- [LinkedIn Jobs – {q_job} in {q_city}]({linkedin_url})")

        st.markdown(tr("### 2. Match & relevance (how to judge a good posting)", "### 2. ስራው እንደሚመስል መገመት"))

        if lang_code == "am":
            st.info(
                "እነዚህን ነጥቦች ይመልከቱ፦\n"
                "- የስራ ርዕስና ተግባር ከክህሎትዎ ጋር እንዲመጣ\n"
                "- የተፈለገው ልምድ ቅርብ እንዲሆን\n"
                "- ቦታ እና የስራ አይነት (on-site / hybrid / remote)\n"
                "- ደመወዝ ከመጠባበቂያዎ ጋር እንዲስማማ\n"
                "- ለአዲስ መጡ ድጋፍ የሚሰጥ ተቋም መሆን"
            )
        else:
            st.info(
                "Look for:\n"
                "- Job title and duties similar to your skills\n"
                "- Required experience close to your background\n"
                "- Location and work arrangement (on-site / hybrid / remote)\n"
                "- Salary range that fits your expectations\n"
                "- Employer offering training or support for newcomers"
            )

        st.markdown(tr("### 3. Newcomer employment centres near you", "### 3. ቅርብ ያሉ የአዲስ መጡ የስራ ማዕከላት"))

        newcomer_query = f"employment services for newcomers near {q_city}"
        newcomer_url = maps_search_url(newcomer_query)

        st.markdown(
            f"- [{tr('Newcomer employment & settlement services near', 'አዲስ መጡ የስራ እና መቀመጫ አገልግሎቶች ቅርብ ከ')}"
            f" {q_city}]({newcomer_url})"
        )
        st.caption(
            tr(
                "These can include YMCA, COSTI, ACCES Employment, immigrant settlement agencies, and community organizations that help with resumes, networking, and interview practice.",
                "ይህ የሚለው YMCA፣ COSTI፣ ACCES Employment፣ የመግቢያ ማዕከላትንና ሌሎች የማህበረሰብ ተቋማትን ሊያካትት ይችላል፣ ሪዙሜ፣ ኔትዎርኪንግ እና ቃለ መጠይቅ ለማሰልጠን ይረዳሉ።",
            )
        )

        st.markdown(tr("### 4. Resume & interview tips (tailored to your role)", "### 4. ለሪዙሜ እና ለቃለ መጠይቅ ምክሮች"))

        if lang_code == "am":
            st.write(
                f"ለ **{q_job}** የሚመሩ ስራዎች፦\n"
                "- ከስራ ልምድዎ ጋር ተመሳሳይ የሆኑ ተግባራትን በግልፅ ያመልክቱ\n"
                "- አንድ ወይም ሁለት ገጽ ያለው የካናዳ ዓይነት ሪዙሜ ይጠቀሙ\n"
                "- ውጤቶችን በቁጥር ያመልክቱ (ለምሳሌ፡ “አስራ 20% ጊዜ ቀነሰ”) \n"
                "- የተለመዱ ጥያቄዎችን ተመልሰው ይለማመዱ፦ 'ስለራስህ ተናገር' ወዘተ"
            )
        else:
            st.write(
                f"For **{q_job}** roles, try to:\n"
                "- Highlight your most recent **work experience** that matches the job duties\n"
                "- Use **Canadian-style resume format** (1–2 pages, no photo, clear bullet points)\n"
                "- Add **quantified results** (e.g., 'reduced processing time by 20%') where possible\n"
                "- Practice answers to common questions such as:\n"
                "  - 'Tell me about yourself'\n"
                "  - 'Why do you want this role?'\n"
                "  - 'Tell me about a time you solved a problem at work'\n"
            )
    else:
        st.warning(
            tr(
                "Please enter both a job type and a city so I can build search links for you.",
                "እባክዎን ስራ አይነትን እና ከተማን ያስገቡ እንዲሁም አገናኞችን እንድገነባልዎ።",
            )
        )

# =========================================================
# Page 6 – Places of Worship (improved, language/country specific)
# =========================================================

elif page_code == "worship":
    st.subheader(tr("🛕 Find a Place of Worship or Spiritual Community", "🛕 የመሰገና ቤት ወይም መንፈሳዊ ማህበር ፈልግ"))

    worship_options = [
        {"code": "christian", "label_en": "Christian church", "label_am": "የክርስቲያን ቤተክርስቲያን"},
        {"code": "muslim", "label_en": "Muslim mosque", "label_am": "የሙስሊም መስጊድ"},
        {"code": "jewish", "label_en": "Jewish synagogue", "label_am": "የይሁዳውያን ሲናጎግ"},
        {"code": "hindu", "label_en": "Hindu temple", "label_am": "የሂንዱ ቤተመቅደስ"},
        {"code": "buddhist", "label_en": "Buddhist temple", "label_am": "የቡዲስት ቤተመቅደስ"},
        {"code": "sikh", "label_en": "Sikh gurdwara", "label_am": "የሲክ ጉርድዋራ"},
        {"code": "other", "label_en": "Other / interfaith centre", "label_am": "ሌላ / የተዋሃደ እምነት ማዕከል"},
    ]

    def worship_label(opt):
        return opt["label_am"] if lang_code == "am" else opt["label_en"]

    worship_choice_index = st.selectbox(
        tr("What type of worship place are you looking for?", "የእምነት ቤት ዓይነት ምንድን ነው የሚፈልጉት?"),
        options=list(range(len(worship_options))),
        format_func=lambda i: worship_label(worship_options[i]),
    )
    worship_choice = worship_options[worship_choice_index]
    worship_code = worship_choice["code"]

    worship_city = st.text_input(
        tr("Your city or postal code", "ከተማዎ ወይም ፖስታ ኮድዎ"),
        placeholder=tr("e.g., Winnipeg, MB or H3Z 2Y7", "ለምሳሌ፡ Winnipeg, MB ወይም H3Z 2Y7"),
    )

    preferred_worship_lang = st.text_input(
        tr(
            "Preferred worship language or country (optional)",
            "የመሰገና ቋንቋ ወይም አገር (በፈቃድ)",
        ),
        placeholder=tr(
            "e.g., Amharic, Arabic, Ethiopian, Filipino",
            "ለምሳሌ፡ Amharic, Arabic, Ethiopian, Filipino",
        ),
    )

    if worship_city.strip():
        # Internal keywords for Google Maps (robust + specific)
        label_map = {
            "christian": "church",
            "muslim": "mosque",
            "jewish": "synagogue",
            "hindu": "hindu temple",
            "buddhist": "buddhist temple",
            "sikh": "gurdwara",
            "other": "spiritual centre",
        }
        place_keyword = label_map.get(worship_code, "church")

        # Build richer query including language/country if provided
        query_parts = []
        if preferred_worship_lang.strip():
            query_parts.append(preferred_worship_lang.strip())
        query_parts.append(place_keyword)
        query = " ".join(query_parts) + f" near {worship_city.strip()}"

        url = maps_search_url(query)

        st.markdown(tr("### Nearest worship centres", "### ቅርብ ያሉ የመሰገና ቤቶች"))

        st.markdown(
            f"- [{tr('See specific results on Google Maps', 'የቋንቋ ወይም የአገር ተስማሚ ውጤቶችን በ Google Maps ላይ ይመልከቱ')} – {query}]({url})"
        )
        st.caption(
            tr(
                "Because we include your language/country (if provided), results can show Ethiopian, Filipino, Arabic, or other specific communities instead of only generic sites.",
                "የቋንቋ ወይም አገር ስም ስንጨምር ውጤቶች ብቻ ጠቅላላ ቤተክርስቲያን ሳይሆኑ ልዩ የኢትዮጵያ ፣ የፊሊፒንስ ፣ የአረብ ወዘተ ማህበረሰቦችን ሊያሳዩ ይችላሉ።",
            )
        )

        st.info(
            tr(
                "You can further refine inside Google Maps by filtering reviews, photos, and service times.",
                "በ Google Maps ውስጥ ግምገማዎች፣ ፎቶዎች እና የአገልግሎት ሰዓት በመመርመር ውጤቶችን ተጨማሪ ማጣፈጥ ትችላለህ።",
            )
        )
    else:
        st.warning(
            tr(
                "Please enter your city or postal code so I can locate nearby places of worship.",
                "እባክዎን ከተማዎን ወይም ፖስታ ኮድዎን ያስገቡ እንዲሁም ቅርብ ያሉ የመሰገና ቤቶችን እንድሰጥዎ።",
            )
        )

# =========================================================
# Page 7 – Food & Cultural Community Support
# =========================================================

elif page_code == "food":
    st.subheader(tr("🥘 Find Your Food, Culture & Community", "🥘 ምግብዎን፣ ባህልዎንና ማህበረሰብዎን ፈልጉ"))

    origin_country = st.text_input(
        tr(
            "Which country or culture do you identify with most?",
            "በየትኛው አገር ወይም ባህል እርስዎን ብዙ ጊዜ ይስማማል?",
        ),
        placeholder=tr("e.g., Ethiopia, India, Philippines, Brazil", "ለምሳሌ፡ Ethiopia, India, Philippines, Brazil"),
    )
    food_city = st.text_input(
        tr(
            "Where are you living now? (city or postal code)",
            "አሁን የምትኖሩበት ቦታ ምንድን ነው? (ከተማ ወይም ፖስታ ኮድ)",
        ),
        placeholder=tr("e.g., Surrey, BC or M1P 4P5", "ለምሳሌ፡ Surrey, BC ወይም M1P 4P5"),
    )

    if origin_country.strip() and food_city.strip():
        o = origin_country.strip()
        c = food_city.strip()

        st.markdown(tr("### 1. Grocery stores with your traditional foods", "### 1. የባህላዊ ምግብዎን የሚሸጡ ሱቆች"))

        grocery_query = f"{o} grocery store near {c}"
        grocery_url = maps_search_url(grocery_query)
        st.markdown(f"- [{tr('Stores selling your food near', 'የምግብዎን የሚሸጡ ሱቆች ቅርብ ከ')} {c}]({grocery_url})")

        st.markdown(tr("### 2. Cultural associations & community groups", "### 2. የባህል ማህበሮችና ማህበረሰብ ቡድኖች"))

        assoc_query = f"{o} community association near {c}"
        assoc_url = google_search_url(assoc_query)
        st.markdown(f"- [{tr('Cultural associations and community groups', 'የባህል ማህበሮችና ማህበረሰብ ቡድኖች')}]({assoc_url})")

        st.markdown(tr("### 3. Restaurants, cafés, and local events", "### 3. ረስቶራንቶች፣ ካፌዎችና የባህል በዓላት"))

        rest_query = f"{o} restaurant near {c}"
        rest_url = maps_search_url(rest_query)
        events_query = f"{o} cultural events {c}"
        events_url = google_search_url(events_query)

        st.markdown(
            f"- [{tr('Restaurants & cafés serving your food near', 'የምግብዎን የሚያቀርቡ ረስቶራንቶችና ካፌዎች ቅርብ ከ')} {c}]({rest_url})"
        )
        st.markdown(f"- [{tr('Local cultural events and festivals', 'የባህል በዓላትና በከተማዊ እንቅስቃሴዎች')}]({events_url})")

        st.caption(
            tr(
                "On these pages you'll usually find **opening hours, phone numbers, websites, and directions**.",
                "በእነዚህ ገፆች ላይ **የመክፈቻ ሰዓቶች፣ ስልክ ቁጥሮች፣ ድህረገፆች እና አቅጣጫዎች** ማግኘት ትችላላችሁ።",
            )
        )

        st.info(
            tr(
                "You are not alone. Connecting with people from your culture and new Canadian friends can make your first months much easier and warmer.",
                "ብቻዎን አይደሉም። ከባህልዎ ጋር እና ከነባር ካናዳውያን ጓደኞች ጋር መገናኘት የመጀመሪያ ወራቶችዎን ቀላል እና ሞቃት ያስራዋል።",
            )
        )
    else:
        st.warning(
            tr(
                "Please fill in both your country/culture and your current city/postal code.",
                "እባክዎን አገርዎን/ባህልዎን እና አሁን የምትኖሩበትን ከተማ/ፖስታ ኮድ ያስገቡ።",
            )
        )

# =========================================================
# Page 8 – Immigration Guides
# =========================================================

elif page_code == "guides":
    st.subheader(tr("📚 Immigration & Settlement Guides", "📚 የመግቢያ እና የመቀመጫ መመሪያዎች"))

    if not guides:
        st.error("No guide data available. Please check `data/immigration_guides.json`.")
    else:
        topics = [g.get("topic") for g in guides]
        topic_choice = st.selectbox(tr("Select a topic", "ርዕስ ይምረጡ"), topics)

        guide = get_guide_by_topic(topic_choice)

        if guide:
            title = translate_dynamic(guide, "topic")
            summary = translate_dynamic(guide, "summary")

            st.markdown(f"## {title}")
            st.write(summary)

            steps = guide.get("steps", [])
            if steps:
                st.markdown(tr("### Key steps", "### ዋና እርምጃዎች"))
                for i, s in enumerate(steps, start=1):
                    st.markdown(f"{i}. {s}")

            links = guide.get("links", [])
            if links:
                st.markdown(tr("### Helpful links", "### ጠቃሚ አገናኞች"))
                for link in links:
                    label = link.get("label", "Link")
                    url = link.get("url", "#")
                    st.markdown(f"- [{label}]({url})")

            st.caption(
                tr(
                    "Always verify with official Government of Canada / provincial websites, especially for legal deadlines, forms, and required documents.",
                    "ሕጋዊ ጊዜ ገደቦች፣ ቅጾች እና የሚያስፈልጉ ሰነዶችን ሲመለከቱ ሁልጊዜ ከመንግስት የካናዳ / የክልል ድህረገፆች ጋር ያረጋግጡ።",
                )
            )

# =========================================================
# Page 9 – About
# =========================================================

elif page_code == "about":
    st.subheader(tr("ℹ️ About MyCanada – Newcomer AI Assistant", "ℹ️ ስለ MyCanada – ለአዲስ መጡ የኤይአይ አጋዥ"))

    if lang_code == "am":
        st.markdown(
            """
            ይህ መተግበሪያ ለካናዳ አዲስ መጡ ሰዎች ቀላል እና ተስፋ አሰጣጭ መመሪያ ለመሆን ተዘጋጀ።  

            - ስለ **መግቢያ መረጃ** (study permit, PR, work permit)  
            - ስለ **ከተሞችና ክልሎች** አማራጮች  
            - ስለ **ባንክ፣ ቤት፣ ስራ፣ መሰገና ቤትና ባህላዊ እርዳታ**  
            - ስለ መጀመሪያ እርምጃዎች ቀላል መመሪያዎች  

            እውነተኛ ህጋዊ ወይም የመግቢያ ምክር አይተካም። ሁልጊዜ መረጃውን ከመንግስት የካናዳ / IRCC ድህረገፆች ጋር ያረጋግጡ።
            """
        )
    else:
        st.markdown(
            """
            This starter app is designed as a **lightweight, extensible Streamlit dashboard**
            to support newcomers in understanding:

            - Basic **immigration FAQs** (study permits, PR, work permits)
            - **City & province options** across Canada
            - **Banking, housing, jobs, worship, and cultural supports**
            - Practical **first-steps guides** for arrival and settlement

            ### How you can extend this

            - Plug in richer FAQ content from official newcomer services
            - Add more structured data for neighbourhoods, rents, and transit
            - Integrate external LLMs (OpenAI, etc.) via `st.secrets` for smarter answers
            - Use real APIs (e.g., job boards, housing platforms, map services) instead of search links
            - Localize content in French, Amharic, Arabic, etc.

            ### Disclaimer

            This tool is for **information and orientation only**.  
            It does **not** provide legal, immigration, or financial advice.
            """
        )

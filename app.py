import json
from pathlib import Path
from difflib import SequenceMatcher  # needed for best_faq_match
import streamlit as st

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


# =========================================================
# Streamlit UI – theming & layout
# =========================================================

# ---------- Custom CSS (warm orange + calm blue, soft background) ----------
st.markdown(
    """
    <style>
    html, body, [class*="css"] {
        font-family: "Segoe UI", -apple-system, BlinkMacSystemFont, "Roboto", sans-serif;
    }

    .stApp {
        background: radial-gradient(circle at 0% 0%, #0f172a 0%, #020617 40%, #020617 100%);
    }

    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        background: linear-gradient(145deg, #fef9c3 0%, #fffbeb 30%, #ecfdf5 65%, #e5f4ff 100%);
        border-radius: 24px;
        box-shadow: 0 22px 60px rgba(15, 23, 42, 0.6);
        margin-top: 1.2rem;
        margin-bottom: 2rem;
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
        font-size: 2.1rem;
        letter-spacing: 0.03em;
    }
    .mc-hero p {
        margin-top: 0;
        font-size: 0.98rem;
        opacity: 0.96;
    }

    /* Small pill tags */
    .mc-pill {
        display: inline-block;
        padding: 0.08rem 0.7rem;
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 600;
        background-color: rgba(15, 23, 42, 0.18);
        margin: 0 0.15rem;
    }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0b1220 0%, #020617 60%, #111827 100%) !important;
        color: #f9fafb !important;
    }
    [data-testid="stSidebar"] * {
        color: #e5e7eb !important;
        font-size: 0.9rem;
    }
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: #facc15 !important;
    }

    /* Make radio & checkbox labels readable against dark sidebar */
    [data-testid="stSidebar"] label {
        color: #e5e7eb !important;
    }

    /* Cards */
    .mc-card {
        background-color: rgba(255, 255, 255, 0.85);
        border-radius: 18px;
        padding: 1rem 1.2rem;
        box-shadow: 0 10px 30px rgba(15, 23, 42, 0.18);
        margin-bottom: 0.9rem;
    }

    .mc-muted {
        color: #4b5563;
        font-size: 0.82rem;
    }

    .mc-chip {
        display: inline-flex;
        align-items: center;
        padding: 0.15rem 0.6rem;
        border-radius: 999px;
        background-color: #fee2e2;
        color: #b91c1c;
        font-size: 0.75rem;
        font-weight: 600;
        margin-right: 0.3rem;
        margin-bottom: 0.2rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# Header / Hero
# =========================================================

st.markdown(
    """
    <div class="mc-hero">
        <h1>MyCanada – Newcomer AI Assistant 🍁</h1>
        <p>Zalates Analytics – AI Data-Cleaning, Integration & Insight Dashboard for newcomers.<br>
        Unify messy information, reduce confusion, and explore warm fall-coloured dashboards 
        for immigration, settlement, and city choices.</p>
        <div style="margin-top:0.4rem;">
            <span class="mc-pill">Immigration basics</span>
            <span class="mc-pill">City & province explorer</span>
            <span class="mc-pill">First weeks in Canada</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.caption(
    "⚠️ This assistant is for general information only. It does **not** replace legal or immigration advice. "
    "Always verify details on official Government of Canada / IRCC websites."
)

# =========================================================
# Sidebar – Data inputs & navigation
# =========================================================

st.sidebar.title("MyCanada Controls")

st.sidebar.subheader("Mode")
page = st.sidebar.radio(
    "Choose what you want to explore:",
    [
        "🤖 Ask the Newcomer Assistant",
        "🏙️ Explore Cities & Provinces",
        "📚 Immigration Guides",
        "ℹ️ About this App",
    ],
)

st.sidebar.markdown("---")
st.sidebar.subheader("Quick filters (optional)")

preferred_region = st.sidebar.multiselect(
    "Preferred region(s) in Canada",
    options=["Atlantic", "Central", "Prairies", "West Coast", "North"],
    help="Used as soft filters when browsing cities.",
)

family_friendly = st.sidebar.checkbox(
    "Show cities with strong family/newcomer support",
    value=False,
)

st.sidebar.markdown("---")
st.sidebar.caption(
    "Built with ❤️ by Zalates Analytics as a learning & onboarding assistant for newcomers."
)

# =========================================================
# Page 1 – Ask the assistant (FAQ-style QA)
# =========================================================

if page == "🤖 Ask the Newcomer Assistant":
    st.subheader("Ask the Newcomer Assistant")

    col_q, col_info = st.columns([2, 1.2])

    with col_q:
        user_question = st.text_input(
            "Type your question about coming to or settling in Canada:",
            placeholder="e.g., How do I apply for a study permit? Do I need a job offer for Express Entry?",
        )
        ask = st.button("Ask MyCanada Assistant")

    with col_info:
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

        st.markdown("### 🗣️ Your question")
        st.write(user_question)

        st.markdown("### 🤖 Assistant answer")
        if faq:
            st.write(faq.get("answer", ""))
            if faq.get("tags"):
                st.markdown(
                    " ".join(f'<span class="mc-chip">{t}</span>' for t in faq["tags"]),
                    unsafe_allow_html=True,
                )
        else:
            st.warning(
                "I could not find a close match in my current FAQ data. "
                "Try rephrasing your question or selecting a guide on the **Immigration Guides** page."
            )

        st.markdown("### 🔍 Closest matched FAQ (for transparency)")
        if faq:
            with st.expander("Show matched FAQ"):
                st.write(f"**Matched question (similarity: {score:.2f})**")
                st.write(faq.get("question", ""))


# =========================================================
# Page 2 – City & Province explorer
# =========================================================

elif page == "🏙️ Explore Cities & Provinces":
    st.subheader("🏙️ Explore Cities & Provinces")

    if not cities:
        st.error("No city data available. Please check `data/cities.json`.")
    else:
        provinces = list_provinces()
        col_filters, col_cards = st.columns([1.2, 2.3])

        with col_filters:
            province_choice = st.selectbox(
                "Select a province or territory",
                options=["(all)"] + provinces,
            )

            settlement_focus = st.multiselect(
                "What matters most to you?",
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
                f"Showing **{len(filtered)}** city(ies) that match your filters."
            )

            if not filtered:
                st.info("Try removing some filters to see more cities.")
            else:
                for city in filtered:
                    name = city.get("name")
                    prov = city.get("province")
                    region_label = city.get("region_label", "")
                    summary = city.get("summary", "")
                    newcomers = city.get("newcomer_support", "")
                    key_sectors = city.get("key_sectors", [])
                    cost_level = city.get("cost_of_living", "Unknown")
                    transit = city.get("transit", "Unknown")

                    st.markdown(
                        f"""
                        <div class="mc-card">
                            <h3 style="margin-bottom:0.1rem;">{name}, {prov}</h3>
                            <p class="mc-muted" style="margin-top:0.1rem;">{region_label}</p>
                            <p style="margin-top:0.4rem;">{summary}</p>
                            <p><strong>Newcomer services:</strong> {newcomers}</p>
                            <p>
                                <strong>Cost of living:</strong> {cost_level} &nbsp; • &nbsp;
                                <strong>Transit:</strong> {transit}
                            </p>
                            <p>
                                {"".join(f'<span class="mc-pill">{sec}</span>' for sec in key_sectors)}
                            </p>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

# =========================================================
# Page 3 – Immigration Guides
# =========================================================

elif page == "📚 Immigration Guides":
    st.subheader("📚 Immigration & Settlement Guides")

    if not guides:
        st.error("No guide data available. Please check `data/immigration_guides.json`.")
    else:
        topics = [g.get("topic") for g in guides]
        topic_choice = st.selectbox("Select a topic", topics)

        guide = get_guide_by_topic(topic_choice)

        if guide:
            st.markdown(f"## {guide.get('topic')}")
            st.write(guide.get("summary", ""))

            steps = guide.get("steps", [])
            if steps:
                st.markdown("### Key steps")
                for i, s in enumerate(steps, start=1):
                    st.markdown(f"{i}. {s}")

            links = guide.get("links", [])
            if links:
                st.markdown("### Helpful links")
                for link in links:
                    label = link.get("label", "Link")
                    url = link.get("url", "#")
                    st.markdown(f"- [{label}]({url})")

            st.caption(
                "Always verify with official Government of Canada / provincial websites, "
                "especially for legal deadlines, forms, and required documents."
            )

# =========================================================
# Page 4 – About
# =========================================================

elif page == "ℹ️ About this App":
    st.subheader("ℹ️ About MyCanada – Newcomer AI Assistant")

    st.markdown(
        """
        This starter app is designed as a **lightweight, extensible Streamlit dashboard**
        to support newcomers in understanding:

        - Basic **immigration FAQs** (study permits, PR, work permits)
        - **City & province options** across Canada
        - Practical **first-steps guides** for arrival and settlement

        ### How you can extend this

        - Plug in richer FAQ content from official newcomer services
        - Add more cities, regions, and filters (e.g., rent levels, industry clusters)
        - Integrate external LLMs (OpenAI, etc.) via `st.secrets` for smarter answers
        - Localize content in French, Amharic, Arabic, etc.

        ### Disclaimer

        This tool is for **information and orientation only**.  
        It does **not** provide legal, immigration, or financial advice.
        """
    )

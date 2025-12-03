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
# Translation system
# =========================================================

TRANSLATIONS = {
    "fr": {
        # Sidebar & navigation
        "MyCanada Controls": "Contrôles MyCanada",
        "Language / ቋንቋ / Langue": "Langue / ቋንቋ / Language",
        "Choose what you want to explore:":
            "Choisissez ce que vous souhaitez explorer :",
        "Quick filters (optional)": "Filtres rapides (optionnel)",
        "Preferred region(s) in Canada":
            "Région(s) préférée(s) au Canada",
        "Used as soft filters when browsing cities.":
            "Utilisé comme filtre souple lors de l’exploration des villes.",
        "Show cities with strong family/newcomer support":
            "Afficher les villes avec un fort soutien aux familles et aux nouveaux arrivants",
        "Built with ❤️ by Zalates Analytics as a learning & onboarding assistant for newcomers.":
            "Créé avec ❤️ par Zalates Analytics comme assistant d’apprentissage et d’accueil pour les nouveaux arrivants.",

        # Page labels
        "🤖 Ask the Newcomer Assistant": "🤖 Poser une question à l’assistant",
        "🏙️ Explore Cities & Provinces": "🏙️ Explorer les villes et provinces",
        "📚 Immigration Guides": "📚 Guides d’immigration",
        "ℹ️ About this App": "ℹ️ À propos de cette application",

        # Hero
        "MyCanada – Newcomer AI Assistant 🍁":
            "MyCanada – Assistant IA pour nouveaux arrivants 🍁",
        "Zalates Analytics – AI Data-Cleaning, Integration & Insight Dashboard for newcomers.":
            "Zalates Analytics – Tableau de bord IA pour le nettoyage, l’intégration et l’analyse des données des nouveaux arrivants.",
        "Unify messy information, reduce confusion, and explore warm fall-coloured dashboards for immigration, settlement, and city choices.":
            "Unifiez des informations dispersées, réduisez la confusion et explorez des tableaux de bord chaleureux pour l’immigration, l’installation et le choix de ville.",
        "Immigration basics": "Notions de base sur l’immigration",
        "City & province explorer": "Explorateur de villes et provinces",
        "First weeks in Canada": "Premières semaines au Canada",
        "This assistant is for general information only. It does **not** replace legal or immigration advice. Always verify details on official Government of Canada / IRCC websites.":
            "Cet assistant fournit des informations générales uniquement. Il ne remplace **pas** les conseils juridiques ou d’immigration. Vérifiez toujours les détails sur les sites officiels du gouvernement du Canada / IRCC.",

        # Ask page
        "Ask the Newcomer Assistant": "Poser une question à l’assistant",
        "Type your question about coming to or settling in Canada:":
            "Écrivez votre question sur la venue ou l’installation au Canada :",
        "e.g., How do I apply for a study permit? Do I need a job offer for Express Entry?":
            "par ex. Comment demander un permis d’études ? Ai-je besoin d’une offre d’emploi pour Entrée express ?",
        "Ask MyCanada Assistant": "Interroger l’assistant MyCanada",
        "Tips for better answers": "Conseils pour de meilleures réponses",
        "Ask one main question at a time.": "Posez une seule question principale à la fois.",
        "Mention if you are a student, worker, or refugee claimant.":
            "Précisez si vous êtes étudiant, travailleur ou demandeur d’asile.",
        "Always double-check details on official IRCC sites.":
            "Vérifiez toujours les détails sur les sites officiels d’IRCC.",
        "🗣️ Your question": "🗣️ Votre question",
        "🤖 Assistant answer": "🤖 Réponse de l’assistant",
        "I could not find a close match in my current FAQ data. Try rephrasing your question or selecting a guide on the **Immigration Guides** page.":
            "Je n’ai pas trouvé de question similaire dans les FAQ actuelles. Essayez de reformuler votre question ou de choisir un guide dans la page **Guides d’immigration**.",
        "🔍 Closest matched FAQ (for transparency)":
            "🔍 Question la plus proche (pour transparence)",
        "Show matched FAQ": "Afficher la FAQ correspondante",

        # Cities page
        "🏙️ Explore Cities & Provinces": "🏙️ Explorer les villes et provinces",
        "No city data available. Please check `data/cities.json`.":
            "Aucune donnée de ville disponible. Veuillez vérifier `data/cities.json`.",
        "Select a province or territory": "Sélectionnez une province ou un territoire",
        "What matters most to you?": "Qu’est-ce qui compte le plus pour vous ?",
        "Affordability": "Coût de la vie",
        "Jobs & economy": "Emplois et économie",
        "Public transit": "Transport en commun",
        "Student life": "Vie étudiante",
        "Immigrant services": "Services aux immigrants",
        "Family & schools": "Famille et écoles",
        "Showing **{n}** city(ies) that match your filters.":
            "Affichage de **{n}** ville(s) correspondant à vos filtres.",
        "Try removing some filters to see more cities.":
            "Essayez de retirer certains filtres pour voir plus de villes.",
        "Newcomer services:": "Services pour nouveaux arrivants :",
        "Cost of living:": "Coût de la vie :",
        "Transit:": "Transport :",

        # Immigration guides page
        "📚 Immigration & Settlement Guides":
            "📚 Guides d’immigration et d’installation",
        "No guide data available. Please check `data/immigration_guides.json`.":
            "Aucune donnée de guide disponible. Veuillez vérifier `data/immigration_guides.json`.",
        "Select a topic": "Sélectionnez un sujet",
        "Key steps": "Étapes clés",
        "Helpful links": "Liens utiles",
        "Always verify with official Government of Canada / provincial websites, especially for legal deadlines, forms, and required documents.":
            "Vérifiez toujours avec les sites officiels du gouvernement du Canada / des provinces, surtout pour les délais légaux, formulaires et documents requis.",

        # About page
        "ℹ️ About MyCanada – Newcomer AI Assistant":
            "ℹ️ À propos de MyCanada – Assistant IA pour nouveaux arrivants",
    },
    "am": {
        # You/they can expand these Amharic translations later.
        "MyCanada Controls": "MyCanada መቆጣጠሪያዎች",
        "Language / ቋንቋ / Langue": "ቋንቋ / Language / Langue",
        "🤖 Ask the Newcomer Assistant": "🤖 ከአዲስ መጡ አጋዥ ጠይቅ",
        "🏙️ Explore Cities & Provinces": "🏙️ ከተሞችን እና ክፍለ አካባቢዎችን አስሱ",
        "📚 Immigration Guides": "📚 የመግቢያ መመሪያዎች",
        "ℹ️ About this App": "ℹ️ ስለዚህ መተግበሪያ",
        "Ask the Newcomer Assistant": "ከአዲስ መጡ አጋዥ ጠይቅ",
    },
}

LANGUAGE_OPTIONS = {
    "English": "en",
    "Français": "fr",
    "Amharic": "am",
}


def t(text: str) -> str:
    """
    Simple translation helper.
    Looks up the string in TRANSLATIONS based on st.session_state["lang"].
    Falls back to the original text if no translation is found.
    """
    lang = st.session_state.get("lang", "en")
    if lang == "en":
        return text
    return TRANSLATIONS.get(lang, {}).get(text, text)


# =========================================================
# Streamlit UI – theming & layout
# =========================================================

# ---------- Custom CSS: improved contrast, font size, alignment ----------
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

    /* Improve general text readability */
    h2, h3, h4 {
        letter-spacing: 0.01em;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# Sidebar – Language + Data inputs & navigation
# =========================================================

# Language selector (applies across app)
with st.sidebar:
    lang_label = st.selectbox(
        "Language / ቋንቋ / Langue",
        list(LANGUAGE_OPTIONS.keys()),
        index=0,
    )
st.session_state["lang"] = LANGUAGE_OPTIONS[lang_label]

st.sidebar.title(t("MyCanada Controls"))

st.sidebar.subheader(t("Mode"))

# Page keys for internal logic
PAGE_CONFIG = {
    "ask": {"label": "🤖 Ask the Newcomer Assistant"},
    "cities": {"label": "🏙️ Explore Cities & Provinces"},
    "guides": {"label": "📚 Immigration Guides"},
    "about": {"label": "ℹ️ About this App"},
}

page_key = st.sidebar.radio(
    t("Choose what you want to explore:"),
    options=list(PAGE_CONFIG.keys()),
    format_func=lambda key: t(PAGE_CONFIG[key]["label"]),
)

st.sidebar.markdown("---")
st.sidebar.subheader(t("Quick filters (optional)"))

REGION_OPTIONS = ["Atlantic", "Central", "Prairies", "West Coast", "North"]

preferred_region = st.sidebar.multiselect(
    t("Preferred region(s) in Canada"),
    options=REGION_OPTIONS,
    format_func=lambda opt: t(opt),
    help=t("Used as soft filters when browsing cities."),
)

family_friendly = st.sidebar.checkbox(
    t("Show cities with strong family/newcomer support"),
    value=False,
)

st.sidebar.markdown("---")
st.sidebar.caption(
    t(
        "Built with ❤️ by Zalates Analytics as a learning & onboarding assistant for newcomers."
    )
)

# =========================================================
# Header / Hero
# =========================================================

st.markdown(
    f"""
    <div class="mc-hero">
        <h1>{t("MyCanada – Newcomer AI Assistant 🍁")}</h1>
        <p>{t("Zalates Analytics – AI Data-Cleaning, Integration & Insight Dashboard for newcomers.")}<br>
        {t("Unify messy information, reduce confusion, and explore warm fall-coloured dashboards for immigration, settlement, and city choices.")}</p>
        <div style="margin-top:0.4rem;">
            <span class="mc-pill">{t("Immigration basics")}</span>
            <span class="mc-pill">{t("City & province explorer")}</span>
            <span class="mc-pill">{t("First weeks in Canada")}</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.caption(
    t(
        "This assistant is for general information only. It does **not** replace legal or immigration advice. "
        "Always verify details on official Government of Canada / IRCC websites."
    )
)

# =========================================================
# Helper functions (dynamic translation support)
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


def translate_dynamic(item: dict, base_key: str) -> str:
    """
    For content coming from JSON, try language-specific keys like
    'summary_fr' or 'summary_am'. Fallback to base_key.
    """
    lang = st.session_state.get("lang", "en")
    if lang == "en":
        return item.get(base_key, "")
    lang_key = f"{base_key}_{lang}"
    return item.get(lang_key, item.get(base_key, ""))


# =========================================================
# Page 1 – Ask the assistant (FAQ-style QA)
# =========================================================

if page_key == "ask":
    st.subheader(t("Ask the Newcomer Assistant"))

    col_q, col_info = st.columns([2, 1.2])

    with col_q:
        user_question = st.text_input(
            t("Type your question about coming to or settling in Canada:"),
            placeholder=t(
                "e.g., How do I apply for a study permit? Do I need a job offer for Express Entry?"
            ),
        )
        ask = st.button(t("Ask MyCanada Assistant"))

    with col_info:
        st.markdown(
            f"""
            <div class="mc-card">
                <strong>{t("Tips for better answers")}</strong>
                <ul style="padding-left:1.1rem;margin-top:0.4rem;">
                    <li>{t("Ask one main question at a time.")}</li>
                    <li>{t("Mention if you are a student, worker, or refugee claimant.")}</li>
                    <li>{t("Always double-check details on official IRCC sites.")}</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if ask and user_question.strip():
        faq, score = best_faq_match(user_question)

        st.markdown(f"### {t('🗣️ Your question')}")
        st.write(user_question)

        st.markdown(f"### {t('🤖 Assistant answer')}")
        if faq:
            answer = translate_dynamic(faq, "answer")
            st.write(answer)
            if faq.get("tags"):
                st.markdown(
                    " ".join(f'<span class="mc-chip">{t(tag)}</span>' for tag in faq["tags"]),
                    unsafe_allow_html=True,
                )
        else:
            st.warning(
                t(
                    "I could not find a close match in my current FAQ data. "
                    "Try rephrasing your question or selecting a guide on the **Immigration Guides** page."
                )
            )

        st.markdown(f"### {t('🔍 Closest matched FAQ (for transparency)')}")
        if faq:
            with st.expander(t("Show matched FAQ")):
                question_text = translate_dynamic(faq, "question")
                st.write(f"**{t('Matched question (similarity: {score:.2f})').format(score=score):s}**")
                st.write(question_text)


# =========================================================
# Page 2 – City & Province explorer
# =========================================================

elif page_key == "cities":
    st.subheader(t("🏙️ Explore Cities & Provinces"))

    if not cities:
        st.error(t("No city data available. Please check `data/cities.json`."))
    else:
        provinces = list_provinces()
        col_filters, col_cards = st.columns([1.2, 2.3])

        with col_filters:
            province_choice = st.selectbox(
                t("Select a province or territory"),
                options=["(all)"] + provinces,
            )

            SETTLEMENT_OPTIONS = [
                "Affordability",
                "Jobs & economy",
                "Public transit",
                "Student life",
                "Immigrant services",
                "Family & schools",
            ]
            settlement_focus = st.multiselect(
                t("What matters most to you?"),
                options=SETTLEMENT_OPTIONS,
                format_func=lambda opt: t(opt),
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

            msg = t("Showing **{n}** city(ies) that match your filters.").format(
                n=len(filtered)
            )
            st.markdown(msg)

            if not filtered:
                st.info(t("Try removing some filters to see more cities."))
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
                            <p><strong>{t("Newcomer services:")}</strong> {newcomers}</p>
                            <p>
                                <strong>{t("Cost of living:")}</strong> {cost_level} &nbsp; • &nbsp;
                                <strong>{t("Transit:")}</strong> {transit}
                            </p>
                            <p>
                                {"".join(f'<span class="mc-pill">{t(sec)}</span>' for sec in key_sectors)}
                            </p>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )


# =========================================================
# Page 3 – Immigration Guides
# =========================================================

elif page_key == "guides":
    st.subheader(t("📚 Immigration & Settlement Guides"))

    if not guides:
        st.error(t("No guide data available. Please check `data/immigration_guides.json`."))
    else:
        topics = [translate_dynamic(g, "topic") or g.get("topic") for g in guides]
        # Keep internal id as original topic
        topic_ids = [g.get("topic") for g in guides]

        topic_choice = st.selectbox(
            t("Select a topic"),
            options=topic_ids,
            format_func=lambda topic_id: translate_dynamic(
                next(g for g in guides if g.get("topic") == topic_id), "topic"
            )
            or topic_id,
        )

        guide = get_guide_by_topic(topic_choice)

        if guide:
            title = translate_dynamic(guide, "topic")
            summary = translate_dynamic(guide, "summary")

            st.markdown(f"## {title}")
            st.write(summary)

            steps = guide.get("steps", [])
            if steps:
                st.markdown(f"### {t('Key steps')}")
                for i, s in enumerate(steps, start=1):
                    # Optionally support translated step_i keys later
                    st.markdown(f"{i}. {s}")

            links = guide.get("links", [])
            if links:
                st.markdown(f"### {t('Helpful links')}")
                for link in links:
                    label = link.get("label", "Link")
                    url = link.get("url", "#")
                    st.markdown(f"- [{label}]({url})")

            st.caption(
                t(
                    "Always verify with official Government of Canada / provincial websites, "
                    "especially for legal deadlines, forms, and required documents."
                )
            )


# =========================================================
# Page 4 – About
# =========================================================

elif page_key == "about":
    st.subheader(t("ℹ️ About MyCanada – Newcomer AI Assistant"))

    # For now, About text is English-only; you can later break into smaller strings and
    # add them to TRANSLATIONS["fr"] / ["am"] if you want full translation.
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

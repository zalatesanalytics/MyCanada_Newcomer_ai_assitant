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


def generate_ai_answer(user_question: str, faq: dict | None, language: str):
    """
    Call OpenAI (if available) to generate a tailored answer as
    'MyCanada Newcomer AI Assistant'. Returns (answer, error_message).
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

    if "Amharic" in language:
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


def translate_to_amharic(text: str):
    """
    Translate English content to Amharic using OpenAI, if configured.
    Returns (translation or None, error_message or None).
    """
    client = get_openai_client()
    if client is None:
        return None, "Translation not available; AI is not configured."

    system_msg = (
        "You are a professional translator. Translate the following Canadian newcomer "
        "support content from English into clear, simple Amharic (አማርኛ). Preserve lists "
        "and structure, keep organization names and URLs in English where appropriate."
    )

    try:
        response = client.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": text},
            ],
            temperature=0.3,
        )
        translated = response.choices[0].message["content"]
        return translated, None
    except Exception as e:
        return None, f"Translation error: {e}"


def translate_section_button(section_text: str, key: str):
    """
    Render a 'Translate this page to Amharic' button and show translation if clicked.
    """
    if st.button("Translate this page to Amharic (አማርኛ)", key=key):
        with st.spinner("Translating to Amharic..."):
            translated, err = translate_to_amharic(section_text)
        if translated:
            st.markdown("#### በአማርኛ ትርጉም")
            st.write(translated)
        else:
            st.warning(err or "Translation not available.")


def improve_resume_with_ai(resume_text: str, job_title: str, city: str, extra_notes: str):
    """
    Use OpenAI to suggest an improved, Canadian-style resume summary & bullet points.
    """
    client = get_openai_client()
    if client is None:
        return None, "AI is not configured; cannot revise resume right now."

    system_msg = (
        "You are a Canadian newcomer employment coach and resume expert. "
        "Rewrite and improve the user's resume content into a Canadian-style resume. "
        "Keep it professional, concise, and tailored to the target job and city. "
        "Do not invent experience; reorganize and highlight what's already there. "
        "Return:\n"
        "- A short professional summary (2–3 sentences)\n"
        "- 6–10 bullet points of key achievements/skills\n"
        "- 3 customized suggestions for improvement (not full text)."
    )

    user_msg = (
        f"Target job in Canada: {job_title or 'Not specified'}\n"
        f"Preferred city/region: {city or 'Not specified'}\n"
        f"User notes / things to highlight: {extra_notes or 'None'}\n\n"
        f"Original resume text:\n{resume_text}\n"
    )

    try:
        response = client.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.5,
        )
        improved = response.choices[0].message["content"]
        return improved, None
    except Exception as e:
        return None, f"Resume AI error: {e}"


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
# Sidebar – Data inputs, language & navigation
# =========================================================

st.sidebar.title("MyCanada Controls")

language = st.sidebar.selectbox(
    "Language / ቋንቋ",
    ["English", "Amharic (አማርኛ)"],
)

st.sidebar.subheader("Mode")
page = st.sidebar.radio(
    "Choose what you want to explore:",
    [
        "🤖 Ask the Newcomer Assistant",
        "🏙️ Explore Cities & Provinces",
        "🏦 Open a Bank Account",
        "🏡 Housing Search",
        "💼 Employment Services",
        "🛕 Places of Worship",
        "🥘 Food & Cultural Community Support",
        "⚖️ Legal & Immigration Help",
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
# Page 1 – Ask the assistant (FAQ-style QA with AI)
# =========================================================

if page == "🤖 Ask the Newcomer Assistant":
    if "Amharic" in language:
        st.subheader("ከ MyCanada አዲስ መጣ ኤይአይ አስስታንት ጋር ጠይቅ")
        question_label = "ስለ ካናዳ መግባት ወይም መቀመጥ ጥያቄህን እዚህ ጻፍ፦"
        question_ph = "ለምሳሌ፡ የንባብ ፈቃድ እንዴት እሰራ? ለ Express Entry የሥራ ስምሪት አስፈላጊ ነው?"
        ask_label = "ከ MyCanada አስስታንት ጠይቅ"
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
        if "Amharic" in language:
            st.markdown(
                """
                <div class="mc-card">
                    <strong>ጠቃሚ መመሪያዎች</strong>
                    <ul style="padding-left:1.1rem;margin-top:0.4rem;">
                        <li>አንድ ዋና ጥያቄ ብቻ ለያይ።</li>
                        <li>ተማሪ፣ ሰራተኛ ወይም እስር የፈጠረብህ መሆንህን ይግለጹ።</li>
                        <li>ሁልጊዜ ከመንግስት የካናዳ / IRCC ድህረገፅ ጋር ያረጋግጡ።</li>
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
        ai_answer, ai_error = generate_ai_answer(user_question, faq, language)

        if "Amharic" in language:
            st.markdown("### 🗣️ ጥያቄህ")
        else:
            st.markdown("### 🗣️ Your question")
        st.write(user_question)

        if "Amharic" in language:
            st.markdown("### 🤖 መልስ ከ MyCanada አስስታንት")
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
                    "I could not find a close match in my current FAQ data. "
                    "Try rephrasing your question or selecting a guide on the **Immigration Guides** page."
                )

        # Transparency: show matched FAQ
        if faq:
            if "Amharic" in language:
                st.markdown("### 🔍 በጣም ተመሳሳይ የተገኘው FAQ")
            else:
                st.markdown("### 🔍 Closest matched FAQ (for transparency)")
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
# Page 3 – Open a Bank Account
# =========================================================

elif page == "🏦 Open a Bank Account":
    st.subheader("🏦 Open a Bank Account in Canada")

    bank_intro_text = (
        "Opening a bank account early helps you **receive your salary, pay rent, and build credit**.\n"
        "Let’s go through the key steps together."
    )
    st.markdown(bank_intro_text)

    location = st.text_input(
        "Where are you right now? (city or postal code)",
        placeholder="e.g., Toronto, ON or M5V 2T6",
    )

    bank_steps_text = """
### 1. Key steps to open a basic chequing account

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
    st.markdown(bank_steps_text)

    bank_programs_text = """
### 2. Newcomer banking programs (Big 5 banks)

Most major banks have **newcomer packages** with no-fee accounts for 6–12 months,
free international transfers, or cash bonuses. Always check the latest details on their websites.
"""
    st.markdown(bank_programs_text)

    bank_links = {
        "RBC – Newcomers to Canada": "https://www.rbc.com/newcomers",
        "TD – New to Canada Banking": "https://www.td.com/ca/en/personal-banking/solutions/new-to-canada",
        "Scotiabank – StartRight® Program": "https://www.scotiabank.com/ca/en/personal/bank/bank-accounts/newcomers.html",
        "CIBC – Newcomer Banking": "https://www.cibc.com/en/personal-banking/newcomers.html",
        "BMO – NewStart® Program": "https://www.bmo.com/main/personal/bank-accounts/newcomers-to-canada",
    }

    for label, url in bank_links.items():
        st.markdown(f"- [{label}]({url})")

    st.markdown("### 3. Find branches near you")

    if location.strip():
        st.success("Here are quick links to find branches close to you on Google Maps:")

        banks = ["RBC", "TD Bank", "Scotiabank", "CIBC", "BMO Bank of Montreal"]

        for b in banks:
            query = f"{b} near {location}"
            url = maps_search_url(query)
            st.markdown(f"- [{b} near {location}]({url})")

        st.caption(
            "Tip: When you open the map, you’ll see **distance, directions, opening hours, and phone numbers**."
        )
    else:
        st.warning("Please type your city or postal code above so I can suggest nearby branches.")

    # Translate this page to Amharic
    bank_page_text_for_translation = (
        bank_intro_text + "\n\n" + bank_steps_text + "\n\n" + bank_programs_text
    )
    translate_section_button(bank_page_text_for_translation, key="tr_bank")


# =========================================================
# Page 4 – Housing Search
# =========================================================

elif page == "🏡 Housing Search":
    st.subheader("🏡 Rental Housing for Newcomers")

    housing_intro_text = (
        "Let’s explore rental options based on your **city, budget, and type of place**."
    )
    st.markdown(housing_intro_text)

    city = st.text_input("Preferred city", placeholder="e.g., Ottawa, ON")
    budget = st.slider(
        "Approximate monthly budget (CAD)",
        min_value=500,
        max_value=4000,
        value=1800,
        step=50,
    )
    accom_type = st.selectbox(
        "Type of accommodation",
        [
            "Any",
            "Room in shared house",
            "Bachelor / studio",
            "1-bedroom apartment",
            "2-bedroom apartment",
            "Family-size house / townhouse",
        ],
    )

    housing_extra_text = ""
    if city.strip():
        st.markdown("### 1. Search rental listings (trusted platforms)")

        city_q = city.strip()
        search_phrase = f"rent {accom_type} {city_q}" if accom_type != "Any" else f"rent apartment {city_q}"

        links = {
            "Rentals.ca": google_search_url(f"site:rentals.ca {search_phrase}"),
            "Kijiji Rentals": google_search_url(f"site:kijiji.ca {search_phrase}"),
            "Facebook Marketplace": "https://www.facebook.com/marketplace/search/?query="
            + quote_plus(search_phrase),
            "PadMapper / Zumper / Others": google_search_url(f"rentals {city_q} apartments"),
        }

        for label, url in links.items():
            st.markdown(f"- [{label} – search for **{city_q}**]({url})")

        st.markdown("### 2. Neighbourhood & rent guidance (approximate)")

        low = max(400, budget - 400)
        mid_low = max(500, budget - 200)
        mid_high = budget + 200
        high = budget + 500

        housing_ranges_text = f"""
These are **very rough ranges** you might see in many Canadian cities.  
Actual prices vary a lot by city and neighbourhood:

- **Budget / shared options**: ~${low}–${mid_low} / month  
- **Typical 1-bedroom**: ~${mid_low}–${mid_high} / month  
- **Larger family units**: ~${mid_high}–${high}+ / month  

Use these numbers only as a **starting point**, and always confirm with the actual listing.
"""
        st.markdown(housing_ranges_text)

        st.markdown("### 3. Transit & commute tips")

        housing_transit_text = (
            "When checking a listing, open it in Google Maps and look for:\n"
            "- Distance to your school / workplace\n"
            "- Bus / subway / LRT lines nearby\n"
            "- Travel time during rush hour\n"
            "- Walking distance to grocery stores and pharmacies"
        )
        st.info(housing_transit_text)

        housing_extra_text = housing_ranges_text + "\n\n" + housing_transit_text
    else:
        st.warning("Please enter a city so I can tailor housing search links for you.")

    housing_page_text_for_translation = housing_intro_text + "\n\n" + housing_extra_text
    translate_section_button(housing_page_text_for_translation, key="tr_housing")


# =========================================================
# Page 5 – Employment Services (with resume upload)
# =========================================================

elif page == "💼 Employment Services":
    st.subheader("💼 Find Jobs & Employment Support")

    jobs_intro_text = (
        "Let’s search for jobs and newcomer employment services that match your goals."
    )
    st.markdown(jobs_intro_text)

    job_title = st.text_input(
        "What type of job are you looking for?",
        placeholder="e.g., Data analyst, PSW, warehouse worker, cashier",
    )
    job_city = st.text_input(
        "Preferred city or region for work",
        placeholder="e.g., Toronto, ON or Calgary, AB",
    )

    jobs_extra_text = ""
    if job_title.strip() and job_city.strip():
        q_job = job_title.strip()
        q_city = job_city.strip()

        st.markdown("### 1. Job postings on trusted Canadian platforms")

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

        st.markdown("### 2. Match & relevance (how to judge a good posting)")

        jobs_match_text = (
            "Look for:\n"
            "- Job title and duties similar to your skills\n"
            "- Required experience close to your background\n"
            "- Location and work arrangement (on-site / hybrid / remote)\n"
            "- Salary range that fits your expectations\n"
            "- Employer offering training or support for newcomers"
        )
        st.info(jobs_match_text)

        st.markdown("### 3. Newcomer employment centres near you")

        newcomer_query = f"employment services for newcomers near {q_city}"
        newcomer_url = maps_search_url(newcomer_query)

        st.markdown(
            f"- [Newcomer employment & settlement services near {q_city}]({newcomer_url})"
        )
        centres_text = (
            "These can include YMCA, COSTI, ACCES Employment, immigrant settlement agencies, "
            "and community organizations that help with resumes, networking, and interview practice."
        )
        st.caption(centres_text)

        st.markdown("### 4. Resume & interview tips (tailored to your role)")

        jobs_resume_tips_text = (
            f"For **{q_job}** roles, try to:\n"
            "- Highlight your most recent **work experience** that matches the job duties\n"
            "- Use **Canadian-style resume format** (1–2 pages, no photo, clear bullet points)\n"
            "- Add **quantified results** (e.g., 'reduced processing time by 20%') where possible\n"
            "- Practice answers to common questions such as:\n"
            "  - 'Tell me about yourself'\n"
            "  - 'Why do you want this role?'\n"
            "  - 'Tell me about a time you solved a problem at work'\n"
        )
        st.write(jobs_resume_tips_text)

        jobs_extra_text = jobs_match_text + "\n\n" + centres_text + "\n\n" + jobs_resume_tips_text
    else:
        st.warning("Please enter both a job type and a city so I can build search links for you.")

    # --- Resume upload & AI revision ---
    st.markdown("### 5. Upload your resume for AI review (beta)")

    st.caption(
        "Upload a simple **text version (.txt)** of your resume. "
        "The assistant will suggest a Canadian-style summary and key bullet points."
    )

    uploaded_resume = st.file_uploader(
        "Upload your resume file (.txt)",
        type=["txt"],
    )
    target_job_title = st.text_input(
        "Target job title in Canada (for tailoring)",
        value=job_title or "",
    )
    target_job_city = st.text_input(
        "City/region where you want to work (for tailoring)",
        value=job_city or "",
    )
    resume_notes = st.text_area(
        "Anything special you want to highlight? (e.g., gaps, volunteering, language skills)",
        placeholder="Optional but helpful context for tailoring your resume...",
    )

    if st.button("Generate improved resume suggestions", key="resume_ai_button"):
        if uploaded_resume is None:
            st.warning("Please upload a .txt resume file first.")
        else:
            raw_bytes = uploaded_resume.read()
            try:
                resume_text = raw_bytes.decode("utf-8", errors="ignore")
            except Exception:
                resume_text = str(raw_bytes)

            with st.spinner("Reviewing your resume with AI..."):
                improved_resume, resume_err = improve_resume_with_ai(
                    resume_text, target_job_title, target_job_city, resume_notes
                )

            if improved_resume:
                st.markdown("#### AI-powered resume suggestions")
                st.write(improved_resume)
                st.caption(
                    "These are **suggestions only**. Always review and edit your resume yourself "
                    "before applying to jobs."
                )
            else:
                st.warning(resume_err or "Something went wrong while revising your resume.")

    # Translate jobs page text to Amharic
    jobs_page_text_for_translation = jobs_intro_text + "\n\n" + jobs_extra_text
    translate_section_button(jobs_page_text_for_translation, key="tr_jobs")


# =========================================================
# Page 6 – Places of Worship
# =========================================================

elif page == "🛕 Places of Worship":
    st.subheader("🛕 Find a Place of Worship or Spiritual Community")

    worship_type = st.selectbox(
        "What type of worship place are you looking for?",
        [
            "Christian church",
            "Muslim mosque",
            "Jewish synagogue",
            "Hindu temple",
            "Buddhist temple",
            "Sikh gurdwara",
            "Other / interfaith centre",
        ],
    )

    worship_city = st.text_input(
        "Your city or postal code",
        placeholder="e.g., Winnipeg, MB or H3Z 2Y7",
    )

    if worship_city.strip():
        label_map = {
            "Christian church": "church",
            "Muslim mosque": "mosque",
            "Jewish synagogue": "synagogue",
            "Hindu temple": "hindu temple",
            "Buddhist temple": "buddhist temple",
            "Sikh gurdwara": "gurdwara",
            "Other / interfaith centre": "spiritual centre",
        }
        place_keyword = label_map.get(worship_type, "church")
        query = f"{place_keyword} near {worship_city.strip()}"
        url = maps_search_url(query)

        st.markdown("### Nearest worship centres")

        st.markdown(
            f"- [See **{worship_type}** locations near {worship_city.strip()} on Google Maps]({url})"
        )
        st.caption(
            "On the map you’ll see **distance, service times, website links, and phone numbers** "
            "for many places of worship. You can also read reviews and see photos."
        )

        st.info(
            "If you prefer a specific language (e.g., Amharic, Arabic, Spanish), you can add it to your search "
            "query in Google Maps for more tailored results."
        )
    else:
        st.warning("Please enter your city or postal code so I can locate nearby places of worship.")

# =========================================================
# Page 7 – Food & Cultural Community Support
# =========================================================

elif page == "🥘 Food & Cultural Community Support":
    st.subheader("🥘 Find Your Food, Culture & Community")

    origin_country = st.text_input(
        "Which country or culture do you identify with most?",
        placeholder="e.g., Ethiopia, India, Philippines, Brazil",
    )
    food_city = st.text_input(
        "Where are you living now? (city or postal code)",
        placeholder="e.g., Surrey, BC or M1P 4P5",
    )

    if origin_country.strip() and food_city.strip():
        o = origin_country.strip()
        c = food_city.strip()

        st.markdown("### 1. Grocery stores with your traditional foods")

        grocery_query = f"{o} grocery store near {c}"
        grocery_url = maps_search_url(grocery_query)
        st.markdown(f"- [Stores selling **{o}** foods near {c}]({grocery_url})")

        st.markdown("### 2. Cultural associations & community groups")

        assoc_query = f"{o} community association near {c}"
        assoc_url = google_search_url(assoc_query)
        st.markdown(f"- [Cultural associations and community groups]({assoc_url})")

        st.markdown("### 3. Restaurants, cafés, and local events")

        rest_query = f"{o} restaurant near {c}"
        rest_url = maps_search_url(rest_query)
        events_query = f"{o} cultural events {c}"
        events_url = google_search_url(events_query)

        st.markdown(f"- [Restaurants & cafés serving **{o}** food near {c}]({rest_url})")
        st.markdown(f"- [Local cultural events and festivals]({events_url})")

        st.caption(
            "On these pages you'll usually find **opening hours, phone numbers, websites, and directions**. "
            "Many communities also organize language schools, youth programs, and holiday celebrations."
        )

        st.info(
            "You are not alone. Connecting with people from your culture **and** new Canadian friends can "
            "make your first months much easier and warmer."
        )
    else:
        st.warning("Please fill in both your country/culture and your current city/postal code.")

# =========================================================
# Page 8 – Legal & Immigration Help
# =========================================================

elif page == "⚖️ Legal & Immigration Help":
    st.subheader("⚖️ Legal & Immigration Help (Information Only)")

    legal_intro_text = """
Getting the right **legal and immigration advice** is important, especially for
complex situations (refugee claims, inadmissibility, appeals, removals, etc.).
This page gives you steps to find qualified help. It does **not** provide legal advice.
"""
    st.markdown(legal_intro_text)

    st.markdown("### 1. Steps to find a legal advisor")

    legal_steps_text = """
1. **Decide what help you need**  
   - General immigration questions  
   - Refugee/PR applications  
   - Detention, hearings, or appeals  

2. **Look for licensed representatives**  
   In Canada, immigration representatives must usually be:  
   - A lawyer in good standing with a **provincial/territorial law society**  
   - A licensed immigration consultant (CICC member)  
   - In some cases, a supervised law student or paralegal  

3. **Check they are authorized**  
   - Use official directories (law society, CICC, or IRCC lists)  
   - Make sure their name and license number match  

4. **Book a consultation**  
   - Ask about fees, timelines, and what they need from you  
   - Bring all documents: permits, refusal letters, emails from IRCC, etc.  

5. **Get everything in writing**  
   - Written retainer/contract, fee structure, and receipts  
   - Keep copies of all forms your representative submits on your behalf
"""
    st.markdown(legal_steps_text)

    st.markdown("### 2. Official directories & tools")

    st.markdown(
        "- [IRCC – Find out if your representative is authorized](https://www.canada.ca/en/immigration-refugees-citizenship/services/immigration-citizenship-representative/choose.html)\n"
        "- [College of Immigration and Citizenship Consultants (CICC) public register](https://college-ic.ca)\n"
        "- Provincial law societies (e.g., Law Society of Ontario, Barreau du Québec, etc.)"
    )

    st.markdown("### 3. Sample list of IRCC-style authorized representatives (demo only)")

    st.caption(
        "These are **sample records only** to show how a future database connection might look. "
        "They are not real recommendations."
    )

    sample_reps = [
        {
            "name": "Alemu Legal Services (Sample)",
            "type": "Immigration Lawyer",
            "city": "Toronto, ON",
            "contact": "info@alemu-legal-sample.ca",
            "license": "LSO-123456 (DEMO)",
        },
        {
            "name": "NewLeaf Immigration Consulting (Sample)",
            "type": "Immigration Consultant (RCIC)",
            "city": "Calgary, AB",
            "contact": "contact@newleaf-rcic-sample.ca",
            "license": "CICC-R000000 (DEMO)",
        },
        {
            "name": "Hope Refugee Law Clinic (Sample)",
            "type": "Community Legal Clinic",
            "city": "Vancouver, BC",
            "contact": "clinic@hope-refugee-sample.ca",
            "license": "Clinic ID-0001 (DEMO)",
        },
    ]

    for rep in sample_reps:
        st.markdown(
            f"""
            **{rep['name']}**  
            • Type: {rep['type']}  
            • Location: {rep['city']}  
            • Contact: {rep['contact']}  
            • License / ID: {rep['license']}
            """
        )

    st.caption(
        "In a future version, this section can be replaced with a **real database** of nearby, "
        "verified representatives filtered by your postal code."
    )

    st.markdown("### 4. Find immigration lawyers or consultants near you")

    legal_city = st.text_input(
        "Your city or postal code (to search for local lawyers/consultants)",
        placeholder="e.g., Toronto, ON or M2M 3X9",
    )

    if legal_city.strip():
        q_city = legal_city.strip()
        search_lawyer_url = google_search_url(f"immigration lawyer near {q_city}")
        search_consultant_url = google_search_url(f"immigration consultant RCIC near {q_city}")
        search_clinic_url = google_search_url(f"legal aid immigration clinic near {q_city}")

        st.markdown(f"- [Immigration lawyers near {q_city}]({search_lawyer_url})")
        st.markdown(f"- [Licensed immigration consultants (RCIC) near {q_city}]({search_consultant_url})")
        st.markdown(f"- [Community legal clinics / legal aid near {q_city}]({search_clinic_url})")

        st.info(
            "When you contact someone, ask if they offer **free or low-cost initial consultations**. "
            "If you have low income, ask about **legal aid** in your province."
        )
    else:
        st.warning("Enter your city or postal code to build local search links for legal help.")

    legal_page_text_for_translation = legal_intro_text + "\n\n" + legal_steps_text
    translate_section_button(legal_page_text_for_translation, key="tr_legal")


# =========================================================
# Page 9 – Immigration Guides
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
# Page 10 – About
# =========================================================

elif page == "ℹ️ About this App":
    st.subheader("ℹ️ About MyCanada – Newcomer AI Assistant")

    st.markdown(
        """
        This starter app is designed as a **lightweight, extensible Streamlit dashboard**
        to support newcomers in understanding:

        - Basic **immigration FAQs** (study permits, PR, work permits)
        - **City & province options** across Canada
        - **Banking, housing, jobs, worship, and cultural supports**
        - Practical **first-steps guides** for arrival and settlement

        It also includes early **AI-powered features** like:
        - Tailored Q&A responses using an LLM (if configured)
        - Resume review suggestions for Canadian-style applications
        - Page-level translation to Amharic (አማርኛ) for key sections

        ### How you can extend this

        - Plug in richer FAQ content from official newcomer services
        - Add more structured data for neighbourhoods, rents, and transit
        - Integrate external LLMs (OpenAI, etc.) via `st.secrets` for smarter answers
        - Use real APIs (e.g., job boards, housing platforms, map services) instead of search links
        - Connect a **real database of IRCC-authorized representatives** for the legal help page
        - Localize content in French, Amharic, Arabic, etc.

        ### Disclaimer

        This tool is for **information and orientation only**.  
        It does **not** provide legal, immigration, or financial advice.
        """
    )

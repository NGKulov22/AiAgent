"""
app.py
------
FilmBot — Streamlit интерфейс за Weaviate Query Agent + Personalization Agent.
Стартирай с: streamlit run app.py
"""

import streamlit as st
import weaviate

from config import (
    WEAVIATE_URL, WEAVIATE_API_KEY, OPENAI_API_KEY,
    MOVIES_COLLECTION, GENRES_COLLECTION, DEMO_QUERIES,
)
from agent import get_client, get_query_agent, ask, reset_agent_context, get_collection_stats
from agent import FilmPersonalization
from data_loader import setup_all


st.set_page_config(
    page_title="FilmBot",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.stChatMessage { border-radius: 12px; }
.metric-container { background: #f8f9fa; border-radius: 8px; padding: 12px; margin-bottom: 8px; }
.rec-card { background: #f0f4ff; border-radius: 10px; padding: 12px; margin-bottom: 10px; border-left: 3px solid #4f8ef7; }
</style>
""", unsafe_allow_html=True)


@st.cache_resource(show_spinner="Свързване към Weaviate Cloud...")
def init_client():
    """Инициализира Weaviate клиента (кешира се за сесията)."""
    if not WEAVIATE_URL or not WEAVIATE_API_KEY:
        return None
    try:
        client = get_client()
        return client
    except Exception as e:
        st.error(f"Грешка при свързване: {e}")
        return None


def ensure_data_loaded(client):
    """Зарежда данните ако колекциите са празни."""
    stats = get_collection_stats(client)
    if stats.get(MOVIES_COLLECTION, 0) == 0 or stats.get(GENRES_COLLECTION, 0) == 0:
        with st.spinner("Зареждане на данните в Weaviate..."):
            setup_all(client)


def init_session_state(client):
    """Инициализира session state при първо зареждане."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "query_agent" not in st.session_state:
        st.session_state.query_agent = get_query_agent(client)
    if "last_response" not in st.session_state:
        st.session_state.last_response = None
    if "persona_id" not in st.session_state:
        st.session_state.persona_id = None
    if "persona_name" not in st.session_state:
        st.session_state.persona_name = None
    if "personalization" not in st.session_state:
        st.session_state.personalization = FilmPersonalization(client)
    if "recommendations" not in st.session_state:
        st.session_state.recommendations = []


def render_sidebar(client):
    """Рендира страничния панел."""
    with st.sidebar:
        st.title("🎬 FilmBot")
        st.caption("Интелигентен асистент за филми")

        st.divider()

        st.subheader("Колекции в Weaviate")
        stats = get_collection_stats(client)
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Филми", stats.get(MOVIES_COLLECTION, 0))
        with col2:
            st.metric("Жанрове", stats.get(GENRES_COLLECTION, 0))

        st.caption(f"Клъстер: `{WEAVIATE_URL[:30]}...`" if WEAVIATE_URL else "Не е свързан")

        st.divider()

        st.subheader("Бързи заявки")
        for i, query in enumerate(DEMO_QUERIES):
            short = query[:45] + "..." if len(query) > 45 else query
            if st.button(short, key=f"demo_{i}", use_container_width=True):
                st.session_state.pending_query = query

        st.divider()

        if st.button("Нов разговор", use_container_width=True, type="secondary"):
            st.session_state.messages = []
            st.session_state.last_response = None
            st.session_state.query_agent = reset_agent_context(client)
            st.rerun()

        st.divider()

        render_personalization_sidebar(client)


def render_personalization_sidebar(client):
    """Рендира секцията за персонализация."""
    st.subheader("Персонализация")

    if st.session_state.persona_id is None:
        with st.expander("Създай профил"):
            p_name = st.text_input("Твоето име", placeholder="Иван")
            genres_all = ["Drama", "Sci-Fi", "Crime", "Action", "Thriller",
                          "Animation", "Horror", "Comedy", "Romance", "War", "Western", "Fantasy"]
            p_genres = st.multiselect("Любими жанрове", genres_all, default=["Drama", "Sci-Fi"])
            p_decade = st.selectbox("Предпочитано десетилетие", ["1990s", "2000s", "2010s", "2020s"])

            if st.button("Създай профил", type="primary"):
                if p_name and p_genres:
                    with st.spinner("Създаване на профил..."):
                        try:
                            pid = st.session_state.personalization.get_or_create_persona(
                                p_name, p_genres, p_decade
                            )
                            st.session_state.persona_id = pid
                            st.session_state.persona_name = p_name

                            seed_movies = {
                                "Drama": "The Shawshank Redemption",
                                "Sci-Fi": "Inception",
                                "Crime": "The Godfather",
                                "Action": "The Dark Knight",
                                "Thriller": "Parasite",
                                "Animation": "Spirited Away",
                                "Horror": "Get Out",
                                "Comedy": "The Truman Show",
                                "Romance": "Amélie",
                                "War": "1917",
                            }
                            for genre in p_genres[:3]:
                                if genre in seed_movies:
                                    st.session_state.personalization.add_interaction(
                                        pid, seed_movies[genre], weight=0.9
                                    )

                            st.session_state.recommendations = (
                                st.session_state.personalization.get_recommendations(pid, limit=5)
                            )
                            st.success(f"Профилът на {p_name} е създаден!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Грешка: {e}")
    else:
        st.success(f"Активен профил: **{st.session_state.persona_name}**")

        if st.session_state.recommendations:
            st.caption("Препоръчано за теб:")
            for rec in st.session_state.recommendations:
                with st.container():
                    st.markdown(f"""
<div class="rec-card">
<strong>{rec['title']}</strong> ({rec['year']})<br>
<small>⭐ {rec['rating']} · {rec['genre']}</small>
</div>
""", unsafe_allow_html=True)

        if st.button("Обнови препоръките"):
            with st.spinner("Обновяване..."):
                st.session_state.recommendations = (
                    st.session_state.personalization.get_recommendations(
                        st.session_state.persona_id, limit=5
                    )
                )
            st.rerun()

        if st.button("Изтрий профил", type="secondary"):
            st.session_state.persona_id = None
            st.session_state.persona_name = None
            st.session_state.recommendations = []
            st.rerun()


def render_chat():
    """Рендира основния чат интерфейс."""
    st.title("💬 FilmBot — Асистент за филми")
    st.caption("Задай въпрос на естествен език за филми, жанрове, препоръки и повече.")

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if "pending_query" in st.session_state:
        query = st.session_state.pop("pending_query")
        process_query(query)

    if prompt := st.chat_input("Въведи въпрос... (напр. 'Покажи ми thriller от 2010-те')"):
        process_query(prompt)


def process_query(query: str):
    """Обработва потребителска заявка и показва отговора."""
    st.session_state.messages.append({"role": "user", "content": query})

    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        with st.spinner("FilmBot мисли..."):
            answer, raw_response = ask(
                st.session_state.query_agent,
                query,
                context=st.session_state.last_response,
            )

        st.markdown(answer)

        if raw_response is not None:
            st.session_state.last_response = raw_response

        if st.session_state.persona_id:
            words = query.lower().split()
            liked_keywords = ["харесвам", "обичам", "страхотен", "гледах", "гледал"]
            if any(w in words for w in liked_keywords):
                try:
                    client = init_client()
                    if client:
                        movies_col = client.collections.get(MOVIES_COLLECTION)
                        results = movies_col.query.bm25(query=query, limit=1)
                        if results.objects:
                            title = results.objects[0].properties.get("title", "")
                            st.session_state.personalization.add_interaction(
                                st.session_state.persona_id, title, weight=0.8
                            )
                except Exception:
                    pass

    st.session_state.messages.append({"role": "assistant", "content": answer})


def main():
    """Главна функция."""
    if not WEAVIATE_URL or not WEAVIATE_API_KEY or not OPENAI_API_KEY:
        st.error("""
**Конфигурационна грешка**

Липсват API ключове. Създай файл `.env` в директорията на проекта:

```
WEAVIATE_URL=https://your-cluster.weaviate.network
WEAVIATE_API_KEY=your-weaviate-api-key
OPENAI_API_KEY=your-openai-api-key
```

След това рестартирай приложението.
        """)
        st.stop()

    client = init_client()
    if client is None:
        st.error("Не може да се свърже с Weaviate Cloud. Провери URL и API ключ.")
        st.stop()

    ensure_data_loaded(client)
    init_session_state(client)
    render_sidebar(client)
    render_chat()


if __name__ == "__main__":
    main()

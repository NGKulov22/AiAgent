import os
from dotenv import load_dotenv

load_dotenv()

WEAVIATE_URL = os.getenv("WEAVIATE_URL")
WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

MOVIES_COLLECTION = "Movies"
GENRES_COLLECTION = "Genres"

FILMBOT_SYSTEM_PROMPT = """You are FilmBot, an intelligent movie assistant powered by a rich database of films and genres.
You help users discover movies, answer questions about films, recommend based on mood or preferences, 
and provide insights about cinema. Always be enthusiastic about movies and provide helpful, 
detailed answers. When listing movies, include relevant details like year, director and rating.
Respond in the same language the user writes in (Bulgarian or English)."""

DEMO_QUERIES = [
    "Покажи ми sci-fi филми с рейтинг над 8.5",
    "Кои жанрове имат най-висок среден рейтинг и какви филми от тях имаме?",
    "А от sci-fi филмите кои са режисирани от Christopher Nolan?",
    "Колко филма имаме с рейтинг над 8.0 и кои са от тях?",
    "Нещо напрегнато за гледане в петък вечер — нещо тъмно и интензивно",
]

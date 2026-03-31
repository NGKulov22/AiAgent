"""
data_loader.py
--------------
Зарежда Movies и Genres колекциите в Weaviate Cloud.
Изпълни еднократно: python data_loader.py
"""

import json
import sys
import weaviate
import weaviate.classes as wvc
from weaviate.classes.config import Property, DataType, Configure

from config import (
    WEAVIATE_URL,
    WEAVIATE_API_KEY,
    OPENAI_API_KEY,
    MOVIES_COLLECTION,
    GENRES_COLLECTION,
)


def _make_vectorizer_config():
    """Връща vectorizer config, съвместим с различни версии на клиента."""
    try:
        return Configure.Vectors.text2vec_openai()
    except AttributeError:
        return Configure.Vectorizer.text2vec_openai()


def _make_generative_config():
    """Връща generative config, съвместим с различни версии на клиента."""
    try:
        return Configure.Generative.openai()
    except Exception:
        return None


def get_client() -> weaviate.WeaviateClient:
    """Връща свързан Weaviate Cloud клиент."""
    if not WEAVIATE_URL or not WEAVIATE_API_KEY:
        print("ГРЕШКА: Липсват WEAVIATE_URL или WEAVIATE_API_KEY в .env файла.")
        sys.exit(1)

    client = weaviate.connect_to_weaviate_cloud(
        cluster_url=WEAVIATE_URL,
        auth_credentials=wvc.init.Auth.api_key(WEAVIATE_API_KEY),
        headers={"X-OpenAI-Api-Key": OPENAI_API_KEY},
    )
    print(f"Свързан към Weaviate Cloud: {WEAVIATE_URL}")
    return client


def create_movies_collection(client: weaviate.WeaviateClient) -> None:
    """Създава колекцията Movies ако не съществува."""
    if client.collections.exists(MOVIES_COLLECTION):
        print(f"Колекцията '{MOVIES_COLLECTION}' вече съществува — пропускам.")
        return

    vectorizer = _make_vectorizer_config()
    generative = _make_generative_config()

    create_kwargs = dict(
        name=MOVIES_COLLECTION,
        description="Колекция от филми и сериали с подробна информация",
        properties=[
            Property(name="title", data_type=DataType.TEXT, description="Заглавие на филма"),
            Property(name="description", data_type=DataType.TEXT, description="Описание на сюжета"),
            Property(name="year", data_type=DataType.INT, description="Година на издаване"),
            Property(name="rating", data_type=DataType.NUMBER, description="IMDb рейтинг (0-10)"),
            Property(name="director", data_type=DataType.TEXT, description="Режисьор"),
            Property(name="country", data_type=DataType.TEXT, description="Държава на производство"),
            Property(name="language", data_type=DataType.TEXT, description="Основен език"),
            Property(name="genre", data_type=DataType.TEXT, description="Жанр"),
            Property(name="duration_min", data_type=DataType.INT, description="Продължителност в минути"),
        ],
    )

    if isinstance(vectorizer, list):
        create_kwargs["vector_config"] = vectorizer
    else:
        create_kwargs["vectorizer_config"] = vectorizer

    if generative:
        create_kwargs["generative_config"] = generative

    client.collections.create(**create_kwargs)
    print(f"Колекцията '{MOVIES_COLLECTION}' създадена успешно.")


def create_genres_collection(client: weaviate.WeaviateClient) -> None:
    """Създава колекцията Genres ако не съществува."""
    if client.collections.exists(GENRES_COLLECTION):
        print(f"Колекцията '{GENRES_COLLECTION}' вече съществува — пропускам.")
        return

    vectorizer = _make_vectorizer_config()
    generative = _make_generative_config()

    create_kwargs = dict(
        name=GENRES_COLLECTION,
        description="Колекция от филмови жанрове с описания и характеристики",
        properties=[
            Property(name="name", data_type=DataType.TEXT, description="Наименование на жанра"),
            Property(name="description", data_type=DataType.TEXT, description="Описание на жанра"),
            Property(name="typical_themes", data_type=DataType.TEXT, description="Типични теми"),
            Property(name="popular_decades", data_type=DataType.TEXT, description="Популярни десетилетия"),
            Property(name="avg_rating", data_type=DataType.NUMBER, description="Среден рейтинг"),
            Property(name="mood", data_type=DataType.TEXT, description="Настроение / усещане"),
        ],
    )

    if isinstance(vectorizer, list):
        create_kwargs["vector_config"] = vectorizer
    else:
        create_kwargs["vectorizer_config"] = vectorizer

    if generative:
        create_kwargs["generative_config"] = generative

    client.collections.create(**create_kwargs)
    print(f"Колекцията '{GENRES_COLLECTION}' създадена успешно.")


def load_movies(client: weaviate.WeaviateClient) -> int:
    """Зарежда филмите от movies.json в Weaviate."""
    with open("data/movies.json", encoding="utf-8") as f:
        movies = json.load(f)

    collection = client.collections.get(MOVIES_COLLECTION)

    existing = collection.aggregate.over_all(total_count=True).total_count
    if existing and existing > 0:
        print(f"'{MOVIES_COLLECTION}' вече съдържа {existing} записа — пропускам зареждането.")
        return existing

    with collection.batch.dynamic() as batch:
        for movie in movies:
            batch.add_object(properties=movie)

    print(f"Заредени {len(movies)} филма в '{MOVIES_COLLECTION}'.")
    return len(movies)


def load_genres(client: weaviate.WeaviateClient) -> int:
    """Зарежда жанровете от genres.json в Weaviate."""
    with open("data/genres.json", encoding="utf-8") as f:
        genres = json.load(f)

    collection = client.collections.get(GENRES_COLLECTION)

    existing = collection.aggregate.over_all(total_count=True).total_count
    if existing and existing > 0:
        print(f"'{GENRES_COLLECTION}' вече съдържа {existing} записа — пропускам зареждането.")
        return existing

    with collection.batch.dynamic() as batch:
        for genre in genres:
            batch.add_object(properties=genre)

    print(f"Заредени {len(genres)} жанра в '{GENRES_COLLECTION}'.")
    return len(genres)


def verify_collections(client: weaviate.WeaviateClient) -> dict:
    """Проверява броя обекти в колекциите и връща статистика."""
    stats = {}
    for name in [MOVIES_COLLECTION, GENRES_COLLECTION]:
        if client.collections.exists(name):
            col = client.collections.get(name)
            count = col.aggregate.over_all(total_count=True).total_count
            stats[name] = count or 0
        else:
            stats[name] = 0
    return stats


def setup_all(client: weaviate.WeaviateClient) -> dict:
    """Създава колекциите и зарежда данните. Връща статистика."""
    create_movies_collection(client)
    create_genres_collection(client)
    load_movies(client)
    load_genres(client)
    stats = verify_collections(client)
    print(f"\nСтатистика: {stats}")
    return stats


if __name__ == "__main__":
    client = get_client()
    try:
        setup_all(client)
        print("\nГотово! Данните са заредени успешно.")
    except Exception as e:
        print(f"ГРЕШКА: {e}")
        raise
    finally:
        client.close()

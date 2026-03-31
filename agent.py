"""
agent.py
--------
Query Agent и Personalization Agent логика за FilmBot.
"""

import weaviate
import weaviate.classes as wvc
from weaviate.agents.query import QueryAgent
from weaviate.agents.personalization import PersonalizationAgent

from config import (
    WEAVIATE_URL,
    WEAVIATE_API_KEY,
    OPENAI_API_KEY,
    MOVIES_COLLECTION,
    GENRES_COLLECTION,
    FILMBOT_SYSTEM_PROMPT,
)


def get_client() -> weaviate.WeaviateClient:
    """Връща свързан Weaviate Cloud клиент."""
    return weaviate.connect_to_weaviate_cloud(
        cluster_url=WEAVIATE_URL,
        auth_credentials=wvc.init.Auth.api_key(WEAVIATE_API_KEY),
        headers={"X-OpenAI-Api-Key": OPENAI_API_KEY},
    )


def get_query_agent(client: weaviate.WeaviateClient) -> QueryAgent:
    """Създава и връща Query Agent конфигуриран с двете колекции.
    
    ВАЖНО: collections приема низове (имена), не Collection обекти.
    """
    agent = QueryAgent(
        client=client,
        collections=[MOVIES_COLLECTION, GENRES_COLLECTION],
        system_prompt=FILMBOT_SYSTEM_PROMPT,
    )
    return agent


def ask(agent: QueryAgent, question: str, context=None) -> tuple[str, object]:
    """
    Изпраща въпрос към Query Agent и връща (отговор, response).
    Подава context за follow-up въпроси.
    
    Returns:
        (answer_text, raw_response) — raw_response може да се подаде
        като context при следващо извикване за follow-up.
    """
    try:
        if context is not None:
            response = agent.ask(question, context=context)
        else:
            response = agent.ask(question)
        answer = response.final_answer or "Няма отговор от агента."
        return answer, response
    except Exception as e:
        return f"Грешка при заявката: {e}", None


def reset_agent_context(client: weaviate.WeaviateClient) -> QueryAgent:
    """Създава нов агент (изчиства контекста / историята)."""
    return get_query_agent(client)


def get_collection_stats(client: weaviate.WeaviateClient) -> dict:
    """Връща броя обекти в двете колекции."""
    stats = {}
    for name in [MOVIES_COLLECTION, GENRES_COLLECTION]:
        try:
            col = client.collections.get(name)
            count = col.aggregate.over_all(total_count=True).total_count
            stats[name] = count or 0
        except Exception:
            stats[name] = 0
    return stats


class FilmPersonalization:
    """
    Обвивка около PersonalizationAgent за персонализирани препоръки.
    """

    def __init__(self, client: weaviate.WeaviateClient):
        self.client = client
        self.agent = PersonalizationAgent(
            client=client,
            reference_collection=MOVIES_COLLECTION,
        )

    def create_persona(self, name: str, favorite_genres: list[str],
                       preferred_decade: str = "2000s", language: str = "English") -> str:
        """
        Създава нова персона и връща нейния ID.

        Args:
            name: Потребителско име
            favorite_genres: Списък с любими жанрове
            preferred_decade: Предпочитано десетилетие
            language: Предпочитан език на филмите

        Returns:
            persona_id (str)
        """
        persona = self.agent.create_persona(
            persona_id=name.lower().replace(" ", "_"),
            properties={
                "name": name,
                "favorite_genres": ", ".join(favorite_genres),
                "preferred_decade": preferred_decade,
                "language": language,
            },
        )
        return persona.persona_id

    def add_interaction(self, persona_id: str, movie_title: str, weight: float = 1.0) -> bool:
        """
        Записва взаимодействие (гледан/харесан филм) за персоната.

        Args:
            persona_id: ID на персоната
            movie_title: Заглавие на филма (ще се търси в колекцията)
            weight: Тежест (0.0 - 1.0), по-висока = по-харесан

        Returns:
            True при успех
        """
        try:
            movies_col = self.client.collections.get(MOVIES_COLLECTION)
            results = movies_col.query.bm25(query=movie_title, limit=1)

            if not results.objects:
                return False

            movie_uuid = str(results.objects[0].uuid)
            self.agent.add_interaction(
                persona_id=persona_id,
                item_id=movie_uuid,
                weight=weight,
            )
            return True
        except Exception as e:
            print(f"Грешка при добавяне на interaction: {e}")
            return False

    def get_recommendations(self, persona_id: str, limit: int = 5) -> list[dict]:
        """
        Връща персонализирани препоръки за дадена персона.

        Args:
            persona_id: ID на персоната
            limit: Брой препоръки

        Returns:
            Списък от речници с данни за филмите
        """
        try:
            results = self.agent.get_objects(
                persona_id=persona_id,
                limit=limit,
            )

            recommendations = []
            for obj in results.objects:
                props = obj.properties
                recommendations.append({
                    "title": props.get("title", "Unknown"),
                    "year": props.get("year", ""),
                    "rating": props.get("rating", ""),
                    "genre": props.get("genre", ""),
                    "director": props.get("director", ""),
                    "description": props.get("description", ""),
                })
            return recommendations
        except Exception as e:
            print(f"Грешка при вземане на препоръки: {e}")
            return []

    def get_or_create_persona(self, name: str, favorite_genres: list[str],
                               preferred_decade: str = "2000s") -> str:
        """Връща съществуваща персона или създава нова."""
        persona_id = name.lower().replace(" ", "_")
        try:
            self.agent.get_persona(persona_id)
            return persona_id
        except Exception:
            return self.create_persona(name, favorite_genres, preferred_decade)


if __name__ == "__main__":
    from config import DEMO_QUERIES

    client = get_client()
    try:
        print("=== FilmBot Query Agent Demo ===\n")
        agent = get_query_agent(client)

        context = None
        for i, query in enumerate(DEMO_QUERIES, 1):
            print(f"Заявка {i}: {query}")
            print("-" * 60)
            answer, context = ask(agent, query, context=context if i > 2 else None)
            print(answer)
            print()

    finally:
        client.close()

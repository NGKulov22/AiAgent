# FilmBot — Интелигентен асистент за филми с Weaviate Agents

FilmBot е AI-powered приложение, което използва **Weaviate Query Agent** за отговаряне на въпроси на естествен език върху база данни от филми, и **Personalization Agent** за персонализирани препоръки.

## Архитектура

```
filmbot/
├── app.py              # Streamlit UI (главно приложение)
├── agent.py            # Query Agent + Personalization Agent логика
├── data_loader.py      # Зареждане на данните в Weaviate Cloud
├── config.py           # Конфигурация и константи
├── requirements.txt    # Python зависимости
├── .env.example        # Шаблон за API ключове
├── .gitignore
└── data/
    ├── movies.json     # 50 филма с подробни данни
    └── genres.json     # 12 жанра с описания
```


## Инсталация

### 1. Клонирай / разархивирай проекта

```bash
cd filmbot
```

### 2. Създай виртуална среда

```bash
python -m venv venv
source venv/bin/activate      # Linux / macOS
venv\Scripts\activate         # Windows
```

### 3. Инсталирай зависимостите

```bash
pip install -r requirements.txt
```

Редактирай `.env` и попълни:

```env
WEAVIATE_URL=https://your-cluster-id.weaviate.network
WEAVIATE_API_KEY=your-weaviate-api-key
OPENAI_API_KEY=sk-your-openai-key
```

**Откъде се взимат ключовете:**
- **Weaviate:** [weaviate.io](https://weaviate.io) → Create free cluster → Details → Copy URL & API Key
- **OpenAI:** [platform.openai.com](https://platform.openai.com) → API Keys → Create new secret key

### 5. Зареди данните (еднократно)

```bash
python data_loader.py
```

### 6. Стартирай приложението

```bash
streamlit run app.py
```

Отвори браузъра на `http://localhost:8501`

## Примерни заявки

| # | Тип | Заявка |
|---|-----|--------|
| 1 | Обикновено търсене | "Покажи ми sci-fi филми с рейтинг над 8.5" |
| 2 | Multi-collection | "Кои жанрове имат най-висок среден рейтинг и какви филми от тях имаме?" |
| 3 | Follow-up | "А от sci-fi филмите кои са режисирани от Christopher Nolan?" |
| 4 | Агрегация | "Колко филма имаме с рейтинг над 8.0?" |
| 5 | Свободна | "Нещо напрегнато за гледане в петък вечер" |

## Използвани агенти

- **Query Agent** — приема естествен език, избира колекции, изпълнява заявки
- **Personalization Agent** — създава потребителски профили и дава персонализирани препоръки

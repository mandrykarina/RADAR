import json
import os
import uuid
from loads2 import insert_article, close, prepare_database, export_recent_news

def normalize_id(article):
    """Проверяет и приводит ID новости к строковому виду"""
    raw_id = article.get("id")

    # Если id отсутствует — генерируем новый
    if raw_id is None:
        new_id = uuid.uuid4().hex
        print(f"⚠️ Отсутствует id, сгенерирован новый: {new_id}")
        article["id"] = new_id
        return article

    # Если id не строка — приводим к строке
    if not isinstance(raw_id, str):
        article["id"] = str(raw_id)
        return article

    # Если id содержит пробелы или другие символы — очищаем
    article["id"] = raw_id.strip()

    # Если id пустой после очистки — генерируем новый
    if not article["id"]:
        new_id = uuid.uuid4().hex
        print(f"⚠️ Пустой id, сгенерирован новый: {new_id}")
        article["id"] = new_id

    return article


def load_all_news():
    """Загружает новости из всех файлов и добавляет их в базу"""
    file_names = [
        "finnhub.json",
        "marketaux.json",
        "newsapi.json",
        "polygon.json"
    ]

    prepare_database()

    for file_name in file_names:
        if not os.path.exists(file_name):
            print(f"Файл {file_name} не найден, пропускаем.")
            continue

        print(f"\nЗагружается файл: {file_name}")
        try:
            with open(file_name, "r", encoding="utf-8") as f:
                articles = json.load(f)

            if not isinstance(articles, list):
                print(f"⚠️ Неверный формат в {file_name} — ожидается список новостей.")
                continue

            for article in articles:
                # Проверка и исправление ID
                article = normalize_id(article)

                try:
                    insert_article(article)
                except Exception as e:
                    print(f"Ошибка при вставке новости {article.get('id')}: {e}")

        except Exception as e:
            print(f"Ошибка при чтении {file_name}: {e}")

    close()
    print("\n✅ Все доступные новости обработаны и добавлены в базу данных.")


if __name__ == "__main__":
    load_all_news()
    export_recent_news()

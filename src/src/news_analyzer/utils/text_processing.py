import re
from typing import List
from collections import Counter


class TextProcessor:
    """Утилиты для обработки текста"""

    def __init__(self):
        self.stop_words = {
            'и', 'в', 'на', 'с', 'по', 'для', 'из', 'к', 'о', 'от', 'до', 'за', 'при', 'про',
            'что', 'как', 'это', 'все', 'был', 'быть', 'или', 'не', 'но', 'же', 'так', 'уже',
            'еще', 'его', 'ее', 'их', 'них', 'том', 'под', 'над', 'при', 'без', 'через'
        }

    def extract_numbers(self, text: str) -> List[float]:
        """Извлечение числовых значений из текста"""

        patterns = [
            r'\b\d+[,.]\d+\b',  # 1.5, 2,3
            r'\b\d+\s*млрд\b',  # 5 млрд
            r'\b\d+\s*млн\b',  # 10 млн
            r'\b\d+\s*%\b',  # 15%
            r'\b\d+\.\d+\s*%\b',  # 2.5%
            r'\$\d+[,.]?\d*\b',  # $100, $1.5
            r'\b\d+\b'  # простые числа
        ]

        numbers = []
        for pattern in patterns:
            matches = re.findall(pattern, text.lower())
            for match in matches:
                try:
                    clean_num = re.sub(r'[^\d.,]', '', match).replace(',', '.')
                    if clean_num:
                        num = float(clean_num)

                        # Конвертация млрд/млн
                        if 'млрд' in match:
                            num *= 1e9
                        elif 'млн' in match:
                            num *= 1e6

                        numbers.append(num)
                except ValueError:
                    continue

        return numbers

    def extract_keywords(self, text: str, top_k: int = 10) -> List[str]:
        """Извлечение ключевых слов из текста"""

        # Очистка и токенизация
        text = text.lower()
        text = re.sub(r'[^а-яё\s]', ' ', text)
        words = text.split()

        # Фильтрация
        words = [w for w in words if w not in self.stop_words and len(w) > 2]

        # Подсчет частоты
        word_freq = Counter(words)

        return [word for word, freq in word_freq.most_common(top_k)]

    def clean_text(self, text: str) -> str:
        """Очистка текста"""

        # Удаление HTML
        text = re.sub(r'<[^>]+>', '', text)

        # Нормализация пробелов
        text = re.sub(r'\s+', ' ', text)

        return text.strip()
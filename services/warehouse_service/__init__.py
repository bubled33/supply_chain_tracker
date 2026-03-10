import numpy as np
from navec import Navec
from typing import Dict, List
import re


class MarketplaceJobMatcher:
    def __init__(self, model_path: str):
        self.navec = Navec.load(model_path)

        self.job_keywords = "ищу вакансия работа требуется нужен найму удаленка сотрудник специалист"
        self.marketplace_keywords = "вайлдберриз wildberries озон ozon маркетплейс товар продажа магазин"
        self.manager_keywords = "менеджер управляющий координатор помощник ассистент администратор"

        print(f"✅ Модель загружена для анализа вакансий")

    def get_sentence_vector(self, text: str) -> np.ndarray:
        words = re.findall(r'\w+', text.lower())
        vectors = []

        for word in words:
            if word in self.navec:
                vectors.append(self.navec[word])

        if not vectors:
            return np.zeros(300)

        return np.mean(vectors, axis=0)

    def cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return np.dot(vec1, vec2) / (norm1 * norm2)

    def analyze_message(self, message: str) -> Dict[str, any]:
        msg_vec = self.get_sentence_vector(message)

        job_vec = self.get_sentence_vector(self.job_keywords)
        marketplace_vec = self.get_sentence_vector(self.marketplace_keywords)
        manager_vec = self.get_sentence_vector(self.manager_keywords)

        job_score = self.cosine_similarity(msg_vec, job_vec)
        marketplace_score = self.cosine_similarity(msg_vec, marketplace_vec)
        manager_score = self.cosine_similarity(msg_vec, manager_vec)

        msg_lower = message.lower()

        has_wb_ozon = any(word in msg_lower for word in [
            'вб', 'wb', 'wildberries', 'вайлдберриз', 'озон', 'ozon', 'маркетплейс'
        ])

        has_job_intent = any(word in msg_lower for word in [
            'ищу', 'нужен', 'требуется', 'вакансия', 'найму', 'работа',
            'сотрудник', 'специалист', 'помощник'
        ])

        has_manager = any(word in msg_lower for word in [
            'менеджер', 'управляющ', 'координатор', 'помощник', 'ассистент'
        ])

        semantic_score = (job_score * 0.3 + marketplace_score * 0.4 + manager_score * 0.3)
        keyword_bonus = 0.0

        if has_wb_ozon:
            keyword_bonus += 0.3
        if has_job_intent:
            keyword_bonus += 0.2
        if has_manager:
            keyword_bonus += 0.2

        final_score = min(semantic_score + keyword_bonus, 1.0)

        is_job_search = final_score >= 0.35 or (has_wb_ozon and has_job_intent)

        return {
            'is_job_search': is_job_search,
            'confidence': float(final_score),
            'scores': {
                'job_intent': float(job_score),
                'marketplace': float(marketplace_score),
                'manager_role': float(manager_score)
            },
            'keywords_found': {
                'marketplace': has_wb_ozon,
                'job_intent': has_job_intent,
                'manager_role': has_manager
            }
        }

    def batch_analyze(self, messages: List[Dict]) -> List[Dict]:
        results = []

        for msg in messages:
            analysis = self.analyze_message(msg['text'])
            results.append({
                'username': msg['username'],
                'text': msg['text'],
                **analysis
            })

        return results


def simulate_telegram_messages():
    return [
        {
            'username': '@Ivan_Petrov',
            'text': 'Ищу менеджера для работы с Wildberries. Удаленка, опыт от года. Пишите в ЛС.'
        },
        {
            'username': '@Marina_Shop',
            'text': 'Требуется помощник для управления магазином на ВБ и Озон. З/п от 50к.'
        },
        {
            'username': '@Alex_B',
            'text': 'Всем привет! Как дела? Кто-нибудь был на концерте вчера?'
        },
        {
            'username': '@Seller_Pro',
            'text': 'Нужен специалист по маркетплейсам (Ozon, WB). Опыт обязателен.'
        },
        {
            'username': '@Random_User',
            'text': 'Продам iPhone 15 Pro в отличном состоянии, недорого'
        },
        {
            'username': '@Business_Owner',
            'text': 'Ищу координатора для работы с поставщиками на Wildberries. Полная занятость.'
        },
        {
            'username': '@Casual_Chat',
            'text': 'Кто знает хороший ресторан в центре? Посоветуйте плз'
        },
        {
            'username': '@HR_Manager',
            'text': 'Вакансия: менеджер маркетплейсов (Озон/ВБ). Опыт от 6 мес. Удаленно.'
        },
        {
            'username': '@Question_Guy',
            'text': 'Как настроить рекламу на Озоне? Подскажите кто знает'
        },
        {
            'username': '@Shop_Admin',
            'text': 'Срочно найму ассистента для управления товарами на WB. Оплата сдельная.'
        },
        {
            'username': '@Crypto_Fan',
            'text': 'Биткоин снова растет! Кто держит, тот молодец 🚀'
        },
        {
            'username': '@NewBusiness',
            'text': 'Нужен сотрудник для обработки заказов с маркетплейсов, можно без опыта'
        }
    ]


if __name__ == "__main__":
    matcher = MarketplaceJobMatcher('./navec_news_v1_1B_250K_300d_100q.tar')

    messages = simulate_telegram_messages()

    print("\n" + "=" * 80)
    print("🔍 АНАЛИЗ СООБЩЕНИЙ ИЗ TELEGRAM ЧАТА")
    print("=" * 80 + "\n")

    results = matcher.batch_analyze(messages)

    job_posts = []
    other_messages = []

    for result in results:
        if result['is_job_search']:
            job_posts.append(result)
        else:
            other_messages.append(result)

    print(f"✅ НАЙДЕНО ВАКАНСИЙ: {len(job_posts)}\n")

    for i, post in enumerate(job_posts, 1):
        print(f"📌 Вакансия #{i}")
        print(f"   Автор: {post['username']}")
        print(f"   Текст: {post['text']}")
        print(f"   Уверенность: {post['confidence']:.1%}")
        print(f"   Детали:")
        print(f"      - Маркетплейс упомянут: {'✓' if post['keywords_found']['marketplace'] else '✗'}")
        print(f"      - Поиск работы: {'✓' if post['keywords_found']['job_intent'] else '✗'}")
        print(f"      - Роль менеджера: {'✓' if post['keywords_found']['manager_role'] else '✗'}")
        print(f"   Оценки: работа={post['scores']['job_intent']:.2f}, "
              f"маркетплейс={post['scores']['marketplace']:.2f}, "
              f"менеджер={post['scores']['manager_role']:.2f}")
        print()

    print(f"\n❌ ОБЫЧНЫЕ СООБЩЕНИЯ (не вакансии): {len(other_messages)}\n")

    for msg in other_messages[:5]:
        print(f"   {msg['username']}: {msg['text'][:60]}...")
        print(f"   (уверенность: {msg['confidence']:.1%})")
        print()

    print("\n" + "=" * 80)
    print("📊 СТАТИСТИКА")
    print("=" * 80)
    print(f"Всего сообщений: {len(messages)}")
    print(f"Вакансий найдено: {len(job_posts)} ({len(job_posts) / len(messages) * 100:.1f}%)")
    print(f"Обычных сообщений: {len(other_messages)} ({len(other_messages) / len(messages) * 100:.1f}%)")

    avg_confidence_jobs = np.mean([p['confidence'] for p in job_posts]) if job_posts else 0
    print(f"Средняя уверенность (вакансии): {avg_confidence_jobs:.1%}")

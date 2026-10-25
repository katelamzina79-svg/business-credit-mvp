class SmartFeedService:
    """Rule-based demo tips. Text deliberately avoids claiming real benefits or offers."""

    @staticmethod
    def get_suggestions(okved: str, status: str, score: int) -> list[dict]:
        suggestions = []
        if okved == "47.11":
            suggestions.append({
                "title": "Подсказка для розничной торговли",
                "text": "Для планирования оборотного финансирования подготовьте прогноз закупок и сезонности продаж. Это демонстрационная рекомендация, не банковское предложение."
            })
        if status == "documents_required":
            suggestions.append({
                "title": "Нужны дополнительные документы",
                "text": "Проверьте список документов, который запросил банк, и подготовьте актуальные файлы для продолжения рассмотрения заявки."
            })
        if score >= 75:
            suggestions.append({
                "title": "Профиль с низким риском по демо-правилам",
                "text": "Тестовая оценка не выявила существенных факторов риска. Итоговое решение принимает банкир; это не гарантия одобрения."
            })
        elif 0 < score < 55:
            suggestions.append({
                "title": "Проверьте финансовую нагрузку",
                "text": "Сравните запрошенную сумму с выручкой и подготовьте пояснение по текущим обязательствам. Оценка основана на синтетических данных."
            })
        if status == "other_terms":
            suggestions.append({
                "title": "Предложены другие условия",
                "text": "Ознакомьтесь с предложением банка и уточните, подходит ли бизнесу новая сумма или срок."
            })
        if not suggestions:
            suggestions.append({
                "title": "Совет для заявки",
                "text": "Подготовьте актуальные сведения о выручке, долгах и цели финансирования — они помогают разобрать заявку."
            })
        return suggestions

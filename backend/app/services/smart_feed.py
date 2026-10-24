class SmartFeedService:
    @staticmethod
    def get_suggestions(okved: str, status: str, score: int) -> list[dict]:
        suggestions = []
        
        # Подсказка по ресторанному бизнесу
        if okved == "47.11":
            suggestions.append({
                "title": "⚡️ Льготы для розничной торговли",
                "text": "Для ОКВЭД 47.11 сейчас действует сниженная ставка на оборотные кредиты. Ваша заявка приоритетна."
            })
        
        # Подсказка по статусу заявки
        if status == "NEED_DOCUMENTS":
            suggestions.append({
                "title": "📂 Ускорение проверки",
                "text": "Загрузите скан Устава в формате PDF, чтобы скоринг-модель автоматически верифицировала доли учредителей."
            })
            
        # Подсказка по качеству компании
        if score > 80:
            suggestions.append({
                "title": "💎 Премиальный статус",
                "text": "Ваш кредитный балл высокий. Вам доступно снижение ставки на 1.5% при подписании договора в течение 24 часов."
            })
            
        if not suggestions:
            suggestions.append({
                "title": "💡 Совет недели",
                "text": "Поддерживайте остаток на расчетном счету выше 100 000 рублей для автоматического продления овердрафта."
            })
            
        return suggestions

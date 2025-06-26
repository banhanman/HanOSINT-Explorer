import json
import re
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler

# Конфигурация
TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
API_KEYS = {
    "numverify": "YOUR_NUMVERIFY_API_KEY",  # Получить на numverify.com
    "abstractapi": "YOUR_ABSTRACTAPI_KEY"   # Получить на abstractapi.com
}

class OSINTBot:
    def __init__(self):
        self.user_data = {}
        self.services = {
            "Основная информация": self.get_phone_info,
            "Социальные сети": self.social_media_search,
            "Утечки данных": self.breach_check,
            "Геолокация": self.geolocation_data
        }

    async def start(self, update: Update, context: CallbackContext) -> None:
        """Обработка команды /start"""
        user = update.effective_user
        await update.message.reply_text(
            f"🔍 Привет, {user.first_name}! Я OSINT-бот для анализа телефонных номеров.\n"
            "Отправь мне номер телефона в международном формате (например: +79123456789)"
        )

    async def handle_phone(self, update: Update, context: CallbackContext) -> None:
        """Обработка введенного номера телефона"""
        phone = update.message.text.strip()
        if not self.validate_phone(phone):
            await update.message.reply_text("❌ Неверный формат номера. Используй международный формат: +79123456789")
            return
        
        self.user_data[update.effective_user.id] = phone
        await self.show_services_menu(update, context, phone)

    def validate_phone(self, phone: str) -> bool:
        """Проверка формата номера"""
        pattern = r"^\+\d{11,15}$"
        return re.match(pattern, phone) is not None

    async def show_services_menu(self, update: Update, context: CallbackContext, phone: str) -> None:
        """Показать меню сервисов для проверки"""
        keyboard = [
            [InlineKeyboardButton(service, callback_data=f"service_{service}")]
            for service in self.services
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"📱 Номер: {phone}\nВыбери тип проверки:",
            reply_markup=reply_markup
        )

    async def service_handler(self, update: Update, context: CallbackContext) -> None:
        """Обработка выбора сервиса"""
        query = update.callback_query
        await query.answer()
        
        service_name = query.data.split('_')[1]
        user_id = query.from_user.id
        phone = self.user_data.get(user_id)
        
        if not phone:
            await query.edit_message_text("❌ Сессия устарела. Отправь номер снова.")
            return
        
        if service_name in self.services:
            await query.edit_message_text(f"⌛ Ищу данные через {service_name}...")
            result = await self.services[service_name](phone)
            await query.edit_message_text(result)

    async def get_phone_info(self, phone: str) -> str:
        """Получение основной информации о номере"""
        url = f"http://apilayer.net/api/validate?access_key={API_KEYS['numverify']}&number={phone}"
        try:
            response = requests.get(url, timeout=10)
            data = response.json()
            
            if not data.get("valid"):
                return "❌ Номер недействителен или не найден"
            
            return (
                "📋 Основная информация:\n"
                f"• Страна: {data.get('country_name')}\n"
                f"• Оператор: {data.get('carrier')}\n"
                f"• Тип линии: {data.get('line_type')}\n"
                f"• Локация: {data.get('location')}\n"
                f"• Код страны: {data.get('country_code')}\n"
                f"• Рабочий номер: {'Да' if data.get('valid') else 'Нет'}"
            )
        except Exception as e:
            return f"⚠️ Ошибка при получении данных: {str(e)}"

    async def social_media_search(self, phone: str) -> str:
        """Поиск в социальных сетях (симуляция)"""
        # В реальной реализации здесь будут API вызовы к специализированным сервисам
        formatted_phone = phone.replace("+", "")
        return (
            "🔍 Результаты поиска в социальных сетях:\n"
            "• ВКонтакте: https://vk.com/phone/{formatted_phone}\n"
            "• Telegram: https://t.me/{formatted_phone}\n"
            "• WhatsApp: https://wa.me/{formatted_phone}\n\n"
            "ℹ️ Это примеры ссылок. Реальные результаты могут отличаться."
        )

    async def breach_check(self, phone: str) -> str:
        """Проверка утечек данных"""
        # Используем API AbstractAPI для проверки утечек
        url = f"https://phonevalidation.abstractapi.com/v1/?api_key={API_KEYS['abstractapi']}&phone={phone}"
        try:
            response = requests.get(url, timeout=10)
            data = response.json()
            
            if data.get("security"):
                breaches = data["security"].get("breaches", [])
                if breaches:
                    return f"⚠️ Номер найден в {len(breaches)} утечках данных!"
                return "✅ Номер не найден в известных утечках данных"
            return "❌ Информация о утечках недоступна"
        except Exception as e:
            return f"⚠️ Ошибка при проверке утечек: {str(e)}"

    async def geolocation_data(self, phone: str) -> str:
        """Получение приблизительной геолокации"""
        # Используем API OpenCelliD (требуется регистрация)
        url = f"https://opencellid.org/cell/get?key=YOUR_KEY&mcc=250&mnc=01&lac=1234&cellid=56789"  # Пример
        return (
            "📍 Приблизительная геолокация:\n"
            "• Город: Москва\n"
            "• Регион: Центральный федеральный округ\n"
            "• Координаты: 55.7558° N, 37.6173° E\n\n"
            "ℹ️ Точность зависит от доступности данных вышек сотовой связи"
        )

def main() -> None:
    """Запуск бота"""
    bot = OSINTBot()
    app = Application.builder().token(TOKEN).build()
    
    # Обработчики команд
    app.add_handler(CommandHandler("start", bot.start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_phone))
    app.add_handler(CallbackQueryHandler(bot.service_handler, pattern=r"^service_"))
    
    # Запуск бота
    app.run_polling()
    print("Бот запущен...")

if __name__ == "__main__":
    main()

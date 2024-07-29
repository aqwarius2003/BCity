from datetime import datetime, timedelta
from django.utils.timezone import make_aware
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CommandHandler, CallbackQueryHandler, ConversationHandler, CallbackContext, MessageHandler, \
    Filters
from django.utils import timezone
from property.models import Appointment, Customer, Salon, Staff, Service

# Определение состояний для ConversationHandler
MENU, BROADCAST = range(2)


class AdminMenu:
    def __init__(self, update: Update, context: CallbackContext):
        self.update = update
        self.context = context

    def show_menu(self):
        keyboard = [
            [InlineKeyboardButton(item["name"], callback_data=item["callback_data"])]
            for item in self.menu_items
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        self.update.message.reply_text("Выберите действие:", reply_markup=reply_markup)

    def remind_tomorrow(self):
        tomorrow = make_aware(datetime.now() + timedelta(days=1)).date()
        appointments = Appointment.objects.filter(date=tomorrow)

        for appointment in appointments:
            self.send_reminder(appointment)

        self.update.callback_query.edit_message_text(text="Напоминание о завтрашних записях отправлено.")

    def send_reminder(self, appointment):
        customer = appointment.customer
        if customer.telegram_id:
            salon = appointment.salon
            staff = appointment.staff
            service = appointment.service
            start_time = appointment.start_time.strftime('%H:%M')
            message = (
                f"Вы завтра записаны:\n"
                f"Салон: {salon.name}, Адрес: {salon.address}\n"
                f"Мастер: {staff.first_name} {staff.last_name}\n"
                f"Время: {start_time}\n"
                f"Услуга: {service.name}\n"
                f"Стоимость: {service.price} руб."
            )
            self.context.bot.send_message(chat_id=customer.telegram_id, text=message)

    def remind_long_absence(self):
        self.update.callback_query.edit_message_text(
            text="Напоминание о давно не посещавших клиентах будет отправлено.")

    def send_messages_to_all(self):
        self.update.callback_query.edit_message_text(text="Введите сообщение для отправки всем пользователям.")
        return BROADCAST

    def broadcast_message(self, message):
        customers = Customer.objects.filter(telegram_id__isnull=False)

        for customer in customers:
            self.context.bot.send_message(chat_id=customer.telegram_id, text=message)

        self.update.message.reply_text("Сообщение отправлено всем пользователям.")
        return MENU

    def choose_date_salon(self):
        today = timezone.localdate()
        tomorrow = today + timedelta(days=1)

        appointments_today = Appointment.objects.filter(date=today)
        appointments_tomorrow = Appointment.objects.filter(date=tomorrow)

        response = "Записи на сегодня:\n"
        response += self.format_appointments(appointments_today)

        response += "\nЗаписи на завтра:\n"
        response += self.format_appointments(appointments_tomorrow)

        self.update.callback_query.edit_message_text(text=response)

    def format_appointments(self, appointments):
        formatted_text = ""
        for appointment in appointments:
            customer = appointment.customer
            service = appointment.service
            staff = appointment.staff
            salon = appointment.salon
            start_time = appointment.start_time.strftime('%H:%M')

            formatted_text += (
                f"Салон: {salon.name}\n"
                f"Мастер: {staff.first_name} {staff.last_name}\n"
                f"Услуга: {service.name}\n"
                f"Цена услуги: {service.price}\n"
                f"Время: {start_time}\n"
                f"Данные клиента: {customer.first_name} {customer.last_name}, {customer.phone}\n"
                "--------------------\n"
            )
        return formatted_text

    def choose_date_master(self):
        self.update.callback_query.edit_message_text(text="Выберите дату для просмотра расписания мастеров.")
        # Здесь можно добавить логику для работы с расписанием мастеров

    def record_client(self):
        self.update.callback_query.edit_message_text(text="Введите данные клиента для записи на прием.")
        # Здесь можно добавить логику для записи клиента

    def handle_callback(self, callback_data):
        action_map = {
            "remind_tomorrow": self.remind_tomorrow,
            "remind_long_absence": self.remind_long_absence,
            "send_messages_to_all": self.send_messages_to_all,
            "choose_date_salon": self.choose_date_salon,
            "choose_date_master": self.choose_date_master,
            "record_client": self.record_client,
            "back": self.show_menu
        }

        action_func = action_map.get(callback_data)
        if action_func:
            action_func()

    menu_items = [
        {"name": "Напомнить о завтрашней записи", "callback_data": "remind_tomorrow"},
        {"name": "Напомнить кто давно не был", "callback_data": "remind_long_absence"},
        {"name": "Отправить сообщения всем", "callback_data": "send_messages_to_all"},
        {"name": "Расписание салонов", "callback_data": "choose_date_salon"},
        {"name": "Расписание мастеров", "callback_data": "choose_date_master"},
        {"name": "Записать клиента", "callback_data": "record_client"},
        {"name": "Назад", "callback_data": "back"},
    ]

def handle_callback(self, callback_data):
    action_map = {
        "remind_tomorrow": self.remind_tomorrow,
        "remind_long_absence": self.remind_long_absence,
        "send_messages_to_all": self.send_messages_to_all,
        "choose_date_salon": self.choose_date_salon,
        "choose_date_master": self.choose_date_master,
        "record_client": self.record_client,
        "back": self.show_menu
    }

    action_func = action_map.get(callback_data)
    if action_func:
        action_func()
    else:
        print(f"Callback data '{callback_data}' не найден в action_map.")


# Обработчик нажатий кнопок
def button(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    admin_menu = AdminMenu(update, context)
    admin_menu.handle_callback(query.data)


# Создание ConversationHandler
admin_conv_handler = ConversationHandler(
    entry_points=[CommandHandler('admin', lambda update, context: AdminMenu(update, context).show_menu())],
    states={
        MENU: [CallbackQueryHandler(button)],
        BROADCAST: [MessageHandler(Filters.text & ~Filters.command,
                                   lambda update, context: AdminMenu(update, context).broadcast_message(
                                       update.message.text))]
    },
    fallbacks=[]
)


# Регистрация обработчика в Telegram боте
def register_admin_handlers(dp):
    dp.add_handler(admin_conv_handler)

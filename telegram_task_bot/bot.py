import logging
import sqlite3
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from config import TELEGRAM_BOT_TOKEN

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class TaskBot:
    def __init__(self, token):
        self.token = token
        self.db_name = 'tasks.db'
        self.init_db()
        
    def init_db(self):
        """Initialize the database and create tasks table if it doesn't exist"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_text TEXT NOT NULL,
                assigned_to TEXT,
                status TEXT DEFAULT 'pending',
                due_date TEXT,
                created_date TEXT,
                chat_id INTEGER,
                message_id INTEGER
            )
        ''')
        conn.commit()
        conn.close()
        logger.info("Database initialized")
    
    def add_task(self, task_text, assigned_to, due_date, chat_id, message_id):
        """Add a new task to the database"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        created_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute('''
            INSERT INTO tasks (task_text, assigned_to, due_date, created_date, chat_id, message_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (task_text, assigned_to, due_date, created_date, chat_id, message_id))
        
        task_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return task_id
    
    def get_task_by_message_id(self, chat_id, message_id):
        """Get a task by its message_id and chat_id"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM tasks WHERE chat_id = ? AND message_id = ?
        ''', (chat_id, message_id))
        
        task = cursor.fetchone()
        conn.close()
        
        return task
    
    def update_task_status(self, chat_id, message_id, new_status):
        """Update the status of a task"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE tasks SET status = ? WHERE chat_id = ? AND message_id = ?
        ''', (new_status, chat_id, message_id))
        
        rows_affected = cursor.rowcount
        conn.commit()
        conn.close()
        
        return rows_affected > 0
    
    def get_pending_tasks(self):
        """Get all pending tasks"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM tasks WHERE status = 'pending'
        ''')
        
        tasks = cursor.fetchall()
        conn.close()
        
        return tasks
    
    def get_tasks_by_user(self, assigned_to):
        """Get tasks assigned to a specific user"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM tasks WHERE assigned_to = ?
        ''', (assigned_to,))
        
        tasks = cursor.fetchall()
        conn.close()
        
        return tasks
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        await update.message.reply_text(
            'Привет! Я бот для управления задачами. '
            'Вы можете использовать меня для создания задач, отслеживания статуса и напоминаний.\n\n'
            'Команды:\n'
            '/tasks - посмотреть все задачи\n'
            '/mytasks - посмотреть задачи, назначенные мне\n'
            '/help - показать помощь'
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        await update.message.reply_text(
            'Как использовать бота:\n\n'
            '1. Чтобы создать задачу: ответьте на сообщение с текстом задачи, '
            'упомяните бота и напишите "Запомни" или "Создай задачу".\n'
            '2. Чтобы обновить статус задачи: напишите "Готово", "В работе", "Ожидает", '
            'ответив на сообщение с задачей.\n'
            '3. Используйте команды:\n'
            '   /tasks - все задачи\n'
            '   /mytasks - задачи, назначенные мне\n'
            '   /status - текущий статус задач'
        )
    
    async def tasks_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send all tasks to the user"""
        tasks = self.get_pending_tasks()
        
        if not tasks:
            await update.message.reply_text('Нет активных задач.')
            return
        
        response = "Список задач:\n\n"
        for task in tasks:
            task_id, task_text, assigned_to, status, due_date, created_date, chat_id, message_id = task
            response += f"ID: {task_id}\n"
            response += f"Задача: {task_text}\n"
            response += f"Назначена: {assigned_to or 'Не назначена'}\n"
            response += f"Статус: {status}\n"
            response += f"Срок: {due_date or 'Не указан'}\n"
            response += f"Создана: {created_date}\n\n"
        
        await update.message.reply_text(response)
    
    async def my_tasks_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send tasks assigned to the current user"""
        # Get username or ID of the current user
        user = update.effective_user
        assigned_to = user.username or str(user.id)
        
        tasks = self.get_tasks_by_user(assigned_to)
        
        if not tasks:
            await update.message.reply_text('Нет задач, назначенных вам.')
            return
        
        response = f"Ваши задачи ({len(tasks)}):\n\n"
        for task in tasks:
            task_id, task_text, assigned_to, status, due_date, created_date, chat_id, message_id = task
            response += f"ID: {task_id}\n"
            response += f"Задача: {task_text}\n"
            response += f"Статус: {status}\n"
            response += f"Срок: {due_date or 'Не указан'}\n"
            response += f"Создана: {created_date}\n\n"
        
        await update.message.reply_text(response)
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming messages"""
        message = update.message
        
        if not message:
            return
        
        text = message.text.lower() if message.text else ""
        chat_id = message.chat_id
        message_id = message.message_id
        
        # Check if this is a reply to another message
        replied_message = message.reply_to_message if message.reply_to_message else None
        
        # Handle task creation
        if replied_message and ('запомни' in text or 'создай задачу' in text or 'задача' in text):
            task_text = replied_message.text
            if task_text:
                # Extract due date if mentioned in the reply
                due_date = self.extract_due_date(text)
                
                # Determine who the task is assigned to
                assigned_to = replied_message.from_user.username or str(replied_message.from_user.id)
                
                task_id = self.add_task(task_text, assigned_to, due_date, chat_id, replied_message.message_id)
                
                response = f"Задача #{task_id} создана:\n{task_text}\n"
                response += f"Назначена: {assigned_to}\n"
                if due_date:
                    response += f"Срок выполнения: {due_date}"
                
                await message.reply_text(response)
            else:
                await message.reply_text("Не удалось создать задачу: нет текста в сообщении, на которое вы ответили.")
        
        # Handle status updates
        elif replied_message:
            # Check if we're updating status
            if 'готово' in text or 'сделано' in text or 'выполнено' in text:
                success = self.update_task_status(chat_id, replied_message.message_id, 'done')
                if success:
                    await message.reply_text("Статус задачи обновлён: выполнено ✅")
                else:
                    await message.reply_text("Не удалось обновить статус задачи.")
            
            elif 'в работе' in text or 'работаю' in text or 'в процессе' in text:
                success = self.update_task_status(chat_id, replied_message.message_id, 'in progress')
                if success:
                    await message.reply_text("Статус задачи обновлён: в работе 🔄")
                else:
                    await message.reply_text("Не удалось обновить статус задачи.")
            
            elif 'ожидает' in text or 'пауза' in text or 'приостановлено' in text:
                success = self.update_task_status(chat_id, replied_message.message_id, 'waiting')
                if success:
                    await message.reply_text("Статус задачи обновлён: ожидает ⏸️")
                else:
                    await message.reply_text("Не удалось обновить статус задачи.")
        
        # Handle general commands that might be in the message text
        elif 'мои задачи' in text:
            await self.my_tasks_command(update, context)
        elif 'все задачи' in text or 'задачи' in text:
            await self.tasks_command(update, context)
    
    def extract_due_date(self, text):
        """Extract due date from text (simplified version)"""
        # This is a simplified version - in real implementation you might want to use dateparser
        # For now, we'll just check for dates in format YYYY-MM-DD
        import re
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', text)
        if date_match:
            return date_match.group(1)
        return None

def main():
    # Use the token from config
    TOKEN = TELEGRAM_BOT_TOKEN
    
    # Create bot instance
    task_bot = TaskBot(TOKEN)
    
    # Create the Application and pass it your bot's token
    application = Application.builder().token(TOKEN).build()
    
    # Register command handlers
    application.add_handler(CommandHandler("start", task_bot.start))
    application.add_handler(CommandHandler("help", task_bot.help_command))
    application.add_handler(CommandHandler("tasks", task_bot.tasks_command))
    application.add_handler(CommandHandler("mytasks", task_bot.my_tasks_command))
    
    # Register message handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, task_bot.handle_message))
    
    # Start the Bot
    print("Starting bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
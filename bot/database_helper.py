import sqlite3
from datetime import datetime
from sqlite3 import Connection

class Database:
    """Class for managing the birthday database."""
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn: Connection = self.connect_db()

    def connect_db(self) -> Connection:
        """Connects to the SQLite database."""
        conn = sqlite3.connect(self.db_path)
        conn.execute('''CREATE TABLE IF NOT EXISTS birthdays
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      user_id INTEGER,
                      name TEXT,
                      birthday DATE,
                      UNIQUE(user_id, name))''')
        conn.commit()
        return conn

    def add_friend(self, user_id: int, name: str, birthday: str) -> None:
        """Adds a birthday to the database."""
        try:
            self.conn.execute("INSERT INTO birthdays (user_id, name, birthday) VALUES (?, ?, ?)",
                              (user_id, name, birthday))
            self.conn.commit()
        except sqlite3.IntegrityError as e:
            print(f"Error adding birthday: {e}")


    def get_birthdays_today(self) -> list:
        """Возвращает список пользователей и их друзей, у которых сегодня день рождения."""
        cursor = self.conn.cursor()
        today = datetime.now().strftime("%m-%d")
        cursor.execute("SELECT user_id, name, id FROM birthdays WHERE strftime('%m-%d', birthday) = ?", (today,))
        return cursor.fetchall()

    def get_birthday_info_by_id(self, id: int):
        """Извлекает информацию о дне рождения по уникальному идентификатору."""
        cursor = self.conn.cursor()
        # Выполните SQL-запрос для получения записи по id
        cursor.execute("SELECT name, birthday FROM birthdays WHERE id = ?", (id,))
        result = cursor.fetchone()

        if result:
            # Если запись найдена, возвращаем словарь с информацией
            return {'name': result[0], 'birthday': result[1]}
        else:
            # Если запись не найдена, возвращаем None
            return None

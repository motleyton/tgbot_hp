import logging
import os
import openai
import json
from telegram import Update

from database_helper import Database

# Load translations
parent_dir_path = os.path.join(os.path.dirname(__file__), os.pardir)
translations_file_path = os.path.join(parent_dir_path, 'translations.json')
with open(translations_file_path, 'r', encoding='utf-8') as f:
    translations = json.load(f)


def localized_text(key, bot_language):
    """
    Return translated text for a key in specified bot_language.
    Keys and translations can be found in the translations.json.
    """
    try:
        return translations[bot_language][key]
    except KeyError:
        logging.warning(f"No translation available for bot_language code '{bot_language}' and key '{key}'")
        if key in translations['en']:
            return translations['en'][key]
        logging.warning(f"No english definition found for key '{key}' in translations.json")
        # return key as text
        return key


class OpenAI:
    def __init__(self, config: dict):
        """
        Initializes the OpenAI helper class with the given configuration.
        :param config: A dictionary containing the GPT configuration
        """
        openai.api_key = config['api_key']
        self.config = config
        self.model_name = config['model']

    def _create_prompt(self, name: str) -> list:
        """
        Creates a chat prompt for generating a birthday greeting including the name.
        """
        system_prompt = [
            {"role": "system",
             "content": "Следующее сообщение должно быть поздравлением с днем рождения на русском языке. \n "
                        "В поздравлении должно явно упоминаться имя именинника и содержаться пожелания счастья, здоровья и успехов. \n "
                        "Поздравление должно быть два-три предложения"},
            {"role": "user", "content": f"Сгенерируй поздравление для моего друга. Его зовут {name}."}
        ]
        return system_prompt

    def generate_birthday_greeting(self, name: str) -> str:
        """
        Generates a birthday greeting for a given name using OpenAI GPT.
        """
        prompt = self._create_prompt(name)
        try:
            response = openai.ChatCompletion.create(
                model=self.model_name,
                messages=prompt,
                max_tokens=200
            )
            return response.choices[0].message['content'].strip()
        except openai.error.InvalidRequestError as e:
            print(f"OpenAI API error received: {e}")
            return "Произошла ошибка при генерации поздравления."







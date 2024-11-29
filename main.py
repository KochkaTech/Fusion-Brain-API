import os
import base64
import json
import logging
from datetime import datetime
from typing import List, Optional

import requests

class ImageGenerationPlatform:


    def __init__(self, config_filename='image_gen_config.json'):

        self.config_filename = config_filename
        self.logger = self._setup_logging()
        self.api_url = 'https://api-key.fusionbrain.ai'
        self._load_or_create_configuration()

    def _setup_logging(self) -> logging.Logger:
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s | %(levelname)s: %(message)s',
            datefmt='%H:%M:%S'
        )
        return logging.getLogger(__name__)

    def _load_or_create_configuration(self):

        try:
            if os.path.exists(self.config_filename):
                with open(self.config_filename, 'r') as config_file:
                    config = json.load(config_file)
                    self.api_key = config.get('api_key')
                    self.secret_key = config.get('secret_key')
            else:
                self._first_time_configuration()
        
        except (FileNotFoundError, json.JSONDecodeError):
            self._first_time_configuration()

        if not self.api_key or not self.secret_key:
            raise ValueError("API credentials are required for image generation")

    def _first_time_configuration(self):

        print("🚀 Создание изображений от Fusion Brain 🖼")
        print("Чтобы начать, вам нужно будет настроить свои учетные данные API.")
        print("Посетите https://fusionbrain.ai чтобы получить ваши ключи.\n")

        self.api_key = input("Введите API ключ: ").strip()
        self.secret_key = input("Введите секретный ключ: ").strip()

        config = {
            'api_key': self.api_key,
            'secret_key': self.secret_key
        }
        
        with open(self.config_filename, 'w') as config_file:
            json.dump(config, config_file, indent=2)
        
        print("\n✅ Ваши клюи сохранены!")

    def generate_image(self, prompt: str, num_images: int = 1) -> List[str]:
        print("Генерация. Ожидайте...")
        
        try:
            auth_headers = {
                'X-Key': f'Key {self.api_key}',
                'X-Secret': f'Secret {self.secret_key}'
            }

            # Get model and generate
            response_models = requests.get(
                f'{self.api_url}/key/api/v1/models', 
                headers=auth_headers
            )
            model_id = response_models.json()[0]['id']

            generation_params = {
                "type": "GENERATE",
                "numImages": num_images,
                "width": 1024,
                "height": 1024,
                "generateParams": {"query": prompt}
            }

            response_generation = requests.post(
                f'{self.api_url}/key/api/v1/text2image/run',
                headers=auth_headers,
                files={
                    'model_id': (None, model_id),
                    'params': (None, json.dumps(generation_params), 'application/json')
                }
            )

            request_uuid = response_generation.json().get('uuid')
            return self._process_generation(request_uuid, prompt)

        except Exception as e:
            self.logger.error(f"Ошибка генерации: {e}")
            return []

    def _process_generation(self, request_uuid: str, prompt: str) -> List[str]:

        import time

        for attempt in range(10):
            response_status = requests.get(
                f'{self.api_url}/key/api/v1/text2image/status/{request_uuid}', 
                headers={
                    'X-Key': f'Key {self.api_key}',
                    'X-Secret': f'Secret {self.secret_key}'
                }
            )
            status_data = response_status.json()

            if status_data.get('status') == 'DONE':
                return self._save_images(status_data.get('images', []), prompt)
            
            if status_data.get('status') == 'FAILED':
                self.logger.error("Generation failed")
                return []

            time.sleep(5)

        return []

    def _save_images(self, base64_images: List[str], prompt: str) -> List[str]:

        saved_paths = []
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        for index, image in enumerate(base64_images, 1):
            safe_filename = f"{timestamp}_{prompt}.png"
            
            try:
                image_data = base64.b64decode(image)
                with open(safe_filename, "wb") as f:
                    f.write(image_data)
                
                saved_paths.append(safe_filename)
                self.logger.info(f"Сохранено: {safe_filename}")
            
            except Exception as e:
                self.logger.error(f"Ошибка сохранения: {e}")

        return saved_paths

    def interactive_mode(self):

        print("\n🌟🌟 Fusion Brain 🌟🌟")
        print("Напишите 'exit' для выхода.")

        while True:
            prompt = input("\nВведите описание изображения: ").strip()
            
            if prompt.lower() in ['exit', 'quit', 'q']:
                print("До свидания!")
                break

            if not prompt:
                print("Введите запрос: ")
                continue

            images = self.generate_image(prompt)
            
            if images:
                print(f"✅ сгенерировано {len(images)} изображение")
                print("Сохранено в эту же папку.")
            else:
                print("❌ Генерация не успешна.")


def main():
    platform = ImageGenerationPlatform()
    platform.interactive_mode()


if __name__ == '__main__':
    main()

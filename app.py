from flask import Flask, request, jsonify
import yt_dlp
import requests
import json
import time
import random
from datetime import datetime, timedelta
import os
import logging

app = Flask(__name__)

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)
app.logger.setLevel(logging.DEBUG)

# Получаем переменные окружения
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_ANON_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    app.logger.error("SUPABASE_URL и SUPABASE_ANON_KEY должны быть установлены")
    raise ValueError("SUPABASE_URL и SUPABASE_ANON_KEY должны быть установлены")

app.logger.info(f"Supabase URL: {SUPABASE_URL}")

class CookieManager:
    def __init__(self):
        self.supabase_url = SUPABASE_URL
        self.supabase_key = SUPABASE_KEY
        self.headers = {
            'apikey': self.supabase_key,
            'Authorization': f'Bearer {self.supabase_key}',
            'Content-Type': 'application/json'
        }
    
    def get_best_cookies(self):
        """Получает лучший набор кукиз из пула"""
        try:
            url = f"{self.supabase_url}/rest/v1/cookies_pool"
            params = {
                'is_active': 'eq.true',
                'order': 'success_rate.desc,last_used.asc',
                'limit': 1
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            app.logger.info(f"Запрос кукиз: {response.status_code}")
            
            if response.status_code == 200:
                cookies_data = response.json()
                app.logger.info(f"Получено кукиз: {len(cookies_data)}")
                
                if not cookies_data:
                    app.logger.warning("Нет активных кукиз в пуле")
                    return None
                
                return cookies_data[0]
            else:
                app.logger.error(f"Ошибка получения кукиз: {response.text}")
                return None
                
        except Exception as e:
            app.logger.error(f"Исключение при получении кукиз: {str(e)}")
            return None
    
    def update_cookie_usage(self, cookie_id, success=True):
        """Обновляет статистику использования кукиз"""
        try:
            url = f"{self.supabase_url}/rest/v1/cookies_pool"
            
            # Получаем текущие данные
            response = requests.get(f"{url}?id=eq.{cookie_id}", headers=self.headers)
            if response.status_code != 200:
                app.logger.error(f"Ошибка получения текущих данных кукиз: {response.text}")
                return
            
            current_data = response.json()[0]
            
            # Обновляем статистику
            new_usage_count = current_data['usage_count'] + 1
            if success:
                new_success_rate = current_data['success_rate']
            else:
                # Понижаем рейтинг при неудаче
                total_attempts = new_usage_count
                successful_attempts = (current_data['success_rate'] / 100) * (total_attempts - 1)
                new_success_rate = (successful_attempts / total_attempts) * 100
            
            update_data = {
                'last_used': datetime.now().isoformat(),
                'usage_count': new_usage_count,
                'success_rate': new_success_rate,
                'is_active': success
            }
            
            patch_response = requests.patch(
                f"{url}?id=eq.{cookie_id}",
                headers=self.headers,
                data=json.dumps(update_data)
            )
            
            app.logger.info(f"Обновление статистики кукиз: {patch_response.status_code}")
            
        except Exception as e:
            app.logger.error(f"Ошибка обновления статистики кукиз: {str(e)}")

cookie_manager = CookieManager()

@app.route('/')
def health_check():
    """Основной роут для проверки работы сервера"""
    return jsonify({
        'status': 'ok', 
        'message': 'yt-dlp server is running',
        'supabase_connected': bool(SUPABASE_URL and SUPABASE_KEY)
    })

@app.route('/health')
def health():
    """Роут для health check"""
    return jsonify({'status': 'healthy'})

@app.route('/download', methods=['POST'])
def download_video():
    """Основной роут для скачивания видео"""
    try:
        app.logger.info("=== Начало обработки запроса на скачивание ===")
        
        data = request.json
        app.logger.info(f"Полученные данные: {data}")
        
        if not data:
            return jsonify({'status': 'error', 'message': 'Нет данных в запросе'}), 400
        
        video_url = data.get('url')
        video_id = data.get('video_id')
        
        if not video_url or not video_id:
            return jsonify({
                'status': 'error', 
                'message': 'Требуются параметры url и video_id'
            }), 400
        
        app.logger.info(f"Скачиваем видео: {video_id} из {video_url}")
        
        # Получаем кукиз
        cookie_data = cookie_manager.get_best_cookies()
        
        if not cookie_data:
            app.logger.warning("Скачивание без кукиз")
            cookies = []
        else:
            app.logger.info(f"Используем кукиз от аккаунта: {cookie_data.get('account_name')}")
            try:
                cookies = json.loads(cookie_data['cookies_json'])
            except:
                app.logger.error("Ошибка парсинга кукиз, продолжаем без них")
                cookies = []
        
        # Настройка yt-dlp с расширенными опциями обхода
        ydl_opts = {
            'format': 'worst[height<=480]/best[height<=720]',
            'outtmpl': f'/tmp/{video_id}.%(ext)s',
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web'],
                    'player_skip': ['webpage'],
                    'skip': ['hls', 'dash']
                }
            },
            'http_headers': {
                'User-Agent': 'com.google.android.youtube/17.31.35 (Linux; U; Android 11) gzip'
            },
            'sleep_interval': 1,
            'max_sleep_interval': 5,
            'ignore_errors': False,
            'no_warnings': False
        }
        
        # Создаем временный файл с кукиз если они есть
        cookie_file = None
        if cookies:
            cookie_file = f'/tmp/cookies_{video_id}.txt'
            try:
                with open(cookie_file, 'w') as f:
                    for cookie in cookies:
                        expiry = cookie.get('expiry', 0)
                        secure = 'TRUE' if cookie.get('secure') else 'FALSE'
                        f.write(f"{cookie['domain']}\tTRUE\t{cookie['path']}\t{secure}\t{expiry}\t{cookie['name']}\t{cookie['value']}\n")
                
                ydl_opts['cookiefile'] = cookie_file
                app.logger.info(f"Создан файл кукиз: {cookie_file}")
            except Exception as e:
                app.logger.error(f"Ошибка создания файла кукиз: {str(e)}")
        
        # Скачивание с задержкой
        app.logger.info("Начинаем скачивание с yt-dlp...")
        
        # Случайная задержка для обхода антибот защиты
        delay = random.uniform(1, 3)
        app.logger.info(f"Ждем {delay:.2f} секунд перед скачиванием...")
        time.sleep(delay)
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(video_url, download=True)
                filename = ydl.prepare_filename(info)
                app.logger.info(f"Видео скачано: {filename}")
                
                # Проверяем существование файла
                if not os.path.exists(filename):
                    raise Exception(f"Файл не найден после скачивания: {filename}")
                
                # Загрузка в Supabase Storage (пока что заглушка)
                file_url = f"https://example.com/videos/{video_id}.mp4"
                
                # Удаляем временные файлы
                if cookie_file and os.path.exists(cookie_file):
                    os.remove(cookie_file)
                if os.path.exists(filename):
                    os.remove(filename)
                
                # Обновляем статистику успешного использования
                if cookie_data:
                    cookie_manager.update_cookie_usage(cookie_data['id'], success=True)
                
                app.logger.info("=== Скачивание успешно завершено ===")
                
                return jsonify({
                    'status': 'success',
                    'file_url': file_url,
                    'video_id': video_id,
                    'title': info.get('title', 'Unknown'),
                    'duration': info.get('duration', 0)
                })
                
            except Exception as download_error:
                app.logger.error(f"Ошибка yt-dlp: {str(download_error)}")
                
                # Обновляем статистику неудачного использования
                if cookie_data:
                    cookie_manager.update_cookie_usage(cookie_data['id'], success=False)
                
                # Удаляем временные файлы
                if cookie_file and os.path.exists(cookie_file):
                    os.remove(cookie_file)
                
                return jsonify({
                    'status': 'error',
                    'message': f'Ошибка скачивания: {str(download_error)}'
                }), 500
        
    except Exception as e:
        app.logger.error(f"Общая ошибка в download_video: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/test-simple', methods=['POST'])
def test_simple():
    """Простой тест для проверки работы сервера"""
    try:
        data = request.json
        app.logger.info(f"Тестовый запрос: {data}")
        
        return jsonify({
            'status': 'success',
            'message': 'Сервер работает!',
            'received_data': data,
            'supabase_url': SUPABASE_URL[:30] + "..." if SUPABASE_URL else None
        })
        
    except Exception as e:
        app.logger.error(f"Ошибка в тесте: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/refresh-cookies', methods=['POST'])
def refresh_cookies_endpoint():
    """Эндпоинт для принудительного обновления кукиз (заглушка)"""
    try:
        data = request.json
        account_name = data.get('account_name', 'all') if data else 'all'
        
        app.logger.info(f"Запрос обновления кукиз для: {account_name}")
        
        return jsonify({
            'status': 'success',
            'message': f'Кукиз обновлены для {account_name}'
        })
        
    except Exception as e:
        app.logger.error(f"Ошибка обновления кукиз: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.logger.info(f"Запуск сервера на порту {port}")
    app.run(host='0.0.0.0', port=port, debug=True)

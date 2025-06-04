from flask import Flask, request, jsonify
import yt_dlp
import requests
import json
import time
import random
from datetime import datetime, timedelta
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os

app = Flask(__name__)

class CookieManager:
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_ANON_KEY')
        self.headers = {
            'apikey': self.supabase_key,
            'Authorization': f'Bearer {self.supabase_key}',
            'Content-Type': 'application/json'
        }
    
    def get_best_cookies(self):
        """Получает лучший набор кукиз из пула"""
        url = f"{self.supabase_url}/rest/v1/cookies_pool"
        params = {
            'is_active': 'eq.true',
            'order': 'success_rate.desc,last_used.asc',
            'limit': 1
        }
        
        response = requests.get(url, headers=self.headers, params=params)
        cookies_data = response.json()
        
        if not cookies_data:
            # Если нет активных кукиз, пытаемся обновить
            self.refresh_all_cookies()
            return self.get_best_cookies()
        
        return cookies_data[0]
    
    def update_cookie_usage(self, cookie_id, success=True):
        """Обновляет статистику использования кукиз"""
        url = f"{self.supabase_url}/rest/v1/cookies_pool"
        
        # Получаем текущие данные
        response = requests.get(f"{url}?id=eq.{cookie_id}", headers=self.headers)
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
            'is_active': success  # Деактивируем при неудаче
        }
        
        requests.patch(
            f"{url}?id=eq.{cookie_id}",
            headers=self.headers,
            data=json.dumps(update_data)
        )
    
    def refresh_cookies(self, account_name):
        """Обновляет кукиз для конкретного аккаунта"""
        try:
            options = uc.ChromeOptions()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            
            driver = uc.Chrome(options=options)
            driver.get('https://www.youtube.com')
            
            # Ждем загрузки страницы
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Имитация человеческого поведения
            time.sleep(random.uniform(3, 7))
            
            # Скроллинг для имитации активности
            driver.execute_script("window.scrollTo(0, 500);")
            time.sleep(random.uniform(1, 3))
            
            # Получение кукиз
            cookies = driver.get_cookies()
            user_agent = driver.execute_script("return navigator.userAgent;")
            
            driver.quit()
            
            # Сохранение в базу
            url = f"{self.supabase_url}/rest/v1/cookies_pool"
            update_data = {
                'cookies_json': json.dumps(cookies),
                'user_agent': user_agent,
                'is_active': True,
                'success_rate': 100.0,
                'updated_at': datetime.now().isoformat()
            }
            
            requests.patch(
                f"{url}?account_name=eq.{account_name}",
                headers=self.headers,
                data=json.dumps(update_data)
            )
            
            return True
            
        except Exception as e:
            print(f"Ошибка обновления кукиз для {account_name}: {e}")
            return False
    
    def refresh_all_cookies(self):
        """Обновляет все неактивные кукиз"""
        url = f"{self.supabase_url}/rest/v1/cookies_pool"
        params = {'is_active': 'eq.false'}
        
        response = requests.get(url, headers=self.headers, params=params)
        inactive_cookies = response.json()
        
        for cookie_data in inactive_cookies:
            self.refresh_cookies(cookie_data['account_name'])
            time.sleep(random.uniform(10, 30))  # Задержка между обновлениями

cookie_manager = CookieManager()

@app.route('/download', methods=['POST'])
def download_video():
    data = request.json
    video_url = data.get('url')
    video_id = data.get('video_id')
    
    try:
        # Получаем лучшие кукиз
        cookie_data = cookie_manager.get_best_cookies()
        
        if not cookie_data:
            return jsonify({
                'status': 'error',
                'message': 'Нет доступных кукиз'
            }), 500
        
        # Настройка yt-dlp с кукиз
        cookies = json.loads(cookie_data['cookies_json'])
        
        ydl_opts = {
            'format': 'best[height<=720]',
            'outtmpl': f'/tmp/{video_id}.%(ext)s',
            'cookiefile': None,  # Используем кукиз из переменной
        }
        
        # Создаем временный файл с кукиз
        cookie_file = f'/tmp/cookies_{video_id}.txt'
        with open(cookie_file, 'w') as f:
            for cookie in cookies:
                f.write(f"{cookie['domain']}\tTRUE\t{cookie['path']}\t{'TRUE' if cookie.get('secure') else 'FALSE'}\t{cookie.get('expiry', 0)}\t{cookie['name']}\t{cookie['value']}\n")
        
        ydl_opts['cookiefile'] = cookie_file
        
        # Скачивание
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            filename = ydl.prepare_filename(info)
        
        # Загрузка в Supabase Storage
        file_url = upload_to_supabase_storage(filename, video_id)
        
        # Обновляем статистику успешного использования
        cookie_manager.update_cookie_usage(cookie_data['id'], success=True)
        
        # Удаляем временные файлы
        os.remove(cookie_file)
        os.remove(filename)
        
        # Планируем обновление кукиз через случайное время
        if cookie_data['usage_count'] > 5:  # После 5 использований
            # Асинхронно обновляем кукиз
            import threading
            def delayed_refresh():
                time.sleep(random.uniform(60, 300))  # 1-5 минут
                cookie_manager.refresh_cookies(cookie_data['account_name'])
            
            threading.Thread(target=delayed_refresh).start()
        
        return jsonify({
            'status': 'success',
            'file_url': file_url,
            'video_id': video_id
        })
        
    except Exception as e:
        # Обновляем статистику неудачного использования
        if 'cookie_data' in locals():
            cookie_manager.update_cookie_usage(cookie_data['id'], success=False)
        
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

def upload_to_supabase_storage(file_path, video_id):
    """Загружает файл в Supabase Storage"""
    storage_url = f"{os.getenv('SUPABASE_URL')}/storage/v1/object/videos/{video_id}.mp4"
    
    with open(file_path, 'rb') as f:
        files = {'file': f}
        headers = {
            'Authorization': f'Bearer {os.getenv("SUPABASE_ANON_KEY")}'
        }
        response = requests.post(storage_url, files=files, headers=headers)
    
    if response.status_code == 200:
        return f"{os.getenv('SUPABASE_URL')}/storage/v1/object/public/videos/{video_id}.mp4"
    else:
        raise Exception(f"Ошибка загрузки в Storage: {response.text}")

@app.route('/refresh-cookies', methods=['POST'])
def refresh_cookies_endpoint():
    """Эндпоинт для принудительного обновления кукиз"""
    data = request.json
    account_name = data.get('account_name', 'all')
    
    if account_name == 'all':
        cookie_manager.refresh_all_cookies()
    else:
        cookie_manager.refresh_cookies(account_name)
    
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

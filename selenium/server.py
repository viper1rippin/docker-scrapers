from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import traceback

app = Flask(__name__)
API_KEY = os.environ.get('API_KEY')

def authenticate():
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return False
    
    parts = auth_header.split(' ')
    if len(parts) != 2 or parts[0] != 'Bearer':
        return False
    
    return parts[1] == API_KEY

@app.route('/selenium', methods=['POST'])
def scrape():
    if not authenticate():
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.json
    url = data.get('url')
    wait_for = data.get('waitFor')
    script = data.get('script')
    timeout = data.get('timeout', 30)

    if not url:
        return jsonify({'error': 'URL is required'}), 400

    driver = None
    try:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        chrome_options.binary_location = '/usr/bin/chromium'

        service = Service('/usr/bin/chromedriver')
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_page_load_timeout(timeout)
        
        driver.get(url)

        if wait_for:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, wait_for))
            )

        if script:
            result = driver.execute_script(script)
        else:
            result = driver.page_source

        driver.quit()

        return jsonify({
            'success': True,
            'data': result,
            'url': url,
            'timestamp': __import__('datetime').datetime.utcnow().isoformat()
        })

    except Exception as e:
        if driver:
            driver.quit()
        
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc(),
            'url': url
        }), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'service': 'selenium'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4444)

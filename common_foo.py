import sys, os, requests, configparser
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

config = configparser.ConfigParser()
config_file = BASE_DIR / 'config.ini'
if os.path.exists(config_file):
    config.read(config_file, encoding='utf-8')
else:
    print("error! config file doesn't exist"); sys.exit()

BACKEND_IP_ADDRESS = config['main']['backend_ip_address']
BACKEND_PORT = config['main']['backend_port']
PATH_INCOME_PRE = config['folders']['path_income_pre']
PATH_INCOME_READY = config['folders']['path_income_ready']
PATH_PROCESSED = config['folders']['path_processed']
PATH_INCORRECTS = config['folders']['path_incorrects']
WAITING_SCANNER_WRITING_FILE_TIME = int(config['tech']['waiting_scanner_writing_file_time'])
MAX_WAITING_TIME = int(config['tech']['max_waiting_time'])

for p in [PATH_INCOME_READY, PATH_PROCESSED, PATH_INCORRECTS]:
    if not os.path.exists(p):
        os.mkdir(p)

USERNAME = config['user']['username']
PWD = config['user']['pwd']



def authorization_in_api():
    #
    url = f'http://{BACKEND_IP_ADDRESS}:{BACKEND_PORT}/token'
    data = {'username': USERNAME, 'password': PWD}
    try:
        response = requests.post(url, data=data)
        if response.status_code == 200:
            return response.json()['access_token']
        else:
            print('Error:', response.status_code)
            return None
    except requests.exceptions.RequestException as e:
        print('Error:', e)
        return None
    

def post_notification(sender, incorrect_file_name, ip, port, api_access_token):
    #
    is_notification = True
    sender = sender
    receiver = 'admin'
    msg_text = f'Ошибка загрузки сканированого файла {incorrect_file_name}'
    data = str({'file_name': incorrect_file_name})
    url = f'http://{ip}:{port}/messages'
    data = {
        'is_notification': is_notification,
        'sender': sender,
        'receiver': receiver,
        'msg_text': msg_text,
        'data': data,
    }
    print('data = ', data)
    try:
        response = requests.post(url, data=data, headers={'Authorization': f'Bearer {api_access_token}'})
        if response.status_code == 200:
            print('[ info ]  создано оповещение о некорректном файле')
            return response.json()

        else:
            print('Error:', response.status_code)
            return None
    except requests.exceptions.RequestException as e:
        print('Error:', e)
        return None
    
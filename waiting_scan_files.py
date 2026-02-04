import sys, os, time, configparser
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

config = configparser.ConfigParser()
config_file = BASE_DIR / 'config.ini'
if os.path.exists(config_file):
    config.read(config_file, encoding='utf-8')
else:
    print("error! config file doesn't exist"); sys.exit()

PATH_INCOME_PRE = config['folders']['path_income_pre']
PATH_INCOME_READY = config['folders']['path_income_ready']
WAITING_SCANNER_WRITING_FILE_TIME = int(config['tech']['waiting_scanner_writing_file_time'])

for p in [PATH_INCOME_PRE, PATH_INCOME_READY]:
    if not os.path.exists(p):
        os.mkdir(p)

while(True):
    print('[ info ]  ожидание нового файла от сканера...')
    time.sleep(1)
    for file_name in os.listdir(PATH_INCOME_PRE):
        print(f'[ info ]  поступил новый файл {file_name}. ожидание сканирования...')
        src_path = os.path.join(PATH_INCOME_PRE, file_name)
        dst_path = os.path.join(PATH_INCOME_READY, file_name)
        if os.path.exists(dst_path):
            if '.' in dst_path: 
                fname_splited = dst_path.rpartition('.')
                dst_path = f'{fname_splited[0]}_1.{fname_splited[2]}'
            else:
                dst_path += '_1'
        attempt = 0
        while(True):
            time.sleep(WAITING_SCANNER_WRITING_FILE_TIME)
            attempt += 1
            try:
                os.replace(src_path, dst_path)
                print('[ info ]  OK - файл отсканирован и перемещен'); break
            except PermissionError as e:
                print(f'[ info ]  {WAITING_SCANNER_WRITING_FILE_TIME * attempt} сек - файл в процессе записи сканером ( {e} )')

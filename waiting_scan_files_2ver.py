import sys, os, time, configparser, shutil
from datetime import date, datetime
from pathlib import Path
from pdf2image import convert_from_path
from pdf2image.exceptions import (
    PDFInfoNotInstalledError,
    PDFPageCountError,
    PDFSyntaxError
)


BASE_DIR = Path(__file__).resolve().parent

config = configparser.ConfigParser()
config_file = BASE_DIR / 'config.ini'
if os.path.exists(config_file):
    config.read(config_file, encoding='utf-8')
else:
    print("error! config file doesn't exist"); sys.exit()

PATH_INCOME_PRE = config['folders']['path_income_pre']
PATH_INCOME_READY = config['folders']['path_income_ready']
PATH_INCORRECTS = config['folders']['path_incorrects']
WAITING_SCANNER_WRITING_FILE_TIME = int(config['tech']['waiting_scanner_writing_file_time'])
MAX_WAITING_TIME = int(config['tech']['max_waiting_time'])

for p in [PATH_INCOME_PRE, PATH_INCOME_READY, PATH_INCORRECTS]:
    if not os.path.exists(p):
        os.mkdir(p)

while(True):
    print('[ info ]  ожидание нового файла от сканера...')
    time.sleep(1)
    for file_name in os.listdir(PATH_INCOME_PRE):
        print(f'[ info ]  поступил новый файл {file_name}.', end=' ')

        src_path = os.path.join(PATH_INCOME_PRE, file_name)
        dst_path = os.path.join(PATH_INCOME_READY, file_name)

        # create filename with postfix for error_dst_path
        file_path_postfix = datetime.now().strftime("%Y%m%d%H%M%S%f")
        if '.' in file_name:
            fname_splited = file_name.rpartition('.')
            new_filename = f'{fname_splited[0]}_{file_path_postfix}.{fname_splited[2]}'
        else:
            new_filename =  f'{file_name}_{file_path_postfix}'
        error_dst_path = os.path.join(PATH_INCORRECTS, new_filename)

        print('dst_path =', dst_path)
        print('error_dst_path =', error_dst_path)

        if os.path.exists(dst_path):
            if '.' in dst_path: 
                fname_splited = dst_path.rpartition('.')
                dst_path = f'{fname_splited[0]}_1.{fname_splited[2]}'
            else:
                dst_path += '_1'
        if os.path.exists(error_dst_path):
            if '.' in error_dst_path: 
                fname_splited = error_dst_path.rpartition('.')
                error_dst_path = f'{fname_splited[0]}_1.{fname_splited[2]}'
            else:
                error_dst_path += '_1'

        if file_name.rpartition('.')[2] != 'pdf':
            if os.path.isdir(src_path):
                # os.replace(src_path, error_dst_path)
                shutil.move(src_path, error_dst_path)
                print(f'\n[ error ]  {file_name} - папка, а не файл - перемещена в Incorrects')
                break
            os.replace(src_path, error_dst_path)
            print(f'\n[ error ]  {file_name} - не PDF-файл - перемещен в Incorrects')
            break
        
        print(f'ожидание сканирования {WAITING_SCANNER_WRITING_FILE_TIME} сек...')
        attempt = 0
        while(True):
            if WAITING_SCANNER_WRITING_FILE_TIME * attempt >= MAX_WAITING_TIME:
                os.replace(src_path, error_dst_path)
                print(f'[ error ]  превышено максимальное время ожидания сканирования {MAX_WAITING_TIME} сек - файл перемещен в Incorrects')                
                break
            time.sleep(WAITING_SCANNER_WRITING_FILE_TIME)
            attempt += 1
            if not os.path.exists(src_path):
                print(f'[ error ]  файл {src_path} не найден')
                break

            try:
                res_read_pdf = convert_from_path(src_path, dpi=400, first_page=1, last_page=1)
                # print('[ info ]  res_read_pdf =', res_read_pdf)
                os.replace(src_path, dst_path)
                print('[ info ]  OK - файл отсканирован и перемещен'); break
            except PDFPageCountError as e:
                print(f'[ info ]  {WAITING_SCANNER_WRITING_FILE_TIME * attempt} сек - файл в процессе записи сканером ( {e} )')
            except Exception as e2:
                os.replace(src_path, error_dst_path)
                print('[ error ]  ошибка файла - файл перемещен в Incorrects'); break

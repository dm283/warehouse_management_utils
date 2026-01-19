#
print('старт утилиты load_files.py')
print('импорт библиотек...')

import sys, os, shutil, configparser, cv2, requests, numpy
from time import sleep
from datetime import date, datetime
from pathlib import Path
from pdf2image import convert_from_path
from qreader import QReader

BASE_DIR = Path(__file__).resolve().parent

config = configparser.ConfigParser()
config_file = BASE_DIR / 'config.ini'
if os.path.exists(config_file):
    config.read(config_file, encoding='utf-8')
else:
    print("error! config file doesn't exist"); sys.exit()

BACKEND_IP_ADDRESS = config['main']['backend_ip_address']
BACKEND_PORT = config['main']['backend_port']
PATH_INCOME = config['folders']['path_income']
PATH_PROCESSED = config['folders']['path_processed']
PATH_INCORRECTS = config['folders']['path_incorrects']

for p in [PATH_INCOME, PATH_PROCESSED, PATH_INCORRECTS]:
    if not os.path.exists(p):
        os.mkdir(p)

USERNAME = config['user']['username']
PWD = config['user']['pwd']


QREADER = QReader()

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
    

def get_user_data(username, api_access_token):
    #
    url = f'http://{BACKEND_IP_ADDRESS}:{BACKEND_PORT}/users/by_name/{username}'
    try:
        response = requests.get(url, headers={'Authorization': f'Bearer {api_access_token}'})
        if response.status_code == 200:
            return response.json()
        else:
            print('Error:', response.status_code)
            return None
    except requests.exceptions.RequestException as e:
        print('Error:', e)
        return None


def get_batch_data(uuid, api_access_token):
    #
    url = f'http://{BACKEND_IP_ADDRESS}:{BACKEND_PORT}/batch_by_uuid/{uuid}'
    try:
        response = requests.get(url, headers={'Authorization': f'Bearer {api_access_token}'})
        if response.status_code == 200:
            return response.json()
        else:
            print('Error:', response.status_code)
            return None
    except requests.exceptions.RequestException as e:
        print('Error:', e)
        return None


def post_document_record(doc_name, doc_id, doc_date, comment, user_uuid_create, api_access_token):
    #
    url = f'http://{BACKEND_IP_ADDRESS}:{BACKEND_PORT}/document_records'
    data = {
        'doc_name': doc_name,
        'doc_id': doc_id,
        'doc_date': doc_date,
        'comment': comment,
        'user_uuid_create': user_uuid_create
    }
    try:
        response = requests.post(url, data=data, headers={'Authorization': f'Bearer {api_access_token}'})
        if response.status_code == 200:
            return response.json()
        else:
            print('Error:', response.status_code)
            return None
    except requests.exceptions.RequestException as e:
        print('Error:', e)
        return None
    

def upload_document(file_path, related_doc_uuid, user_uuid, api_access_token):
    #
    url = f'http://{BACKEND_IP_ADDRESS}:{BACKEND_PORT}/upload_file_for_carpass/{related_doc_uuid}'
    data = {
        'customer_name': 'deprecated',
        'contact_uuid': 'deprecated',
        'post_user_id': user_uuid
    }
    try:
        with open(file_path, 'rb') as file:
            response = requests.put(url, data=data, files={'file': file}, headers={'Authorization': f'Bearer {api_access_token}'})
        if response.status_code == 200:
            return response.json()
        else:
            print('Error:', response.status_code)
            return None
    except requests.exceptions.RequestException as e:
        print('Error:', e)
        return None


def post_related_doc_rec(obj_type, obj_type_name, contact_uuid, obj_uuid, doc_uuid, user_uuid, api_access_token):
    #
    url = f'http://{BACKEND_IP_ADDRESS}:{BACKEND_PORT}/create_related_docs_record'
    data = {
        'obj_type': obj_type,
        'obj_type_name': obj_type_name,
        'contact_uuid': contact_uuid,
        'obj_uuid': obj_uuid,
        'user_uuid': user_uuid,
        'doc_uuid': doc_uuid
    }
    try:
        response = requests.post(url, data=data, headers={'Authorization': f'Bearer {api_access_token}'})
        if response.status_code == 200:
            return response.json()
        else:
            print('Error:', response.status_code)
            return None
    except requests.exceptions.RequestException as e:
        print('Error:', e)
        return None


def convert_pdf_to_jpg(pdf_pages_folder, jpg_files_folder):
    # convert pdf pages to jpg files
    counter = int()

    # if elements quantity per page is 1 then set dpi = 400, else 200 
    # (because not every elements is decoded if dpi 400 and quantity of element 20 for example)
    # dpi = 400 if dmtx_cnt_per_page == 1 else 200
    dpi = 400
        
    pdf_files = os.listdir(pdf_pages_folder)
    # pdf_files.sort(key=lambda x: int(x.partition('.')[0]))

    print('converting pdf to jpg ...')
    for file in pdf_files:
        print(file, end='\r')
        image = convert_from_path( os.path.join(pdf_pages_folder, file), dpi=dpi, )
        image[0].save(f'{jpg_files_folder}/page'+ str(counter) +'.jpg', 'JPEG')
        

        ############### new for mts
        image_cv2 = cv2.cvtColor(cv2.imread(f'{jpg_files_folder}/page'+ str(counter) +'.jpg'), cv2.COLOR_BGR2RGB)
        decoded_text = QREADER.detect_and_decode(image=image_cv2)
        print('decoded_text: ', decoded_text)
        decoded_batch_uuid = decoded_text[0].split('\n')[0].partition(':')[2].strip()
        print('decoded_batch_uuid =', decoded_batch_uuid)
        #################

        counter += 1
    print(f'ok. converted {counter} files')


def move_income_file(dst, file_name, file_path):
    #
    file_path_postfix = datetime.now().strftime("%Y%m%d%H%M%S%f")
    fname_splited = file_name.rpartition('.')
    new_filename = f'{fname_splited[0]}_{file_path_postfix}.{fname_splited[2]}'
    new_file_path = os.path.join(dst, new_filename)
    shutil.move(file_path, new_file_path)
    print('[ info ]  файл', file_name, 'перемещён в папку', dst.rpartition('/')[-1])


def file_attachment_to_batch_process(batch_uuid, file_name, file_path):
    # actions for attachment file to batch object

    # check batch exists and get batch data
    batch_data = get_batch_data(uuid=batch_uuid, api_access_token=api_access_token)
    if batch_data:
        # print(f'check is batch uuid {batch_uuid} exists  -  OK')
        print(f'[ info ]  партия {batch_uuid} существует  -  ОК')
    else:
        print(f'[ error ]  партия {batch_uuid} не существует')
        return 1
        # print('Failed to fetch posts from API.')

    # create document_record
    current_datetime = datetime.now(); year = current_datetime.year; month = current_datetime.month; day = current_datetime.day
    res_posted_doc_rec = post_document_record(doc_name=file_name, doc_id='-', doc_date=date(year,month,day), comment='posted by system utility', 
                            user_uuid_create=user_info['uuid'], api_access_token=api_access_token)
    # print('document_record posted. related_doc_uui =', res_posted_doc_rec['uuid'])
    print('[ info ]  запись document_record добавлена с uuid', res_posted_doc_rec['uuid'])

    # create document (upload)
    res_upload_doc = upload_document(file_path=file_path, related_doc_uuid=res_posted_doc_rec['uuid'], 
                    user_uuid=user_info['uuid'], api_access_token=api_access_token)
    #print('document uploaded. filename =', res_upload_doc)
    print('[ info ]  запись document добавлена (файл загружен)')

    # attach doc to batch
    res_attach_doc_to_batch = post_related_doc_rec(
        obj_type='Партия товаров',
        obj_type_name='Партии товаров',
        contact_uuid=batch_data['contact_uuid'],
        obj_uuid=batch_uuid,
        doc_uuid=res_posted_doc_rec['uuid'],
        user_uuid=user_info['uuid'],
        api_access_token=api_access_token
    )
    # print(f'document has been attached to batch {batch_uuid}')
    print(f'[ info ]  файл прикреплен к партии товаров {batch_uuid}  -  OK')


print(f'авторизация пользователя {USERNAME} в API ...', end=' ')
api_access_token = authorization_in_api()
print('OK')
print(f'получение данных о пользователе {USERNAME} ...', end=' ')
user_info = get_user_data(username=USERNAME, api_access_token=api_access_token)
print('OK')


while(True):
    print('[ info ]  ожидание нового файла...')
    for file_name in os.listdir(PATH_INCOME):
        sleep(1)
        file_path = os.path.join(PATH_INCOME, file_name)
        if not os.path.isfile(file_path):
            continue
        print(f'[ info ]  поступил новый файл {file_name}')
        try:
            page1_image_pil = convert_from_path(file_path, dpi=400, first_page=1, last_page=1)[0]
            page1_image_cv2 = cv2.cvtColor(numpy.array(page1_image_pil), cv2.COLOR_RGB2BGR)
            qrcode_decoded_text = QREADER.detect_and_decode(image=page1_image_cv2)
            if 'UUID' in qrcode_decoded_text[0]:
                # add in if statement qr-code check (some mark uuid or smthg)
                decoded_batch_uuid = qrcode_decoded_text[0].split('\n')[0].partition(':')[2].strip()
                print(f'[ info ]  файл {file_name} корректный, qr-код распознан')
                print(f'[ info ]  uuid партии товаров:', decoded_batch_uuid)
            else:
                raise Exception
                
            print('[ info ]  проводим привязку к партии товаров...')
            res_attach_file = file_attachment_to_batch_process(decoded_batch_uuid, file_name=file_name, file_path=file_path)
            if res_attach_file == 1:
                move_income_file(dst=PATH_INCORRECTS, file_name=file_name, file_path=file_path)
                continue
            
            move_income_file(dst=PATH_PROCESSED, file_name=file_name, file_path=file_path)
            
        except Exception as e:
            print(f'[ error ]  файл {file_name} некорректный')
            move_income_file(dst=PATH_INCORRECTS, file_name=file_name, file_path=file_path)

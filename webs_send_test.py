import requests, json
from time import sleep
from websockets.sync.client import connect
from common_foo import authorization_in_api, BACKEND_IP_ADDRESS, BACKEND_PORT, PATH_INCOME_READY, PATH_PROCESSED, \
        PATH_INCORRECTS, USERNAME, PWD


TIME_DELAY_CHECK_DB = 5


print(f'авторизация пользователя {USERNAME} в API ...', end=' ')
api_access_token = authorization_in_api()
print('OK')


def get_new_notifications(api_access_token):
    #
    url = f'http://{BACKEND_IP_ADDRESS}:{BACKEND_PORT}/messages/notifications/news/admin'
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
    

def send_websocket_msg():
    with connect("ws://localhost:8001/ws/system") as websocket:
        data = {'receiver':'admin', 'message':'test_msg'}
        websocket.send(json.dumps(data))
        
        # message = websocket.recv()
        # print(f"Received: {message}")


while True:
    print('[ info ]  проверка новых оповещений в базе данных...')
    new_notifications = get_new_notifications(api_access_token)
    # print('new_messages =', new_messages)
    if new_notifications:
        print('[ info ]  есть новые оповещения - отправка маяка в чат для активации колокольчика')
        send_websocket_msg()
    else:
        print('[ info ]  нет новых оповещений')
    sleep(TIME_DELAY_CHECK_DB)

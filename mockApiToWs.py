import requests
import time
import websocket

api_url = "http://192.168.1.175:8000/status"  # ここにAPIのエンドポイントURLを入力


#ws = websocket.create_connection("ws://localhost:8000/ws")
while True:
    try:
        response = requests.get(api_url)
        response.raise_for_status()  # エラーが発生した場合に例外を発生させる
        # APIからのレスポンスを処理
        print(response.text) # レスポンスをJSONとして表示
    except requests.exceptions.RequestException as e:
        print(f"APIリクエストエラー: {e}")
    
    #else:


    time.sleep(1)
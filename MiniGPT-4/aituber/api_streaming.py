import redis
from aituber.app_streaming import (generate_from_api, reset_api,
                                   upload_image_from_api)
from fastapi import FastAPI, File,WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# how to start server
# ```
# uvicorn aituber.api_streaming:app --reload --port 8000 --workers 1 --ws-max-size 1
# ```

app = FastAPI()

# CORS設定
origins = [
    "*",
    "http://localhost",
    "http://localhost:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

image_cache_client = redis.Redis(host='127.0.0.1', port=6379, db=0)
IMAGE_KEY = "image_key"


class GenerateInput(BaseModel):
    text: str
    max_new_tokens: int = 256
    min_length: int = 16
    temperature: float = 1.0


@app.post("/generate")
async def generate(input: GenerateInput):
    return StreamingResponse(
        generate_from_api(
            [input.text], max_new_tokens=input.max_new_tokens, min_length=input.min_length, temperature=input.temperature
        ),
        media_type="application/json",
    )


@app.post("/image")
async def upload_image(file: bytes = File(...)):
    # Memcachedに画像を保存する
    image_cache_client.set(IMAGE_KEY, file)
    upload_image_from_api(file)
    return '{"message": "ok"}'


@app.post("/image/refresh")
async def refresh_image():
    reset_api()
    # 最新画像をMemcachedから読み取る
    file = image_cache_client.get(IMAGE_KEY)
    if file:
        upload_image_from_api(file)
        return '{"message": "ok"}'
    return '{"message": "ng"}'


@app.get("/status")
async def get_status():
    # 最新画像をMemcachedから読み取る
    file = image_cache_client.get(IMAGE_KEY)
    if not file:
        print('Error: get memcache')
        raise Exception('Error: get memcache')

    # 履歴をリセットして新しい応答文を生成する
    reset_api()
    upload_image_from_api(file)
    texts = [
        '   実況するゲームの概要：『Elite Dangerous』は、広大な宇宙を舞台にした大規模マルチプレイヤーオンラインゲーム（MMO）です。プレイヤーは宇宙船を操縦し、貿易、戦闘、探査など、様々な活動を通じて宇宙を自由に冒険できます。1984年の初代「Elite」から続くシリーズの最新作で、現代の世代に向けて、リアルな銀河系を再現したオープンワールド体験を提供しています。\
            ゲームの特徴:\
            自由な宇宙:\
            プレイヤーは、広大な宇宙空間を自由に移動し、様々な星系や惑星を探索できます。\
            多種多様なプレイスタイル:\
            貿易、戦闘、探査、採掘など、自分の好みに合わせたプレイスタイルでゲームを楽しめます。\
            宇宙船のカスタマイズ:\
            多数の宇宙船が登場し、自由に改造やカスタマイズが可能です。\
            大規模マルチプレイヤー:\
            他のプレイヤーと協力したり、時には競い合ったりしながら、広大な宇宙を冒険できます。\
            進化するストーリー:\
            プレイヤーの行動がゲーム内の世界に影響を与え、ストーリーが進化していきます。\
            ゲームの目的:\
            ゲームに明確な目的はなく、プレイヤーは自由な目標を設定して宇宙を冒険できます。貿易で富を築いたり、戦闘で名を上げたり、宇宙の謎を解き明かしたりと、プレイヤー次第で様々な楽しみ方が可能です。\
            Elite dangorousというゲームのプレイ画面。今の状況を説明して',
        # NOTE: 状況説明後、AITuberが何か付加的なコメントをランダムにコメントする
        [
            'このあとどうなると思いますか？',
            'あなたならどうしますか？',
        ]
    ]

    def post_rule_process(text, output, messages):
        # NOTE: このあとどうなると思いますか？という質問の場合は、応答文の最初に「この後は、」を付けている
        # (ユーザには応答文だけ返るので、つけないと唐突な印象となり、つける少しうるさく感じる。もう少し自然な感じにしたい)
        if 'このあとどうなると思いますか？' in text and not messages[-1][1]:
            output = "。この後は、" + output
        print(output)
        return output

    return StreamingResponse(
        generate_from_api(
            texts, max_new_tokens=64, min_length=8, temperature=1, post_process=post_rule_process
        ),
        media_type="application/json",
    )

@app.post("/reset")
async def reset():
    # 履歴をリセット
    reset_api()
    return '{"message": "ok"}'

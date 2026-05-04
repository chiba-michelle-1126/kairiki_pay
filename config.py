# ===== Imports / ライブラリ =====
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))

# ===== Config / 設定データ =====
# 所持金の上限（インフレ防止・ゲームバランス調整）
MAX_MONEY = 100000000

# ショップの商品データ
SHOP_ITEMS = {
    "coffee": {
        "name": "コーヒー",
        "price": 300
    },
    "ticket": {
        "name": "ガチャチケット",
        "price": 1000
    },
    "crown": {
        "name": "王冠",
        "price": 10000
    }
}

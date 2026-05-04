from datetime import datetime
import random

from storage import save_json
from config import MAX_MONEY

def clamp_money(money, user_id):
    money[user_id] = max(0, min(MAX_MONEY, money[user_id]))

# 仕事のロジック
def do_work(user_id, money, last_work):
    today = datetime.now().date().isoformat()

    if user_id not in money:
        money[user_id] = 0

    if user_id in last_work and last_work[user_id] == today:
        return False, money[user_id]

    money[user_id] += 100
    clamp_money(money, user_id)
    save_json("money.json", money)

    last_work[user_id] = today
    save_json("last_work.json", last_work)

    return True, money[user_id]

# ガチャのロジック
def do_gacha(user_id, money):
    if user_id not in money:
        money[user_id] = 0

    cost = 100

    if money[user_id] < cost:
        return False, None, None, money[user_id]

    money[user_id] -= cost

    prizes = [
        ("大当たり！", 500),
        ("当たり！", 200),
        ("普通", 100),
        ("ちょいハズレ", 50),
        ("ハズレ", 10)
    ]

    result_name, reward = random.choices(
        prizes,
        weights=[2, 8, 30, 40, 20]
    )[0]

    money[user_id] += reward
    clamp_money(money, user_id)
    save_json("money.json", money)

    return True, result_name, reward, money[user_id]

# アイテム購入のロジック
def do_buy(user_id, item_id, money, inventory, shop_items):
    if item_id not in shop_items:
        return False, "そのアイテムは存在しません", None

    item = shop_items[item_id]
    price = item["price"]

    if user_id not in money:
        money[user_id] = 0

    if money[user_id] < price:
        return False, "お金が足りません", None

    money[user_id] -= price
    clamp_money(money, user_id)
    save_json("money.json", money)

    if user_id not in inventory:
        inventory[user_id] = {}

    if item_id not in inventory[user_id]:
        inventory[user_id][item_id] = 0

    inventory[user_id][item_id] += 1
    save_json("inventory.json", inventory)

    return True, item, money[user_id]
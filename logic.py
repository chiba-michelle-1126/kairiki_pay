from datetime import datetime
from storage import save_json
from config import MAX_MONEY


def clamp_money(money, user_id):
    money[user_id] = max(0, min(MAX_MONEY, money[user_id]))


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
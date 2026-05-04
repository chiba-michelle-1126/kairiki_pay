# ===== Imports / ライブラリ =====
import discord
from discord.ext import commands
import json
import random
import math
from datetime import datetime
from discord import app_commands
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))

# ===== Bot Settings (Bot設定) =====
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ===== Load / Save Functions (データの読み込み・保存用の関数)=====
# データを「読み込む処理」
def load_money():
    try:
        with open("money.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# データを「保存する処理」
def save_money():
    with open("money.json", "w", encoding="utf-8") as f:
        json.dump(money, f, ensure_ascii=False, indent=2)

# 最終使用日を「読み込む処理」
def load_last_work():
    try:
        with open("last_work.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# 最終使用日を「保存する処理」
def save_last_work():
    with open("last_work.json", "w", encoding="utf-8") as f:
        json.dump(last_work, f, ensure_ascii=False, indent=2)

# アイテム所持データを読み込む処理
def load_inventory():
    try:
        with open("inventory.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

#アイテム所持データを保存する処理
def save_inventory():
    with open("inventory.json", "w", encoding="utf-8") as f:
        json.dump(inventory, f, ensure_ascii=False, indent=2)

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

# ===== State / 状態データ =====
# 実際の所持金データを読み込む
money = load_money()

# 最終使用日データを読み込む
last_work = load_last_work()

# アイテム所持データを読み込む
inventory = load_inventory()

# ===== Utils / 共通処理 =====
# 所持金を0以上MAX_MONEY以下に調整する関数
def clamp_money(user_id):
    money[user_id] = max(0, min(MAX_MONEY, money[user_id])) 

# 残高確認のEmbedを作成する関数
def create_balance_embed(user, balance):
    embed = discord.Embed(
        title="💰 残高確認",
        description=f"{user.display_name} の現在の残高",
        color=discord.Color.gold()
    )

    embed.add_field(
        name="所持金",
        value=f"{balance}円",
        inline=False
    )

    return embed

# 1日1回のログインボーナス処理
def do_work(user_id):
    today = datetime.now().date().isoformat()

    if user_id not in money:
        money[user_id] = 0

    if user_id in last_work and last_work[user_id] == today:
        return False, money[user_id]

    money[user_id] += 100
    clamp_money(user_id)
    save_money()

    last_work[user_id] = today
    save_last_work()

    return True, money[user_id]

# ガチャ処理
def do_gacha(user_id):
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
    clamp_money(user_id)
    save_money()

    return True, result_name, reward, money[user_id]


# ガチャ結果のEmbedを作る
def create_gacha_embed(user, result_name, reward, balance):
    embed = discord.Embed(
        title="🎲 ガチャ結果",
        description=f"{user.display_name} がガチャを引きました！",
        color=discord.Color.purple()
    )

    embed.add_field(name="結果", value=result_name, inline=False)
    embed.add_field(name="獲得金額", value=f"{reward}円", inline=True)
    embed.add_field(name="現在の残高", value=f"{balance}円", inline=True)

    return embed

# アイテム購入のEmbedを作る
def do_buy(user_id, item_id):
    if item_id not in SHOP_ITEMS:
        return False, "そのアイテムは存在しません", None

    item = SHOP_ITEMS[item_id]
    price = item["price"]

    if user_id not in money:
        money[user_id] = 0

    if money[user_id] < price:
        return False, "お金が足りません", None

    # お金減らす
    money[user_id] -= price
    clamp_money(user_id)
    save_money()

    # インベントリ追加
    if user_id not in inventory:
        inventory[user_id] = {}

    if item_id not in inventory[user_id]:
        inventory[user_id][item_id] = 0

    inventory[user_id][item_id] += 1
    save_inventory()

    return True, item, money[user_id]

def create_buy_embed(user, item, balance):
    embed = discord.Embed(
        title="🛒 購入完了",
        description=f"{user.display_name} が購入しました",
        color=discord.Color.green()
    )

    embed.add_field(name="アイテム", value=item["name"], inline=False)
    embed.add_field(name="価格", value=f"{item['price']}円", inline=True)
    embed.add_field(name="残高", value=f"{balance}円", inline=True)

    return embed

# ===== UI Classes / UIクラス=====
class MenuView(discord.ui.View):
    # 残高確認ボタンが押されたときの処理
    @discord.ui.button(label="残高確認", style=discord.ButtonStyle.primary)
    async def balance_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = str(interaction.user.id)

        if user_id not in money:
            money[user_id] = 0
            save_money()

        embed = create_balance_embed(interaction.user, money[user_id])

        await interaction.response.send_message(embed=embed, ephemeral=True)

    # 仕事ボタンが押されたときの処理
    @discord.ui.button(label="仕事する", style=discord.ButtonStyle.success)
    async def work_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = str(interaction.user.id)
        today = datetime.now().date().isoformat()

        if user_id not in money:
            money[user_id] = 0

        if user_id in last_work and last_work[user_id] == today:
            await interaction.response.send_message(
                "今日はもう働きました。また明日ね。",
                ephemeral=True
            )
            return

        money[user_id] += 100
        clamp_money(user_id)
        save_money()

        last_work[user_id] = today
        save_last_work()

        embed = discord.Embed(
            title="💼 お仕事完了！",
            description=f"{interaction.user.display_name} が働きました",
            color=discord.Color.green()
        )

        embed.add_field(name="💰 獲得金額", value="100円", inline=False)
        embed.add_field(name="🏦 現在の残高", value=f"{money[user_id]}円", inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ガチャボタンが押されたときの処理
    @discord.ui.button(label="ガチャ", style=discord.ButtonStyle.danger)
    async def gacha_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = str(interaction.user.id)

        success, result_name, reward, balance = do_gacha(user_id)

        if not success:
            await interaction.response.send_message(
                "ガチャを引くには100円必要です",
                ephemeral=True
            )
            return

        embed = create_gacha_embed(interaction.user, result_name, reward, balance)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ショップボタンが押されたときの処理    
    @discord.ui.button(label="ショップ", style=discord.ButtonStyle.secondary)
    async def shop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🛒 ショップ",
            description="購入できるアイテム一覧",
            color=discord.Color.blue()
        )

        for item_id, item in SHOP_ITEMS.items():
            embed.add_field(
                name=item["name"],
                value=f"ID: `{item_id}` / 価格: {item['price']}円",
                inline=False
            )

        embed.set_footer(text="購入方法: !buy アイテムID")

        await interaction.response.send_message(embed=embed, ephemeral=True)


    @discord.ui.button(label="所持アイテム", style=discord.ButtonStyle.secondary)
    async def inventory_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = str(interaction.user.id)

        if user_id not in inventory or not inventory[user_id]:
            await interaction.response.send_message("何も持っていません。", ephemeral=True)
            return

        embed = discord.Embed(
            title="🎒 所持アイテム",
            description=f"{interaction.user.display_name} のアイテム一覧",
            color=discord.Color.blue()
        )

        for item_id, count in inventory[user_id].items():
            item_name = SHOP_ITEMS[item_id]["name"]
            embed.add_field(
                name=item_name,
                value=f"{count}個",
                inline=False
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)
        

# ===== Events / イベント =====
# スラッシュコマンドを有効にするためのイベント
# 本番用にする時は ↓ これ
"""
@bot.event
async def setup_hook():
    await bot.tree.sync()
"""    

# 開発用にする時は ↓ これ
@bot.event
async def setup_hook():
    guild = discord.Object(id=GUILD_ID)
    await bot.tree.sync(guild=guild)
    
# BOT起動時に動くイベント関数
@bot.event
async def on_ready():
    print(f"ログインしました: {bot.user}")

# ===== Commands / コマンド =====
# ここから下に !コマンド を追加していきます
# /コマンドが使えないバグが発生した時のための保険として、まずは !コマンド を実装しておきます
#残高を確認するコマンド
@bot.command()
async def balance(ctx):
    user_id = str(ctx.author.id)

    if user_id not in money:
        money[user_id] = 0
        clamp_money(user_id)
        save_money()

    embed = discord.Embed(
        title="💰 残高確認",
        description=f"{ctx.author.display_name} の現在の残高",
        color=discord.Color.gold()
    )

    embed.add_field(
        name="所持金",
        value=f"{money[user_id]}円",
        inline=False
    )

    await ctx.send(embed=embed)

#1日1回ログインボーナスがもらえるコマンド
@bot.command()
async def work(ctx):
    user_id = str(ctx.author.id)
    today = datetime.now().date().isoformat()

    # 初回対策
    if user_id not in money:
        money[user_id] = 0

    # 今日もう使ってるかチェック
    if user_id in last_work and last_work[user_id] == today:
        await ctx.send("今日はもう働いてるよ！また明日ね。")
        return

    # 実行
    money[user_id] += 100
    clamp_money(user_id)
    save_money()

    last_work[user_id] = today
    save_last_work()

    embed = discord.Embed(
        title="💼 お仕事完了！",
        description=f"{ctx.author.display_name} が働きました",
        color=discord.Color.green()
    )

    embed.add_field(
        name="💰 獲得金額",
        value="100円",
        inline=False
    )

    embed.add_field(
        name="🏦 現在の残高",
        value=f"{money[user_id]}円",
        inline=False
    )

    await ctx.send(embed=embed)

@bot.command()
async def pay(ctx, member: discord.Member, amount: int):
    sender_id = str(ctx.author.id)
    receiver_id = str(member.id)

    if amount <= 0:
        await ctx.send("1円以上を指定してね")
        return

    if sender_id not in money:
        money[sender_id] = 0

    if receiver_id not in money:
        money[receiver_id] = 0

    if money[sender_id] < amount:
        await ctx.send("残高が足りないよ")
        return

    money[sender_id] -= amount
    money[receiver_id] += amount
    clamp_money(sender_id)
    clamp_money(receiver_id)
    save_money()

    await ctx.send(
        f"{ctx.author.display_name} から {member.display_name} に {amount}円送金しました！"
    )    
@bot.command()
async def rank(ctx):
    if not money:
        await ctx.send("まだ誰もお金を持っていません")
        return

    ranking = sorted(money.items(), key=lambda x: x[1], reverse=True)

    embed = discord.Embed(
        title="🏆 所持金ランキング",
        description="上位5名を表示します",
        color=discord.Color.gold()
    )

    for i, (user_id, amount) in enumerate(ranking[:5], start=1):
        user = await bot.fetch_user(int(user_id))
        embed.add_field(
            name=f"{i}位",
            value=f"{user.display_name}：{amount}円",
            inline=False
        )

    await ctx.send(embed=embed)

@bot.command()
async def gacha(ctx):
    user_id = str(ctx.author.id)

    if user_id not in money:
        money[user_id] = 0

    cost = 100

    if money[user_id] < cost:
        await ctx.send("ガチャを引くには100円必要です")
        return

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
    clamp_money(user_id)
    save_money()

    embed = discord.Embed(
        title="🎲 ガチャ結果",
        description=f"{ctx.author.display_name} がガチャを引きました！",
        color=discord.Color.purple()
    )

    embed.add_field(
        name="結果",
        value=result_name,
        inline=False
    )

    embed.add_field(
        name="獲得金額",
        value=f"{reward}円",
        inline=True
    )

    embed.add_field(
        name="現在の残高",
        value=f"{money[user_id]}円",
        inline=True
    )

    await ctx.send(embed=embed)

# ショップを表示するコマンド
@bot.command()
async def shop(ctx):
    embed = discord.Embed(
        title="🛒 ショップ",
        description="購入できるアイテム一覧",
        color=discord.Color.blue()
    )

    for item_id, item in SHOP_ITEMS.items():
        embed.add_field(
            name=f"{item['name']}",
            value=f"ID: `{item_id}` / 価格: {item['price']}円",
            inline=False
        )

    embed.set_footer(text="購入方法: !buy アイテムID")

    await ctx.send(embed=embed)

# アイテムを購入するコマンド
@bot.command()
async def buy(ctx, item_id: str):
    user_id = str(ctx.author.id)

    if item_id not in SHOP_ITEMS:
        await ctx.send("そのアイテムは存在しません。`!shop` で確認してね。")
        return

    if user_id not in money:
        money[user_id] = 0

    item = SHOP_ITEMS[item_id]
    price = item["price"]

    if money[user_id] < price:
        await ctx.send("残高が足りません。")
        return

    money[user_id] -= price
    clamp_money(user_id)
    save_money()

    # アイテム追加
    if user_id not in inventory:
        inventory[user_id] = {}

    if item_id not in inventory[user_id]:
        inventory[user_id][item_id] = 0

    inventory[user_id][item_id] += 1
    save_inventory()

    embed = discord.Embed(
        title="🛍️ 購入完了",
        description=f"{ctx.author.display_name} が {item['name']} を購入しました！",
        color=discord.Color.green()
    )

    embed.add_field(
        name="支払金額",
        value=f"{price}円",
        inline=True
    )

    embed.add_field(
        name="残高",
        value=f"{money[user_id]}円",
        inline=True
    )

    await ctx.send(embed=embed)

# 所持アイテムを確認するコマンド
@bot.command(name="inventory")
async def inventory_cmd(ctx):
    user_id = str(ctx.author.id)

    if user_id not in inventory or not inventory[user_id]:
        await ctx.send("何も持っていません。")
        return

    embed = discord.Embed(
        title="🎒 所持アイテム",
        description=f"{ctx.author.display_name} のアイテム一覧",
        color=discord.Color.blue()
    )

    for item_id, count in inventory[user_id].items():
        item_name = SHOP_ITEMS[item_id]["name"]
        embed.add_field(
            name=item_name,
            value=f"{count}個",
            inline=False
        )

    await ctx.send(embed=embed) 

# アイテムを使用するコマンド
@bot.command()
async def use(ctx, item_id: str):
    user_id = str(ctx.author.id)

    if user_id not in inventory or item_id not in inventory[user_id] or inventory[user_id][item_id] <= 0:
        await ctx.send("そのアイテムを持っていません。")
        return

    if item_id == "coffee":
        inventory[user_id][item_id] -= 1
        money[user_id] += 50
        clamp_money(user_id)

        save_inventory()
        save_money()

        await ctx.send(f"☕ コーヒーを使いました！50円回復。現在の残高: {money[user_id]}円")

    elif item_id == "ticket":
        inventory[user_id][item_id] -= 1

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
        clamp_money(user_id)

        save_inventory()
        save_money()

        await ctx.send(
            f"🎫 ガチャチケットを使いました！\n"
            f"結果: {result_name}\n"
            f"獲得: {reward}円\n"
            f"現在の残高: {money[user_id]}円"
        )

    elif item_id == "crown":
        await ctx.send("👑 王冠は使用できません。持っているだけで名誉です。")

    else:
        await ctx.send("そのアイテムは使用できません。")
# これより上に !コマンド を追加していきます


# /balance コマンドを追加
@bot.tree.command(
    name="balance",
    description="残高を確認します",
    guild=discord.Object(id=GUILD_ID)
)
async def slash_balance(interaction: discord.Interaction):
    user_id = str(interaction.user.id)

    if user_id not in money:
        money[user_id] = 0
        save_money()

    embed = create_balance_embed(interaction.user, money[user_id])

    await interaction.response.send_message(embed=embed, ephemeral=True)
    
# /menuコマンド を追加していきます
@bot.tree.command(name="menu", description="操作メニューを表示します")
async def menu(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📋 メニュー",
        description="ボタンから操作できます",
        color=discord.Color.blue()
    )

    await interaction.response.send_message(
        embed=embed,
        view=MenuView(),
        ephemeral=True 
    )

# /work コマンドを追加
@bot.tree.command(
    name="work",
    description="1日1回ログインボーナスを受け取ります",
    guild=discord.Object(id=GUILD_ID)
)

async def slash_work(interaction: discord.Interaction):
    user_id = str(interaction.user.id)

    success, balance = do_work(user_id)

    if not success:
        await interaction.response.send_message(
            "今日はもう働いてるよ！また明日ね。",
            ephemeral=True
        )
        return

    embed = discord.Embed(
        title="💼 お仕事完了！",
        description=f"{interaction.user.display_name} が働きました",
        color=discord.Color.green()
    )

    embed.add_field(name="💰 獲得金額", value="100円", inline=False)
    embed.add_field(name="🏦 現在の残高", value=f"{balance}円", inline=False)

    await interaction.response.send_message(embed=embed, ephemeral=True)

# /gacha コマンドを追加
@bot.tree.command(
    name="gacha",
    description="100円でガチャを引きます",
    guild=discord.Object(id=GUILD_ID)
)
async def slash_gacha(interaction: discord.Interaction):
    user_id = str(interaction.user.id)

    success, result_name, reward, balance = do_gacha(user_id)

    if not success:
        await interaction.response.send_message(
            "ガチャを引くには100円必要です",
            ephemeral=True
        )
        return

    embed = create_gacha_embed(interaction.user, result_name, reward, balance)

    await interaction.response.send_message(embed=embed, ephemeral=True)

# /buy コマンドを追加
@bot.tree.command(
    name="buy",
    description="アイテムを購入します",
    guild=discord.Object(id=GUILD_ID)
)
async def slash_buy(interaction: discord.Interaction, item_id: str):
    user_id = str(interaction.user.id)

    success, result, balance = do_buy(user_id, item_id)

    if not success:
        await interaction.response.send_message(result, ephemeral=True)
        return

    embed = create_buy_embed(interaction.user, result, balance)

    await interaction.response.send_message(embed=embed, ephemeral=True)


# ここから下に エラーハンドリング を追加していきます
# これより上に エラーハンドリング を追加していきます

bot.run(TOKEN)



"""
/menuコマンド の確認

ボタン増やす👇
残高 / work / ガチャ
"""

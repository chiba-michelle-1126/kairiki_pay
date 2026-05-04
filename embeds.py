# ===== Imports / ライブラリ =====
import discord

# ===== embeds / 埋め込み =====
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

# アイテム購入のEmbedを作る関数
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

# アイテム使用のEmbedを作る
def create_use_embed(user, result_text, data):
    embed = discord.Embed(
        title="🎁 アイテム使用",
        description=f"{user.display_name} がアイテムを使用しました",
        color=discord.Color.orange()
    )

    embed.add_field(name="結果", value=result_text, inline=False)

    if data["reward"] != 0:
        embed.add_field(name="獲得金額", value=f"{data['reward']}円", inline=True)

    embed.add_field(name="現在の残高", value=f"{data['balance']}円", inline=True)

    return embed

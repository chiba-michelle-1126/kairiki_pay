# ===== Imports / ライブラリ =====
import discord

from logic import do_use
from embeds import create_use_embed

# ===== Views / ビュー =====

class UseView(discord.ui.View):
    def __init__(self, user_id, money, inventory):
        super().__init__()
        self.user_id = user_id
        self.money = money
        self.inventory = inventory

    @discord.ui.button(label="☕ コーヒーを使う", style=discord.ButtonStyle.primary)
    async def use_coffee(self, interaction: discord.Interaction, button: discord.ui.Button):
        success, result_text, data = do_use(self.user_id, "coffee", self.money, self.inventory)
        
        if not success:
            await interaction.response.send_message(result_text, ephemeral=True)
            return

        if data["reward"] != 0:
            add_money_log(
                user_id=self.user_id,
                action="use:coffee",
                amount=data["reward"],
                balance_after=data["balance"]
            )

        embed = create_use_embed(interaction.user, result_text, data)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="🎫 チケットを使う", style=discord.ButtonStyle.primary)
    async def use_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        success, result_text, data = do_use(self.user_id, "ticket", money, inventory)

        if not success:
            await interaction.response.send_message(result_text, ephemeral=True)
            return

        embed = create_use_embed(interaction.user, result_text, data)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="👑 王冠を使う", style=discord.ButtonStyle.primary)
    async def use_crown(self, interaction: discord.Interaction, button: discord.ui.Button):
        success, result_text, data = do_use(self.user_id, "crown", money, inventory)

        if not success:
            await interaction.response.send_message(result_text, ephemeral=True)
            return

        embed = create_use_embed(interaction.user, result_text, data)
        await interaction.response.send_message(embed=embed, ephemeral=True)
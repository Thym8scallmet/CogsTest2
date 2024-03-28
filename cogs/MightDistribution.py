import json
from typing import List

import discord
from discord import app_commands
from discord.ext import commands


class MightDistribution(commands.Cog):
  def __init__(self, client: commands.Bot):
      self.client = client

  async def load_player_data(self) -> List[dict]:
      with open('playerlist.json', 'r', encoding='utf-8') as file:
          data = json.load(file)
      return sorted(data, key=lambda x: x['might'], reverse=True)

  async def prepare_embed(self) -> discord.Embed:
    players = await self.load_player_data()

    # Allocate players to lanes to achieve a balanced might distribution
    lane1, lane2 = [], []
    lane3 = players[40:]  # Remaining players go here
    top_40_players = players[:40]

    lane1_might, lane2_might = 0, 0

    for player in top_40_players:
        # Place the player in the lane with the lesser total might
        if lane1_might <= lane2_might:
            lane1.append(player)
            lane1_might += player['might']
        else:
            lane2.append(player)
            lane2_might += player['might']
    lane3_might = sum(player['might'] for player in lane3)

    embed = discord.Embed(title="Player Might Distribution", description="Players are divided into three lanes based on balanced might distribution.", color=0x00ff00)

    for index, (lane, total_might) in enumerate(zip([lane1, lane2, lane3], [lane1_might, lane2_might, lane3_might]), start=1):
        lane_description = '\n'.join([f"{idx + 1}. {player['name']}: {player['might']}" for idx, player in enumerate(lane)])
        lane_description += f"\n**Total Might**: {total_might}"
        embed.add_field(name=f"Lane {index}", value=lane_description, inline=False)

    return embed

  @app_commands.command(name="might_distribution", description="Distributes the might of the players")
  async def might_distribution(self, interaction: discord.Interaction):
      embed = await self.prepare_embed()
      await interaction.response.send_message(embed=embed)

async def setup(client:commands.Bot) -> None:
  await client.add_cog(MightDistribution(client))
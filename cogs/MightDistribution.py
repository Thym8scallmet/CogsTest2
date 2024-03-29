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
      return sorted(data, key=lambda x: x.get('might', 0), reverse=True)

  async def save_player_data(self, players: List[dict]) -> None:
    with open('playerlist.json', 'w', encoding='utf-8') as file:
      json.dump(players, file, indent=4)
   
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

    embed = discord.Embed(
        title="Flag Capture Lane Setup",
        description=
        "Players are divided into three lanes based on balanced might distribution.",
        color=0x00ff00)

    for index, (lane, total_might) in enumerate(zip(
        [lane1, lane2, lane3], [lane1_might, lane2_might, lane3_might]),
                                                start=1):
      lane_description = '\n'.join([
          f"{idx + 1}. {player['name']}: {player['might']:,}"
          for idx, player in enumerate(lane)
      ])
      lane_description += f"\n**Total Might**: {total_might:,}"
      embed.add_field(name=f"Lane {index}",
                      value=lane_description,
                      inline=False)

    return embed

  @app_commands.command(name="might_distribution",
                        description="Distributes the might of the players")
  async def might_distribution(self, interaction: discord.Interaction):
    embed = await self.prepare_embed()
    await interaction.response.send_message(embed=embed)

  @app_commands.command(name="display_players", description="Displays all the players and their might.")
  async def display_players(self, interaction: discord.Interaction):
      players = await self.load_player_data()
      embed = discord.Embed(title="Players List", color=0x00ff00)
      display_text = '\n'.join(f"{player['name']}: {player['might']}" for player in players)
      embed.description = display_text
      await interaction.response.send_message(embed=embed, ephemeral=True)  
  
  @app_commands.command(
      name="add_player",
      description="Add a new player with Flag Capture march might.")
  async def add_player(self, interaction: discord.Interaction, name: str,
                       might: int):
    players = await self.load_player_data()
    players.append({"name": name, "might": might})
    await self.save_player_data(players)
    await interaction.response.send_message(
        f"Added player {name} with might {might}.")    

  # Autocomplete callback function
  async def player_name_autocomplete(self, interaction: discord.Interaction, current: str):
    players = await self.load_player_data()
    return [
        app_commands.Choice(name=player['name'], value=player['name'])
        for player in players if current.lower() in player['name'].lower()
    ][:25]  # Limit to 25 entries

  @app_commands.command(name="remove_player", description="Remove a player by their name.")
  @app_commands.autocomplete(name=player_name_autocomplete)  # Linking autocomplete to the 'name' parameter
  async def remove_player(self, interaction: discord.Interaction, name: str):
      players = await self.load_player_data()
      players = [player for player in players if player['name'] != name]
      await self.save_player_data(players)
      await interaction.response.send_message(f"Removed player {name}.")

  @app_commands.command(name="adjust_might", description="Adjust the might of a player.")
  @app_commands.autocomplete(name=player_name_autocomplete)  # Linking autocomplete to the 'name' parameter
  async def adjust_might(self, interaction: discord.Interaction, name: str, new_might: int):
    players = await self.load_player_data()
    for player in players:
      if player['name'] == name:
        player['might'] = new_might
        await self.save_player_data(players)
        await interaction.response.send_message(f"Updated {name}'s might to {new_might}.")
        return
    await interaction.response.send_message(f"Player {name} not found.")

async def setup(client: commands.Bot) -> None:
  await client.add_cog(MightDistribution(client))
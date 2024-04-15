import json
import os
import uuid

import deepl
import discord
from discord import app_commands
from discord.ext import commands


class TranslationJobRemovalSelect(discord.ui.Select):

  def __init__(self, translation_mapping, client=None, **kwargs):
    super().__init__(**kwargs)
    if client is None:
      raise ValueError("Client parameter must not be None")
    self.client = client
    self.translation_mapping = translation_mapping
    options = []
    for job_id, job_details in translation_mapping.items():
      source_channel_id = job_details["source_channel"]
      for target_channel_id, target_language in job_details["target_channels"]:
        source_channel = self.client.get_channel(int(source_channel_id))
        target_channel = self.client.get_channel(int(target_channel_id))
        if source_channel and target_channel:
          label = f"{source_channel.name} to {target_channel.name} ({target_language})"
          options.append(
              discord.SelectOption(
                  label=label,
                  description=
                  f"From {source_channel.name} to {target_channel.name}",
                  value=job_id))
    self.placeholder = 'Choose a translation job to remove...'
    self.options = options

  async def callback(self, interaction: discord.Interaction):
    job_id = self.values[0]
    job_details = self.translation_mapping.pop(job_id, None)
    if job_details:
      source_channel = self.client.get_channel(
          int(job_details["source_channel"]))
      target_channels_info = ", ".join([
          self.client.get_channel(int(target[0])).name
          for target in job_details["target_channels"]
      ])
      if source_channel:
        cog = interaction.client.get_cog('AutoTranslate')
        if cog:
          cog.save_translation_jobs()
        await interaction.response.send_message(
            f"Removed translation job: From {source_channel.name} to {target_channels_info}.",
            ephemeral=True)
      else:
        await interaction.response.send_message(
            "Failed to remove the selected translation job.", ephemeral=True)
    else:
      await interaction.response.send_message(
          "Failed to remove the selected translation job.", ephemeral=True)


class TranslationJobRemovalView(discord.ui.View):

  def __init__(self, client, translation_mapping, *args, **kwargs):
    super().__init__(*args, **kwargs)  # Correctly call the superclass __init__
    self.add_item(TranslationJobRemovalSelect(translation_mapping, client))


class AutoTranslate(commands.Cog):

  def __init__(self, client: commands.Bot):
    self.client = client
    deepl_key = os.getenv("DEEPLKEY")
    if deepl_key is None:
      raise ValueError("DEEPLKEY environment variable is not set")
    self.translator = deepl.Translator(deepl_key)
    self.language_dict = self.load_language_dict()
    self.translation_mapping = self.load_translation_jobs()
    self.allowed_guild_ids = {1045479020940234783,
                              383365467894710272}  # Add your guild IDs here

  def guild_check(self, interaction: discord.Interaction):
    return interaction.guild_id and interaction.guild_id in self.allowed_guild_ids

  def load_language_dict(self):
    try:
      with open('cogs/cogfiles/LanguageDict.json', 'r') as lang_file:
        return json.load(lang_file)
    except Exception as e:
      print(f"Failed to load language dictionary: {e}")
      return {}

  def load_translation_jobs(self):
    translate_jobs_path = 'cogs/cogfiles/TranslateJobs.json'
    if not os.path.exists(translate_jobs_path):
      with open(translate_jobs_path, 'w') as jobs_file:
        json.dump({}, jobs_file)
      print(
          "TranslateJobs.json did not exist and was created with an empty dictionary."
      )
      return {}

    try:
      with open(translate_jobs_path, 'r') as jobs_file:
        return json.load(jobs_file)
    except json.JSONDecodeError:
      with open(translate_jobs_path, 'w') as jobs_file:
        json.dump({}, jobs_file)
      print(
          "TranslateJobs.json contains invalid JSON. Initializing with an empty dictionary."
      )
      return {}
    except Exception as e:
      print(f"Failed to load translation jobs: {e}")
      return {}

  def save_translation_jobs(self):
    try:
      with open('cogs/cogfiles/TranslateJobs.json', 'w') as jobs_file:
        json.dump(self.translation_mapping, jobs_file, indent=4)
    except Exception as e:
      print(f"Failed to save translation jobs: {e}")

  @commands.Cog.listener()
  async def on_message(self, message):
    if message.author.bot or not message.guild or message.guild.id not in self.allowed_guild_ids:
      return

    for job_id, job_details in self.translation_mapping.items():
      source_channel_id = job_details["source_channel"]
      if str(message.channel.id) == source_channel_id:
        for target_channel_id, target_language_code in job_details[
            "target_channels"]:
          target_channel = self.client.get_channel(int(target_channel_id))
          if target_channel:
            try:
              result = self.translator.translate_text(
                  text=message.content, target_lang=target_language_code)
              translated_text = result.text
              embed = discord.Embed(
                  title=f"Message from {message.author.display_name}",
                  description=translated_text,
                  color=0x3498db)
              # Optionally, you can add footer, timestamp or any other info to embed.
              embed.set_footer(text=f"Translated to {target_language_code}")
              embed.timestamp = message.created_at
              # Send embed
              await target_channel.send(embed=embed)
            except Exception as e:
              print(f"Error during translation: {e}")

  async def target_language_autocomplete(
      self, interaction: discord.Interaction,
      current: str) -> list[app_commands.Choice[str]]:
    return [
        app_commands.Choice(name=lang, value=code)
        for lang, code in self.language_dict.items()
        if current.lower() in lang.lower()
    ][:25]

  @app_commands.command(
      name="set_channel_translation",
      description=
      "Set a source channel, a target channel, and the target language for automatic translation."
  )
  @app_commands.describe(
      source_channel="The channel to be translated from.",
      target_channel="The channel to post translated messages to.")
  @app_commands.autocomplete(target_language=target_language_autocomplete)
  async def set_translate(self, interaction: discord.Interaction,
                          source_channel: discord.TextChannel,
                          target_channel: discord.TextChannel,
                          target_language: str):
    if not self.guild_check(interaction):
      await interaction.response.send_message(
          "Your server does not have access to this feature.", ephemeral=True)
      return

    if source_channel.id == target_channel.id:
      await interaction.response.send_message(
          "Source and target channels must be different.", ephemeral=True)
      return

    if target_language not in self.language_dict.values():
      await interaction.response.send_message(
          "The specified language is not supported.", ephemeral=True)
      return

    job_id = str(uuid.uuid4())
    job_details = {
        "source_channel": str(source_channel.id),
        "target_channels": [(str(target_channel.id), target_language)]
    }

    self.translation_mapping[job_id] = job_details
    self.save_translation_jobs()

    await interaction.response.send_message(
        f"Set translations from {source_channel.mention} to {target_channel.mention} in the specified language.",
        ephemeral=True)

  @app_commands.command(name="remove_translation_job",
                        description="Remove a translation job.")
  async def remove_translate(self, interaction: discord.Interaction):
    if not self.guild_check(interaction):
      await interaction.response.send_message(
          "Your server does not have access to this feature.", ephemeral=True)
      return

    if not self.translation_mapping:
      await interaction.response.send_message("No translation jobs to remove.",
                                              ephemeral=True)
      return

    view = TranslationJobRemovalView(self.client, self.translation_mapping)
    await interaction.response.send_message(
        "Select the translation job you wish to remove:",
        view=view,
        ephemeral=True)


async def setup(client):
  await client.add_cog(AutoTranslate(client))

from typing import List
import discord

from BotSettings import BotSettings
from MaraBot import MaraBot

class BeansGambaSettingsModal(discord.ui.Modal, title='Beans Settings'):
    beans_gamba_cost = discord.ui.TextInput(label='', required=False, custom_id=BotSettings.BEANS_GAMBA_DEFAULT)
    beans_gamba_min = discord.ui.TextInput(label='', required=False, custom_id=BotSettings.BEANS_GAMBA_MIN)
    beans_gamba_max = discord.ui.TextInput(label='', required=False, custom_id=BotSettings.BEANS_GAMBA_MAX)
    beans_gamba_cooldown = discord.ui.TextInput(label='', required=False, custom_id=BotSettings.BEANS_GAMBA_COOLDOWN)

    def __init__(self, bot: MaraBot, settings: BotSettings):
        super().__init__()
        
        self.settings = settings
        self.bot = bot
        self.command = 'beans gamba setup'
        
        self.beans_gamba_cost.label = self.settings.get_setting_title(BotSettings.BEANS_SUBSETTINGS_KEY, BotSettings.BEANS_GAMBA_DEFAULT)
        self.beans_gamba_cooldown.label = self.settings.get_setting_title(BotSettings.BEANS_SUBSETTINGS_KEY, BotSettings.BEANS_GAMBA_COOLDOWN)
        self.beans_gamba_max.label = self.settings.get_setting_title(BotSettings.BEANS_SUBSETTINGS_KEY, BotSettings.BEANS_GAMBA_MAX)
        self.beans_gamba_min.label = self.settings.get_setting_title(BotSettings.BEANS_SUBSETTINGS_KEY, BotSettings.BEANS_GAMBA_MIN)
    
    async def on_submit(self, interaction: discord.Interaction):
        text_inputs = [
            self.beans_gamba_cost,
            self.beans_gamba_cooldown,
            self.beans_gamba_max,
            self.beans_gamba_min
        ]
        errors: List[discord.ui.TextInput] = []
        
        for text_input in text_inputs:
            if not text_input.value.lstrip('-').isdigit():
                errors.append(text_input)
                
        if len(errors) != 0:
            message = f'Illegal values:\n{', \n'.join([f'{text_input.label}({text_input.value})' for text_input in errors])}'
            await self.bot.response('Beans', interaction, message, self.command, args=[text_input.label for text_input in text_inputs])
            return
            
        self.settings.set_beans_gamba_cost(interaction.guild_id, int(self.beans_gamba_cost.value))
        self.settings.set_beans_gamba_cooldown(interaction.guild_id, int(self.beans_gamba_cooldown.value))
        self.settings.set_beans_gamba_max(interaction.guild_id, int(self.beans_gamba_max.value))
        self.settings.set_beans_gamba_min(interaction.guild_id, int(self.beans_gamba_min.value))
        
        await self.bot.response('Beans', interaction, f'Settings were successfully updated.', self.command, args=[text_input.value for text_input in text_inputs])
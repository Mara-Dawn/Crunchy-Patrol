import discord

from BotUtil import BotUtil
from MaraBot import MaraBot
from datalayer.UserRankings import UserRankings
from view.RankingType import RankingType

class ShopEmbed(discord.Embed):
    
    TITLES = {
        RankingType.SLAP: "Slap Rankings",
        RankingType.PET: "Pet Rankings",
        RankingType.FART: "Fart Rankings",
        RankingType.SLAP_RECIEVED: "Slaps Recieved Rankings",
        RankingType.PET_RECIEVED: "Pets Recieved  Rankings",
        RankingType.FART_RECIEVED: "Farts Recieved  Rankings",
        RankingType.TIMEOUT_TOTAL: "Total Timeout Duration Rankings",
        RankingType.TIMEOUT_COUNT: "Timeout Count Rankings",
        RankingType.JAIL_TOTAL: "Total Jail Duration Rankings",
        RankingType.JAIL_COUNT: "Jail Count Rankings",
        RankingType.SPAM_SCORE: "Spam Score Rankings",
    }
    
    def __init__(self, bot: MaraBot,  interaction: discord.Interaction):
        super().__init__(
            title=f"Beans Shop for {interaction.guild.name}",
            color=discord.Colour.purple(),
            description='Spend your hard earned beans here!'
        )
        
        # leaderbord_msg = ''
        # data = user_rankings.get_rankings(type)
        # rank = 1
        # for (id, amount) in data:
        #     leaderbord_msg += f'**{rank}.** {BotUtil.get_name(bot, interaction.guild_id, id, 100)} `{amount}`\n'
        #     rank += 1
        #     if rank == 30:
        #         break
        
        self.add_field(name="Test", value='asdf')
        self.set_image(url="attachment://jail_wide.png")
        self.set_author(name="Crunchy Patrol", icon_url="attachment://police.png")
from typing import Any

import discord

from datalayer.ranking import Ranking
from view.types import RankingType


class RankingEmbed(discord.Embed):

    def __init__(
        self,
        interaction: discord.Interaction,
        ranking_type: RankingType,
        rankings: dict[str, Any],
    ):
        super().__init__(
            title=f"Leaderbords for {interaction.guild.name}",
            color=discord.Colour.purple(),
            description=Ranking.DEFINITIONS[ranking_type].description,
        )

        leaderbord_msg = ""
        rank = 1
        for user_name, amount in rankings.items():
            leaderbord_msg += f"**{rank}.** {user_name} `{amount}`\n"
            rank += 1
            if rank == 30:
                break

        self.add_field(name="", value=leaderbord_msg)
        self.set_image(url="attachment://ranking_img.png")
        self.set_author(name="Crunchy Patrol", icon_url="attachment://police.png")
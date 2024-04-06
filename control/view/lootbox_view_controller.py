import datetime
import discord
from control.view import ViewController
from events import (
    BeansEvent,
    BotEvent,
    InventoryEvent,
    LootBoxEvent,
    UIEvent,
)
from events.types import BeansEventType, LootBoxEventType, UIEventType
from items.types import ItemType
from view import ViewMenu


class LootBoxViewController(ViewController):

    async def listen_for_event(self, event: BotEvent):
        pass

    async def handle_lootbox_claim(
        self, interaction: discord.Interaction, view: ViewMenu, owner_id: int = None
    ):
        await interaction.response.defer()

        guild_id = interaction.guild_id
        member_id = interaction.user.id

        stun_base_duration = self.item_manager.get_item(
            guild_id, ItemType.BAT
        ).get_value()
        stunned_remaining = self.event_manager.get_stunned_remaining(
            guild_id, interaction.user.id, stun_base_duration
        )

        if stunned_remaining > 0:
            timestamp_now = int(datetime.datetime.now().timestamp())
            remaining = int(timestamp_now + stunned_remaining)
            await interaction.followup.send(
                f"You are currently stunned from a bat attack. Try again <t:{remaining}:R>",
                ephemeral=True,
            )
            return

        if owner_id is not None and member_id != owner_id:
            await interaction.followup.send(
                "This is a personalized lootbox, only the owner can claim it.",
                ephemeral=True,
            )
            return

        view.stop()

        message = await interaction.original_response()
        loot_box = self.database.get_loot_box_by_message_id(guild_id, message.id)

        title = "A Random Treasure has Appeared"
        if owner_id is not None:
            title = f"{interaction.user.display_name}'s Random Treasure Chest"

        description = f"This treasure was claimed by: \n <@{member_id}>"
        description += "\n\nThey slowly open the chest and reveal..."
        embed = discord.Embed(
            title=title, description=description, color=discord.Colour.purple()
        )

        beans = loot_box.get_beans()

        if beans < 0:
            bean_balance = self.database.get_member_beans(guild_id, interaction.user.id)
            if bean_balance + beans < 0:
                beans = -bean_balance

            embed.add_field(
                name="Oh no, it's a Mimic!",
                value=f"It munches away at your beans, eating `🅱️{abs(beans)}` of them.",
                inline=False,
            )
            embed.set_image(url="attachment://mimic.gif")
            attachment = discord.File("./img/mimic.gif", "mimic.gif")
        else:
            embed.add_field(
                name="A Bunch of Beans!",
                value=f"A whole  `🅱️{beans}` of them.",
                inline=False,
            )
            embed.set_image(url="attachment://treasure_open.png")
            attachment = discord.File("./img/treasure_open.png", "treasure_open.png")

        log_message = f"{interaction.user.display_name} claimed a loot box containing {beans} beans"

        if loot_box.get_item_type() is not None:
            embed.add_field(name="Woah, a Shiny Item!", value="", inline=False)

            item = self.item_manager.get_item(guild_id, loot_box.get_item_type())

            item.add_to_embed(embed, 33, count=item.get_base_amount())

            log_message += f" and 1x {item.get_name()}"

            event = InventoryEvent(
                datetime.datetime.now(),
                guild_id,
                member_id,
                loot_box.get_item_type(),
                0,
                item.get_base_amount(),
            )
            await self.controller.dispatch_event(event)

        event = BeansEvent(
            datetime.datetime.now(),
            guild_id,
            BeansEventType.LOOTBOX_PAYOUT,
            member_id,
            beans,
        )
        await self.controller.dispatch_event(event)

        event_type = LootBoxEventType.CLAIM
        if owner_id is not None:
            event_type = LootBoxEventType.OPEN

        event = LootBoxEvent(
            datetime.datetime.now(), guild_id, loot_box.get_id(), member_id, event_type
        )
        await self.controller.dispatch_event(event)

        self.logger.log(interaction.guild_id, log_message, cog="Beans")

        await interaction.edit_original_response(
            embed=embed, view=None, attachments=[attachment]
        )

        if owner_id is not None:
            new_user_balance = self.database.get_member_beans(guild_id, member_id)

            event = UIEvent(
                guild_id, member_id, UIEventType.REFRESH_SHOP, new_user_balance
            )
            await self.controller.dispatch_ui_event(event)

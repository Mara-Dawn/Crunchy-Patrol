import asyncio
import copy

import discord
from combat.actors import Actor
from combat.encounter import Encounter, EncounterContext, TurnData
from combat.skills.skill import Skill
from combat.skills.types import DamageInstance, SkillEffect
from control.combat.combat_actor_manager import CombatActorManager
from control.combat.combat_enemy_manager import CombatEnemyManager
from control.controller import Controller
from control.logger import BotLogger
from control.service import Service
from datalayer.database import Database
from discord.ext import commands
from events.bot_event import BotEvent


class CombatEmbedManager(Service):

    def __init__(
        self,
        bot: commands.Bot,
        logger: BotLogger,
        database: Database,
        controller: Controller,
    ):
        super().__init__(bot, logger, database)
        self.controller = controller
        self.enemy_manager: CombatEnemyManager = self.controller.get_service(
            CombatEnemyManager
        )
        self.actor_manager: CombatActorManager = self.controller.get_service(
            CombatActorManager
        )
        self.log_name = "Combat Embeds"

    async def listen_for_event(self, event: BotEvent):
        pass

    def get_spawn_embed(
        self, encounter: Encounter, show_info: bool = False
    ) -> discord.Embed:
        enemy = self.enemy_manager.get_enemy(encounter.enemy_type)
        title = "A random Enemy appeared!"

        embed = discord.Embed(title=title, color=discord.Colour.purple())

        enemy_name = f"> ~* Lvl. {encounter.enemy_level} - {enemy.name} *~"
        content = f'```python\n"{enemy.description}"```'
        embed.add_field(name=enemy_name, value=content, inline=False)

        if show_info:
            enemy_info = f"```ansi\n[37m{enemy.information}```"
            embed.add_field(name="", value=enemy_info, inline=False)
            return embed

        embed.set_image(url=f"attachment://{enemy.image}")

        return embed

    def add_health_bar(
        self,
        embed: discord.Embed,
        current_hp: int,
        max_hp: int,
        hide_hp: bool = True,
        max_width: int = 44,
    ):
        health = f"{current_hp}/{max_hp}"
        fraction = current_hp / max_hp
        percentage = f"{round(fraction * 100, 1)}".rstrip("0").rstrip(".")

        bar_start = "|"
        bar_end = f"| {percentage}%"

        bar_length = max_width - len(bar_start) - len(bar_end)

        missing_health_length = int(bar_length * (1 - fraction))
        health_length = bar_length - missing_health_length

        missing_health_bar = " " * missing_health_length
        health_bar = "█" * health_length

        content = "```" + bar_start + health_bar + missing_health_bar + bar_end + "```"

        title = "Health:"
        if not hide_hp:
            title += f" {health}"

        embed.add_field(name=title, value=content)

    def add_text_bar(
        self,
        embed: discord.Embed,
        name: str,
        value: str,
        max_width: int = 45,
    ):
        spacing = ""
        content_length = len(value)
        if content_length < max_width:
            spacing = " " * (max_width - content_length)

        embed_content = "```\n" + value + spacing + "```"
        embed.add_field(name=name, value=embed_content, inline=False)

    async def get_combat_embed(self, context: EncounterContext) -> discord.Embed:
        enemy = context.opponent.enemy

        title = f"> ~* Lvl. {context.opponent.level} - {enemy.name} *~"
        content = f'```python\n"{enemy.description}"```'
        embed = discord.Embed(
            title=title, description=content, color=discord.Colour.red()
        )

        current_hp = await self.actor_manager.get_actor_current_hp(
            context.opponent, context.combat_events
        )
        max_hp = context.opponent.max_hp
        self.add_health_bar(embed, current_hp, max_hp, max_width=38)

        skill_list = []
        for skill in enemy.skills:
            skill_list.append(skill.name)

        self.add_text_bar(
            embed, name="Skills:", value=", ".join(skill_list), max_width=38
        )

        if enemy.information != "":
            self.add_text_bar(
                embed,
                name="Additional Information:",
                value=enemy.information,
                max_width=38,
            )

        embed.set_image(url=f"attachment://{enemy.image}")

        return embed

    async def get_combat_success_embed(
        self, context: EncounterContext
    ) -> discord.Embed:
        enemy = context.opponent.enemy

        title = f"> ~* Lvl. {context.opponent.level} - {enemy.name} *~"
        content = f'```python\n"{enemy.description}"```'
        embed = discord.Embed(
            title=title, description=content, color=discord.Colour.green()
        )

        current_hp = await self.actor_manager.get_actor_current_hp(
            context.opponent, context.combat_events
        )
        max_hp = context.opponent.max_hp
        self.add_health_bar(embed, current_hp, max_hp, max_width=38)

        defeated_message = f"You successfully defeated *{enemy.name}*."
        embed.add_field(name="Congratulations!", value=defeated_message, inline=False)

        embed.set_image(url=f"attachment://{enemy.image}")

        return embed

    async def get_combat_failed_embed(self, context: EncounterContext) -> discord.Embed:
        enemy = context.opponent.enemy

        title = f"> ~* Lvl. {context.opponent.level} - {enemy.name} *~"
        content = f'```python\n"{enemy.description}"```'
        embed = discord.Embed(
            title=title, description=content, color=discord.Colour.red()
        )

        current_hp = await self.actor_manager.get_actor_current_hp(
            context.opponent, context.combat_events
        )
        max_hp = context.opponent.max_hp
        self.add_health_bar(embed, current_hp, max_hp, max_width=38)

        defeated_message = f"You were defeated by *{enemy.name}*."
        embed.add_field(name="Failure!", value=defeated_message, inline=False)

        embed.set_image(url=f"attachment://{enemy.image}")

        return embed

    async def get_character_turn_embed(
        self, context: EncounterContext
    ) -> discord.Embed:
        actor = context.get_current_actor()

        turn_number = context.get_current_turn_number()
        title = f"Turn {turn_number}: {actor.name}"

        content = f"It is your turn <@{actor.id}>. Please select an action."
        embed = discord.Embed(
            title=title, description=content, color=discord.Colour.blurple()
        )

        current_hp = await self.actor_manager.get_actor_current_hp(
            actor, context.combat_events
        )
        max_hp = int(actor.max_hp)
        self.add_health_bar(embed, current_hp, max_hp, hide_hp=False)

        embed.add_field(name="Your Skills:", value="", inline=False)

        for skill in actor.skills:
            actor.get_skill_data(skill).add_to_embed(embed=embed, show_data=True)

        if actor.image is not None:
            embed.set_thumbnail(url=actor.image)

        return embed

    async def get_loot_embed(self, member: discord.Member, beans: int):
        title = f"{member.display_name}'s Loot"
        embed = discord.Embed(title=title, color=discord.Colour.green())
        message = f"You gain 🅱️{beans} beans and the following items:"
        self.add_text_bar(embed, "", message)
        embed.set_thumbnail(url=member.display_avatar.url)
        return embed

    async def get_embed_attack_data(
        self,
        current_actor: Actor,
        target: Actor,
        skill: Skill,
        damage_instance: DamageInstance,
    ):
        outcome_title = ""
        damage_info = ""

        total_damage = target.get_damage_after_defense(
            skill, damage_instance.scaled_value
        )

        display_dmg = damage_instance.value
        if current_actor.is_enemy:
            display_dmg = total_damage

        match skill.skill_effect:
            case SkillEffect.PHYSICAL_DAMAGE:
                outcome_title = "Attack Damage"
                damage_info = f"**{display_dmg}** [phys]"
            case SkillEffect.MAGICAL_DAMAGE:
                outcome_title = "Spell Damage"
                damage_info = f"**{display_dmg}** [magic]"

        if damage_instance.is_crit:
            damage_info = "CRIT! " + damage_info

        return outcome_title, damage_info

    async def handle_actor_turn_embed(
        self,
        turn_data: list[TurnData],
        context: EncounterContext,
    ):
        actor = turn_data[0].actor
        color = discord.Color.blurple()
        if actor.is_enemy:
            color = discord.Color.red()

        actor_name = f"<@{actor.id}>"
        if actor.is_enemy:
            actor_name = f"*{actor.name}*"

        turn_number = context.get_current_turn_number()
        title = f"Turn {turn_number}: {actor.name}"

        full_embed = None

        for turn in turn_data:
            skill_data = actor.get_skill_data(turn.skill)

            skill = skill_data.skill

            description = f"{actor_name} chose the action"

            if full_embed is None:
                full_embed = discord.Embed(
                    title=title, description=description, color=color
                )
                full_embed.set_thumbnail(url=actor.image)
                skill_data.add_to_embed(full_embed)

                yield full_embed
            else:
                embed = copy.deepcopy(full_embed)
                embed.add_field(name="", value=description)
                skill_data.add_to_embed(embed)
                full_embed = embed

                yield full_embed

            for target, damage_instance, remaiming_hp in turn.damage_data:
                await asyncio.sleep(1.5)

                to_name = f"<@{target.id}>"
                if target.is_enemy:
                    to_name = f"*{target.name}*"

                outcome_title, damage_info = await self.get_embed_attack_data(
                    current_actor=actor,
                    target=target,
                    skill=skill,
                    damage_instance=damage_instance,
                )

                embed = copy.deepcopy(full_embed)
                embed.add_field(name="Target", value=to_name, inline=True)
                embed.add_field(name=outcome_title, value="", inline=True)
                embed.add_field(name="Target Health", value="", inline=True)

                yield embed

                await asyncio.sleep(1)

                loading_icons = [
                    "🎲",
                    "🎲🎲",
                    "🎲🎲🎲",
                ]

                i = 0
                current = i
                while i <= 5:
                    current = i % len(loading_icons)
                    icon = loading_icons[current]

                    embed = copy.deepcopy(full_embed)
                    embed.add_field(name="Target", value=to_name, inline=True)
                    embed.add_field(name=outcome_title, value=icon, inline=True)
                    embed.add_field(name="Target Health", value="", inline=True)
                    yield embed

                    await asyncio.sleep((1 / 10) * (i * 2))
                    i += 1

                embed = copy.deepcopy(full_embed)
                embed.add_field(name="Target", value=to_name, inline=True)
                embed.add_field(name=outcome_title, value=damage_info, inline=True)
                embed.add_field(name="Target Health", value="", inline=True)
                yield embed

                await asyncio.sleep(1)

                percentage = f"{round(remaiming_hp/target.max_hp * 100, 1)}".rstrip(
                    "0"
                ).rstrip(".")
                display_hp = f"{percentage}%"

                full_embed.add_field(name="Target", value=to_name, inline=True)
                full_embed.add_field(name=outcome_title, value=damage_info, inline=True)
                full_embed.add_field(
                    name="Target Health", value=display_hp, inline=True
                )
                yield full_embed

    def get_turn_skip_embed(
        self, actor: Actor, reason: str, context: EncounterContext
    ) -> discord.Embed:
        turn_number = context.get_current_turn_number()
        title = f"Turn {turn_number}: {actor.name}"

        actor_name = f"*{actor.name}*"

        content = f"{actor_name}'s turn is skipped."

        embed = discord.Embed(
            title=title, description="", color=discord.Colour.light_grey()
        )
        self.add_text_bar(embed, "", content)

        if actor.image is not None:
            embed.set_thumbnail(url=actor.image)
        embed.add_field(name="Reason", value=reason)
        return embed

    async def get_round_embed(self, context: EncounterContext):
        embed = discord.Embed(title="New Round", color=discord.Colour.green())
        initiative_list = context.get_current_initiative()
        initiative_display = ""

        for idx, actor in enumerate(initiative_list):
            number = idx + 1
            current_hp = await self.actor_manager.get_actor_current_hp(
                actor, context.combat_events
            )
            fraction = current_hp / actor.max_hp
            percentage = f"{round(fraction * 100, 1)}".rstrip("0").rstrip(".")
            display_hp = f"[{percentage}%]" if not actor.is_enemy else ""
            if initiative_display == "":
                width = 45
                text = f"{number}. >> {actor.name} << {display_hp}"
                spacing = " " * max(0, width - len(text))
                initiative_display += f"\n{text}{spacing}"
                continue
            initiative_display += f"\n{number}. {actor.name} {display_hp}"
        initiative_display = f"```python\n{initiative_display}```"
        embed.add_field(name="Turn Order:", value=initiative_display, inline=False)

        embed.set_thumbnail(url=self.bot.user.display_avatar)
        return embed

    def get_notification_embed(
        self, title: str, message: str, actor: Actor = None
    ) -> discord.Embed:
        embed = discord.Embed(title=title, color=discord.Colour.light_grey())
        self.add_text_bar(embed, "", message)
        if actor is not None:
            embed.set_thumbnail(url=actor.image)
        return embed

    def get_actor_defeated_embed(self, actor: Actor) -> discord.Embed:
        title = f"*{actor.name}* was defeated!"
        message = ""
        if not actor.is_enemy:
            message = "Their future turns will be skipped."
        return self.get_notification_embed(title, message, actor)

    def get_actor_join_embed(self, user: discord.Member) -> discord.Embed:
        title = "A new player joined the battle!"
        message = f"Good luck {user.display_name}!"
        return self.get_notification_embed(title, message)
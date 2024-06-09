import random
from collections import Counter

import discord
from combat.enemies.enemy import Enemy
from combat.equipment import CharacterEquipment
from combat.gear.types import CharacterAttribute, GearModifierType
from combat.skills.skill import CharacterSkill, Skill
from combat.skills.types import SkillEffect, SkillInstance, SkillType


class Actor:

    CHARACTER_ENCOUNTER_SCALING_FACOTR = 1
    OPPONENT_ENCOUNTER_SCALING_FACTOR = 0.95
    OPPONENT_LEVEL_SCALING_FACTOR = 0.97
    OPPONENT_DAMAGE_VARIANCE = 0.05
    SKILL_TYPE_PENALTY = 0.2

    # Based on avg player health
    OPPONENT_DAMAGE_BASE = {
        1: 274.05,
        2: 331.78,
        3: 393.60,
        4: 471.88,
        5: 563.82,
        6: 618.98,
        7: 671.76,
        8: 734.08,
        9: 792.80,
        10: 845.32,
        11: 1012.75,
        12: 1076.95,
    }

    def __init__(
        self,
        id: int,
        name: str,
        max_hp: int,
        initiative: int,
        is_enemy: bool,
        skills: list[Skill],
        skill_cooldowns: dict[SkillType, int],
        skill_stacks_used: dict[SkillType, int],
        defeated: bool,
        image: str,
    ):
        self.id = id
        self.name = name
        self.max_hp = max_hp
        self.initiative = initiative
        self.is_enemy = is_enemy
        self.skills = skills
        self.skill_cooldowns = skill_cooldowns
        self.skill_stacks_used = skill_stacks_used
        self.defeated = defeated
        self.image = image

    def get_skill_data(self, skill: Skill) -> CharacterSkill:
        pass

    def get_skill_effect(
        self, skill: Skill, combatant_count: int = 1, force_roll: int = None
    ) -> list[SkillInstance]:
        pass

    def get_damage_after_defense(self, skill: Skill, incoming_damage: int) -> float:
        pass


class Character(Actor):

    BASE_INITIATIVE = 10

    def __init__(
        self,
        member: discord.Member,
        skill_slots: dict[int, Skill],
        skill_cooldowns: dict[SkillType, int],
        skill_stacks_used: dict[int, int],
        equipment: CharacterEquipment,
        defeated: bool,
    ):
        self.member = member
        self.equipment = equipment
        max_hp = self.equipment.attributes[CharacterAttribute.MAX_HEALTH]
        initiative = (
            self.BASE_INITIATIVE
            + self.equipment.gear_modifiers[GearModifierType.DEXTERITY]
        )
        self.skill_slots = skill_slots
        super().__init__(
            id=member.id,
            name=member.display_name,
            max_hp=max_hp,
            initiative=initiative,
            is_enemy=False,
            skills=[skill for skill in skill_slots.values() if skill is not None],
            skill_cooldowns=skill_cooldowns,
            skill_stacks_used=skill_stacks_used,
            defeated=defeated,
            image=member.avatar.url,
        )

    def get_skill_data(self, skill: Skill) -> CharacterSkill:
        weapon_min_roll = self.equipment.weapon.modifiers[
            GearModifierType.WEAPON_DAMAGE_MIN
        ]
        weapon_max_roll = self.equipment.weapon.modifiers[
            GearModifierType.WEAPON_DAMAGE_MAX
        ]

        skill_type = skill.type
        skill_id = skill.id
        stacks_used = 0
        last_used = None

        if skill_id in self.skill_stacks_used:
            stacks_used = self.skill_stacks_used[skill_id]

        if skill_type in self.skill_cooldowns:
            last_used = self.skill_cooldowns[skill.base_skill.skill_type]

        penalty = (
            self.skill_slots[0].base_skill.skill_effect != skill.base_skill.skill_effect
            and skill.base_skill.skill_effect != SkillEffect.HEALING
        )

        return CharacterSkill(
            skill=skill,
            last_used=last_used,
            stacks_used=stacks_used,
            min_roll=self.get_skill_effect(skill, force_roll=weapon_min_roll)[
                0
            ].raw_value,
            max_roll=self.get_skill_effect(skill, force_roll=weapon_max_roll)[
                0
            ].raw_value,
            penalty=penalty,
        )

    def get_skill_effect(
        self,
        skill: Skill,
        combatant_count: int = 1,
        force_roll: int = None,
    ) -> list[SkillInstance]:
        skill_base_value = skill.base_skill.base_value
        weapon_min_roll = self.equipment.weapon.modifiers[
            GearModifierType.WEAPON_DAMAGE_MIN
        ]
        weapon_max_roll = self.equipment.weapon.modifiers[
            GearModifierType.WEAPON_DAMAGE_MAX
        ]

        modifier = 1
        base_dmg_type = self.skill_slots[0].base_skill.skill_effect

        match skill.base_skill.skill_effect:
            case SkillEffect.PHYSICAL_DAMAGE:
                modifier += self.equipment.attributes[
                    CharacterAttribute.PHYS_DAMAGE_INCREASE
                ]
                if base_dmg_type != skill.base_skill.skill_effect:
                    modifier *= self.SKILL_TYPE_PENALTY
            case SkillEffect.MAGICAL_DAMAGE:
                modifier += self.equipment.attributes[
                    CharacterAttribute.MAGIC_DAMAGE_INCREASE
                ]
                if base_dmg_type != skill.base_skill.skill_effect:
                    modifier *= self.SKILL_TYPE_PENALTY
            case SkillEffect.HEALING:
                modifier += self.equipment.attributes[CharacterAttribute.HEALING_BONUS]

        encounter_scaling = 1
        if combatant_count > 1:
            encounter_scaling = (
                1 / combatant_count * self.CHARACTER_ENCOUNTER_SCALING_FACOTR
            )

        attack_count = skill.base_skill.hits
        skill_instances = []
        for _ in range(attack_count):
            weapon_roll = force_roll
            if weapon_roll is None:
                weapon_roll = random.randint(int(weapon_min_roll), int(weapon_max_roll))

            crit_roll = random.random()
            critical_hit = False
            critical_modifier = 1
            if crit_roll < self.equipment.attributes[CharacterAttribute.CRIT_RATE]:
                critical_hit = True
                critical_modifier = self.equipment.attributes[
                    CharacterAttribute.CRIT_DAMAGE
                ]

            skill_instance = SkillInstance(
                weapon_roll=weapon_roll,
                skill_base=skill_base_value,
                modifier=modifier,
                critical_modifier=critical_modifier,
                encounter_scaling=encounter_scaling,
                is_crit=critical_hit,
            )
            skill_instances.append(skill_instance)

        return skill_instances

    def get_damage_after_defense(self, skill: Skill, incoming_damage: int) -> float:

        modifier = 1
        flat_reduction = 0

        match skill.base_skill.skill_effect:
            case SkillEffect.PHYSICAL_DAMAGE:
                modifier -= self.equipment.attributes[
                    CharacterAttribute.PHYS_DAMAGE_REDUCTION
                ]
                flat_reduction = int(
                    self.equipment.gear_modifiers[GearModifierType.ARMOR] / 4
                )
            case SkillEffect.MAGICAL_DAMAGE:
                modifier -= self.equipment.attributes[
                    CharacterAttribute.MAGIC_DAMAGE_REDUCTION
                ]
            case SkillEffect.HEALING:
                pass

        return int(max(0, ((incoming_damage * modifier) - flat_reduction)))


class Opponent(Actor):

    def __init__(
        self,
        enemy: Enemy,
        level: int,
        max_hp: int,
        skills: list[Skill],
        skill_cooldowns: dict[SkillType, int],
        skill_stacks_used: dict[int, int],
        defeated: bool,
    ):
        super().__init__(
            id=None,
            name=enemy.name,
            max_hp=max_hp,
            initiative=enemy.initiative,
            is_enemy=True,
            skills=skills,
            skill_cooldowns=skill_cooldowns,
            skill_stacks_used=skill_stacks_used,
            defeated=defeated,
            image=f"attachment://{enemy.image}",
        )
        self.level = level
        self.enemy = enemy

        multiplier = 0

        # for skill in self.skills:
        #     cooldown = skill.base_skill.cooldown + 1
        #     multiplier += skill.base_skill.base_value * skill.base_skill.hits / cooldown

        rotation_length = 1
        already_used = [1]

        sorted_skills = sorted(
            self.skills, key=lambda x: x.base_skill.base_value, reverse=True
        )

        for skill in sorted_skills:
            cooldown = skill.base_skill.cooldown + 1

            if cooldown in already_used:
                continue

            for value in already_used:
                if value % cooldown == 0:
                    already_used.append(cooldown)
                    continue

            rotation_length *= cooldown
            already_used.append(cooldown)

        skill_rotation = []
        for index in range(rotation_length):
            for skill in sorted_skills:
                if skill not in skill_rotation:
                    skill_rotation.append(skill)
                    break
                last_used = next(
                    i
                    for i in reversed(range(len(skill_rotation)))
                    if skill_rotation[i] == skill
                )
                turns_passed = len(skill_rotation) - last_used - 1
                if turns_passed >= skill.base_skill.cooldown:
                    skill_rotation.append(skill)
                    break

            if len(skill_rotation) != index + 1:
                skill_rotation.append(None)

        skill_uses = Counter()
        for skill in skill_rotation:
            if skill is None:
                continue
            skill_uses[skill.base_skill.type] += 1

        multiplier = 0
        for skill in sorted_skills:
            multiplier += (
                skill.base_skill.base_value
                * skill.base_skill.hits
                * skill_uses[skill.base_skill.type]
                / rotation_length
            )

        self.average_skill_multi = multiplier

    def get_skill_data(self, skill: Skill) -> CharacterSkill:
        base_damage = self.OPPONENT_DAMAGE_BASE[self.level] / self.enemy.damage_scaling
        weapon_min_roll = int(base_damage * (1 - self.OPPONENT_DAMAGE_VARIANCE))
        weapon_max_roll = int(base_damage * (1 + self.OPPONENT_DAMAGE_VARIANCE))

        skill_id = skill.id
        stacks_used = 0

        if skill_id in self.skill_stacks_used:
            stacks_used = self.skill_stacks_used[skill_id]

        return CharacterSkill(
            skill=skill,
            last_used=self.skill_cooldowns[skill.base_skill.skill_type],
            stacks_used=stacks_used,
            min_roll=self.get_skill_effect(skill, force_roll=weapon_min_roll)[
                0
            ].raw_value,
            max_roll=self.get_skill_effect(skill, force_roll=weapon_max_roll)[
                0
            ].raw_value,
        )

    def get_skill_effect(
        self,
        skill: Skill,
        combatant_count: int = 1,
        force_roll: int = None,
    ) -> list[SkillInstance]:

        skill_base_value = skill.base_skill.base_value
        skill_scaling = skill_base_value / self.average_skill_multi

        base_damage = self.OPPONENT_DAMAGE_BASE[self.level] / self.enemy.damage_scaling

        weapon_min_roll = int(base_damage * (1 - self.OPPONENT_DAMAGE_VARIANCE))
        weapon_max_roll = int(base_damage * (1 + self.OPPONENT_DAMAGE_VARIANCE))

        modifier = pow(
            self.OPPONENT_LEVEL_SCALING_FACTOR, (self.level - self.enemy.min_level)
        )

        match skill.base_skill.skill_effect:
            case SkillEffect.PHYSICAL_DAMAGE:
                modifier += self.enemy.attributes[
                    CharacterAttribute.PHYS_DAMAGE_INCREASE
                ]
            case SkillEffect.MAGICAL_DAMAGE:
                modifier += self.enemy.attributes[
                    CharacterAttribute.MAGIC_DAMAGE_INCREASE
                ]
            case SkillEffect.HEALING:
                modifier += self.enemy.attributes[CharacterAttribute.HEALING_BONUS]

        encounter_scaling = 1
        raw_attack_count = skill.base_skill.hits
        attack_count = raw_attack_count

        if combatant_count > 1 and not skill.base_skill.aoe:
            attack_count_scaling = max(1, combatant_count * 0.75)
            attack_count = int(raw_attack_count * attack_count_scaling)
            encounter_scaling = (
                combatant_count
                * Actor.OPPONENT_ENCOUNTER_SCALING_FACTOR
                * raw_attack_count
                / attack_count
            )

        attacks = []
        for _ in range(attack_count):
            weapon_roll = random.randint(weapon_min_roll, weapon_max_roll)

            crit_roll = random.random()
            critical_hit = False
            critical_modifier = 1
            if crit_roll < self.enemy.attributes[CharacterAttribute.CRIT_RATE]:
                critical_hit = True
                critical_modifier = self.enemy.attributes[
                    CharacterAttribute.CRIT_DAMAGE
                ]

            damage_instance = SkillInstance(
                weapon_roll=weapon_roll,
                skill_base=skill_scaling,
                modifier=modifier,
                critical_modifier=critical_modifier,
                encounter_scaling=encounter_scaling,
                is_crit=critical_hit,
            )
            attacks.append(damage_instance)

        return attacks

    def get_damage_after_defense(self, skill: Skill, incoming_damage: int) -> float:

        modifier = 1
        flat_reduction = 0

        match skill.base_skill.skill_effect:
            case SkillEffect.PHYSICAL_DAMAGE:
                modifier -= self.enemy.attributes[
                    CharacterAttribute.PHYS_DAMAGE_REDUCTION
                ]
            case SkillEffect.MAGICAL_DAMAGE:
                modifier -= self.enemy.attributes[
                    CharacterAttribute.MAGIC_DAMAGE_REDUCTION
                ]
            case SkillEffect.HEALING:
                pass

        return int(max(0, ((incoming_damage - flat_reduction) * modifier)))
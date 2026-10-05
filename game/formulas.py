"""Fórmulas de juego. Python puro: sin Django, sin estado, sin números de balance hardcodeados.

Todos los multiplicadores y umbrales vienen de `Balance` (data/balance.yaml).
Los multiplicadores se combinan de forma multiplicativa.
"""

from game.loader import (
    ARMOR_WEIGHTS,
    STATS,
    WEAPON_CLASSES,
    Balance,
    CharacterClass,
    FocusModifier,
    Race,
)

ARMOR = "armor"
WEAPON = "weapon"
_GEAR_SUBTYPES = {ARMOR: ARMOR_WEIGHTS, WEAPON: WEAPON_CLASSES}


def starting_stats(race: Race, balance: Balance) -> dict[str, int]:
    """Estadísticas iniciales de un personaje según su raza (GDD 3.1)."""
    stats = {stat: balance.character_defaults.base_stat for stat in STATS}
    for stat, bonus in race.stat_bonuses.items():
        stats[stat] += bonus
    return stats


def _check_quest_type(name: str, balance: Balance) -> None:
    if name not in balance.stat_for_quest_type:
        raise ValueError(f"Tipo de misión/enfoque desconocido: '{name}'")


def focus_modifier(focus: str, quest_type: str, balance: Balance) -> FocusModifier:
    """Multiplicadores de poder y desgaste según el enfoque elegido (GDD 4.2).

    El enfoque es ideal cuando coincide con el tipo de misión.
    """
    _check_quest_type(focus, balance)
    _check_quest_type(quest_type, balance)
    return balance.focus_ideal if focus == quest_type else balance.focus_non_ideal


def class_power_multiplier(char_class: CharacterClass, quest_type: str, balance: Balance) -> float:
    """Bono de clase al poder: solo en el tipo de misión de la clase (GDD 3.3)."""
    _check_quest_type(quest_type, balance)
    in_type = char_class.quest_type_bonus == quest_type
    return balance.class_power_multiplier if in_type else 1.0


def class_wear_multiplier(char_class: CharacterClass, quest_type: str, balance: Balance) -> float:
    """Reducción leve de desgaste de la clase en su tipo de misión (placeholder AJUSTABLE)."""
    _check_quest_type(quest_type, balance)
    in_type = char_class.quest_type_bonus == quest_type
    return balance.class_wear_multiplier if in_type else 1.0


def effective_power(
    base_power: float,
    focus: str,
    quest_type: str,
    char_class: CharacterClass,
    balance: Balance,
) -> float:
    """Poder efectivo = poder base × multiplicador de enfoque × bono de clase."""
    return (
        base_power
        * focus_modifier(focus, quest_type, balance).power
        * class_power_multiplier(char_class, quest_type, balance)
    )


def effective_wear(
    base_wear: float,
    focus: str,
    quest_type: str,
    char_class: CharacterClass,
    balance: Balance,
) -> float:
    """Desgaste efectivo = desgaste base × multiplicador de enfoque × reducción de clase."""
    return (
        base_wear
        * focus_modifier(focus, quest_type, balance).wear
        * class_wear_multiplier(char_class, quest_type, balance)
    )


def is_proficient(kind: str, subtype: str, race: Race, char_class: CharacterClass) -> bool:
    """¿El personaje tiene competencia con este equipo? Raza y clase se suman (GDD 3.4).

    kind: 'armor' (subtype = peso: light/medium/heavy) o 'weapon' (subtype = clase de arma:
    light/ranged/martial). Las razas solo otorgan competencia de armadura.
    """
    if kind not in _GEAR_SUBTYPES:
        raise ValueError(f"Tipo de equipo desconocido: '{kind}'")
    if subtype not in _GEAR_SUBTYPES[kind]:
        raise ValueError(f"'{subtype}' no es válido para equipo tipo '{kind}'")
    if kind == ARMOR:
        return subtype in race.armor_proficiencies or subtype in char_class.armor_proficiencies
    return subtype in char_class.weapon_proficiencies


def gear_factor(
    kind: str, subtype: str, race: Race, char_class: CharacterClass, balance: Balance
) -> float:
    """1.0 con competencia; sin competencia el equipo aporta solo una fracción de su bono."""
    if is_proficient(kind, subtype, race, char_class):
        return 1.0
    return balance.unproficient_gear_factor


def gear_bonus(
    item_bonus: float,
    kind: str,
    subtype: str,
    race: Race,
    char_class: CharacterClass,
    balance: Balance,
) -> float:
    """Bono que un ítem realmente aporta al personaje, según su competencia."""
    return item_bonus * gear_factor(kind, subtype, race, char_class, balance)

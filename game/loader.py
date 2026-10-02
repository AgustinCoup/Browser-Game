"""Carga y valida los datos de juego (data/*.yaml). Python puro: no importa Django.

El resultado es inmutable: dataclasses congeladas, tuplas y mapeos de solo lectura.
"""

import math
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any

import yaml

DEFAULT_DATA_DIR = Path(__file__).resolve().parent.parent / "data"

STATS = ("strength", "dexterity", "wisdom", "constitution")
ARMOR_WEIGHTS = ("light", "medium", "heavy")
WEAPON_CLASSES = ("light", "ranged", "martial")
ROLE_TAGS = ("vanguard", "stealth", "arcane", "support")


class DataValidationError(ValueError):
    """Un archivo de data/ falta o tiene un formato/valor inválido."""


@dataclass(frozen=True)
class Trait:
    id: str
    description: str


@dataclass(frozen=True)
class ChooseBonus:
    count: int
    amount: int


@dataclass(frozen=True)
class Race:
    id: str
    name: str
    stat_bonuses: Mapping[str, int]
    choose_bonus: ChooseBonus | None
    armor_proficiencies: tuple[str, ...]
    traits: tuple[Trait, ...]


@dataclass(frozen=True)
class CharacterClass:
    id: str
    name: str
    quest_type_bonus: str
    role_tag: str
    weapon_proficiencies: tuple[str, ...]
    armor_proficiencies: tuple[str, ...]
    traits: tuple[Trait, ...]


@dataclass(frozen=True)
class FocusModifier:
    power: float
    wear: float


@dataclass(frozen=True)
class CharacterDefaults:
    base_stat: int
    level: int
    xp: int
    gold: int


@dataclass(frozen=True)
class Balance:
    stat_for_quest_type: Mapping[str, str]
    focus_ideal: FocusModifier
    focus_non_ideal: FocusModifier
    class_power_multiplier: float
    class_wear_multiplier: float
    unproficient_gear_factor: float
    character_defaults: CharacterDefaults


@dataclass(frozen=True)
class GameData:
    balance: Balance
    races: Mapping[str, Race]
    classes: Mapping[str, CharacterClass]


# --- helpers de validación -------------------------------------------------


def _read_yaml(path: Path) -> Any:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise DataValidationError(f"Falta el archivo de datos: {path.name}") from exc
    except yaml.YAMLError as exc:
        raise DataValidationError(f"YAML inválido en {path.name}: {exc}") from exc


def _require(obj: Any, key: str, where: str) -> Any:
    if not isinstance(obj, dict) or key not in obj:
        raise DataValidationError(f"{where}: falta el campo obligatorio '{key}'")
    return obj[key]


def _str(obj: Any, key: str, where: str) -> str:
    value = _require(obj, key, where)
    if not isinstance(value, str) or not value:
        raise DataValidationError(f"{where}: '{key}' debe ser un texto no vacío")
    return value


def _int(obj: Any, key: str, where: str, minimum: int = 0) -> int:
    value = _require(obj, key, where)
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise DataValidationError(f"{where}: '{key}' debe ser un entero >= {minimum}")
    return value


def _positive_float(obj: Any, key: str, where: str) -> float:
    value = _require(obj, key, where)
    if (
        isinstance(value, bool)
        or not isinstance(value, int | float)
        or not math.isfinite(value)
        or value <= 0
    ):
        raise DataValidationError(f"{where}: '{key}' debe ser un número finito > 0")
    return float(value)


def _choice(value: Any, allowed: tuple[str, ...], where: str) -> str:
    if value not in allowed:
        raise DataValidationError(f"{where}: valor '{value}' inválido; permitidos: {allowed}")
    return value


def _choice_list(obj: Any, key: str, allowed: tuple[str, ...], where: str) -> tuple[str, ...]:
    values = _require(obj, key, where)
    if not isinstance(values, list):
        raise DataValidationError(f"{where}: '{key}' debe ser una lista")
    return tuple(_choice(v, allowed, f"{where}.{key}") for v in values)


def _traits(obj: Any, where: str) -> tuple[Trait, ...]:
    raw = _require(obj, "traits", where)
    if not isinstance(raw, list):
        raise DataValidationError(f"{where}: 'traits' debe ser una lista")
    return tuple(
        Trait(_str(t, "id", f"{where}.traits"), _str(t, "description", f"{where}.traits"))
        for t in raw
    )


def _entries(path: Path) -> list[dict]:
    raw = _read_yaml(path)
    if not isinstance(raw, list) or not raw:
        raise DataValidationError(f"{path.name}: debe ser una lista no vacía")
    if not all(isinstance(entry, dict) for entry in raw):
        raise DataValidationError(f"{path.name}: cada elemento debe ser un mapa")
    return raw


def _index_by_id(items: list, kind: str) -> Mapping[str, Any]:
    indexed: dict[str, Any] = {}
    for item in items:
        if item.id in indexed:
            raise DataValidationError(f"{kind}: id duplicado '{item.id}'")
        indexed[item.id] = item
    return MappingProxyType(indexed)


# --- parsers por archivo ---------------------------------------------------


def _parse_stat_bonuses(raw: Any, where: str) -> Mapping[str, int]:
    if not isinstance(raw, dict):
        raise DataValidationError(f"{where}: 'stat_bonuses' debe ser un mapa")
    bonuses = {
        _choice(stat, STATS, f"{where}.stat_bonuses"): _int(raw, stat, f"{where}.stat_bonuses")
        for stat in raw
    }
    return MappingProxyType(bonuses)


def _parse_choose_bonus(choose: dict | None, where: str) -> ChooseBonus | None:
    if choose is None:
        return None
    count = _int(choose, "count", where, 1)
    if count > len(STATS):
        raise DataValidationError(f"{where}: 'choose_bonus.count' no puede superar {len(STATS)}")
    return ChooseBonus(count, _int(choose, "amount", where, 1))


def _parse_race(raw: Any) -> Race:
    where = f"races.yaml[{raw.get('id', '?') if isinstance(raw, dict) else '?'}]"
    choose = raw.get("choose_bonus")
    if "choose_bonus" in raw and not isinstance(choose, dict):
        raise DataValidationError(f"{where}: 'choose_bonus' debe ser un mapa con count y amount")
    return Race(
        id=_str(raw, "id", where),
        name=_str(raw, "name", where),
        stat_bonuses=_parse_stat_bonuses(_require(raw, "stat_bonuses", where), where),
        choose_bonus=_parse_choose_bonus(choose, where),
        armor_proficiencies=_choice_list(raw, "armor_proficiencies", ARMOR_WEIGHTS, where),
        traits=_traits(raw, where),
    )


def _parse_class(raw: Any, quest_types: tuple[str, ...]) -> CharacterClass:
    where = f"classes.yaml[{raw.get('id', '?') if isinstance(raw, dict) else '?'}]"
    return CharacterClass(
        id=_str(raw, "id", where),
        name=_str(raw, "name", where),
        quest_type_bonus=_choice(_require(raw, "quest_type_bonus", where), quest_types, where),
        role_tag=_choice(_require(raw, "role_tag", where), ROLE_TAGS, where),
        weapon_proficiencies=_choice_list(raw, "weapon_proficiencies", WEAPON_CLASSES, where),
        armor_proficiencies=_choice_list(raw, "armor_proficiencies", ARMOR_WEIGHTS, where),
        traits=_traits(raw, where),
    )


def _parse_focus(raw: Any, key: str) -> FocusModifier:
    where = f"balance.yaml focus.{key}"
    section = _require(raw, key, where)
    return FocusModifier(
        power=_positive_float(section, "power", where),
        wear=_positive_float(section, "wear", where),
    )


def _parse_quest_types(raw: Any) -> Mapping[str, str]:
    where = "balance.yaml quest_types"
    section = _require(raw, "quest_types", where)
    if not isinstance(section, dict) or not section:
        raise DataValidationError(f"{where}: debe ser un mapa no vacío")
    return MappingProxyType({qt: _choice(stat, STATS, where) for qt, stat in section.items()})


def _parse_balance(raw: Any) -> Balance:
    focus = _require(raw, "focus", "balance.yaml")
    class_bonus = _require(raw, "class_bonus", "balance.yaml")
    gear = _require(raw, "gear", "balance.yaml")
    defaults = _require(raw, "character_defaults", "balance.yaml")
    where = "balance.yaml character_defaults"
    ideal = _parse_focus(focus, "ideal")
    non_ideal = _parse_focus(focus, "non_ideal")
    unproficient = _positive_float(gear, "unproficient_factor", "balance.yaml gear")
    if ideal.power < non_ideal.power or ideal.wear > non_ideal.wear:
        raise DataValidationError(
            "balance.yaml focus: el enfoque ideal debe dar más poder y menos desgaste "
            "que el no ideal"
        )
    if unproficient > 1:
        raise DataValidationError("balance.yaml gear: 'unproficient_factor' debe ser <= 1")
    return Balance(
        stat_for_quest_type=_parse_quest_types(raw),
        focus_ideal=ideal,
        focus_non_ideal=non_ideal,
        class_power_multiplier=_positive_float(class_bonus, "power", "balance.yaml class_bonus"),
        class_wear_multiplier=_positive_float(class_bonus, "wear", "balance.yaml class_bonus"),
        unproficient_gear_factor=unproficient,
        character_defaults=CharacterDefaults(
            base_stat=_int(defaults, "base_stat", where),
            level=_int(defaults, "level", where, 1),
            xp=_int(defaults, "xp", where),
            gold=_int(defaults, "gold", where),
        ),
    )


def load_game_data(data_dir: Path | str = DEFAULT_DATA_DIR) -> GameData:
    """Lee data/balance.yaml, races.yaml y classes.yaml y devuelve datos validados e inmutables."""
    data_dir = Path(data_dir)
    balance = _parse_balance(_read_yaml(data_dir / "balance.yaml"))
    quest_types = tuple(balance.stat_for_quest_type)
    races = [_parse_race(r) for r in _entries(data_dir / "races.yaml")]
    classes = [_parse_class(c, quest_types) for c in _entries(data_dir / "classes.yaml")]
    return GameData(
        balance=balance,
        races=_index_by_id(races, "races.yaml"),
        classes=_index_by_id(classes, "classes.yaml"),
    )

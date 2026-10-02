from dataclasses import replace

import pytest

from game import formulas
from game.loader import FocusModifier, load_game_data

DATA = load_game_data()
BALANCE = DATA.balance
QUEST_TYPES = ("combat", "infiltration", "mystery")


# --- multiplicador de enfoque ----------------------------------------------


@pytest.mark.parametrize("quest_type", QUEST_TYPES)
def test_ideal_focus_gives_more_power_and_less_wear(quest_type):
    modifier = formulas.focus_modifier(quest_type, quest_type, BALANCE)

    assert modifier.power == pytest.approx(1.20)
    assert modifier.wear == pytest.approx(0.80)


@pytest.mark.parametrize(
    ("focus", "quest_type"),
    [(f, q) for f in QUEST_TYPES for q in QUEST_TYPES if f != q],
)
def test_non_ideal_focus_gives_less_power_and_more_wear(focus, quest_type):
    modifier = formulas.focus_modifier(focus, quest_type, BALANCE)

    assert modifier.power == pytest.approx(0.90)
    assert modifier.wear == pytest.approx(1.30)


def test_unknown_focus_or_quest_type_raises():
    with pytest.raises(ValueError, match="cooking"):
        formulas.focus_modifier("cooking", "combat", BALANCE)
    with pytest.raises(ValueError, match="cooking"):
        formulas.focus_modifier("combat", "cooking", BALANCE)


def test_focus_numbers_come_from_balance_not_from_code():
    custom = replace(
        BALANCE,
        focus_ideal=FocusModifier(power=2.0, wear=0.5),
        focus_non_ideal=FocusModifier(power=0.5, wear=2.0),
    )

    assert formulas.focus_modifier("combat", "combat", custom) == FocusModifier(2.0, 0.5)
    assert formulas.focus_modifier("combat", "mystery", custom) == FocusModifier(0.5, 2.0)


# --- bono de clase ---------------------------------------------------------


def test_class_bonus_applies_only_in_its_quest_type():
    warrior = DATA.classes["warrior"]

    assert formulas.class_power_multiplier(warrior, "combat", BALANCE) == pytest.approx(1.10)
    assert formulas.class_power_multiplier(warrior, "infiltration", BALANCE) == 1.0
    assert formulas.class_power_multiplier(warrior, "mystery", BALANCE) == 1.0


@pytest.mark.parametrize(
    ("class_id", "quest_type"),
    [("warrior", "combat"), ("rogue", "infiltration"), ("mage", "mystery")],
)
def test_each_class_gets_its_bonus_in_its_type(class_id, quest_type):
    char_class = DATA.classes[class_id]

    assert formulas.class_power_multiplier(char_class, quest_type, BALANCE) == pytest.approx(1.10)
    assert formulas.class_wear_multiplier(char_class, quest_type, BALANCE) == pytest.approx(0.95)


def test_class_wear_reduction_applies_only_in_its_quest_type():
    rogue = DATA.classes["rogue"]

    assert formulas.class_wear_multiplier(rogue, "combat", BALANCE) == 1.0


def test_class_numbers_come_from_balance_not_from_code():
    custom = replace(BALANCE, class_power_multiplier=1.5, class_wear_multiplier=0.5)
    mage = DATA.classes["mage"]

    assert formulas.class_power_multiplier(mage, "mystery", custom) == 1.5
    assert formulas.class_wear_multiplier(mage, "mystery", custom) == 0.5


# --- poder y desgaste efectivos (multiplicativos) ---------------------------


def test_effective_power_ideal_focus_with_class_bonus_stacks_multiplicatively():
    warrior = DATA.classes["warrior"]

    power = formulas.effective_power(100, "combat", "combat", warrior, BALANCE)

    assert power == pytest.approx(100 * 1.20 * 1.10)


def test_effective_power_non_ideal_focus_without_class_bonus():
    warrior = DATA.classes["warrior"]

    power = formulas.effective_power(100, "mystery", "infiltration", warrior, BALANCE)

    assert power == pytest.approx(100 * 0.90)


def test_effective_wear_stacks_multiplicatively():
    mage = DATA.classes["mage"]

    wear = formulas.effective_wear(50, "mystery", "mystery", mage, BALANCE)
    non_ideal = formulas.effective_wear(50, "combat", "mystery", mage, BALANCE)

    assert wear == pytest.approx(50 * 0.80 * 0.95)
    assert non_ideal == pytest.approx(50 * 1.30 * 0.95)


# --- competencia de equipo --------------------------------------------------


def test_race_armor_proficiency_gives_full_bonus():
    dwarf, mage = DATA.races["dwarf"], DATA.classes["mage"]

    assert formulas.is_proficient("armor", "heavy", dwarf, mage)
    assert formulas.gear_factor("armor", "heavy", dwarf, mage, BALANCE) == 1.0


def test_class_weapon_proficiency_gives_full_bonus():
    elf, rogue = DATA.races["elf"], DATA.classes["rogue"]

    assert formulas.gear_factor("weapon", "light", elf, rogue, BALANCE) == 1.0


def test_no_proficiency_gives_half_bonus():
    elf, mage = DATA.races["elf"], DATA.classes["mage"]

    assert formulas.gear_factor("armor", "heavy", elf, mage, BALANCE) == pytest.approx(0.50)
    assert formulas.gear_factor("weapon", "martial", elf, mage, BALANCE) == pytest.approx(0.50)


def test_race_and_class_proficiencies_add_up():
    # Humano (media por raza) con una clase que aporta armadura pesada: ambas valen.
    human = DATA.races["human"]
    heavy_class = replace(DATA.classes["warrior"], armor_proficiencies=("heavy",))

    assert formulas.is_proficient("armor", "medium", human, heavy_class)
    assert formulas.is_proficient("armor", "heavy", human, heavy_class)
    assert not formulas.is_proficient("armor", "light", human, heavy_class)


def test_warrior_is_proficient_with_all_weapons_from_start():
    human, warrior = DATA.races["human"], DATA.classes["warrior"]

    for weapon_class in ("light", "ranged", "martial"):
        assert formulas.is_proficient("weapon", weapon_class, human, warrior)


def test_races_do_not_grant_weapon_proficiency():
    # Supuesto documentado en data/races.yaml: las razas solo otorgan armadura.
    mage = DATA.classes["mage"]

    for race in DATA.races.values():
        assert not formulas.is_proficient("weapon", "light", race, mage)


def test_gear_bonus_scales_the_item_bonus():
    elf, mage = DATA.races["elf"], DATA.classes["mage"]

    assert formulas.gear_bonus(20, "armor", "light", elf, mage, BALANCE) == 20
    assert formulas.gear_bonus(20, "armor", "heavy", elf, mage, BALANCE) == pytest.approx(10)


def test_unproficient_factor_comes_from_balance_not_from_code():
    custom = replace(BALANCE, unproficient_gear_factor=0.25)
    elf, mage = DATA.races["elf"], DATA.classes["mage"]

    assert formulas.gear_factor("armor", "heavy", elf, mage, custom) == 0.25


def test_invalid_gear_kind_or_weight_raises():
    elf, mage = DATA.races["elf"], DATA.classes["mage"]

    with pytest.raises(ValueError, match="shield"):
        formulas.is_proficient("shield", "light", elf, mage)
    with pytest.raises(ValueError, match="ranged"):
        formulas.is_proficient("armor", "ranged", elf, mage)
    with pytest.raises(ValueError, match="martial"):
        formulas.is_proficient("armor", "martial", elf, mage)

import shutil
from pathlib import Path

import pytest
import yaml

from game.loader import DataValidationError, load_game_data

REAL_DATA = Path(__file__).resolve().parents[2] / "data"


@pytest.fixture
def data_dir(tmp_path):
    """Copia de data/ que cada test puede romper sin tocar los archivos reales."""
    target = tmp_path / "data"
    shutil.copytree(REAL_DATA, target)
    return target


def edit_yaml(data_dir, filename, mutate):
    path = data_dir / filename
    content = yaml.safe_load(path.read_text(encoding="utf-8"))
    path.write_text(yaml.safe_dump(mutate(content) or content), encoding="utf-8")


def test_loads_real_data_with_mvp_races_and_classes():
    data = load_game_data()

    assert set(data.races) == {"human", "dwarf", "elf", "halfling"}
    assert set(data.classes) == {"warrior", "rogue", "mage"}


def test_races_carry_gdd_traits():
    data = load_game_data()

    assert data.races["dwarf"].stat_bonuses["constitution"] == 2
    assert data.races["elf"].stat_bonuses["wisdom"] == 2
    assert data.races["halfling"].stat_bonuses["dexterity"] == 2
    assert data.races["human"].choose_bonus.count == 2
    assert data.races["human"].armor_proficiencies == ("medium",)
    assert data.races["dwarf"].armor_proficiencies == ("heavy",)
    assert data.races["halfling"].traits[0].id == "lucky"


def test_classes_carry_gdd_traits():
    data = load_game_data()

    assert data.classes["warrior"].quest_type_bonus == "combat"
    assert data.classes["warrior"].weapon_proficiencies == ("light", "ranged", "martial")
    assert data.classes["rogue"].weapon_proficiencies == ("light",)
    assert data.classes["mage"].weapon_proficiencies == ()
    assert data.classes["mage"].quest_type_bonus == "mystery"


def test_balance_reads_gdd_numbers():
    balance = load_game_data().balance

    assert balance.focus_ideal.power == 1.20
    assert balance.focus_ideal.wear == 0.80
    assert balance.focus_non_ideal.power == 0.90
    assert balance.focus_non_ideal.wear == 1.30
    assert balance.class_power_multiplier == 1.10
    assert balance.unproficient_gear_factor == 0.50
    assert balance.stat_for_quest_type["combat"] == "strength"


def test_loaded_data_is_immutable():
    data = load_game_data()

    with pytest.raises(TypeError):
        data.races["new"] = data.races["elf"]
    with pytest.raises(AttributeError):
        data.races["elf"].id = "other"


def test_missing_file_raises_clear_error(data_dir):
    (data_dir / "races.yaml").unlink()

    with pytest.raises(DataValidationError, match="races.yaml"):
        load_game_data(data_dir)


def test_missing_required_field_raises(data_dir):
    def drop_name(races):
        del races[0]["name"]

    edit_yaml(data_dir, "races.yaml", drop_name)

    with pytest.raises(DataValidationError, match="name"):
        load_game_data(data_dir)


def test_unknown_stat_raises(data_dir):
    def bad_stat(races):
        races[1]["stat_bonuses"] = {"charisma": 2}

    edit_yaml(data_dir, "races.yaml", bad_stat)

    with pytest.raises(DataValidationError, match="charisma"):
        load_game_data(data_dir)


def test_unknown_armor_weight_raises(data_dir):
    def bad_weight(races):
        races[0]["armor_proficiencies"] = ["super_heavy"]

    edit_yaml(data_dir, "races.yaml", bad_weight)

    with pytest.raises(DataValidationError, match="super_heavy"):
        load_game_data(data_dir)


def test_unknown_weapon_class_raises(data_dir):
    def bad_weapon(classes):
        classes[0]["weapon_proficiencies"] = ["laser"]

    edit_yaml(data_dir, "classes.yaml", bad_weapon)

    with pytest.raises(DataValidationError, match="laser"):
        load_game_data(data_dir)


def test_unknown_quest_type_in_class_raises(data_dir):
    def bad_type(classes):
        classes[0]["quest_type_bonus"] = "cooking"

    edit_yaml(data_dir, "classes.yaml", bad_type)

    with pytest.raises(DataValidationError, match="cooking"):
        load_game_data(data_dir)


def test_duplicate_id_raises(data_dir):
    def duplicate(races):
        races[1]["id"] = races[0]["id"]

    edit_yaml(data_dir, "races.yaml", duplicate)

    with pytest.raises(DataValidationError, match="duplicad"):
        load_game_data(data_dir)


def test_non_numeric_balance_value_raises(data_dir):
    def bad_number(balance):
        balance["focus"]["ideal"]["power"] = "mucho"

    edit_yaml(data_dir, "balance.yaml", bad_number)

    with pytest.raises(DataValidationError, match="power"):
        load_game_data(data_dir)


def test_non_positive_multiplier_raises(data_dir):
    def zero(balance):
        balance["focus"]["ideal"]["power"] = 0

    edit_yaml(data_dir, "balance.yaml", zero)

    with pytest.raises(DataValidationError, match="power"):
        load_game_data(data_dir)

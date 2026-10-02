import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from apps.characters.models import Character

pytestmark = pytest.mark.django_db


@pytest.fixture
def user():
    return get_user_model().objects.create_user("aldric", password="x")


def test_new_character_gets_defaults_from_game_data(user):
    character = Character.objects.create(user=user, race="dwarf", char_class="warrior")

    assert (character.strength, character.dexterity) == (10, 10)
    assert (character.wisdom, character.constitution) == (10, 10)
    assert (character.level, character.xp, character.gold) == (1, 0, 0)
    assert character.created_at is not None


def test_valid_character_passes_validation(user):
    character = Character(user=user, race="elf", char_class="mage")

    character.full_clean()


@pytest.mark.parametrize(("race", "char_class"), [("orc", "mage"), ("elf", "paladin")])
def test_unknown_race_or_class_fails_validation(user, race, char_class):
    character = Character(user=user, race=race, char_class=char_class)

    with pytest.raises(ValidationError):
        character.full_clean()


def test_only_one_character_per_user(user):
    Character.objects.create(user=user, race="elf", char_class="mage")

    with pytest.raises(IntegrityError):
        Character.objects.create(user=user, race="dwarf", char_class="warrior")


def test_negative_stats_are_rejected(user):
    character = Character(user=user, race="elf", char_class="mage", strength=-1)

    with pytest.raises(ValidationError):
        character.full_clean()


def test_level_must_be_at_least_one(user):
    character = Character(user=user, race="elf", char_class="mage", level=0)

    with pytest.raises(ValidationError):
        character.full_clean()


def test_str_is_readable(user):
    character = Character(user=user, race="elf", char_class="mage")

    assert str(character) == "aldric (elf mage, nivel 1)"


def test_database_rejects_level_zero_even_without_validation(user):
    with pytest.raises(IntegrityError):
        Character.objects.create(user=user, race="elf", char_class="mage", level=0)

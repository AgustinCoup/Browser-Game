from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

from .gamedata import get_game_data


def validate_race(value: str) -> None:
    if value not in get_game_data().races:
        raise ValidationError("Raza desconocida: %(value)s", params={"value": value})


def validate_class(value: str) -> None:
    if value not in get_game_data().classes:
        raise ValidationError("Clase desconocida: %(value)s", params={"value": value})


# Valores iniciales: salen de data/balance.yaml (character_defaults), no del código.
def default_stat() -> int:
    return get_game_data().balance.character_defaults.base_stat


def default_level() -> int:
    return get_game_data().balance.character_defaults.level


def default_xp() -> int:
    return get_game_data().balance.character_defaults.xp


def default_gold() -> int:
    return get_game_data().balance.character_defaults.gold


class Character(models.Model):
    """Personaje de un jugador. Raza y clase se validan contra data/ (no hay choices
    en el campo para que agregar contenido no genere migraciones)."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="character"
    )
    race = models.CharField(max_length=32, validators=[validate_race])
    char_class = models.CharField(max_length=32, validators=[validate_class])

    strength = models.PositiveSmallIntegerField(default=default_stat)
    dexterity = models.PositiveSmallIntegerField(default=default_stat)
    wisdom = models.PositiveSmallIntegerField(default=default_stat)
    constitution = models.PositiveSmallIntegerField(default=default_stat)

    level = models.PositiveSmallIntegerField(
        default=default_level, validators=[MinValueValidator(1)]
    )
    xp = models.PositiveIntegerField(default=default_xp)
    gold = models.PositiveIntegerField(default=default_gold)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.user.get_username()} ({self.race} {self.char_class}, nivel {self.level})"

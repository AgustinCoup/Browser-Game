"""Acceso cacheado a los datos de juego (data/) desde la capa Django."""

from functools import lru_cache

from game.loader import GameData, load_game_data


@lru_cache(maxsize=1)
def get_game_data() -> GameData:
    return load_game_data()

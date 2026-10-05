from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render

from .gamedata import get_game_data
from .models import Character
from game.formulas import starting_stats


@login_required
def crear_personaje(request):
    data = get_game_data()
    error = None

    if request.method == "POST":
        raza = request.POST.get("raza")
        clase = request.POST.get("clase")

        if raza not in data.races or clase not in data.classes:
            error = "Raza o clase inválida."
        elif Character.objects.filter(user=request.user).exists():
            error = "Ya tienes un personaje creado."
        else:
            stats = starting_stats(data.races[raza], data.balance)
            Character.objects.create(user=request.user, race=raza, char_class=clase, **stats)
            return HttpResponse("Personaje creado exitosamente.")

    contexto = {
        "razas": data.races.values(),
        "clases": data.classes.values(),
        "error": error,
    }
    return render(request, "characters/crear_personaje.html", contexto)

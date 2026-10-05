# Register your models here.
from django.contrib import admin

from .models import Character

@admin.register(Character)
class CharacterAdmin(admin.ModelAdmin):
    list_display = ("user", "race", "char_class", "strength", "dexterity", "wisdom", "constitution")
# Guía de desarrollo paso a paso

Instrucciones para tocar cada parte del proyecto. Documento vivo: lo vamos ampliando.

**Convención de estado de cada receta:**
- ✅ **Funciona hoy**: el código y los tests ya lo soportan.
- 🟡 **Propuesta**: el formato todavía no existe; es lo que se propone construir. Según `CLAUDE.md`, antes de implementarlo se acuerda un plan.

Antes de empezar cualquier receta, leé la sección del GDD que corresponda (`docs/GDD.md`). Si lo que querés hacer contradice al GDD, avisá en vez de elegir uno.

---

## 0. Cómo comprobar que no rompiste nada

Después de cualquier cambio en `data/` o en el código:

```
pytest
ruff check . && ruff format .
```

`pytest` no necesita MySQL ni `.env`. El primer test que falla te dice qué archivo y qué campo está mal (el loader da mensajes como `races.yaml[gnome]: falta el campo obligatorio 'armor_proficiencies'`).

---

## 1. Cómo añadir una raza ✅

**Archivos que se tocan:** `data/races.yaml` y, si querés, `tests/game/test_loader.py`.
No se toca código ni se crean migraciones: las razas no están en la base de datos como tabla, se validan contra el YAML.

**Pasos:**
1. Abrí `data/races.yaml`. Arriba hay una plantilla comentada.
2. Copiá el bloque al final del archivo y sacale los `#`.
3. Completá los campos (todos obligatorios salvo `choose_bonus`):

```yaml
- id: gnome              # único, minúsculas, sin espacios, máx. 32 caracteres
  name: Gnomo            # lo que ve el jugador
  stat_bonuses:          # claves válidas: strength, dexterity, wisdom, constitution
    wisdom: 1            # enteros >= 0. Si no tiene bonos fijos: stat_bonuses: {}
    constitution: 1
  armor_proficiencies: [light]   # light, medium y/o heavy; [] si ninguna
  traits:                # [] si no tiene
    - id: tinkerer
      description: Texto del rasgo.
```

4. Opcional, bono a elección del jugador (como el humano): agregá debajo de `stat_bonuses`
```yaml
  choose_bonus:
    count: 2     # a cuántos stats distintos (1 a 4)
    amount: 1    # cuánto suma a cada uno
```
5. Corré `pytest`. Si el loader rechaza algo, el mensaje te dice qué.

**Qué hay que saber:**
- El `id` se guarda tal cual en `Character.race`. **No lo cambies** una vez que existan personajes con esa raza: quedarían apuntando a una raza que no existe.
- Las razas solo dan competencia de **armadura** (supuesto del GDD 3.4).
- Los `traits` hoy son solo descriptivos: no afectan ninguna fórmula. Para que un rasgo tenga efecto hay que escribir código en `game/` (ver recetas 9 y 10).
- El contenido tiene que ser propio, sin nombres ni lore protegidos de D&D (regla 10).
- Todavía **no se aplican** los `stat_bonuses` al crear un personaje; eso va con la pantalla de creación (receta 8).

---

## 2. Cómo añadir una clase ✅

**Archivo:** `data/classes.yaml`.

```yaml
- id: cleric
  name: Clérigo
  quest_type_bonus: mystery      # combat | infiltration | mystery (los define balance.yaml)
  role_tag: support              # vanguard | stealth | arcane | support
  weapon_proficiencies: [light]  # light, ranged y/o martial; [] si ninguna
  armor_proficiencies: []        # light, medium y/o heavy; [] si ninguna
  traits: []
```

**Qué hay que saber:**
- `quest_type_bonus` es el tipo de misión donde la clase recibe +10% de poder y ×0.95 de desgaste. Esos números salen de `data/balance.yaml` (`class_bonus`), no de la clase.
- Si la clase necesita **un efecto nuevo** que no sea ese bono (por ejemplo "el pícaro gasta menos consumibles"), el YAML solo lo describe: hay que programar el efecto en `game/formulas.py` con sus tests.
- Mismo cuidado con el `id`: no lo cambies con personajes existentes.
- La clase puede darse con cualquier raza (4 × N combinaciones); revisá que ninguna combinación quede absurda.

---

## 3. Cómo añadir una plantilla de misión ✅

**Archivo:** `data/quests.yaml` (arriba hay una plantilla comentada).

```yaml
- id: sewer_smugglers          # único, minúsculas, sin espacios
  name: Contrabandistas en las cloacas
  quest_type: combat           # combat | infiltration | mystery
  tier: 1                      # nivel de la misión, entero >= 1
  duration_minutes: 10         # cuánto dura la expedición
  difficulty: 40               # se compara contra poder + equipo + tirada
  rewards:
    xp: 30
    gold: 20
  base_wear: 5                 # desgaste base del equipo, antes de multiplicadores
  expires_after_hours: 24      # cuánto vive en el tablón
  cities: [hierrafuerte]       # dónde puede aparecer
  description: Texto corto del tablón.
```

**Qué hay que saber:**
- Una **plantilla** es el molde. Cada vez que el sistema genere una misión en un tablón, creará una **instancia** (fila en la base de datos) a partir de la plantilla. Las instancias todavía no existen (ver sección "Dónde va cada cosa").
- **"Arriesgada" no es un campo.** Cualquier misión puede serlo; lo decide el spawn (GDD 4.3).
- `cities` hoy son ids de texto libre. Todavía no hay un archivo `data/cities.yaml` que los valide, así que un typo en una ciudad pasaría sin error. Cuando exista ese archivo, el loader tiene que validar que las ciudades existan.
- Todos los números son placeholders `[AJUSTABLE]`: se calibran con simulación en `sim/`, no a ojo.

---

## 4. Cómo cambiar un número de balance ✅

**Archivo:** `data/balance.yaml`. Es lo único que se toca.
Ejemplo: pasar el enfoque ideal de ×1.20 a ×1.15 → cambiá `focus.ideal.power`.

El loader controla que el enfoque ideal siga dando más poder y menos desgaste que el no ideal, y que `unproficient_factor` no supere 1.

**Después:** si algún test tiene el número viejo escrito (por ejemplo `test_formulas.py` usa `1.20`), va a fallar. Eso es esperado: actualizá el test **y** el GDD (donde dice 1.20, para que no se contradigan).

---

## 5. Cómo añadir una arma o una armadura 🟡

**Estado real:** esto **todavía no existe**. No hay formato de ítems en `data/`, ni modelo, ni validación. Lo que sí está decidido (GDD 3.4 y 6):
- Las **armaduras** tienen peso: `light`, `medium`, `heavy`.
- Las **armas** tienen clase: `light`, `ranged`, `martial`.
- El ítem tiene un bono; sin competencia aporta 50%.
- Tiene durabilidad y puede tener afijos aleatorios.
- El GDD marca como `[DIFERIDO]` qué ítems concretos entran en cada categoría.

**Propuesta de cómo sería** (para acordar cuando toque hacer ítems):
1. Crear `data/items.yaml` con una lista de plantillas:
```yaml
- id: iron_sword
  name: Espada de hierro
  kind: weapon            # weapon | armor
  subtype: martial        # weapon: light/ranged/martial; armor: light/medium/heavy
  bonus: 5
  max_durability: 100
  price: 50
  rarity: common
```
2. Agregar una dataclass `ItemTemplate` y su parser en `game/loader.py`, siguiendo el patrón de `Race`.
3. Agregar `items` a `GameData` y cargarlo en `load_game_data`.
4. Tests en `tests/game/test_loader.py`.
5. `game/formulas.py` ya tiene `gear_bonus(item_bonus, kind, subtype, race, char_class, balance)` listo para usarse: ya recibe `kind` y `subtype`.

Cuando lleguemos acá se propone un plan y se espera tu OK, como pide `CLAUDE.md`.

---

## 6. Cómo añadir una fórmula nueva ✅

**Archivos:** `game/formulas.py` y `tests/game/test_formulas.py`. Regla 7 de `CLAUDE.md`: cada fórmula nueva lleva tests.

**Pasos (en este orden, test primero):**
1. Si la fórmula usa un número nuevo (un multiplicador, un umbral), **primero** agregalo a `data/balance.yaml`.
2. Agregalo a la dataclass `Balance` y al parser `_parse_balance` en `game/loader.py` (con la validación que corresponda).
3. Escribí el test en `tests/game/test_formulas.py` con el resultado esperado.
4. Escribí la función en `formulas.py`. Reglas: **sin Django, sin estado, sin números escritos a mano**; todo entra por parámetros.
5. Corré `pytest`.

**Anatomía de una regla** (ver la explicación en la conversación para `effective_power`):
- Una función pequeña por concepto (`focus_modifier`, `class_power_multiplier`, …).
- Las funciones compuestas (`effective_power`) multiplican los resultados de las pequeñas.
- Los valores inválidos lanzan `ValueError` (no devuelven algo silenciosamente equivocado).

---

## 7. Cómo añadir un campo a un modelo (por ejemplo, un campo al personaje) ✅

**Archivos:** `apps/<app>/models.py` + una migración nueva.

1. Editá el modelo, por ejemplo `apps/characters/models.py`.
2. Si el valor inicial es un número de balance, **no lo escribas en el modelo**: ponelo en `data/balance.yaml` (`character_defaults`), agregalo al loader y creá una función `default_xxx()` como las que ya existen.
3. Generá la migración: `python manage.py makemigrations`
4. **Revisá el archivo generado** en `apps/<app>/migrations/` (regla de `CLAUDE.md`: las migraciones siempre se revisan antes de commitear).
5. Aplicala: `python manage.py migrate`
6. Escribí el test en `tests/<app>/`.
7. Verificá que no falten migraciones: `python manage.py makemigrations --check --dry-run`

**Cuidado:** cambiar el tipo de una columna con datos reales duele. Pensá el tipo antes (por eso `xp` y `gold` son `BigInteger`).

---

## 8. Cómo añadir una pantalla (de punta a punta) 🟡

Hoy solo existe `/admin/`. Así se arma una pantalla en este proyecto (Django + HTMX, sin SPA).

**El camino que recorre una petición:**
```
Navegador → config/urls.py → apps/<app>/urls.py → views.py → (models.py / game/) → template .html → Navegador
```

**Pasos (ejemplo: pantalla "crear personaje"):**

1. **URL.** Crear `apps/characters/urls.py`:
```python
from django.urls import path
from . import views

app_name = "characters"
urlpatterns = [
    path("crear/", views.create_character, name="create"),
]
```
2. **Conectarla** en `config/urls.py`: agregar `path("personaje/", include("apps.characters.urls"))` (y `include` en el import).
3. **Vista.** En `apps/characters/views.py`: una función que recibe la petición y devuelve una página. Reglas del proyecto para la vista:
   - Exigir usuario logueado (`@login_required`).
   - **Nunca confiar en el cliente** (regla 1): el formulario manda "quiero ser enano guerrero"; el servidor valida contra `get_game_data()` y calcula los stats. El cliente jamás manda números de stats.
   - Si toca oro, ítems o cupos: envolver en `transaction.atomic()` y bloquear con `select_for_update()` (regla 5).
   - La lógica de reglas **no va en la vista**: la vista llama a funciones de `game/`.
4. **Formulario.** Un `forms.Form` de Django con campos `race` y `char_class` (choices tomadas de `get_game_data()`), más el "+1 a dos stats" si la raza es humana. Valida los datos de entrada.
5. **Template.** Crear `apps/characters/templates/characters/create.html`. Django lo encuentra solo gracias a `APP_DIRS=True` en `settings/base.py`. Se usa HTML con etiquetas de Django (`{{ variable }}`, `{% if %}`, `{% csrf_token %}` dentro de todo formulario POST).
6. **HTMX** (cuando haga falta): agregás atributos al HTML, por ejemplo `hx-post="..." hx-target="#resultado"`. La vista devuelve **solo un fragmento** de HTML (un template parcial) y HTMX lo coloca en la página sin recargar.
7. **Tests:** usar el `client` de pytest-django: `client.post(url, {...})` y verificar el resultado.
8. **Con qué hay que conectarla:** con una URL en `config/urls.py` (paso 2), con el modelo (para leer/guardar) y con `game/` (para las reglas). No necesita nada más.

**Los bonos de raza** (+2 Constitución del enano, etc.) se aplican en el paso 3, dentro de la vista de creación, llamando a una función nueva de `game/` (por ejemplo `game/formulas.py: starting_stats(race, base_stat, choices)`), con su test. Así la regla vive en `game/` y no queda escondida en la vista.

---

## 9. Dónde va cada cosa (ítems, instancias de misión, expediciones) 🟡

Regla práctica: **si se guarda por jugador y cambia con el tiempo → modelo en `apps/<app>/models.py`. Si es una regla o un número → `game/` o `data/`.**

| Cosa | Dónde | Por qué |
|---|---|---|
| Plantilla de ítem ("Espada de hierro") | `data/items.yaml` + parser en `game/loader.py` | Es contenido fijo y editable, igual que razas y clases |
| Ítem concreto de un jugador (con su durabilidad y afijos) | Modelo `ItemInstance` en `apps/items/models.py` | Es una fila por jugador que cambia (se desgasta, se vende) |
| Plantilla de misión | `data/quests.yaml` (**ya existe**) | Contenido fijo |
| Misión publicada en un tablón | Modelo `QuestInstance` en `apps/quests/models.py` | Se crea con el spawn y vence |
| Expedición (jugador saliendo a una misión) | Modelo `Expedition` en `apps/quests/models.py` | Fila con `termina_en` y semilla guardada (regla 4) |
| La fórmula que decide si la misión sale bien | `game/combat.py` | Lógica pura, simulable |
| Cómo se pierde un ítem en una misión arriesgada | `game/risk.py` | Idem, con semilla reproducible |
| El texto narrado del log | `game/narrative.py` | Idem |
| Lo que **conecta** ambos mundos (leer la fila, llamar a `game/`, guardar el resultado) | Funciones de servicio en la app (por ejemplo `apps/quests/services.py`) o en la vista | Para que `game/` siga sin importar Django |

Ejemplo de flujo al resolver una expedición: `apps/quests` carga la fila de `Expedition`, saca los datos que necesita, llama a `game/combat.py` pasándole números y la semilla, recibe un resultado y lo guarda de nuevo en la base. La lógica de azar está en `game/`; la base de datos, en `apps/`.

---

## 10. Qué son los `_` en Python (por si lo ves en el código)

- **`_nombre` al principio** (`_check_quest_type`, `_require`): convención que significa "uso interno de este archivo, no lo uses desde afuera". Python no lo impide; es una señal para quien lee.
- **`__init__.py`**: archivo (a veces vacío) que le dice a Python "esta carpeta es un paquete importable".
- **`_` solo**: variable que se descarta a propósito.
- **`UPPER_SNAKE_CASE`** (`STATS`, `ARMOR`): constantes.

---

## Pendiente de ampliar
- Cómo añadir una ciudad y su sabor de spawn (`data/cities.yaml` no existe aún).
- Cómo añadir un consumible.
- Cómo escribir un script de simulación en `sim/`.
- Cómo añadir una tarea en segundo plano.

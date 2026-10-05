# CLAUDE.md

Juego web de rol por misiones asincrónicas (estilo Gladiatus, fantasía propia cercana a D&D, región de Vaelgard). El diseño completo está en `docs/GDD.md`: **leelo antes de implementar cualquier mecánica**. Si el código y el GDD se contradicen, avisame en vez de elegir uno.

## Glosario del dominio
- **Stats:** Fuerza, Destreza, Sabiduría, Constitución. Constitución es transversal (vida y menos desgaste de equipo en cualquier misión).
- **Tipo de misión:** combate, infiltración o misterio. Lo define el spawn.
- **Enfoque:** lo elige el jugador al salir (combate, infiltración o misterio) y usa Fuerza, Destreza o Sabiduría respectivamente. Enfoque ideal = el que coincide con el tipo de misión.
- **Misión arriesgada:** etiqueta que puede tener cualquier misión. Mejor botín; si falla hay castigo (ver reglas en el GDD, sección 4.3).
- **Competencia de equipo:** el equipo tiene peso (ligero, medio, pesado). Sin competencia aporta menos bono. Raza y clase otorgan competencias y se suman.
- **Temporada:** reset global del juego. **Legado / Ecos:** ventajas permanentes entre temporadas.
- **Razas MVP:** humano, enano, elfo, mediano. **Clases MVP:** guerrero, pícaro, mago.

## Stack
- Python 3.12+, **Django**, MySQL 8 (InnoDB, utf8mb4); tests con SQLite
- Frontend: templates de Django + **HTMX** (+ Alpine.js si hace falta). Sin SPA.
- Tareas en segundo plano: Celery + Redis (o alternativa simple a decidir)
- Tests: pytest + pytest-django. Lint/format: Ruff. pre-commit.
- Deploy: Docker Compose

## Estructura (objetivo)
```
config/            # settings, urls
apps/
  characters/      # personaje, razas, clases
  quests/          # tablones, plantillas, instancias, expediciones
  parties/         # misiones grupales y confirmación
  items/           # ítems, rareza, durabilidad, tienda NPC
  market/          # mercado entre jugadores (post-MVP)
  seasons/         # temporadas y legado (post-MVP)
game/              # LÓGICA PURA de juego, sin importar Django
  formulas.py      # stats, multiplicadores de enfoque, competencias, costos
  combat.py        # motor de resolución de misiones
  risk.py          # misiones arriesgadas: castigos y pérdida de ítems
  narrative.py     # generación del log narrado
data/              # razas, clases, ítems, plantillas de misión, ciudades (YAML/JSON)
sim/               # scripts de simulación de economía y balance
docs/GDD.md
```

## Reglas que NUNCA se rompen
1. **El servidor es autoritativo.** El cliente pide acciones; nunca envía resultados ni cantidades. Validar permisos y estado en cada acción.
2. **Todo el tiempo en UTC** en el servidor. Nunca confiar en el reloj del cliente.
3. **Evaluación perezosa:** no hay tick global. Se guarda `valor`, `tasa`, `ultima_actualizacion` y se calcula al leer.
4. **Las expediciones son filas con `termina_en`.** Se resuelven al vencer, con **semilla aleatoria guardada** para poder reproducirlas (incluida la pérdida de ítems en misiones arriesgadas).
5. **Toda operación que toque oro, ítems o cupos va en transacción** con bloqueo de fila (`select_for_update`) para evitar doble gasto y condiciones de carrera.
6. **Misiones grupales:** la confirmación final bloquea la fila del grupo para que la misión se lance una sola vez. Los consumibles se gastan al lanzar; si falta alguno, la misión sale sin él. El timeout de confirmación es de 24 h.
7. **Fórmulas, costos y balance viven en `game/` y `data/`**, no dispersos en vistas o modelos. Cada fórmula nueva lleva tests.
8. **`game/` no importa Django.** Debe poder testearse y simularse sola.
9. **Registrar cada transacción económica** (log de auditoría) para detectar bugs de duplicación.
10. Contenido propio: no usar nombres, criaturas ni lore protegidos de D&D.

## Convenciones
- Código y nombres técnicos en inglés; textos del juego y documentación en español.
- Cambios chicos y verificables, en rama propia, con tests.
- Migraciones siempre revisadas antes de commitear.
- No hardcodear números de balance (multiplicadores de enfoque, bonos de clase, pesos de spawn, frecuencia de arriesgadas, etc.): van a `data/`. Los números marcados [AJUSTABLE] en el GDD se calibran con simulación.

## Comandos
```
# Setup (una vez)
python -m venv .venv && .venv/Scripts/activate      # Windows; en Linux/Mac: source .venv/bin/activate
pip install -r requirements/dev.txt
cp .env.example .env                                 # completar SECRET_KEY y DATABASE_URL
pre-commit install

pytest                                               # tests (SQLite en memoria, no requiere MySQL)
ruff check . && ruff format .                        # lint + formato
python manage.py check                               # chequeo de configuración
python manage.py makemigrations --check --dry-run    # verifica que no falten migraciones
python manage.py migrate                             # aplica migraciones (requiere MySQL según .env)
python manage.py runserver
docker compose up --build                            # app + MySQL con Docker Compose
```

## Cómo trabajar conmigo
- Para mecánicas nuevas: primero proponé un **plan** y esperá mi OK antes de escribir código.
- Antes de cualquier mecánica económica o de balance, escribí un script en `sim/` que simule 30 días de juego y mostrá los números.
- Explicá en pocas líneas las decisiones de diseño en las partes críticas (economía, autenticación, concurrencia).
- Si algo del GDD está marcado como [ABIERTO] o [PROPUESTA], preguntame en vez de decidir solo.
- **Modo aprendizaje (por defecto):** soy novato en Python y HTML y quiero entender todo. Yo escribo el código; vos guiás. No edites archivos del proyecto salvo que te lo pida (podés leerlos y correr comandos de solo lectura). Esto aplica a este proyecto salvo que diga lo contrario.
  - Un paso por vez. Explicá el porqué en lenguaje simple (qué hace cada línea y cómo encaja en Django/HTML) y terminá cada paso con una tarea concreta para que yo la escriba.
  - Dame pistas y fragmentos cortos, no la solución completa. Si me trabo, mostrame más.
  - Cuando haya lógica de juego: TDD. Primero el test (que falle y lo veamos fallar), después la función en `game/`, después usarla en la vista.
  - Cuando te pegue código mío, revisalo: qué está bien, bugs y detalles de estilo (Ruff: `ruff check . --fix` y `ruff format .`).
  - Los tests se corren con `pytest` en el venv (no dentro de Docker: el contenedor solo tiene `requirements/base.txt`). Docker es para ver el juego en el navegador.
  - Antes de arrancar, mirá el estado del repo (`git diff`, `docs/PENDIENTES.md`) para saber dónde estoy, y proponé el siguiente paso pequeño.
- Orden sugerido de trabajo: 1) esqueleto del proyecto y modelos de datos, 2) `game/formulas.py` con tests (empezando por el multiplicador de enfoque ideal vs no ideal), 3) un tablón con spawn ponderado, 4) expedición con timer y log narrado, 5) equipo con durabilidad y tienda NPC, 6) misiones arriesgadas.

# Cosas que faltan tener y entender

Lista viva. Marcá con `[x]` lo que vayas completando.
Estado revisado el 2026-10-02.

## A. Cosas que faltan instalar o configurar

### [ ] A1. Archivo `.env` (lo más urgente, sin esto Django no arranca)
Hoy **no existe** `.env`. Django exige `SECRET_KEY` y `DATABASE_URL` y falla si faltan.
1. Copiá `.env.example` a `.env` (en PowerShell: `Copy-Item .env.example .env`).
2. Cambiá `SECRET_KEY=cambiame` por una clave larga y al azar. Para generarla:
   `python -c "import secrets; print(secrets.token_urlsafe(50))"`
3. `.env` nunca se sube a git (ya está en `.gitignore`).

> Los **tests** (`pytest`) NO necesitan `.env` ni MySQL: `config/settings/test.py` pone sus propios valores y usa SQLite en memoria.

### [ ] A2. Una base de datos MySQL para correr el juego "de verdad"
Hoy **no hay MySQL instalado**. Para `runserver` y `migrate` necesitás uno. Dos caminos:

| Camino | Qué es | Cuándo conviene |
|---|---|---|
| **Docker Compose** (recomendado por el proyecto) | Docker levanta MySQL y la app en contenedores con un solo comando | Es lo que define `docker-compose.yml`. Evita instalar MySQL a mano y deja el entorno igual al de producción |
| MySQL instalado directo en Windows | Instalador de MySQL Community Server | Si Docker te da problemas. Después ajustás `DATABASE_URL` en `.env` |

### [ ] A3. Docker Desktop (¿hace falta? Sí si elegís el camino recomendado)
Hoy **no está instalado**. Pasos en Windows 10:
1. Bajá **Docker Desktop for Windows** desde docker.com.
2. Necesita **WSL 2** (Windows Subsystem for Linux). El instalador lo ofrece activar. Puede pedir reiniciar la PC.
3. Si pide virtualización y falla: entrá a la BIOS y activá "Virtualization" (VT-x / SVM).
4. Verificá: abrí una terminal nueva y corré `docker --version` y `docker compose version`.
5. Primera vez: `docker compose up --build` en la carpeta del proyecto (tarda unos minutos).
6. En otra terminal, con los contenedores arriba: `docker compose exec web python manage.py migrate`.

Cuando llegues a este punto, avisame y lo hacemos juntos paso a paso.

> Docker **no es obligatorio para empezar a desarrollar las reglas**: `game/`, `data/` y los tests corren solos con Python. Lo necesitás recién cuando quieras ver el juego en el navegador.

### [ ] A4. Pasos de setup que ya están documentados en `CLAUDE.md` (sección Comandos)
- Crear el entorno virtual: `.venv` ya existe en tu carpeta.
- `pip install -r requirements/dev.txt`
- `pre-commit install`

Nota: `mysqlclient` se compila al instalar y en Windows suele dar error si no hay herramientas de compilación. Si `pip install` falla en ese paquete, decímelo y lo resolvemos (es otro motivo para usar Docker, donde ya está resuelto en el `Dockerfile`).

### [ ] A5. Versión de Python
Tenés Python 3.14.5; el proyecto pide 3.12+ y el Dockerfile usa 3.12. Debería andar, pero si algo raro falla al instalar paquetes, esa diferencia es la primera sospecha.

## B. Cosas que faltan construir (del lado del código)

- [ ] Vistas, URLs y templates del juego (hoy solo existe `/admin/`). Ver `docs/GUIA_DESARROLLO.md`, sección "Cómo añadir una pantalla".
- [ ] Pantalla de creación de personaje, que es donde se aplican los bonos de raza y el "+1 a dos stats" del humano.
- [ ] Modelos de ítems, instancias de misión y expediciones (ver `GUIA_DESARROLLO.md`, sección "Dónde va cada cosa").
- [ ] `game/combat.py`, `game/risk.py`, `game/narrative.py`.
- [ ] Scripts de simulación en `sim/` (obligatorios antes de cualquier mecánica económica).
- [ ] Tareas en segundo plano (spawn de misiones y resolución de expediciones): Celery + Redis u otra alternativa. Decisión abierta.
- [ ] HTMX en los templates.
- [ ] Datos de ítems en `data/` (armas y armaduras). Todavía no existe el formato.

## C. Conceptos para entender (marcá a medida que los entiendas)

- [ ] **YAML**: formato de texto para datos, como JSON pero legible y con comentarios.
- [ ] **Django**: framework web de Python. Ver explicación en la conversación; resumen en `GUIA_DESARROLLO.md`.
- [ ] **Modelo / migración**: clase Python que representa una tabla / archivo que cambia la tabla.
- [ ] **Vista / URL / template**: cómo una dirección del navegador termina en una página.
- [ ] **HTMX**: atributos en el HTML que piden fragmentos al servidor sin recargar la página.
- [ ] **Transacciones y `select_for_update`**: evitar que dos acciones simultáneas dupliquen oro o ítems.
- [ ] **Semilla aleatoria**: guardar el número inicial del azar para poder reproducir una misión.
- [ ] **Evaluación perezosa**: no hay reloj global; se calcula el estado al leerlo.
- [ ] **Zona horaria y UTC**: ver nota en la conversación sobre UTC-3.

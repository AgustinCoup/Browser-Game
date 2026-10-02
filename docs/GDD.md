# GDD v1 — Juego web de rol por misiones (working title: "Tablón")

> Documento vivo. Marcas: **[DECIDIDO]** lo definió el autor del juego. **[AJUSTABLE]** número inicial para calibrar con simulación. **[PROPUESTA]** idea de Claude pendiente de aprobación. **[ABIERTO]** falta decidir. **[DIFERIDO]** queda para después del MVP.

## 1. Visión

Juego de navegador asincrónico, estilo Gladiatus, con fantasía cercana a D&D (razas, clases y lore propios). Cada jugador tiene un personaje con identidad mecánica desde el inicio (raza + clase), hace misiones cortas desde tablones de ciudades de la región de **Vaelgard**, consigue xp, oro y equipo mágico, y a largo plazo se une con otros jugadores para misiones difíciles. El juego se organiza en **temporadas globales** con reinicio y ventajas permanentes. **[DECIDIDO]**

Tono de los logs de misión: **épico / oscuro** **[DECIDIDO]**.

## 2. Core loop

> Elijo una misión del tablón → elijo el enfoque y llevo consumibles → salgo (tarda X minutos) → vuelvo con xp, oro y loot → el equipo se desgasta y gasto oro en repararlo y reponer → eso me permite encarar misiones más difíciles.

Meta-loop: temporada → reset → Legado (ventajas permanentes) + posibilidad de cambiar de clase en la próxima run.

## 3. Personaje

### 3.1 Stats **[DECIDIDO]**
Cuatro stats primarios:

| Stat | Rol |
|---|---|
| **Fuerza** | Poder en misiones de **combate** |
| **Destreza** | Poder en misiones de **infiltración** |
| **Sabiduría** | Poder en misiones de **misterio** |
| **Constitución** | Transversal: aporta vida y reduce el desgaste de equipo en cualquier tipo de misión |

Derivados (Vida, Defensa, Evasión, Crítico, Poder de hechizo): fórmulas en `game/formulas.py`. Los valores exactos de Constitución son **[AJUSTABLE]**.

Valores iniciales de un personaje nuevo **[DECIDIDO por ahora, AJUSTABLE — placeholders]**: cada stat base 10 (más los bonos de raza), nivel 1, xp 0, oro 0. Viven en `data/balance.yaml`.

### 3.2 Razas **[DECIDIDO]**
| Raza | Rasgos |
|---|---|
| **Humano** | +1 a dos stats a elección. Competencia en equipo de peso medio por defecto |
| **Enano** | +2 Constitución. Competencia en equipo pesado |
| **Elfo** | +2 Sabiduría. Competencia en equipo ligero |
| **Mediano** | +2 Destreza. Competencia en equipo ligero. **Suerte:** una vez por misión relanza la peor tirada del resultado |

### 3.3 Clases **[DECIDIDO]**
| Clase | Rasgos |
|---|---|
| **Guerrero** | Bono en misiones de combate. Competencia en todas las armas desde el inicio |
| **Pícaro** | Bono en misiones de infiltración. Competencia en armas ligeras. Consumibles de infiltración más eficientes |
| **Mago** | Bono en misiones de misterio. Combate sin armas usando hechizos. Bono a los efectos de los objetos mágicos |

Bono de clase: **+10% de poder efectivo** en su tipo de misión **[DECIDIDO por ahora, AJUSTABLE]**.

Además, la clase **reduce levemente el desgaste de equipo** en su tipo de misión: **×0.95** **[DECIDIDO por ahora, AJUSTABLE — placeholder]**. Se combina de forma **multiplicativa** con el multiplicador de enfoque (ver 4.2).

### 3.4 Competencias de equipo **[DECIDIDO por ahora, AJUSTABLE]**
El equipo tiene peso (ligero, medio, pesado) y las razas y clases otorgan competencia. **Usar equipo sin competencia no está prohibido: el equipo aporta menos bono de lo normal.** **[DECIDIDO]**

Reglas **[DECIDIDO por ahora, AJUSTABLE]**:
- Sin competencia, el equipo aporta **50% de su bono**.
- Las competencias de raza y de clase **se suman**: basta con que una de las dos la otorgue.

Clasificación **[DECIDIDO]**: el **peso** (ligero, medio, pesado) es propio de las **armaduras**; las **armas** se clasifican en **ligeras, a distancia y marciales**.

Supuestos de implementación **[DECIDIDO por ahora, AJUSTABLE]**:
- Las **razas** otorgan competencia solo de **armadura** (por peso); las **clases** otorgan competencia de **armas** (Guerrero: ligeras, a distancia y marciales; Pícaro: ligeras; Mago: ninguna, usa hechizos). Las clases no otorgan competencia de armadura por ahora.
- Un usuario tiene **un solo personaje**.

Pendiente **[DIFERIDO]**: qué ítems concretos entran en cada peso de armadura y cada clase de arma, al diseñar los datos de ítems.

### 3.5 Etiquetas de rol **[DECIDIDO por ahora]**
Vanguardia, Sigilo, Arcano, Apoyo. Cada clase aporta una; se usan para los incentivos blandos de cooperación (sección 5).

Todo definido como **datos** (YAML/JSON), no hardcodeado. MVP: 4 razas × 3 clases = 12 combinaciones.

## 4. Misiones

### 4.1 Tablones y spawn **[DECIDIDO]**
- Cada ciudad tiene un tablón. Un job periódico genera instancias desde plantillas, hasta un tope por ciudad y tier, con vencimiento.
- **El spawn es aleatorio y ponderado por el "sabor" de cada ciudad** (ver sección 12). Si un jugador se especializa, a veces no tendrá misiones de su tipo cerca y deberá viajar, esperar o salir de su zona de confort.
- Cada jugador ve y toma misiones de forma independiente (la misión individual no desaparece para el resto).

### 4.2 Tipos de misión y enfoque **[DECIDIDO, números AJUSTABLE]**
**Tipo de misión** (lo define el spawn): **combate**, **infiltración** o **misterio**.

**Enfoque** (lo elige el jugador al salir): combate, infiltración o misterio. Usa el stat correspondiente (Fuerza, Destreza, Sabiduría). El **enfoque ideal** es el que coincide con el tipo de misión:

| Situación | Poder efectivo | Desgaste de equipo |
|---|---|---|
| Enfoque ideal | ×1.20 | ×0.80 |
| Enfoque no ideal | ×0.90 | ×1.30 |

Los multiplicadores de enfoque, el bono de clase (3.3) y los demás se combinan de forma **multiplicativa** **[DECIDIDO]**. Ejemplo: enfoque ideal + bono de clase = poder ×1.20 × 1.10 = ×1.32; desgaste ×0.80 × 0.95 = ×0.76.

Valores iniciales para calibrar con simulación. Cualquier enfoque es posible: el jugador evalúa costo/beneficio. Fórmula orientativa de resolución: `éxito = poder_efectivo + equipo + tirada(semilla) vs dificultad`.

Efecto buscado: especializarte da ventaja real, pero el spawn por ciudad te obliga a diversificar un poco.

### 4.3 Misiones arriesgadas **[DECIDIDO por ahora, AJUSTABLE]**
Cualquier misión (de cualquier tipo) puede aparecer con la **etiqueta "arriesgada"**: mejor botín, pero con castigo si falla.

Si una misión arriesgada falla:
- Sin recompensa
- Doble desgaste de equipo
- Estado **Herido** (tiempo de recuperación antes de salir de nuevo; la duración es proporcional al nivel de la misión)
- Una tirada decide si se pierde **oro** (cantidad proporcional al nivel de la misión) o un **ítem**

Reglas **[DECIDIDO por ahora, AJUSTABLE]**:
- **Frecuencia:** aparece 1 misión arriesgada por ciudad cada 8 horas.
- **Botín:** 50% mejor que una misión normal equivalente.

**Pérdida de ítem** **[DECIDIDO por ahora, AJUSTABLE]**: cuando la tirada decide por ítem, se elige **al azar entre todos los ítems del jugador**, ponderado por rareza. Cuanto **mayor es el nivel de la misión arriesgada respecto del nivel del personaje**, más chances hay de perder un ítem más raro. La fórmula exacta de los pesos es **[ABIERTO]** y se define con simulación (en `game/`, con tests y semilla reproducible).

Riesgo de diseño a vigilar: perder un ítem muy raro puede frustrar mucho. Si pasa, se puede acotar con un tope de rareza o un seguro.

### 4.4 Resolución
- La expedición es una fila con `termina_en`. Al vencer, el servidor simula con una **semilla aleatoria guardada** (reproducible) y genera un **log narrado** (plantillas épicas/oscuras).
- Todas las decisiones se toman antes de salir: enfoque, consumibles, equipo, compañeros.

### 4.5 Viaje **[DECIDIDO por ahora]**
Viajar entre ciudades cuesta tiempo y algo de oro (sink), con una tabla de distancias simple.

## 5. Misiones grupales

Flujo asincrónico **[DECIDIDO]**:
1. Se publica una misión grupal con N slots.
2. Los jugadores se anotan. **La misión no avanza hasta que todos los slots estén completos.**
3. Con el equipo completo comienza la **fase de confirmación**: cada jugador ve la composición completa y puede **confirmar** o **salirse**.
4. Si **todos confirman**, la misión se lanza **en el momento en que confirma el último** (no hace falta coincidir conectados).
5. Si alguien se sale, su slot se reabre y **todas las confirmaciones se reinician**.

Reglas cerradas **[DECIDIDO]**:
- **Timeout de confirmación: 24 h.** Si vence, quienes no confirmaron salen, sus slots se reabren y se reinician las confirmaciones.
- **Los consumibles se gastan al lanzar la misión**, no antes. Si a alguien le falta uno en ese momento, **la misión se lanza sin el faltante**.
- Sin reserva de consumibles y **sin cooldown** al salirse. Riesgo conocido: alguien podría entrar y salir repetidamente; revisar si aparece en la práctica.
- La confirmación final **bloquea la fila del grupo** (`select_for_update`) para que la misión se lance una sola vez aunque dos jugadores confirmen a la vez.

Incentivos blandos a la cooperación **[PROPUESTA]**:
- Obstáculos opcionales que resuelve una etiqueta concreta (un pícaro abre la puerta gratis; un guerrero la fuerza y pierde durabilidad).
- Bono pequeño por diversidad de roles (más botín o menos desgaste).
- Se puede jugar sin sinergia, pero con ella es más barato y rápido.

**[DIFERIDO]**: cómo se aplican tipo y enfoque en misiones grupales de varias etapas, y compañeros NPC contratables.

## 6. Economía

Principio: todo recurso que entra (faucet) tiene una forma de salir (sink).

- **Faucets**: oro de misiones, loot, venta a NPC.
- **Sinks**: reparación, consumibles, comisión del mercado, tasa por publicar, viaje, servicios (posada, entrenador), oro perdido en misiones arriesgadas fallidas.
- Equipo con **durabilidad**; venta a NPC a precio bajo para que el mercado entre jugadores sea la vía de ganancia.
- Loot con **afijos aleatorios** y nivel de ítem.
- Antes de implementar, **simular** en `sim/` cuánto oro entra y sale por jugador por día en cada etapa.

## 7. Temporadas y Legado **[DECIDIDO]**

- Temporadas **globales**: todos reinician juntos.
- **Duración: 12 semanas + 1 semana de intertemporada** (para elegir clase y gastar Legado). **La primera temporada es un piloto de 4 semanas** para probar balance con pocos jugadores.
- Al completar una temporada se ganan **Ecos** (puntos de Legado) según participación y logros. Se gastan en:
  - Desbloquear clases y variantes de inicio (bonos **horizontales**, sin tope)
  - Títulos y cosméticos
  - Bonos **verticales** pequeños, con **tope total de +10% en stats iniciales**, para que el veterano no aplaste al nuevo
- **Cambiar de clase** en la próxima run es parte de la recompensa del reset.
- Se puede **retirarse** antes de que termine la temporada para rehacer el personaje.

## 8. Modelo de datos (borrador)

`Character`, `Race`, `Class`, `ItemTemplate`, `ItemInstance`, `QuestTemplate`, `QuestInstance`, `Expedition`, `CombatLog`, `MarketListing`, `Party` (+ `PartyMember` con estado de confirmación), `Season`, `Legacy`.

## 9. MVP

- 4 razas, 3 clases (sección 3)
- 1 ciudad con tablón (**Hierrafuerte**) y ~10 plantillas de misión de los 3 tipos
- Misión individual con enfoque, timer y log narrado
- Equipo con durabilidad, 1 tienda NPC, consumibles
- Misiones arriesgadas (sección 4.3) **[DECIDIDO]**
- **Fuera del MVP**: más ciudades y viaje, mercado entre jugadores, grupos, temporadas y Legado

## 10. Contenido y derechos
Razas, clases, criaturas y lore **propios**. Las razas y clases genéricas (humano, enano, elfo, mediano, guerrero, pícaro, mago) son arquetipos comunes de la fantasía, pero no se deben usar criaturas, nombres ni lore protegidos de D&D. Si se quiere usar el SRD, verificar los términos vigentes. Los nombres de ciudades son provisorios: verificar que no choquen con marcas existentes antes de publicar.

## 11. Pendientes (resumen)
1. Qué cuenta como arma y qué como armadura en cada peso: se define al diseñar los datos de ítems (3.4)
2. Fórmula exacta de los pesos por rareza y nivel relativo en la pérdida de ítems (4.3)
3. Incentivos blandos de cooperación en grupos, post-MVP (5)
4. Lore de Vaelgard y justificación narrativa del reset de temporada: **[DIFERIDO]**, no hace falta por ahora (12)

## 12. Mundo: región de Vaelgard **[DECIDIDO]**

Lore, historia y tono de la región: **[DIFERIDO]**. Ciudades aprobadas por ahora (nombres provisorios) con los pesos de spawn por tipo de misión **[AJUSTABLE]**:

| Ciudad | Personalidad | Combate | Infiltración | Misterio |
|---|---|---|---|---|
| **Hierrafuerte** | Fortaleza de guarniciones y mercenarios | 60% | 20% | 20% |
| **Marenegra** | Puerto de canales, contrabando y gremios ocultos | 20% | 60% | 20% |
| **Alta Cendra** | Ciudad de academias, archivos y magos | 15% | 25% | 60% |
| **Vadoplata** | Cruce de rutas y centro del mercado, equilibrada | 34% | 33% | 33% |
| **Hondonar** | Minas abiertas sobre ruinas antiguas | 35% | 20% | 45% |

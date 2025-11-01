# LOGICA MOTOR SIMULACION

Vamos a diseñar un motor que sea robusto, balanceable y divertido, conectando todas las entidades que ya definimos.

La clave no es simular física real (eso es para un racing sim), sino simular **rendimiento** y **probabilidad** (eso es para un manager sim).

Aquí está la arquitectura del motor de simulación, dividido en fases.

## 1. El Concepto Central: El "Performance Score" (PS)
En lugar de calcular directamente "tiempos de vuelta" en segundos (lo cual es muy difícil de balancear), vamos a calcular un "**Performance Score**" (PS) abstracto para cada piloto en cada vuelta.

* Un PS más alto significa una vuelta más rápida.

* El tiempo total de carrera será un cálculo inverso basado en la suma de los PS de todas las vueltas.

* Esto nos permite sumar y restar "puntos de rendimiento" de diferentes fuentes (motor, piloto, neumáticos) de forma sencilla.

## 2. Fase 1: Simulación de Clasificación (El "PS Ideal")
Aquí medimos el rendimiento puro del coche y el piloto, sin tráfico, sin desgaste a largo plazo, y con combustible mínimo. Este será nuestro `PS_Base` para la carrera.

La fórmula se calcula una vez por piloto para la Qually:

### A. Factor Coche (Adaptado al Circuito)
Primero, vemos qué tan bueno es el coche para este circuito específico.

`Adaptacion_Coche_Circuito = (Coche.motor * Circuito.potencia_influencia) + (Coche.aerodinamica * Circuito.aero_influencia) + (Coche.manejo * Circuito.manejo_influencia)`

* Ejemplo: En Monza (`potencia_influencia = 0.8`), el `Coche.motor` importa muchísimo más que el `Coche.manejo`. En Mónaco (`manejo_influencia = 0.7`), es al revés.

### B. Factor Piloto (Habilidad Pura)
`Rendimiento_Piloto = (Piloto.velocidad * 0.6) + (Piloto.consistencia * 0.2) + (Piloto.experiencia * 0.2)`

### C. PS de Clasificación (Final)
Ahora combinamos ambos, dándole más peso al coche (esto es F1).

`PS_Qually = (Adaptacion_Coche_Circuito * 0.7) + (Rendimiento_Piloto * 0.3)`

* Balanceo: Este `0.7` y `0.3` es nuestra "perilla" principal de balanceo. ¿Importa más el coche o el piloto? Empezamos con 70/30.

### D. Variabilidad (RNG)
Añadimos el factor "suerte" o "vuelta mágica".

`RNG_Factor = random_number(-1, 1) * (1 - Piloto.consistencia / 100) * (Piloto.riesgo / 100)`

* Un piloto consistente (alta `consistencia`) tendrá un `RNG_Factor` cercano a cero (tiempos estables).

* Un piloto arriesgado (alto `riesgo`) tendrá un `RNG_Factor` más amplio (puede hacer una pole increíble o un error costoso).

`PS_Qually_Final = PS_Qually + (PS_Qually * RNG_Factor)`

El resultado de esto ordena la parrilla de salida.

## 3. Fase 2: Simulación de Carrera (El Bucle Principal)
Este es el corazón del backend. El servidor Flask ejecutará un bucle, `for vuelta in 1...Circuito.vueltas:`.

Dentro de ese bucle, otro bucle: `for piloto in lista_de_pilotos:`.

Para cada piloto, en cada vuelta, calculamos su `PS_Vuelta_Carrera`.

`PS_Vuelta_Carrera = PS_Base + Modificadores_Dinamicos`

`PS_Base` es el `PS_Qually` que calculamos antes (el rendimiento ideal). Los `Modificadores_Dinamicos` son lo que hace la carrera interesante:

### A. Modificador: Neumáticos (`mod_neumaticos`)
* Cada compuesto (Blando, Medio, Duro) tiene un `PS_bono_base` (ej: Blando +5, Medio +2, Duro 0) y un `factor_desgaste` (ej: Blando 1.0, Medio 0.6, Duro 0.3).

* `desgaste_vuelta = Circuito.desgaste_neumaticos * factor_desgaste`

* `neumatico.desgaste_actual += desgaste_vuelta`

* `penalizacion_desgaste = (neumatico.desgaste_actual ^ 2) * K` (El desgaste no es lineal; un 80% de desgaste penaliza mucho más que un 40%. Usamos una constante `**K**` para balancear).

* `mod_neumaticos = PS_bono_base - penalizacion_desgaste`

### B. Modificador: Combustible (`mod_combustible`)
* El coche empieza con una carga (ej: 100 kg).

* `coche.combustible_actual -= Coche.consumo_combustible` (por vuelta).

* `penalizacion_peso = coche.combustible_actual * K_fuel` (Una constante K_fuel que define cuánto penaliza el peso).

* `mod_combustible = -penalizacion_peso` (El coche es más lento al principio y más rápido al final).

### C. Modificador: Estrategia de Ritmo y ERS (`mod_ritmo`)
Esta es la **decisión del jugador** (o IA). El piloto tiene un "Ritmo":

1. **Conservador**: Carga `Coche.componentes.ERS` (batería). `mod_ritmo = -5`.

2. **Normal**: Neutral. `mod_ritmo = 0`.

3. **Ataque ("Push")**: Gasta batería. `mod_ritmo = +7`. (No se puede usar si la batería está vacía).

### D. Modificador: Tráfico y DRS (`mod_trafico`)
* El motor calcula la distancia con el coche de adelante (`distancia_adelante`).

* `if distancia_adelante < 1.0s AND en_zona_DRS`: -> `mod_trafico = +8` (Bono DRS).

* `if distancia_adelante < 0.8s AND NO en_zona_DRS`: -> `mod_trafico = -3` (Penalización por "aire sucio").

### E. Modificador: Cansancio y Errores (mod_piloto)
* `Piloto.estado_fisico` y `Piloto.estado_mental` bajan lentamente cada vuelta.

* `Piloto.prob_error` (que definimos en las entidades) aumenta a medida que baja su estado.

* `mod_piloto` es un pequeño penalizador si el piloto está cansado.

## 4. Eventos (RNG) y Decisiones Estratégicas
Después de calcular el `PS_Vuelta_Carrera` de cada piloto, el motor corre una "lotería" de eventos para esa vuelta.

* **Error de Piloto**:

  * `if random() < Piloto.prob_error`: -> **Evento "Bloqueo de Ruedas"**.

  * Impacto: El `PS_Vuelta_Carrera` de esta vuelta se reduce en un 40%.

* **Fallo Mecánico**:

  * `prob_fallo = (1 - Coche.fiabilidad / 100) + (Coche.componentes[motor].desgaste / 100)`

  * `if random() < prob_fallo`: -> **Evento "Fallo de Motor"**.

  * Impacto: Abandono (DNF) o modo "limp-home" (cojear hasta boxes) con un `PS` muy bajo.

* **Eventos de Pista (Safety Car, Clima)**:

  * `if random() < Circuito.prob_safety_car`: -> **Evento "Safety Car"**.

  * Impacto: Todos los coches se agrupan (se resetean las distancias). Esto es un trigger estratégico clave: ¿parar en boxes ahora?

  * `if random() < Circuito.prob_lluvia`: -> **Evento "Empieza a llover"**.

  * Impacto: Todos los coches con gomas de seco reciben un `mod_neumaticos = -50` (penalización masiva), forzando a todos a parar.

## 5. Acción Estratégica: La Parada en Boxes (Pit Stop)
Esto no es un evento de RNG, es una acción (disparada por el jugador o la IA).

* Cuando un coche entra a boxes, no calcula un `PS` para esa vuelta.

* Se le asigna un "costo de tiempo" (que se traducirá a una penalización de PS total):

* `Tiempo_Pit = Tiempo_Pitlane_Base + Tiempo_Cambio_Gomas`

* `Tiempo_Cambio_Gomas` se calcula basado en la `habilidad`, `fatiga` y `moral` del `Staff.Mecánico`.

  * Un buen equipo: 2.5s. Un mal equipo: 4.5s.

  * También hay una `prob_error_pit` (basada en `Staff.errores`) de que la parada dure 10s.

El coche sale con `neumatico.desgaste_actual = 0` y `coche.combustible_actual` (si se permite recargar).
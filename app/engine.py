# Contenido para: app/engine.py

import random
import time
from app.models import Piloto, Coche, Circuito
from app import db

# --- Constantes de Balanceo del Juego ---
# Estas son las "perillas" que ajustaremos para hacer el juego divertido.

# Ponderación de Qually: ¿Qué importa más, el coche o el piloto?
W_QUALLY_COCHE = 0.70  # 70%
W_QUALLY_PILOTO = 0.30 # 30%

# Ponderación de Ritmo de Piloto (Qually)
W_PILOTO_VELOCIDAD = 0.6
W_PILOTO_CONSISTENCIA = 0.2
W_PILOTO_EXPERIENCIA = 0.2

# Modificadores de Carrera (puntos de PS)
MOD_RITMO_ATAQUE = 7.0
MOD_RITMO_CONSERVADOR = -5.0
MOD_DRS = 8.0
MOD_AIRE_SUCIO = -3.0
K_FUEL_PENALTY = 0.02 # Puntos de PS perdidos por cada kg de combustible
K_NEUMATICO_PENALTY = 0.05 # Multiplicador de penalización por desgaste (cuadrático)
PROB_ERROR_PILOTO_BASE = 0.01 # Probabilidad base de error por vuelta
PROB_FALLO_MECANICO_BASE = 0.005 # Probabilidad base de fallo por vuelta
TIEMPO_BASE_PIT_STOP = 22.0 # Segundos (incluye entrada y salida)


class PilotoEnCarrera:
    """
    Clase interna para manejar el ESTADO VIVO de un piloto durante la simulación.
    No se guarda en la BD, vive solo en el motor.
    """
    def __init__(self, piloto_db: Piloto, coche_db: Coche):
        self.piloto_db = piloto_db  # El objeto Piloto de la BD (datos estáticos)
        self.coche_db = coche_db    # El objeto Coche de la BD (datos estáticos)

        # --- Estado Dinámico (cambia cada vuelta) ---
        self.ps_base = 0.0          # Performance Score Ideal (calculado en Qually)
        self.tiempo_total_carrera = 0.0 # Segundos acumulados
        self.vuelta_actual = 0
        self.posicion_actual = 0
        self.esta_en_pista = True   # False si choca o abandona (DNF)
        self.esta_en_pit_lane = False
        
        # Estado de componentes
        self.combustible_actual = 110.0 # kg
        self.bateria_ers = 100.0      # %
        
        # Neumáticos (simplificado por ahora)
        self.neumatico_compuesto = "Medio"
        self.neumatico_desgaste = 0.0   # %
        self.neumatico_vueltas = 0      # Vueltas con este compuesto

        # Estrategia
        self.ritmo_actual = "Normal" # Normal, Ataque, Conservador
        self.solicitar_pit_stop = False

    def actualizar_desgaste(self, factor_desgaste_circuito):
        """Actualiza el desgaste del neumático"""
        # El desgaste base se multiplica por el factor del circuito
        desgaste_base_vuelta = 1.5 # % por vuelta en un compuesto Medio
        self.neumatico_desgaste += desgaste_base_vuelta * factor_desgaste_circuito
        self.neumatico_vueltas += 1

    def actualizar_combustible(self):
        """Actualiza el combustible"""
        # Simplificado: consumo fijo por vuelta
        self.combustible_actual -= 1.8 # kg por vuelta

    def actualizar_bateria_ers(self):
        """Actualiza la batería según el ritmo"""
        if self.ritmo_actual == "Ataque":
            self.bateria_ers = max(0, self.bateria_ers - 10) # Gasta 10%
        elif self.ritmo_actual == "Conservador":
            self.bateria_ers = min(100, self.bateria_ers + 5) # Carga 5%
        else: # Normal
            self.bateria_ers = min(100, self.bateria_ers + 2) # Carga leve


class SimulationEngine:
    """
    El Cerebro. Orquesta toda la simulación de una carrera.
    """
    def __init__(self, circuito_id):
        self.circuito = db.session.get(Circuito, circuito_id)
        if not self.circuito:
            raise Exception(f"Circuito con id {circuito_id} no encontrado")

        self.vuelta_actual = 0
        self.vueltas_totales = self.circuito.vueltas
        self.log_eventos = []
        self.terminada = False
        self.estado_pista = "Seco" # Seco, Lluvia, SafetyCar

        # Cargamos los pilotos y coches
        self.pilotos_en_carrera = self._cargar_participantes()
        self.orden_pilotos = [] # Lista de IDs ordenados por posición

    def _cargar_participantes(self):
        """Carga todos los pilotos y sus coches desde la BD"""
        pilotos_db = db.session.query(Piloto).filter(Piloto.equipo_id.isnot(None)).all()
        coches_db = db.session.query(Coche).all()
        
        # Mapeo de coche por equipo_id para fácil acceso
        coches_map = {c.equipo_id: c for c in coches_db}
        
        lista_pilotos = []
        for p in pilotos_db:
            coche = coches_map.get(p.equipo_id)
            if coche:
                lista_pilotos.append(PilotoEnCarrera(p, coche))
            else:
                print(f"Advertencia: Piloto {p.nombre} no tiene coche asignado.")
        
        return lista_pilotos

    def simular_clasificacion(self):
        """
        FASE 1: Calcula el PS_Base para todos los pilotos.
        """
        print("Iniciando simulación de Clasificación...")
        resultados_qually = []

        for p in self.pilotos_en_carrera:
            # 1. Factor Coche (Adaptado al Circuito)
            c = p.coche_db
            adaptacion_coche = (c.motor * self.circuito.potencia_influencia) + \
                               (c.aerodinamica * self.circuito.aero_influencia) + \
                               (c.chasis * self.circuito.manejo_influencia)
            
            # 2. Factor Piloto (Habilidad Pura)
            pil = p.piloto_db
            rendimiento_piloto = (pil.velocidad * W_PILOTO_VELOCIDAD) + \
                                 (pil.consistencia * W_PILOTO_CONSISTENCIA) + \
                                 (pil.experiencia * W_PILOTO_EXPERIENCIA)

            # 3. PS de Clasificación (Final)
            ps_qually = (adaptacion_coche * W_QUALLY_COCHE) + \
                        (rendimiento_piloto * W_QUALLY_PILOTO)
            
            # 4. Variabilidad (RNG)
            # Un piloto inconsistente (baja consistencia) y arriesgado (alto riesgo)
            # tendrá una variabilidad mucho mayor.
            rango_variabilidad = (1 - (pil.consistencia / 100)) + (pil.riesgo / 100)
            rng_factor = random.uniform(-rango_variabilidad, rango_variabilidad)
            
            ps_qually_final = ps_qually + (ps_qually * (rng_factor / 10)) # Dividimos por 10 para que no sea tan extremo
            
            p.ps_base = ps_qually_final # Guardamos el PS ideal
            resultados_qually.append((p, ps_qually_final))

        # Ordenar por mejor PS (más alto) para la parrilla
        resultados_qually.sort(key=lambda x: x[1], reverse=True)
        
        # Asignar posiciones iniciales y orden
        self.orden_pilotos = []
        for i, (piloto, _) in enumerate(resultados_qually):
            piloto.posicion_actual = i + 1
            self.orden_pilotos.append(piloto) # Ya queda ordenado para la carrera
            
        self.log_eventos.append("Clasificación terminada. Parrilla establecida.")
        print("Clasificación terminada.")

    def run_simulation(self):
        """
        FASE 2: El bucle principal de la carrera.
        """
        if not self.orden_pilotos:
            self.simular_clasificacion()

        print(f"Iniciando simulación de Carrera ({self.vueltas_totales} vueltas)...")

        for i in range(self.vueltas_totales):
            self.vuelta_actual = i + 1
            self.log_eventos.append(f"--- INICIO VUELTA {self.vuelta_actual} ---")
            
            # 1. Manejar eventos globales (SC, Lluvia)
            self._manejar_eventos_globales()

            # 2. Bucle por cada piloto (en orden de posición)
            for j, piloto in enumerate(self.orden_pilotos):
                
                if not piloto.esta_en_pista:
                    continue # Saltamos si está DNF

                # 3. Decisiones de estrategia (¿Parar en boxes?)
                self._aplicar_estrategias_piloto(piloto)

                # 4. Simular la vuelta
                if piloto.esta_en_pit_lane:
                    self._simular_parada_en_boxes(piloto)
                else:
                    self._simular_vuelta_para_piloto(piloto, j) # j es su posición
            
            # 5. Reordenar posiciones basado en el tiempo total acumulado
            self._actualizar_posiciones()

        self.terminada = True
        self.log_eventos.append("¡CARRERA TERMINADA!")
        print("Simulación completada.")

    def _simular_vuelta_para_piloto(self, piloto: PilotoEnCarrera, posicion_actual):
        """
        EL CORAZÓN DEL MOTOR.
        Calcula el PS, lo convierte a tiempo y lo suma.
        """
        
        # 1. Cargar el PS_Base
        ps_base = piloto.ps_base 

        # 2. Calcular Modificadores Dinámicos
        mod_neumaticos = self._calcular_mod_neumaticos(piloto)
        mod_combustible = self._calcular_mod_combustible(piloto)
        mod_ritmo_ers = self._calcular_mod_ritmo(piloto)
        
        # 3. Modificador Tráfico/DRS (simplificado)
        mod_trafico_drs = 0
        if posicion_actual > 0: # Si no es el líder
            coche_delante = self.orden_pilotos[posicion_actual - 1]
            distancia = coche_delante.tiempo_total_carrera - piloto.tiempo_total_carrera
            if distancia < 1.0:
                mod_trafico_drs = MOD_DRS # Bono DRS
            elif distancia < 1.5:
                mod_trafico_drs = MOD_AIRE_SUCIO # Penalización aire sucio

        # 4. Sumar todo
        ps_vuelta_actual = ps_base + mod_neumaticos + mod_combustible + \
                           mod_ritmo_ers + mod_trafico_drs
        
        # 5. Check de Eventos/Errores (RNG)
        (ps_final_vuelta, evento) = self._check_eventos_piloto(piloto, ps_vuelta_actual)
        if evento:
            self.log_eventos.append(evento)

        # 6. Convertir PS a tiempo y sumar
        tiempo_vuelta = self._convertir_ps_a_tiempo(ps_final_vuelta)
        piloto.tiempo_total_carrera += tiempo_vuelta
        
        # 7. Actualizar estado del piloto
        piloto.actualizar_desgaste(self.circuito.desgaste_neumaticos)
        piloto.actualizar_combustible()
        piloto.actualizar_bateria_ers()
        piloto.vuelta_actual = self.vuelta_actual

    def _aplicar_estrategias_piloto(self, piloto: PilotoEnCarrera):
        """Decide si el piloto debe parar o cambiar de ritmo"""
        
        # Estrategia de IA simple: parar si el desgaste es muy alto
        if not piloto.solicitar_pit_stop and piloto.neumatico_desgaste > 70:
            print(f"IA: {piloto.piloto_db.nombre} parará por desgaste.")
            piloto.solicitar_pit_stop = True

        # Si el piloto (jugador o IA) solicita pit stop, entra en esta vuelta
        if piloto.solicitar_pit_stop:
            piloto.esta_en_pit_lane = True
            piloto.solicitar_pit_stop = False # Reseteamos la solicitud
            self.log_eventos.append(f"V{self.vuelta_actual}: {piloto.piloto_db.nombre} entra a boxes.")

    def _simular_parada_en_boxes(self, piloto: PilotoEnCarrera):
        """Añade el tiempo de la parada en boxes"""
        
        # Aquí iría la lógica de habilidad de mecánicos
        tiempo_cambio_gomas = random.uniform(2.5, 4.5) 
        
        tiempo_total_pit = TIEMPO_BASE_PIT_STOP + tiempo_cambio_gomas
        
        piloto.tiempo_total_carrera += tiempo_total_pit
        
        # Reseteamos neumáticos
        piloto.neumatico_desgaste = 0.0
        piloto.neumatico_vueltas = 0
        piloto.neumatico_compuesto = "Duro" # Asumimos que cambia a Duro
        
        piloto.esta_en_pit_lane = False # Sale de boxes para la prox vuelta
        print(f"{piloto.piloto_db.nombre} salió de boxes.")

    def _actualizar_posiciones(self):
        """Reordena la lista 'self.orden_pilotos' basada en tiempo total"""
        # Filtramos DNF primero
        en_pista = [p for p in self.orden_pilotos if p.esta_en_pista]
        dnf = [p for p in self.orden_pilotos if not p.esta_en_pista]
        
        # Ordenamos a los que siguen en pista
        en_pista.sort(key=lambda p: p.tiempo_total_carrera)
        
        # Reasignamos posiciones
        self.orden_pilotos = en_pista + dnf
        for i, piloto in enumerate(self.orden_pilotos):
            piloto.posicion_actual = i + 1

    # --- Funciones de Modificadores y RNG ---

    def _calcular_mod_neumaticos(self, p: PilotoEnCarrera):
        # Penalización cuadrática por desgaste
        penalizacion = (p.neumatico_desgaste ** 2) * K_NEUMATICO_PENALTY
        # Aquí podríamos añadir bonos por compuesto (ej: Blando +5, Duro -2)
        return -penalizacion

    def _calcular_mod_combustible(self, p: PilotoEnCarrera):
        penalizacion = p.combustible_actual * K_FUEL_PENALTY
        return -penalizacion

    def _calcular_mod_ritmo(self, p: PilotoEnCarrera):
        if p.ritmo_actual == "Ataque":
            if p.bateria_ers > 10:
                return MOD_RITMO_ATAQUE
            else:
                p.ritmo_actual = "Normal" # No puede atacar
                return 0
        if p.ritmo_actual == "Conservador":
            return MOD_RITMO_CONSERVADOR
        return 0

    def _check_eventos_piloto(self, p: PilotoEnCarrera, ps_vuelta):
        """Chequea Errores de Piloto y Fallos Mecánicos"""
        
        # 1. Error de Piloto
        # Pilotos inconsistentes y arriesgados erran más
        prob_error = PROB_ERROR_PILOTO_BASE + \
                     (1 - p.piloto_db.consistencia / 100) + \
                     (p.piloto_db.riesgo / 100)
        
        if random.random() < (prob_error / 20): # /20 para balancear
            ps_modificado = ps_vuelta * 0.8 # Pierde 20% de rendimiento
            evento = f"V{self.vuelta_actual}: ¡Error de {p.piloto_db.nombre}! Pierde tiempo."
            return (ps_modificado, evento)

        # 2. Fallo Mecánico
        prob_fallo = PROB_FALLO_MECANICO_BASE + (1 - p.coche_db.fiabilidad / 100)
        
        if random.random() < (prob_fallo / 50): # /50 para balancear
            p.esta_en_pista = False # DNF
            evento = f"V{self.vuelta_actual}: ¡FALLO MECÁNICO para {p.piloto_db.nombre}! ¡Está fuera!"
            return (0, evento) # PS Cero

        return (ps_vuelta, None) # Sin eventos

    def _manejar_eventos_globales(self):
        """Chequea si sale un Safety Car o empieza a llover"""
        if random.random() < (self.circuito.prob_safety_car / 10): # /10 para balancear
            self.estado_pista = "SafetyCar"
            self.log_eventos.append(f"V{self.vuelta_actual}: ¡SAFETY CAR! ¡SAFETY CAR!")
            # Aquí iría la lógica de agrupar a los coches
            
    def _convertir_ps_a_tiempo(self, ps):
        """
        Convierte el Performance Score (PS) abstracto a segundos.
        Esta es una fórmula de "mapeo" que podemos ajustar.
        Un PS más alto debe dar un tiempo de vuelta más bajo.
        """
        # Fórmula base: 100 segundos (base_time) - (PS * 0.1)
        # Esto es muy simple, pero funciona.
        # Asumimos que un PS de 200 nos da 80s, y un PS de 150 nos da 85s.
        base_time = 100.0 
        factor_conversion = 0.1
        
        tiempo = base_time - (ps * factor_conversion)
        
        # Añadir pequeña variabilidad aleatoria
        tiempo += random.uniform(-0.05, 0.05)
        
        return max(tiempo, 60.0) # Evitar tiempos negativos o absurdos

    # --- Métodos Públicos (para la API) ---

    def get_status(self):
        """Devuelve el estado actual de la simulación para el frontend"""
        
        # Preparamos los datos de los pilotos para enviar
        pilotos_status = []
        for p in self.orden_pilotos:
            pilotos_status.append({
                "posicion": p.posicion_actual,
                "nombre": p.piloto_db.nombre,
                "equipo_id": p.piloto_db.equipo_id,
                "tiempo_total": p.tiempo_total_carrera,
                "desgaste_neumatico": p.neumatico_desgaste,
                "combustible": p.combustible_actual,
                "bateria": p.bateria_ers,
                "en_pista": p.esta_en_pista,
                "en_pits": p.esta_en_pit_lane
            })

        return {
            "vuelta_actual": self.vuelta_actual,
            "vueltas_totales": self.vueltas_totales,
            "estado_pista": self.estado_pista,
            "terminada": self.terminada,
            "pilotos": pilotos_status,
            "log_eventos": self.log_eventos[-10:] # Últimos 10 eventos
        }

    def update_piloto_strategy(self, piloto_id, accion):
        """
        Permite al jugador (API) cambiar la estrategia de su piloto.
        """
        piloto_a_actualizar = None
        for p in self.pilotos_en_carrera:
            if p.piloto_db.id == piloto_id:
                piloto_a_actualizar = p
                break
        
        if not piloto_a_actualizar:
            return {"error": "Piloto no encontrado en simulación"}

        if accion == "solicitar_pit_stop":
            piloto_a_actualizar.solicitar_pit_stop = True
            return {"status": f"Pit stop solicitado para {piloto_a_actualizar.piloto_db.nombre}"}
        
        if accion in ["Normal", "Ataque", "Conservador"]:
            piloto_a_actualizar.ritmo_actual = accion
            return {"status": f"Ritmo de {piloto_a_actualizar.piloto_db.nombre} fijado en {accion}"}

        return {"error": "Acción no reconocida"}
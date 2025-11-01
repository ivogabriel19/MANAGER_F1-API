# Contenido para: app/routes.py

from flask import Blueprint, request, jsonify
from app import db, create_app
from app.models import Circuito
from app.engine import SimulationEngine
import threading
import time

# Creamos un "Blueprint", que es un grupo de rutas para nuestra API
api_bp = Blueprint('api', __name__)

# --- GESTIÓN DE ESTADO (simple) ---
# Usamos un diccionario global para guardar las simulaciones activas.
# En una app "pro", usarías Redis para esto, pero esto es perfecto para empezar.
# Guardará: {"sim_id_123": <objeto SimulationEngine>, "sim_id_456": ...}
active_simulations = {}


def simulation_thread_target(app_context, circuito_id, sim_id):
    """
    Esta es la función que se ejecutará en el hilo separado.
    Necesita el 'app_context' para poder hablar con la base de datos.
    """
    with app_context:
        print(f"Thread {sim_id}: Creando motor de simulación...")
        try:
            # 1. Crear el motor DENTRO del contexto del thread
            engine = SimulationEngine(circuito_id=circuito_id)
            
            # 2. Guardarlo en el dict global para que /status lo encuentre
            active_simulations[sim_id] = engine
            
            # 3. ¡Correr la simulación! (Esta es la parte que tarda)
            engine.run_simulation()
            
            print(f"Thread {sim_id}: Simulación completada.")
            # (Opcional: podrías añadir lógica para limpiar simulaciones viejas)
        
        except Exception as e:
            # Si algo falla en el thread, guardamos el error
            print(f"ERROR en el thread de simulación {sim_id}: {e}")
            active_simulations[sim_id] = {"error": str(e)}


# --- ENDPOINTS DE LA API ---

@api_bp.route('/circuits', methods=['GET'])
def get_circuits():
    """Devuelve la lista de todos los circuitos disponibles."""
    try:
        circuitos_db = db.session.query(Circuito).all()
        circuitos_list = [
            {"id": c.id, "nombre": c.nombre, "pais": c.pais, "vueltas": c.vueltas}
            for c in circuitos_db
        ]
        return jsonify(circuitos_list), 200
    except Exception as e:
        return jsonify({"error": f"Error al leer circuitos: {str(e)}"}), 500


@api_bp.route('/simulation/start', methods=['POST'])
def start_simulation():
    """
    Inicia una nueva simulación en un hilo separado.
    Responde INMEDIATAMENTE con un ID de simulación.
    """
    data = request.json
    circuito_id = data.get('circuito_id')
    if not circuito_id:
        return jsonify({"error": "circuito_id es requerido"}), 400

    try:
        # 1. Crear un ID único para esta simulación
        sim_id = f"sim_{int(time.time())}"
        
        # 2. Obtener el contexto de la app para pasarlo al thread
        app = create_app()
        app_context = app.app_context()

        # 3. Poner un "placeholder" para que el frontend sepa que está iniciando
        active_simulations[sim_id] = {"status": "Iniciando simulación..."}

        # 4. Iniciar el thread!
        thread = threading.Thread(
            target=simulation_thread_target, 
            args=(app_context, circuito_id, sim_id)
        )
        thread.start()

        print(f"API: Solicitud de inicio para {sim_id} aceptada.")
        
        # 5. Devolver el ID inmediatamente
        return jsonify({
            "message": "Simulación iniciada.",
            "sim_id": sim_id
        }), 202 # 202 "Accepted" (Aceptado)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route('/simulation/status', methods=['GET'])
def get_simulation_status():
    """
    El frontend llamará a esta ruta 1 vez por segundo
    para obtener el estado "en vivo" de la carrera.
    """
    sim_id = request.args.get('sim_id')
    if not sim_id:
        return jsonify({"error": "sim_id es requerido"}), 400

    sim_object = active_simulations.get(sim_id)
    
    if not sim_object:
        return jsonify({"error": "Simulación no encontrada o ha caducado"}), 404
    
    # Si aún se está iniciando o dio error (es un dict)
    if isinstance(sim_object, dict):
        return jsonify(sim_object)
    
    # Si ya es un objeto SimulationEngine, le pedimos el estado
    return jsonify(sim_object.get_status())


@api_bp.route('/simulation/strategy', methods=['POST'])
def update_strategy():
    """Permite al jugador enviar órdenes a sus pilotos."""
    data = request.json
    sim_id = data.get('sim_id')
    piloto_id = data.get('piloto_id') # ID del piloto de la BD
    accion = data.get('accion')      # "solicitar_pit_stop", "Ataque", "Normal"

    if not all([sim_id, piloto_id, accion]):
        return jsonify({"error": "sim_id, piloto_id, y accion son requeridos"}), 400

    engine = active_simulations.get(sim_id)
    if not engine or isinstance(engine, dict):
        return jsonify({"error": "Simulación no está activa"}), 404

    if engine.terminada:
        return jsonify({"error": "La simulación ya ha terminado"}), 400
    
    # Delegamos la acción al motor
    result = engine.update_piloto_strategy(piloto_id, accion)
    
    if "error" in result:
        return jsonify(result), 400
    
    return jsonify(result), 200
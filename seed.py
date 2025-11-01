# Contenido para: seed.py (Versión 2)

from app import create_app, db
from app.models import Circuito, Equipo, Piloto, Coche, Staff

# Creamos una instancia de la app para tener el contexto
app = create_app()

def seed_data():
    """Función principal para poblar la base de datos."""
    
    # Usamos app_context() para poder interactuar con la base de datos
    with app.app_context():
        
        print("Iniciando el proceso de 'seed'...")
        
        # --- 1. BORRADO DE DATOS ANTIGUOS ---
        # Borramos en orden inverso para respetar las 'foreign keys'
        print("Borrando datos antiguos...")
        db.session.query(Piloto).delete()
        db.session.query(Coche).delete()
        db.session.query(Staff).delete()
        db.session.query(Equipo).delete()
        db.session.query(Circuito).delete()
        db.session.commit() # Guardamos el borrado

        # --- 2. CREACIÓN DE CIRCUITOS ---
        print("Creando circuitos...")
        circuitos = [
            Circuito(nombre="Bahréin (Sakhir)", pais="Bahréin", vueltas=57, potencia_influencia=0.4, aero_influencia=0.2, manejo_influencia=0.4, desgaste_neumaticos=0.7, prob_safety_car=0.3),
            Circuito(nombre="Jeddah (Arabia Saudita)", pais="Arabia Saudita", vueltas=50, potencia_influencia=0.5, aero_influencia=0.3, manejo_influencia=0.2, desgaste_neumaticos=0.3, prob_safety_car=0.8),
            Circuito(nombre="Melbourne (Australia)", pais="Australia", vueltas=58, potencia_influencia=0.3, aero_influencia=0.3, manejo_influencia=0.4, desgaste_neumaticos=0.5, prob_safety_car=0.7),
            Circuito(nombre="Imola (Italia)", pais="Italia", vueltas=63, potencia_influencia=0.4, aero_influencia=0.3, manejo_influencia=0.3, desgaste_neumaticos=0.4, prob_safety_car=0.6),
            Circuito(nombre="Mónaco (Montecarlo)", pais="Mónaco", vueltas=78, potencia_influencia=0.1, aero_influencia=0.4, manejo_influencia=0.5, desgaste_neumaticos=0.2, prob_safety_car=0.9),
            Circuito(nombre="Silverstone (Gran Bretaña)", pais="Gran Bretaña", vueltas=52, potencia_influencia=0.3, aero_influencia=0.5, manejo_influencia=0.2, desgaste_neumaticos=0.8, prob_safety_car=0.4),
            Circuito(nombre="Monza (Italia)", pais="Italia", vueltas=53, potencia_influencia=0.6, aero_influencia=0.2, manejo_influencia=0.2, desgaste_neumaticos=0.3, prob_safety_car=0.3),
            Circuito(nombre="Marina Bay (Singapur)", pais="Singapur", vueltas=61, potencia_influencia=0.2, aero_influencia=0.3, manejo_influencia=0.5, desgaste_neumaticos=0.6, prob_safety_car=1.0),
            Circuito(nombre="Suzuka (Japón)", pais="Japón", vueltas=53, potencia_influencia=0.4, aero_influencia=0.4, manejo_influencia=0.2, desgaste_neumaticos=0.7, prob_safety_car=0.5),
            Circuito(nombre="Interlagos (Brasil)", pais="Brasil", vueltas=71, potencia_influencia=0.4, aero_influencia=0.3, manejo_influencia=0.3, desgaste_neumaticos=0.6, prob_safety_car=0.7)
        ]
        db.session.bulk_save_objects(circuitos)
        db.session.commit()
        print(f"Se crearon {len(circuitos)} circuitos.")

        # --- 3. CREACIÓN DE EQUIPOS, COCHES Y PILOTOS ---
        print("Creando equipos, pilotos y coches...")
        
        # Usamos un diccionario para definir los equipos y sus miembros
        # Las stats están de 0 a 100
        datos_equipos = [
            {
                "equipo": {"nombre": "Red Bull Racing", "presupuesto": 200000000, "reputacion": 95},
                "coche": {"motor": 95, "aerodinamica": 98, "chasis": 90, "fiabilidad": 90},
                "pilotos": [
                    {"nombre": "Max Verstappen", "velocidad": 99, "consistencia": 98, "riesgo": 50, "experiencia": 85, "feedback_tecnico": 80, "salario": 55000000},
                    {"nombre": "Sergio Pérez", "velocidad": 88, "consistencia": 75, "riesgo": 40, "experiencia": 90, "feedback_tecnico": 70, "salario": 15000000}
                ]
            },
            {
                "equipo": {"nombre": "Ferrari", "presupuesto": 190000000, "reputacion": 98},
                "coche": {"motor": 96, "aerodinamica": 92, "chasis": 93, "fiabilidad": 80},
                "pilotos": [
                    {"nombre": "Charles Leclerc", "velocidad": 97, "consistencia": 85, "riesgo": 70, "experiencia": 75, "feedback_tecnico": 80, "salario": 35000000},
                    {"nombre": "Carlos Sainz", "velocidad": 90, "consistencia": 92, "riesgo": 30, "experiencia": 80, "feedback_tecnico": 85, "salario": 20000000}
                ]
            },
            {
                "equipo": {"nombre": "McLaren", "presupuesto": 170000000, "reputacion": 90},
                "coche": {"motor": 90, "aerodinamica": 94, "chasis": 90, "fiabilidad": 88},
                "pilotos": [
                    {"nombre": "Lando Norris", "velocidad": 96, "consistencia": 90, "riesgo": 50, "experiencia": 70, "feedback_tecnico": 82, "salario": 30000000},
                    {"nombre": "Oscar Piastri", "velocidad": 92, "consistencia": 88, "riesgo": 60, "experiencia": 60, "feedback_tecnico": 78, "salario": 10000000}
                ]
            },
            {
                "equipo": {"nombre": "Mercedes", "presupuesto": 180000000, "reputacion": 92},
                "coche": {"motor": 91, "aerodinamica": 90, "chasis": 94, "fiabilidad": 85},
                "pilotos": [
                    {"nombre": "Lewis Hamilton", "velocidad": 95, "consistencia": 95, "riesgo": 40, "experiencia": 99, "feedback_tecnico": 95, "salario": 45000000},
                    {"nombre": "George Russell", "velocidad": 91, "consistencia": 89, "riesgo": 65, "experiencia": 70, "feedback_tecnico": 85, "salario": 18000000}
                ]
            },
            {
                "equipo": {"nombre": "Aston Martin", "presupuesto": 150000000, "reputacion": 85},
                "coche": {"motor": 90, "aerodinamica": 88, "chasis": 87, "fiabilidad": 82},
                "pilotos": [
                    {"nombre": "Fernando Alonso", "velocidad": 94, "consistencia": 96, "riesgo": 40, "experiencia": 99, "feedback_tecnico": 98, "salario": 25000000},
                    {"nombre": "Lance Stroll", "velocidad": 82, "consistencia": 70, "riesgo": 60, "experiencia": 75, "feedback_tecnico": 65, "salario": 8000000}
                ]
            },
            # --- Equipos de media tabla ---
            {
                "equipo": {"nombre": "Alpine", "presupuesto": 130000000, "reputacion": 75},
                "coche": {"motor": 82, "aerodinamica": 80, "chasis": 81, "fiabilidad": 75},
                "pilotos": [
                    {"nombre": "Pierre Gasly", "velocidad": 87, "consistencia": 80, "riesgo": 55, "experiencia": 80, "feedback_tecnico": 70, "salario": 7000000},
                    {"nombre": "Esteban Ocon", "velocidad": 86, "consistencia": 82, "riesgo": 50, "experiencia": 81, "feedback_tecnico": 72, "salario": 7000000}
                ]
            },
            {
                "equipo": {"nombre": "Williams", "presupuesto": 110000000, "reputacion": 80},
                "coche": {"motor": 85, "aerodinamica": 78, "chasis": 80, "fiabilidad": 80},
                "pilotos": [
                    {"nombre": "Alex Albon", "velocidad": 89, "consistencia": 85, "riesgo": 50, "experiencia": 78, "feedback_tecnico": 85, "salario": 6000000},
                    {"nombre": "Logan Sargeant", "velocidad": 78, "consistencia": 65, "riesgo": 75, "experiencia": 50, "feedback_tecnico": 60, "salario": 1000000}
                ]
            },
            # --- Equipos de fondo ---
            {
                "equipo": {"nombre": "RB (Visa Cash App RB)", "presupuesto": 120000000, "reputacion": 70},
                "coche": {"motor": 88, "aerodinamica": 81, "chasis": 82, "fiabilidad": 78},
                "pilotos": [
                    {"nombre": "Yuki Tsunoda", "velocidad": 86, "consistencia": 78, "riesgo": 70, "experiencia": 65, "feedback_tecnico": 70, "salario": 3000000},
                    {"nombre": "Daniel Ricciardo", "velocidad": 85, "consistencia": 80, "riesgo": 50, "experiencia": 90, "feedback_tecnico": 75, "salario": 5000000}
                ]
            },
            {
                "equipo": {"nombre": "Sauber (Stake)", "presupuesto": 100000000, "reputacion": 65},
                "coche": {"motor": 84, "aerodinamica": 76, "chasis": 78, "fiabilidad": 70},
                "pilotos": [
                    {"nombre": "Valtteri Bottas", "velocidad": 84, "consistencia": 88, "riesgo": 30, "experiencia": 92, "feedback_tecnico": 80, "salario": 4000000},
                    {"nombre": "Zhou Guanyu", "velocidad": 81, "consistencia": 80, "riesgo": 50, "experiencia": 60, "feedback_tecnico": 70, "salario": 2000000}
                ]
            },
            {
                "equipo": {"nombre": "Haas F1 Team", "presupuesto": 90000000, "reputacion": 60},
                "coche": {"motor": 84, "aerodinamica": 75, "chasis": 76, "fiabilidad": 65},
                "pilotos": [
                    {"nombre": "Kevin Magnussen", "velocidad": 83, "consistencia": 75, "riesgo": 75, "experiencia": 85, "feedback_tecnico": 70, "salario": 3000000},
                    {"nombre": "Nico Hülkenberg", "velocidad": 85, "consistencia": 86, "riesgo": 40, "experiencia": 90, "feedback_tecnico": 78, "salario": 3000000}
                ]
            }
        ]

        # Recorremos la lista y creamos los objetos en la BD
        for data in datos_equipos:
            # 1. Crear el Equipo
            nuevo_equipo = Equipo(
                nombre=data["equipo"]["nombre"],
                presupuesto=data["equipo"]["presupuesto"],
                reputacion=data["equipo"]["reputacion"]
            )
            db.session.add(nuevo_equipo)
            # ¡Importante! Hacemos "flush" para obtener el ID del nuevo equipo
            # sin hacer commit todavía.
            db.session.flush() 
            
            # 2. Crear el Coche, asignando el ID del equipo
            nuevo_coche = Coche(
                motor=data["coche"]["motor"],
                aerodinamica=data["coche"]["aerodinamica"],
                chasis=data["coche"]["chasis"],
                fiabilidad=data["coche"]["fiabilidad"],
                equipo_id=nuevo_equipo.id # ¡Aquí está la relación!
            )
            db.session.add(nuevo_coche)
            
            # 3. Crear los Pilotos, asignando el ID del equipo
            for p_data in data["pilotos"]:
                nuevo_piloto = Piloto(
                    nombre=p_data["nombre"],
                    velocidad=p_data["velocidad"],
                    consistencia=p_data["consistencia"],
                    riesgo=p_data["riesgo"],
                    experiencia=p_data["experiencia"],
                    feedback_tecnico=p_data["feedback_tecnico"],
                    salario=p_data["salario"],
                    equipo_id=nuevo_equipo.id # ¡Aquí está la relación!
                )
                db.session.add(nuevo_piloto)
        
        # --- 4. COMMIT FINAL ---
        try:
            # Ahora sí, guardamos todo en la base de datos
            db.session.commit()
            print(f"¡Éxito! Se crearon {len(datos_equipos)} equipos con sus coches y pilotos.")
            
        except Exception as e:
            # Si algo sale mal, hacemos rollback
            db.session.rollback()
            print(f"Error al agregar equipos y pilotos: {e}")
        
        finally:
            # Cerramos la sesión
            db.session.close()

# --- Ejecutar el script ---
if __name__ == '__main__':
    seed_data()
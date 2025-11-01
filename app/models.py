from app import db # Importamos la instancia 'db' de nuestro __init__.py

# --- Entidades Principales ---

class Equipo(db.Model):
    __tablename__ = 'equipos'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), unique=True, nullable=False)
    presupuesto = db.Column(db.Float, default=100000000.0)
    reputacion = db.Column(db.Float, default=50.0)
    base_tecnica = db.Column(db.String(100))
    
    # Relaciones (El 'backref' crea una propiedad virtual en el otro modelo)
    pilotos = db.relationship('Piloto', backref='equipo', lazy=True)
    staff = db.relationship('Staff', backref='equipo', lazy=True)
    coche = db.relationship('Coche', backref='equipo', uselist=False, lazy=True) # uselist=False para 1-a-1

class Piloto(db.Model):
    __tablename__ = 'pilotos'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    edad = db.Column(db.Integer)
    nacionalidad = db.Column(db.String(50))
    
    # Estadísticas clave de rendimiento
    velocidad = db.Column(db.Float, default=70.0)
    consistencia = db.Column(db.Float, default=70.0)
    riesgo = db.Column(db.Float, default=30.0)
    experiencia = db.Column(db.Float, default=50.0)
    feedback_tecnico = db.Column(db.Float, default=50.0)
    
    # Contrato y estado
    salario = db.Column(db.Float, default=1000000.0)
    contrato_duracion = db.Column(db.Integer, default=1) # Años
    moral = db.Column(db.Float, default=70.0)
    
    # Clave foránea para la relación 1-a-N con Equipo
    equipo_id = db.Column(db.Integer, db.ForeignKey('equipos.id'), nullable=True) # Nullable=True para agentes libres

class Coche(db.Model):
    __tablename__ = 'coches'
    id = db.Column(db.Integer, primary_key=True)
    temporada = db.Column(db.Integer, default=2025)
    
    # Estadísticas de desarrollo
    motor = db.Column(db.Float, default=50.0)
    aerodinamica = db.Column(db.Float, default=50.0)
    chasis = db.Column(db.Float, default=50.0)
    fiabilidad = db.Column(db.Float, default=50.0)
    
    # Desgaste de componentes (simplificado por ahora)
    desgaste_motor = db.Column(db.Float, default=0.0)
    desgaste_caja = db.Column(db.Float, default=0.0)
    
    # Clave foránea para la relación 1-a-1 con Equipo
    equipo_id = db.Column(db.Integer, db.ForeignKey('equipos.id'), unique=True, nullable=False)

class Staff(db.Model):
    __tablename__ = 'staff'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    rol = db.Column(db.String(50)) # Ej: "Ingeniero de Pista", "Estratega", "Mecánico Jefe"
    habilidad = db.Column(db.Float, default=50.0)
    salario = db.Column(db.Float, default=50000.0)
    moral = db.Column(db.Float, default=70.0)
    
    equipo_id = db.Column(db.Integer, db.ForeignKey('equipos.id'), nullable=True)

# --- Entidades de Simulación ---

class Circuito(db.Model):
    __tablename__ = 'circuitos'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), unique=True, nullable=False)
    pais = db.Column(db.String(50))
    vueltas = db.Column(db.Integer, default=50)
    
    # Influencias (las claves de nuestro motor)
    potencia_influencia = db.Column(db.Float, default=0.33) # Peso del motor
    aero_influencia = db.Column(db.Float, default=0.33)    # Peso de la aerodinámica
    manejo_influencia = db.Column(db.Float, default=0.33)  # Peso del chasis
    
    # Características del circuito
    desgaste_neumaticos = db.Column(db.Float, default=0.5) # Factor de 0 a 1
    prob_safety_car = db.Column(db.Float, default=0.1)     # Probabilidad por vuelta
    prob_lluvia = db.Column(db.Float, default=0.05)
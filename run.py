from app import create_app, db
from app.models import Equipo, Piloto, Coche, Staff, Circuito

# Creamos la instancia de la app
app = create_app()

# Esto es útil para el modo 'flask shell'
# Permite acceder a 'db' y a los modelos sin importarlos manualmente
@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'Equipo': Equipo,
        'Piloto': Piloto,
        'Coche': Coche,
        'Staff': Staff,
        'Circuito': Circuito
    }

if __name__ == '__main__':
    # (app.run() no se usa aquí, lo haremos con el comando 'flask run')
    pass
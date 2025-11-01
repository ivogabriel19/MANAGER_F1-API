## 1. Estructura de Carpetas

`
MANAGER_F1/
|
├── app/
│   ├── __init__.py         # Inicializa la app Flask y la BD
│   ├── models.py           # Define las tablas de la BD (¡Clave!)
│   ├── engine.py           # Nuestro motor de simulación (aún vacío)
│   ├── routes.py           # Las API endpoints (aún vacío)
│   └── config.py           # Configuración (claves de BD, etc.)
|
├── migrations/             # (Lo generará la herramienta de migración)
|
├── run.py                  # El archivo que ejecutas para iniciar el servidor
├── requirements.txt        # Las librerías de Python
└── .env                    # (Oculto) Para guardar tu contraseña de la BD
`
## 2. Dependencias (requirements.txt)
  Corre pip install -r requirements.txt en tu terminal para instalarlas.
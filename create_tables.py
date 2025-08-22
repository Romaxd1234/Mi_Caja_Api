# create_tables.py
from database import engine, metadata
# IMPORTAR TODAS LAS TABLAS
from models import tiendas, empleados, inventario, ventas, cortes_diarios, cortes_semanales, prestamos

metadata.create_all(engine)
print("Tablas creadas correctamente.")

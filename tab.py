from sqlalchemy import create_engine, inspect, text

# ---------------------
# Configura tu DB de Render
# ---------------------
DATABASE_URL = "postgresql://invex_db_user:uR4BGxN3VLcanhCdVSO6laFUgtzzCiwG@dpg-d2kacbv5r7bs73ekh5bg-a.oregon-postgres.render.com:5432/invex_db"


# Crear engine
engine = create_engine(DATABASE_URL)

# Crear inspector para listar tablas
inspector = inspect(engine)

# Listar todas las tablas
tablas = inspector.get_table_names()
print("Tablas en la base de datos:")
for t in tablas:
    print(" -", t)

print("\n=== Registros por tabla ===\n")
with engine.connect() as conn:
    for tabla in tablas:
        print(f"Tabla: {tabla}")
        result = conn.execute(text(f"SELECT * FROM {tabla}"))
        rows = result.fetchall()
        if not rows:
            print("  (sin registros)")
        else:
            for row in rows:
                print(" ", row)
        print("-" * 40)

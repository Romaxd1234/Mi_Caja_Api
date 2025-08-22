from sqlalchemy import (
    Table, Column, Integer, String, Float, Boolean,
    DateTime, ForeignKey, JSON, UniqueConstraint, Index, func
)
from database import metadata
from datetime import datetime

# ---------------------
# Tabla Tiendas
# ---------------------
tiendas = Table(
    "tiendas",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("nombre", String(100), nullable=False, unique=True),
    Column("password", String(255), nullable=False),
    Column("patron", JSON, nullable=True)
)

# ---------------------
# Tabla Empleados
# ---------------------
empleados = Table(
    "empleados",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("tienda_id", Integer, ForeignKey("tiendas.id", ondelete="CASCADE")),
    Column("nombre", String(100), nullable=False),
    Column("puesto", String(100), nullable=False),
    Column("sueldo", Float, nullable=False),
    Column("password", String(255), nullable=False),
    Column("nota", String(255), default=""),
    UniqueConstraint("tienda_id", "nombre", name="uq_empleado_por_tienda")
)

# ---------------------
# Tabla Inventario
# ---------------------
inventario = Table(
    "inventario",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("tienda_id", Integer, ForeignKey("tiendas.id", ondelete="CASCADE")),
    Column("producto", String(150), nullable=False),
    Column("precio", Float, nullable=False),
    Column("piezas", Integer, nullable=False),
    UniqueConstraint("tienda_id", "producto", name="uq_producto_por_tienda")
)

# ---------------------
# Tabla Ventas
# ---------------------
ventas = Table(
    "ventas",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("tienda_id", Integer, ForeignKey("tiendas.id", ondelete="CASCADE")),
    Column("usuario", String(100), nullable=False),
    Column("productos", JSON, nullable=False),
    Column("total", Float, nullable=False),
    Column("fuera_inventario", Boolean, default=False),
    Column("fecha", DateTime, server_default=func.now())
)

# ---------------------
# Tabla Cortes Diarios
# ---------------------
cortes_diarios = Table(
    "cortes_diarios",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("tienda_id", Integer, ForeignKey("tiendas.id", ondelete="CASCADE")),
    Column("usuario_que_corto", String(100), nullable=False),
    Column("ventas", JSON, nullable=False),
    Column("total", Float, nullable=False),
    Column("fecha", DateTime, server_default=func.now())
)

# ---------------------
# Tabla Cortes Semanales
# ---------------------
cortes_semanales = Table(
    "cortes_semanales",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("tienda_id", Integer, ForeignKey("tiendas.id", ondelete="CASCADE")),
    Column("cortes_diarios", JSON, nullable=False),
    Column("fecha", DateTime, server_default=func.now())
)

# ---------------------
# Tabla Prestamos
# ---------------------
prestamos = Table(
    "prestamos",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("empleado_id", Integer, ForeignKey("empleados.id", ondelete="CASCADE")),
    Column("cantidad", Float, nullable=False),
    Column("descripcion", String(255), default=""),
    Column("fecha", DateTime, server_default=func.now())
)

# Índices recomendados para consultas frecuentes
Index("idx_empleados_tienda", empleados.c.tienda_id)
Index("idx_inventario_tienda", inventario.c.tienda_id)
Index("idx_ventas_tienda", ventas.c.tienda_id)

from fastapi import FastAPI, HTTPException
from typing import List, Optional
from pydantic import BaseModel
import json
import os

app = FastAPI()

# Rutas de archivos para ejemplo: en producción quizá querrás base de datos
TIENDA_JSON = "data/tiendas/abarrotes.json"
VENTAS_JSON = "data/ventas.json"
INVENTARIO_JSON = "data/inventario.json"


# MODELOS DE DATOS
class Producto(BaseModel):
    producto: str
    precio: float
    piezas: Optional[int] = None
    cantidad: Optional[int] = None

class Venta(BaseModel):
    fecha: str
    usuario: str
    productos: List[Producto]
    total: float
    fuera_inventario: bool

class InventarioItem(BaseModel):
    producto: str
    precio: float
    piezas: int

class TiendaInfo(BaseModel):
    nombre: str
    patron_password: str

class PatronInfo(BaseModel):
    nombre: str
    password: str

class Prestamo(BaseModel):
    cantidad: str
    mensaje: str
    pendiente: bool

class Empleado(BaseModel):
    nombre: str
    puesto: str
    sueldo: str
    nota: str = ""
    password: str
    prestamo: Prestamo

class EmpleadosLista(BaseModel):
    lista: List[Empleado]

class TiendaCompleta(BaseModel):
    tienda: TiendaInfo
    patron: PatronInfo
    empleados: EmpleadosLista
    ultimo_acceso: dict
    ultimo_acceso_empleado: dict
    ultimo_empleado: dict


# FUNCIONES AUXILIARES
def leer_json(path):
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def guardar_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


# RUTAS DE API

@app.get("/tienda", response_model=TiendaCompleta)
def obtener_tienda():
    data = leer_json(TIENDA_JSON)
    if not data:
        raise HTTPException(status_code=404, detail="Tienda no encontrada")
    return data

@app.post("/ventas")
def agregar_venta(venta: Venta):
    ventas = leer_json(VENTAS_JSON) or []
    ventas.append(venta.dict())
    guardar_json(VENTAS_JSON, ventas)
    return {"mensaje": "Venta agregada correctamente"}

@app.get("/ventas", response_model=List[Venta])
def listar_ventas():
    ventas = leer_json(VENTAS_JSON) or []
    return ventas

@app.get("/inventario", response_model=List[InventarioItem])
def obtener_inventario():
    data = leer_json(INVENTARIO_JSON)
    if not data:
        return []
    return data.get("inventario", [])

@app.post("/inventario")
def agregar_producto_inventario(item: InventarioItem):
    data = leer_json(INVENTARIO_JSON) or {"inventario": []}
    inventario = data.get("inventario", [])

    # Buscar si producto ya existe
    for prod in inventario:
        if prod["producto"] == item.producto:
            prod["piezas"] += item.piezas
            prod["precio"] = item.precio
            guardar_json(INVENTARIO_JSON, data)
            return {"mensaje": "Producto actualizado en inventario"}

    # Si no existe, agregar
    inventario.append(item.dict())
    guardar_json(INVENTARIO_JSON, data)
    return {"mensaje": "Producto agregado al inventario"}

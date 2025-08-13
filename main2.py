from fastapi import FastAPI, HTTPException, status
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

class LoginData(BaseModel):
    nombre: str
    patron_password: str

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

@app.post("/tienda/login")
def login_tienda(login_data: LoginData):
    if not os.path.exists(TIENDA_JSON):
        raise HTTPException(status_code=404, detail="Tienda no encontrada")

    with open(TIENDA_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    tienda = data.get("tienda", {})
    nombre_guardado = tienda.get("nombre", "").lower()
    password_guardado = tienda.get("patron_password", "")

    if login_data.nombre.lower() == nombre_guardado and login_data.patron_password == password_guardado:
        return {"mensaje": "Login exitoso"}
    else:
        raise HTTPException(status_code=401, detail="Nombre o contraseña incorrectos")


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

@app.post("/tienda", status_code=status.HTTP_201_CREATED)
def crear_tienda(tienda: TiendaInfo):
    # Verifica que no exista tienda
    if os.path.exists(TIENDA_JSON):
        return {"error": "Ya existe una tienda creada"}

    datos_tienda = {
        "tienda": {
            "nombre": tienda.nombre,
            "patron_password": tienda.patron_password
        },
        "patron": {
            "nombre": tienda.nombre,
            "password": tienda.patron_password
        },
        "empleados": {
            "lista": []
        },
        "ultimo_acceso": {},
        "ultimo_acceso_empleado": {},
        "ultimo_empleado": {}
    }

    guardar_json(TIENDA_JSON, datos_tienda)
    return {"mensaje": "Tienda creada correctamente"}

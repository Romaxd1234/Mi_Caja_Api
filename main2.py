from fastapi import FastAPI, HTTPException
from typing import List, Optional
from pydantic import BaseModel
import json
import os
from datetime import datetime

app = FastAPI()

# Archivos JSON
TIENDAS_JSON = "data/tiendas.json"
VENTAS_JSON = "data/ventas.json"
INVENTARIO_JSON = "data/inventario.json"

# -------------------- MODELOS --------------------
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
    empleados: EmpleadosLista
    ultimo_acceso: dict

# -------------------- FUNCIONES AUXILIARES --------------------
def leer_json(path):
    if not os.path.exists(path):
        carpeta = os.path.dirname(path)
        if carpeta and not os.path.exists(carpeta):
            os.makedirs(carpeta, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump([], f)
        return []
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def guardar_json(path, data):
    carpeta = os.path.dirname(path)
    if carpeta and not os.path.exists(carpeta):
        os.makedirs(carpeta, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def buscar_tienda(nombre):
    tiendas = leer_json(TIENDAS_JSON)
    for tienda in tiendas:
        if tienda["tienda"]["nombre"].lower() == nombre.lower():
            return tienda
    return None

# -------------------- RUTAS --------------------
@app.post("/tienda")
def crear_tienda(tienda: TiendaInfo):
    tiendas = leer_json(TIENDAS_JSON)
    if buscar_tienda(tienda.nombre):
        return {"error": "Ya existe una tienda con ese nombre"}

    nueva_tienda = {
        "tienda": {"nombre": tienda.nombre, "patron_password": tienda.patron_password},
        "empleados": {"lista": []},
        "ultimo_acceso": {}
    }
    tiendas.append(nueva_tienda)
    guardar_json(TIENDAS_JSON, tiendas)
    return {"mensaje": "Tienda creada correctamente"}

@app.post("/tienda/login")
def login_tienda(login_data: LoginData):
    tienda = buscar_tienda(login_data.nombre)
    if not tienda:
        raise HTTPException(status_code=404, detail="Tienda no encontrada")
    if login_data.patron_password != tienda["tienda"]["patron_password"]:
        raise HTTPException(status_code=401, detail="Nombre o contraseña incorrectos")

    ahora = datetime.now()
    tienda["ultimo_acceso"] = {
        "fecha": ahora.strftime("%Y-%m-%d"),
        "hora": ahora.strftime("%H:%M:%S")
    }

    tiendas = leer_json(TIENDAS_JSON)
    for i, t in enumerate(tiendas):
        if t["tienda"]["nombre"].lower() == login_data.nombre.lower():
            tiendas[i] = tienda
            break
    guardar_json(TIENDAS_JSON, tiendas)
    return {"mensaje": "Login exitoso", "ultimo_acceso": tienda["ultimo_acceso"]}

@app.get("/tienda", response_model=List[TiendaCompleta])
def listar_tiendas():
    return leer_json(TIENDAS_JSON)

@app.get("/tienda/{nombre_tienda}/patron/password")
def obtener_patron(nombre_tienda: str):
    tienda = buscar_tienda(nombre_tienda)
    if not tienda:
        raise HTTPException(status_code=404, detail="Tienda no encontrada")
    
    patron = tienda["tienda"]
    return {"nombre": patron.get("nombre", ""), "password": patron.get("patron_password", "")}

@app.post("/tienda/{nombre_tienda}/patron/password")
def guardar_patron(nombre_tienda: str, data: LoginData):
    tienda = buscar_tienda(nombre_tienda)
    if not tienda:
        raise HTTPException(status_code=404, detail="Tienda no encontrada")
    
    # Guardar nombre y contraseña del patrón
    tienda["tienda"]["nombre"] = data.nombre
    tienda["tienda"]["patron_password"] = data.patron_password
    
    # Guardar cambios en el JSON
    tiendas = leer_json(TIENDAS_JSON)
    for i, t in enumerate(tiendas):
        if t["tienda"]["nombre"].lower() == nombre_tienda.lower():
            tiendas[i] = tienda
            break
    guardar_json(TIENDAS_JSON, tiendas)
    
    return {"mensaje": "Datos del patrón guardados correctamente"}

@app.post("/ventas")
def agregar_venta(venta: Venta):
    ventas = leer_json(VENTAS_JSON)
    ventas.append(venta.dict())
    guardar_json(VENTAS_JSON, ventas)
    return {"mensaje": "Venta agregada correctamente"}

@app.get("/ventas", response_model=List[Venta])
def listar_ventas():
    return leer_json(VENTAS_JSON)

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

    for prod in inventario:
        if prod["producto"] == item.producto:
            prod["piezas"] += item.piezas
            prod["precio"] = item.precio
            guardar_json(INVENTARIO_JSON, data)
            return {"mensaje": "Producto actualizado en inventario"}

    inventario.append(item.dict())
    data["inventario"] = inventario
    guardar_json(INVENTARIO_JSON, data)
    return {"mensaje": "Producto agregado al inventario"}

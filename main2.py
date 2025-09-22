from fastapi import FastAPI, HTTPException, APIRouter
from pydantic import BaseModel
import json
from typing import List, Optional
from datetime import datetime
from databases import Database
from sqlalchemy import Boolean 
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, JSON

# ---------------------
# Base de datos
# ---------------------
DATABASE_URL = "postgresql://postgres.bkenrvxjxdtvwhdstspn:JakeAG1234@aws-1-us-east-2.pooler.supabase.com:5432/postgres"
database = Database(DATABASE_URL)
metadata = MetaData()

tiendas_table = Table(
    "tiendas",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("nombre", String, nullable=False),
    Column("password", String, nullable=False),
    Column("patron", JSON),
    Column("empleados", JSON),
    Column("inventario", JSON),
    Column("ventas", JSON),
    Column("cortes", JSON),
    Column("dispositivos_registrados", JSON, default=[]),  # NUEVO
    Column("dispositivos_permitidos", Integer, default=2),  # NUEVO
    Column("permitir_ventas_fuera_inventario", Boolean, default=False) 
)

engine = create_engine(DATABASE_URL)
metadata.create_all(engine)

# ---------------------
# FastAPI
# ---------------------
app = FastAPI(title="API Tiendas Completa")

# ---------------------
# Modelos
# ---------------------

class PrestamoUpdate(BaseModel):
    id: Optional[int]
    cantidad: Optional[float]
    descripcion: Optional[str]

class EmpleadoUpdate(BaseModel):
    nombre: Optional[str]
    puesto: Optional[str]
    sueldo: Optional[float]
    password: Optional[str]
    nota: Optional[str]
    prestamos: Optional[List[PrestamoUpdate]]

class ProductoVenta(BaseModel):
    producto: str
    precio: float
    cantidad: int = 1

class VentaRequest(BaseModel):
    usuario: str
    productos: List[ProductoVenta]
    fuera_inventario: bool = True

class PrestamoRequest(BaseModel):
    cantidad: float
    descripcion: str = ""

class DispositivoRequest(BaseModel):
    uuid: str

class DispositivosPermitidosRequest(BaseModel):
    dispositivos_permitidos: int

# ---------------------
# Funciones utilitarias
# ---------------------
def crear_estructura_tienda(nombre: str, password: str):
    return {
        "patron": None,
        "empleados": [],
        "inventario": [],
        "ventas": [],
        "cortes": {"diarios": [], "semanales": []},
        "dispositivos_registrados": [],  # NUEVO
        "dispositivos_permitidos": 2,   # NUEVO
        "permitir_ventas_fuera_inventario": False
    }


async def obtener_tienda_json(tienda_id: int):
    query = tiendas_table.select().where(tiendas_table.c.id == tienda_id)
    tienda = await database.fetch_one(query)
    if not tienda:
        raise HTTPException(status_code=404, detail="Tienda no encontrada")
    
    tienda_dict = dict(tienda)
    
    # Campos JSON que necesitamos parsear
    campos_json = {
        "patron": None,                   # dict o None
        "empleados": [],                  # lista
        "inventario": [],                 # lista
        "ventas": [],                     # lista
        "cortes": {"diarios": [], "semanales": []},  # dict con listas
        "dispositivos_registrados": [],    # lista
        "permitir_ventas_fuera_inventario": False
    }
    
    for campo, default in campos_json.items():
        valor = tienda_dict.get(campo)
        if isinstance(valor, str):
            try:
                tienda_dict[campo] = json.loads(valor)
            except Exception:
                tienda_dict[campo] = default
        elif valor is None:
            tienda_dict[campo] = default

    return tienda_dict


import json

async def actualizar_tienda(tienda_id: int, datos: dict):
    campos_json = ["patron", "empleados", "inventario", "ventas", "cortes", "dispositivos_registrados"]
    datos_serializados = datos.copy()
    
    for campo in campos_json:
        if campo in datos_serializados:
            datos_serializados[campo] = json.dumps(datos_serializados[campo])
    
    await database.execute(
        tiendas_table.update()
        .where(tiendas_table.c.id == tienda_id)
        .values(**datos_serializados)
    )


# ---------------------
# Routers existentes
# ---------------------
tiendas_router = APIRouter(prefix="/tiendas", tags=["Tiendas"])
patron_router = APIRouter(prefix="/tiendas/{tienda_id}/patron", tags=["Patrón"])
empleados_router = APIRouter(prefix="/tiendas/{tienda_id}/empleados", tags=["Empleados"])
inventario_router = APIRouter(prefix="/tiendas/{tienda_id}/inventario", tags=["Inventario"])
ventas_router = APIRouter(prefix="/tiendas/{tienda_id}/ventas", tags=["Ventas"])
cortes_router = APIRouter(prefix="/tiendas/{tienda_id}/cortes", tags=["Cortes"])
prestamos_router = APIRouter(prefix="/tiendas/{tienda_id}/empleados/{empleado_id}/prestamos", tags=["Préstamos"])

# ---------------------
# Endpoints dispositivos NUEVOS
# ---------------------
dispositivos_router = APIRouter(prefix="/tiendas/{tienda_id}/dispositivos", tags=["Dispositivos"])

@dispositivos_router.get("/")
async def obtener_dispositivos(tienda_id: int):
    tienda = await obtener_tienda_json(tienda_id)
    return {"dispositivos_registrados": tienda.get("dispositivos_registrados", [])}

@dispositivos_router.post("/")
async def registrar_dispositivo(tienda_id: int, dispositivo: DispositivoRequest):
    tienda = await obtener_tienda_json(tienda_id)
    registrados = tienda.get("dispositivos_registrados", [])
    max_dispositivos = tienda.get("dispositivos_permitidos", 2)
    
    # Primero check duplicado
    if dispositivo.uuid in registrados:
        raise HTTPException(status_code=400, detail="Dispositivo ya registrado")
    
    # Luego check de límite
    if len(registrados) >= max_dispositivos:
        raise HTTPException(status_code=400, detail="Límite de dispositivos alcanzado")
    
    # Agregar dispositivo
    registrados.append(dispositivo.uuid)
    await actualizar_tienda(tienda_id, {"dispositivos_registrados": registrados})
    return {"mensaje": "Dispositivo registrado", "uuid": dispositivo.uuid}


@dispositivos_router.put("/permitidos")
async def actualizar_dispositivos_permitidos(tienda_id: int, data: DispositivosPermitidosRequest):
    await actualizar_tienda(tienda_id, {"dispositivos_permitidos": data.dispositivos_permitidos})
    return {"mensaje": "Cantidad máxima de dispositivos actualizada", "dispositivos_permitidos": data.dispositivos_permitidos}

@dispositivos_router.delete("/{uuid_dispositivo}")
async def eliminar_dispositivo(tienda_id: int, uuid_dispositivo: str):
    tienda = await obtener_tienda_json(tienda_id)
    registrados = tienda.get("dispositivos_registrados", [])
    if uuid_dispositivo not in registrados:
        raise HTTPException(status_code=404, detail="Dispositivo no encontrado")
    registrados = [d for d in registrados if d != uuid_dispositivo]
    await actualizar_tienda(tienda_id, {"dispositivos_registrados": registrados})
    return {"mensaje": "Dispositivo eliminado"}
# ---------------------
# Rutas Tiendas
# ---------------------
@tiendas_router.get("/")
async def listar_tiendas():
    resultado = await database.fetch_all(tiendas_table.select())
    return [dict(t) for t in resultado]

@tiendas_router.post("/")
async def crear_tienda(nombre: str, password: str):
    estructura = crear_estructura_tienda(nombre, password)
    query = tiendas_table.insert().values(
        nombre=nombre,
        password=password,
        patron=estructura["patron"],
        empleados=estructura["empleados"],
        inventario=estructura["inventario"],
        ventas=estructura["ventas"],
        cortes=estructura["cortes"]
    ).returning(tiendas_table)
    nueva = await database.fetch_one(query)
    return dict(nueva)

@tiendas_router.get("/{tienda_id}")
async def obtener_tienda(tienda_id: int):
    return await obtener_tienda_json(tienda_id)

@tiendas_router.delete("/{tienda_id}")
async def eliminar_tienda(tienda_id: int):
    await database.execute(tiendas_table.delete().where(tiendas_table.c.id == tienda_id))
    return {"mensaje": "Tienda eliminada"}

# ---------------------
# Rutas Patrón
# ---------------------
@patron_router.get("/")
async def obtener_patron(tienda_id: int):
    tienda = await obtener_tienda_json(tienda_id)
    return tienda["patron"]

@patron_router.post("/")
async def crear_patron(tienda_id: int, nombre: str, password: str):
    nuevo_patron = {"nombre": nombre, "password": password}
    await actualizar_tienda(tienda_id, {"patron": nuevo_patron})
    return nuevo_patron

@patron_router.delete("/")
async def eliminar_patron(tienda_id: int):
    await actualizar_tienda(tienda_id, {"patron": None})
    return {"mensaje": "Patrón eliminado"}

# ---------------------
# Rutas Empleados
# ---------------------
@empleados_router.get("/")
async def listar_empleados(tienda_id: int):
    tienda = await obtener_tienda_json(tienda_id)
    return tienda["empleados"]

@empleados_router.post("/")
async def crear_empleado(tienda_id: int, nombre: str, puesto: str, sueldo: float, password: str, nota: str = ""):
    tienda = await obtener_tienda_json(tienda_id)
    nuevo = {"id": len(tienda["empleados"])+1, "nombre": nombre, "puesto": puesto, "sueldo": sueldo, "password": password, "nota": nota, "prestamos": []}
    empleados = tienda["empleados"] + [nuevo]
    await actualizar_tienda(tienda_id, {"empleados": empleados})
    return nuevo

@empleados_router.put("/{empleado_id}")
async def editar_empleado(tienda_id: int, empleado_id: int, data: EmpleadoUpdate):
    tienda = await obtener_tienda_json(tienda_id)
    empleado = next((e for e in tienda["empleados"] if e["id"] == empleado_id), None)
    if not empleado: 
        raise HTTPException(status_code=404, detail="Empleado no encontrado")
    
    update_dict = data.dict(exclude_unset=True)

    # Actualizar campos básicos
    for key in ["nombre", "puesto", "sueldo", "password", "nota"]:
        if key in update_dict:
            empleado[key] = update_dict[key]

    # Actualizar préstamos si vienen
    if "prestamos" in update_dict:
        for prestamo in update_dict["prestamos"]:
            prestamo_id = prestamo.get("id")
            existing = next((p for p in empleado["prestamos"] if p["id"] == prestamo_id), None)
            if existing:
                if "cantidad" in prestamo:
                    existing["cantidad"] = float(prestamo["cantidad"])
                if "pendiente" in prestamo:
                    existing["pendiente"] = prestamo["pendiente"]
            else:
                # nuevo préstamo
                nuevo_id = (max([p["id"] for p in empleado["prestamos"]] + [0]) + 1)
                empleado["prestamos"].append({
                    "id": nuevo_id,
                    "cantidad": prestamo.cantidad,
                    "descripcion": prestamo.descripcion,
                    "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })

    # Guardar cambios
    await actualizar_tienda(tienda_id, {"empleados": tienda["empleados"]})
    return empleado


@empleados_router.delete("/{empleado_id}")
async def eliminar_empleado(tienda_id: int, empleado_id: int):
    tienda = await obtener_tienda_json(tienda_id)
    empleados = [e for e in tienda["empleados"] if e["id"] != empleado_id]
    await actualizar_tienda(tienda_id, {"empleados": empleados})
    return {"mensaje": "Empleado eliminado"}

# ---------------------
# Rutas Inventario
# ---------------------
@inventario_router.get("/")
async def listar_inventario(tienda_id: int):
    tienda = await obtener_tienda_json(tienda_id)
    return tienda["inventario"]

@inventario_router.post("/")
async def agregar_producto(tienda_id: int, producto: str, precio: float, piezas: int):
    tienda = await obtener_tienda_json(tienda_id)
    nuevo = {"id": len(tienda["inventario"])+1, "producto": producto, "precio": precio, "piezas": piezas}
    inventario = tienda["inventario"] + [nuevo]
    await actualizar_tienda(tienda_id, {"inventario": inventario})
    return nuevo

@inventario_router.put("/{producto_id}")
async def editar_producto(tienda_id: int, producto_id: int, producto: str = None, precio: float = None, piezas: int = None):
    tienda = await obtener_tienda_json(tienda_id)
    prod = next((p for p in tienda["inventario"] if p["id"] == producto_id), None)
    if not prod: raise HTTPException(status_code=404)
    if producto: prod["producto"] = producto
    if precio: prod["precio"] = precio
    if piezas: prod["piezas"] = piezas
    await actualizar_tienda(tienda_id, {"inventario": tienda["inventario"]})
    return prod

@inventario_router.delete("/{producto_id}")
async def eliminar_producto(tienda_id: int, producto_id: int):
    tienda = await obtener_tienda_json(tienda_id)
    inventario = [p for p in tienda["inventario"] if p["id"] != producto_id]
    await actualizar_tienda(tienda_id, {"inventario": inventario})
    return {"mensaje": "Producto eliminado"}

# ---------------------
# Rutas Ventas
# ---------------------
@ventas_router.get("/", include_in_schema=False)
@ventas_router.get("")
async def listar_ventas(tienda_id: int):
    tienda = await obtener_tienda_json(tienda_id)
    return tienda["ventas"]

@ventas_router.post("/")
async def agregar_venta(tienda_id: int, venta: VentaRequest):
    print("Venta recibida:", venta.dict())

    tienda = await obtener_tienda_json(tienda_id)

    # Calcular total
    total = sum(p.precio * p.cantidad for p in venta.productos)
    permitir_fuera = tienda.get("permitir_ventas_fuera_inventario", False)

    fuera_inventario = False  # bandera general para esta venta

    # Verificar y actualizar inventario
    for producto_vendido in venta.productos:
        encontrado = False
        for prod_inventario in tienda["inventario"]:
            if prod_inventario["producto"] == producto_vendido.producto:
                encontrado = True
                cantidad_vendida = int(producto_vendido.cantidad)

                if cantidad_vendida > prod_inventario["piezas"]:
                    if not permitir_fuera:
                        raise HTTPException(
                            status_code=400,
                            detail=f"No hay suficiente stock de {producto_vendido.producto} "
                                   f"(disponible {prod_inventario['piezas']})"
                        )
                    else:
                        fuera_inventario = True

                # Descontar si hay piezas
                if prod_inventario["piezas"] >= cantidad_vendida:
                    prod_inventario["piezas"] -= cantidad_vendida
                break

        if not encontrado:
            # Si el producto no está en inventario, solo marcamos la venta como "fuera"
            fuera_inventario = True

    # Crear registro de venta
    nueva_venta = {
        "id": len(tienda["ventas"]) + 1,
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "usuario": venta.usuario,
        "productos": [p.dict() for p in venta.productos],
        "total": total,
        "fuera_inventario": fuera_inventario
    }

    # Guardar venta e inventario actualizado
    ventas = tienda["ventas"] + [nueva_venta]
    await actualizar_tienda(tienda_id, {
        "ventas": ventas,
        "inventario": tienda["inventario"]
    })

    return nueva_venta

@ventas_router.post("")
async def agregar_venta_sin_slash(tienda_id: int, venta: VentaRequest):
    return await agregar_venta(tienda_id, venta)


@ventas_router.delete("/{venta_id}")
async def eliminar_venta(tienda_id: int, venta_id: int):
    tienda = await obtener_tienda_json(tienda_id)
    ventas = [v for v in tienda["ventas"] if v["id"] != venta_id]
    await actualizar_tienda(tienda_id, {"ventas": ventas})
    return {"mensaje": "Venta eliminada"}

# ---------------------
# Rutas Cortes
# ---------------------
@cortes_router.get("/diarios")
async def listar_cortes_diarios(tienda_id: int):
    tienda = await obtener_tienda_json(tienda_id)
    return tienda["cortes"]["diarios"]

@cortes_router.post("/diarios")
async def crear_corte_diario(tienda_id: int, usuario_que_corto: str):
    tienda = await obtener_tienda_json(tienda_id)
    corte = {
        "id": len(tienda["cortes"]["diarios"])+1,
        "fecha": datetime.now().strftime("%Y-%m-%d"),
        "hora": datetime.now().strftime("%H:%M:%S"),
        "usuario_que_corto": usuario_que_corto,
        "ventas": tienda["ventas"].copy(),
        "total": sum(v["total"] for v in tienda["ventas"])
    }
    cortes_diarios = tienda["cortes"]["diarios"] + [corte]
    cortes = {"diarios": cortes_diarios, "semanales": tienda["cortes"]["semanales"]}
    await actualizar_tienda(tienda_id, {"cortes": cortes, "ventas": []})
    return corte

@cortes_router.delete("/diarios/{corte_id}")
async def eliminar_corte_diario(tienda_id: int, corte_id: int):
    tienda = await obtener_tienda_json(tienda_id)
    diarios = [c for c in tienda["cortes"]["diarios"] if c["id"] != corte_id]
    cortes = {"diarios": diarios, "semanales": tienda["cortes"]["semanales"]}
    await actualizar_tienda(tienda_id, {"cortes": cortes})
    return {"mensaje": "Corte diario eliminado"}

@cortes_router.get("/semanales")
async def listar_cortes_semanales(tienda_id: int):
    tienda = await obtener_tienda_json(tienda_id)
    return tienda["cortes"]["semanales"]

@cortes_router.post("/semanales")
async def crear_corte_semanal(tienda_id: int):
    tienda = await obtener_tienda_json(tienda_id)
    corte = {"id": len(tienda["cortes"]["semanales"])+1, "fecha": datetime.now().strftime("%Y-%m-%d"), "cortes_diarios": tienda["cortes"]["diarios"].copy()}
    cortes_semanales = tienda["cortes"]["semanales"] + [corte]
    cortes = {"diarios": [], "semanales": cortes_semanales}
    await actualizar_tienda(tienda_id, {"cortes": cortes})
    return corte

@cortes_router.delete("/semanales/{corte_id}")
async def eliminar_corte_semanal(tienda_id: int, corte_id: int):
    tienda = await obtener_tienda_json(tienda_id)
    semanales = [c for c in tienda["cortes"]["semanales"] if c["id"] != corte_id]
    cortes = {"diarios": tienda["cortes"]["diarios"], "semanales": semanales}
    await actualizar_tienda(tienda_id, {"cortes": cortes})
    return {"mensaje": "Corte semanal eliminado"}

# ---------------------
# Rutas Préstamos
# ---------------------
@prestamos_router.get("/")
async def listar_prestamos(tienda_id: int, empleado_id: int):
    tienda = await obtener_tienda_json(tienda_id)
    empleado = next((e for e in tienda["empleados"] if e["id"] == empleado_id), None)
    if not empleado: raise HTTPException(status_code=404)
    return empleado["prestamos"]

@prestamos_router.post("/")
async def agregar_prestamo(tienda_id: int, empleado_id: int, prestamo: PrestamoRequest):
    tienda = await obtener_tienda_json(tienda_id)
    empleado = next((e for e in tienda["empleados"] if e["id"] == empleado_id), None)
    if not empleado: raise HTTPException(status_code=404)
    nuevo = {
        "id": len(empleado["prestamos"])+1,
        "cantidad": prestamo.cantidad,
        "descripcion": prestamo.descripcion,
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    empleado["prestamos"].append(nuevo)
    empleados = [e if e["id"] != empleado_id else empleado for e in tienda["empleados"]]
    await actualizar_tienda(tienda_id, {"empleados": empleados})
    return nuevo

@prestamos_router.put("/{prestamo_id}")
async def editar_prestamo(tienda_id: int, empleado_id: int, prestamo_id: int, cantidad: float = None, descripcion: str = None):
    tienda = await obtener_tienda_json(tienda_id)
    empleado = next((e for e in tienda["empleados"] if e["id"] == empleado_id), None)
    if not empleado:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")
    
    prestamo = next((p for p in empleado["prestamos"] if p["id"] == prestamo_id), None)
    if not prestamo:
        raise HTTPException(status_code=404, detail="Préstamo no encontrado")
    
    if cantidad is not None:
        prestamo["cantidad"] = cantidad
    if descripcion is not None:
        prestamo["descripcion"] = descripcion
    
    empleados = [e if e["id"] != empleado_id else empleado for e in tienda["empleados"]]
    await actualizar_tienda(tienda_id, {"empleados": empleados})
    return prestamo

@prestamos_router.delete("/{prestamo_id}")
async def eliminar_prestamo(tienda_id: int, empleado_id: int, prestamo_id: int):
    tienda = await obtener_tienda_json(tienda_id)
    empleado = next((e for e in tienda["empleados"] if e["id"] == empleado_id), None)
    if not empleado:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")
    
    prestamos = [p for p in empleado["prestamos"] if p["id"] != prestamo_id]
    empleado["prestamos"] = prestamos
    
    empleados = [e if e["id"] != empleado_id else empleado for e in tienda["empleados"]]
    await actualizar_tienda(tienda_id, {"empleados": empleados})
    return {"mensaje": "Préstamo eliminado"}

# ---------------------
# Eventos Startup / Shutdown
# ---------------------
@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

# ---------------------
# Incluir routers
# ---------------------
app.include_router(tiendas_router)
app.include_router(patron_router)
app.include_router(empleados_router)
app.include_router(inventario_router)
app.include_router(ventas_router)
app.include_router(cortes_router)
app.include_router(prestamos_router)
app.include_router(dispositivos_router) 

@app.get("/")
async def raiz():
    return {"mensaje": "API Tiendas completa lista para usar"}
from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.properties import ListProperty, StringProperty
from datetime import datetime
from fuzzywuzzy import process
from kivy.graphics import Rectangle
import os
from kivy.resources import resource_add_path
import json
import requests

API_URL = "https://mi-caja-api.onrender.com/tiendas"

class VentaInventario(Screen):
    productos = ListProperty([])  # Inventario completo
    nombre_usuario = StringProperty("")

    def __init__(self, **kwargs):
        super(VentaInventario, self).__init__(**kwargs)
        self.tienda_id = None
        self.carrito = []
        self.producto_seleccionado = None
        self.boton_seleccionado = None
        self.nombre_usuario = ""

        # Layout base con fondo

        self.layout = FloatLayout()  # <-- se crea primero
        self.add_widget(self.layout)

        with self.layout.canvas.before:
            self.fondo_rect = Rectangle(source="fondo.png", pos=self.layout.pos, size=self.layout.size)
        self.layout.bind(size=self._update_rect, pos=self._update_rect)

        # Layout principal vertical encima
        self.layout_principal = BoxLayout(orientation='vertical', spacing=10, padding=10)
        self.layout.add_widget(self.layout_principal)

        # Barra de búsqueda
        layout_busqueda = BoxLayout(size_hint_y=None, height=40, spacing=10)
        self.input_busqueda = TextInput(hint_text="Buscar producto...", multiline=False)
        self.boton_buscar = Button(text="Buscar", size_hint_x=None, width=100)
        self.boton_buscar.bind(on_release=self.buscar)
        layout_busqueda.add_widget(self.input_busqueda)
        layout_busqueda.add_widget(self.boton_buscar)
        self.layout_principal.add_widget(layout_busqueda)

        self.label_seleccion = Label(text="Producto seleccionado: Ninguno", size_hint_y=None, height=30)
        self.layout_principal.add_widget(self.label_seleccion)

        # Lista resultados
        self.scroll_resultados = ScrollView()
        self.grid_resultados = GridLayout(cols=1, spacing=10, size_hint_y=None)
        self.grid_resultados.bind(minimum_height=self.grid_resultados.setter('height'))
        self.scroll_resultados.add_widget(self.grid_resultados)
        self.layout_principal.add_widget(self.scroll_resultados)

        # Cantidad piezas y botón seleccionar
        layout_cantidad = BoxLayout(size_hint_y=None, height=40, spacing=10)
        self.input_piezas = TextInput(hint_text="Piezas", multiline=False, input_filter='int', size_hint_x=0.3)
        self.boton_seleccionar = Button(text="Seleccionar", size_hint_x=0.7)
        self.boton_seleccionar.bind(on_release=self.agregar_al_carrito)
        self.boton_eliminar = Button(text="Eliminar", size_hint_x=0.7)
        self.boton_eliminar.bind(on_release=self.eliminar_producto)
        layout_cantidad.add_widget(self.input_piezas)
        layout_cantidad.add_widget(self.boton_seleccionar)
        layout_cantidad.add_widget(self.boton_eliminar)
        self.layout_principal.add_widget(layout_cantidad)

        # Botones Volver y Finalizar compra
        layout_botones_final = BoxLayout(size_hint_y=None, height=40, spacing=10)
        self.boton_volver = Button(text="Volver")
        self.boton_volver.bind(on_release=self.volver_a_principal)
        self.boton_finalizar = Button(text="Finalizar compra")
        self.boton_finalizar.bind(on_release=lambda x: self.mostrar_popup_carrito())
        layout_botones_final.add_widget(self.boton_volver)
        layout_botones_final.add_widget(self.boton_finalizar)
        self.layout_principal.add_widget(layout_botones_final)

    def _update_rect(self, *args):
        self.fondo_rect.pos = self.layout.pos
        self.fondo_rect.size = self.layout.size

    # --------------------- Funciones API ---------------------
    def set_tienda_id(self, tienda_id):
        self.tienda_id = tienda_id
        self.cargar_productos()

    def set_usuario(self, nombre):
        self.nombre_usuario = nombre

    def cargar_productos(self):
        if not self.tienda_id:
            print("Tienda ID no seteada")
            self.productos = []
            return
        try:
            resp = requests.get(f"{API_URL}/{self.tienda_id}/inventario/")
            print(resp.status_code, resp.text)  # <<-- agregar debug
            if resp.status_code == 200:
                inventario = resp.json()
                print("Inventario crudo:", inventario)  # <<-- agregar debug
                self.productos = [prod for prod in inventario if prod.get('piezas', 0) > 0]
                print("Productos filtrados:", self.productos)
            else:
                self.productos = []
                print("Error cargando inventario:", resp.status_code, resp.text)
        except Exception as e:
            self.productos = []
            print("Error API cargar productos:", e)
        self.mostrar_resultados(self.productos)

    def guardar_productos_api(self):
        """Actualiza inventario en API después de venta"""
        if not self.tienda_id:
            return
        for item in self.productos:
            try:
                resp = requests.put(
                    f"{API_URL}/{self.tienda_id}/inventario/{item['id']}",
                    params={"producto": item['producto'], "precio": float(item['precio']), "piezas": int(item['piezas'])}
                )
                if resp.status_code != 200:
                    print(f"Error actualizando {item['producto']}:", resp.text)
            except Exception as e:
                print("Error API actualizar producto:", e)

    def confirmar_venta(self, instance):
        """Confirma venta: descuenta inventario y guarda venta en API como objeto JSON"""
        if not self.tienda_id:
            self.mostrar_mensaje("Tienda no definida")
            return

        if not self.carrito:
            self.mostrar_mensaje("No hay productos en el carrito")
            return

        # Descontar piezas localmente
        for item_carrito in self.carrito:
            for prod in self.productos:
                if prod['producto'] == item_carrito['producto'] and prod['precio'] == item_carrito['precio']:
                    prod['piezas'] -= item_carrito['cantidad']
                    if prod['piezas'] < 0:
                        prod['piezas'] = 0

        # Actualizar inventario en API
        self.guardar_productos_api()

        # Armar diccionario de venta para API
        datos_venta = {
            "usuario": self.nombre_usuario,
            "fuera_inventario": False,  # o True si quieres que no descuente inventario
            "productos": [
                {
                    "producto": item["producto"],
                    "precio": float(item["precio"]),
                    "cantidad": int(item["cantidad"])
                }
                for item in self.carrito
            ]
        }

        try:
            print("Datos a enviar a API (diccionario):", json.dumps(datos_venta, indent=2))

            # Enviar la venta como JSON
            resp = requests.post(
                f"{API_URL}/{self.tienda_id}/ventas/",
                json=datos_venta
            )

            if resp.status_code not in (200, 201):
                print("Error detalle API:", resp.text)
                self.mostrar_mensaje(f"Error guardando venta en API: {resp.text}")
                return

        except Exception as e:
            import traceback
            traceback.print_exc()
            self.mostrar_mensaje(f"Error API venta: {e}")
            return

        # Limpiar carrito y actualizar UI si todo salió bien
        self.carrito.clear()
        self.mostrar_resultados(self.productos)
        if hasattr(self, 'popup') and self.popup:
            self.popup.dismiss()
        self.mostrar_mensaje("Venta confirmada con éxito.")


    # --------------------- Funciones UI (sin cambios) ---------------------
    def buscar(self, instance):
        texto = self.input_busqueda.text.strip()
        if texto:
            productos_filtrados = self.buscar_producto_clave(texto)
            self.mostrar_resultados(productos_filtrados)
        else:
            self.mostrar_resultados(self.productos)

    def buscar_producto_clave(self, texto_busqueda):
        productos_nombres = [prod['producto'] for prod in self.productos]
        # Extraer resultados sin score_cutoff
        resultados = process.extract(texto_busqueda, productos_nombres, limit=10)
        # Filtrar manualmente los que tengan score >= 60
        resultados = [r for r in resultados if r[1] >= 60]
        # Conseguir índices en la lista original
        indices = [productos_nombres.index(r[0]) for r in resultados]
        return [self.productos[i] for i in indices]


    def mostrar_resultados(self, lista_productos):
        self.grid_resultados.clear_widgets()
        productos_filtrados = [prod for prod in lista_productos if prod.get('piezas', 0) > 0]
        for idx, prod in enumerate(productos_filtrados):
            piezas = prod.get('piezas', 0)
            btn = Button(text=f"{prod['producto']}  -  ${prod['precio']}  -  {piezas} piezas", size_hint_y=None, height=40)
            btn.bind(on_release=lambda btn, i=idx, lp=productos_filtrados: self.seleccionar_producto(i, lp, btn))
            btn.background_color = (1, 1, 1, 1) if self.boton_seleccionado != btn else (0,0,1,1)
            self.grid_resultados.add_widget(btn)

    def seleccionar_producto(self, index, lista_actual, boton):
        self.producto_seleccionado = lista_actual[index]
        if self.boton_seleccionado:
            self.boton_seleccionado.background_color = (1, 1, 1, 1)
        boton.background_color = (0, 0, 1, 1)
        self.boton_seleccionado = boton
        self.label_seleccion.text = f"Producto seleccionado: {self.producto_seleccionado['producto']}"

    def agregar_al_carrito(self, instance):
        if not self.producto_seleccionado:
            self.mostrar_mensaje("Por favor seleccione un producto.")
            return
        try:
            piezas = int(self.input_piezas.text.strip())
            if piezas <= 0:
                raise ValueError()
        except:
            self.mostrar_mensaje("Cantidad de piezas inválida.")
            return

        if piezas > self.producto_seleccionado.get('piezas', 0):
            self.mostrar_mensaje(f"No hay suficientes piezas disponibles. Solo quedan {self.producto_seleccionado.get('piezas', 0)}")
            return

        encontrado = False
        for item in self.carrito:
            if item['producto'] == self.producto_seleccionado['producto'] and item['precio'] == self.producto_seleccionado['precio']:
                item['cantidad'] += piezas
                encontrado = True
                break
        if not encontrado:
            nuevo_item = self.producto_seleccionado.copy()
            nuevo_item['cantidad'] = piezas
            self.carrito.append(nuevo_item)

        self.input_piezas.text = ''
        if self.boton_seleccionado:
            self.boton_seleccionado.background_color = (1, 1, 1, 1)
            self.boton_seleccionado = None
            self.producto_seleccionado = None

    def eliminar_producto(self, instance):
        if not self.producto_seleccionado:
            self.mostrar_mensaje("No hay ningún producto seleccionado para eliminar.")
            return
        nombre = self.producto_seleccionado.get('producto', None)
        if not nombre:
            self.mostrar_mensaje("Producto seleccionado inválido.")
            return
        eliminado = False
        for i, item in enumerate(self.carrito):
            if item['producto'] == nombre:
                del self.carrito[i]
                eliminado = True
                break
        self.mostrar_mensaje(f"Producto '{nombre}' eliminado del carrito." if eliminado else "El producto seleccionado no está en el carrito.")

    def mostrar_mensaje(self, texto):
        popup = Popup(title="Aviso", content=Label(text=texto), size_hint=(0.6,0.4))
        popup.open()

    def mostrar_popup_carrito(self):
        contenido = BoxLayout(orientation='vertical', spacing=10, padding=10)
        grid = GridLayout(cols=2, size_hint_y=None, spacing=5)
        grid.bind(minimum_height=grid.setter('height'))

        total = 0
        for item in self.carrito:
            subtotal = item['cantidad'] * float(item['precio'])
            total += subtotal
            lbl_prod = Label(text=f"{item['cantidad']} {item['producto']}", size_hint_y=None, height=30)
            lbl_sub = Label(text=f"${subtotal:.2f}", size_hint_y=None, height=30, halign='right', valign='middle')
            lbl_sub.bind(size=lbl_sub.setter('text_size'))
            grid.add_widget(lbl_prod)
            grid.add_widget(lbl_sub)

        scroll = ScrollView(size_hint=(1,0.7))
        scroll.add_widget(grid)
        contenido.add_widget(scroll)

        layout_abajo = BoxLayout(size_hint_y=None, height=40, spacing=10)
        btn_cancelar = Button(text="Cancelar")
        btn_total = Button(text=f"Total = ${total:.2f}")
        layout_abajo.add_widget(btn_cancelar)
        layout_abajo.add_widget(btn_total)
        contenido.add_widget(layout_abajo)

        self.popup = Popup(title="Carrito de venta", content=contenido, size_hint=(0.8,0.8), auto_dismiss=False)
        btn_cancelar.bind(on_release=lambda x: self.popup.dismiss())
        def on_click_total(instance):
            try:
                self.confirmar_venta(instance)
            except Exception as e:
                import traceback
                traceback.print_exc()
                self.mostrar_mensaje(f"Ocurrió un error: {e}")

        btn_total.bind(on_release=on_click_total)

        self.popup.open()

    def on_enter(self):
        if self.tienda_id:
            self.cargar_productos()
        else:
            print("Tienda ID aún no seteada, esperar antes de cargar inventario")

    def volver_a_principal(self, instance):
        self.manager.current = 'pantalla_principal'

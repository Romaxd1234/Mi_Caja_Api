from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget
from kivy.uix.image import Image
from kivy.properties import ListProperty
from kivy.resources import resource_add_path
from kivy.graphics import Rectangle
import os
import requests

API_URL = "https://mi-caja-api.onrender.com/tiendas"

class VentanaInventario(Screen):
    productos = ListProperty([])

    def __init__(self, **kwargs):
        super(VentanaInventario, self).__init__(**kwargs)
        self.producto_seleccionado = None

        # Assets
        ruta_assets = os.path.join(os.path.dirname(__file__), "assets")
        resource_add_path(ruta_assets)

        # Fondo con canvas
        with self.canvas.before:
            self.fondo_rect = Rectangle(source="fondo.png", pos=self.pos, size=self.size)
        self.bind(size=self._update_rect, pos=self._update_rect)

        # Layout principal
        self.layout_principal = BoxLayout(orientation='vertical', spacing=10, padding=10)
        self.add_widget(self.layout_principal)

        # Inputs y botón agregar
        self.layout_superior = BoxLayout(size_hint_y=None, height=40, spacing=10)
        self.input_producto = TextInput(hint_text='Producto', multiline=False)
        self.input_precio = TextInput(hint_text='Precio', multiline=False, input_filter='float')
        self.input_piezas = TextInput(hint_text='Piezas', multiline=False, input_filter='int')
        self.boton_agregar = Button(text='Agregar', size_hint_x=None, width=100)
        self.boton_agregar.bind(on_release=self.agregar_producto)
        self.layout_superior.add_widget(self.input_producto)
        self.layout_superior.add_widget(self.input_precio)
        self.layout_superior.add_widget(self.input_piezas)
        self.layout_superior.add_widget(self.boton_agregar)
        self.layout_principal.add_widget(self.layout_superior)

        # Scroll y grid para productos
        self.scrollview = ScrollView()
        self.grid_productos = GridLayout(cols=1, spacing=10, size_hint_y=None)
        self.grid_productos.bind(minimum_height=self.grid_productos.setter('height'))
        self.scrollview.add_widget(self.grid_productos)
        self.layout_principal.add_widget(self.scrollview)

        # Layout inferior botones
        layout_inferior = BoxLayout(size_hint_y=None, height=100, padding=10, spacing=20)

        col_izquierda = BoxLayout(orientation='vertical', spacing=10)
        self.boton_editar = Button(text='Editar', size_hint_y=None, height=40, disabled=True)
        self.boton_editar.bind(on_release=self.editar_producto)
        self.boton_volver = Button(text='Volver', size_hint_y=None, height=40)
        self.boton_volver.bind(on_release=self.volver_a_principal)
        col_izquierda.add_widget(self.boton_editar)
        col_izquierda.add_widget(Widget())
        col_izquierda.add_widget(self.boton_volver)

        col_derecha = BoxLayout(orientation='vertical', spacing=10)
        self.boton_eliminar = Button(text='Eliminar', size_hint_y=None, height=40, disabled=True)
        self.boton_eliminar.bind(on_release=self.eliminar_producto)
        self.boton_ir_a_ventas = Button(text='Ir a Ventas', size_hint_y=None, height=40)
        self.boton_ir_a_ventas.bind(on_release=self.ir_a_ventas)
        col_derecha.add_widget(self.boton_eliminar)
        col_derecha.add_widget(Widget())
        col_derecha.add_widget(self.boton_ir_a_ventas)

        widget_espacio = Widget(size_hint_x=None, width=20)
        layout_inferior.add_widget(col_izquierda)
        layout_inferior.add_widget(widget_espacio)
        layout_inferior.add_widget(col_derecha)
        self.layout_principal.add_widget(Widget(size_hint_y=None, height=20))
        self.layout_principal.add_widget(layout_inferior)

    # --------------------- Funciones ---------------------
    def _update_rect(self, *args):
        self.fondo_rect.pos = self.pos
        self.fondo_rect.size = self.size
        
    def set_tienda_api(self, tienda):
        """Recibe la tienda seleccionada desde AbrirTiendaScreen"""
        self.tienda_actual = tienda
        self.cargar_productos()

    def ir_a_ventas(self, instance):
        self.manager.current = 'venta_inventario'

    def volver_a_principal(self, instance):
        self.manager.current = 'pantalla_principal'

    def cargar_productos(self):
        if not hasattr(self, 'tienda_actual') or not self.tienda_actual:
            self.productos = []
            return
        try:
            resp = requests.get(f"{API_URL}/{self.tienda_actual['id']}/inventario/")
            if resp.status_code == 200:
                self.productos = resp.json()
            else:
                self.productos = []
        except:
            self.productos = []
        self.actualizar_lista()

    def agregar_producto(self, instance):
        if not hasattr(self, 'tienda_actual') or not self.tienda_actual:
            print("No hay tienda seleccionada")
            return

        nombre = self.input_producto.text.strip()
        precio = self.input_precio.text.strip()
        piezas = self.input_piezas.text.strip()

        if not (nombre and precio and piezas):
            print("Faltan datos para agregar el producto")
            return

        try:
            resp = requests.post(
                f"{API_URL}/{self.tienda_actual['id']}/inventario/",
                params={"producto": nombre, "precio": float(precio), "piezas": int(piezas)}
            )
            if resp.status_code == 200:
                self.input_producto.text = ''
                self.input_precio.text = ''
                self.input_piezas.text = ''
                self.cargar_productos()
            else:
                print("Error al agregar producto:", resp.text)
        except Exception as e:
            print("Error API agregar:", e)

    def actualizar_lista(self):
        self.grid_productos.clear_widgets()
        for prod in self.productos:
            btn = Button(
                text=f"{prod['producto']} - ${prod['precio']} - {prod['piezas']} piezas",
                size_hint_y=None, height=40
            )
            btn.prod_id = prod['id']  # guardamos el ID del producto
            btn.bind(on_release=lambda btn: self.seleccionar_producto(btn.prod_id))
            self.grid_productos.add_widget(btn)

        self.boton_editar.disabled = True
        self.boton_eliminar.disabled = True
        self.producto_seleccionado = None

    def seleccionar_producto(self, prod_id):
        # Buscamos el índice real en self.productos usando el ID
        for idx, prod in enumerate(self.productos):
            if prod['id'] == prod_id:
                self.producto_seleccionado = idx
                break
        self.boton_editar.disabled = False
        self.boton_eliminar.disabled = False

    def editar_producto(self, instance):
        if self.producto_seleccionado is None or not hasattr(self, 'tienda_actual'):
            return

        prod = self.productos[self.producto_seleccionado]
        self.input_producto.text = prod['producto']
        self.input_precio.text = str(prod['precio'])
        self.input_piezas.text = str(prod['piezas'])

        # Borrar producto anterior en la API usando ID
        try:
            requests.delete(f"{API_URL}/{self.tienda_actual['id']}/inventario/{prod['id']}")
        except:
            pass
        self.cargar_productos()

    def eliminar_producto(self, instance):
        if self.producto_seleccionado is None or not hasattr(self, 'tienda_actual'):
            return

        prod = self.productos[self.producto_seleccionado]
        try:
            requests.delete(f"{API_URL}/{self.tienda_actual['id']}/inventario/{prod['id']}")
        finally:
            self.cargar_productos()

    def on_enter(self):
        self.cargar_productos()

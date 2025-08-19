from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.popup import Popup
from kivy.uix.widget import Widget
from kivy.uix.image import Image
from kivy.properties import ListProperty
import json
import os

class VentanaInventario(Screen):
    productos = ListProperty([])

    def __init__(self, **kwargs):
        super(VentanaInventario, self).__init__(**kwargs)
        self.ruta_tienda = None

        # Layout y fondo
        self.layout = FloatLayout()
        self.add_widget(self.layout)

        fondo = Image(
            source=r'C:\Users\USER\Documents\APP\APP\assets\fondo.png',
            allow_stretch=True,
            keep_ratio=False,
            size_hint=(1, 1),
            pos_hint={'x': 0, 'y': 0}
        )
        self.layout.add_widget(fondo)

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

        # Botones editar, eliminar

        self.layout_principal.add_widget(Widget(size_hint_y=None, height=20))

        # Layout horizontal inferior con dos columnas
        layout_inferior = BoxLayout(size_hint_y=None, height=100, padding=10, spacing=20)

        # Columna izquierda con botón Editar arriba y Volver abajo
        col_izquierda = BoxLayout(orientation='vertical', spacing=10)
        self.boton_editar = Button(text='Editar', size_hint_y=None, height=40)
        self.boton_editar.bind(on_release=self.editar_producto)
        self.boton_editar.disabled = True
        self.boton_volver = Button(text='Volver', size_hint_y=None, height=40)
        self.boton_volver.bind(on_release=self.volver_a_principal)
        col_izquierda.add_widget(self.boton_editar)
        col_izquierda.add_widget(Widget())  # espacio flexible entre botones
        col_izquierda.add_widget(self.boton_volver)

        # Columna derecha con botón Eliminar arriba y Ir a Ventas abajo
        col_derecha = BoxLayout(orientation='vertical', spacing=10)
        self.boton_eliminar = Button(text='Eliminar', size_hint_y=None, height=40)
        self.boton_eliminar.bind(on_release=self.eliminar_producto)
        self.boton_eliminar.disabled = True
        self.boton_ir_a_ventas = Button(text='Ir a Ventas', size_hint_y=None, height=40)
        self.boton_ir_a_ventas.bind(on_release=self.ir_a_ventas)
        col_derecha.add_widget(self.boton_eliminar)
        col_derecha.add_widget(Widget())  # espacio flexible entre botones
        col_derecha.add_widget(self.boton_ir_a_ventas)

        # Widget central para espacio vacío (medio)
        widget_espacio = Widget(size_hint_x=None, width=20)

        # Agregar columnas y espacio al layout inferior
        layout_inferior.add_widget(col_izquierda)
        layout_inferior.add_widget(widget_espacio)
        layout_inferior.add_widget(col_derecha)

        # Agregar layout inferior al layout principal
        self.layout_principal.add_widget(Widget(size_hint_y=None, height=20))  # espacio arriba si quieres
        self.layout_principal.add_widget(layout_inferior)


        self.producto_seleccionado = None

        self.cargar_productos()
        self.actualizar_lista()

    def ir_a_ventas(self, instance):
        self.manager.current = 'venta_inventario'

    def set_ruta_tienda(self, ruta):
        self.ruta_tienda = ruta
        self.cargar_productos()
        self.actualizar_lista()

    def volver_a_principal(self, instance):
        self.manager.current = 'pantalla_principal'

    def cargar_productos(self):
        if not self.ruta_tienda or not os.path.exists(self.ruta_tienda):
            self.productos = []
            return
        with open(self.ruta_tienda, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # FILTRAR productos con piezas > 0
            self.productos = [prod for prod in data.get('inventario', []) if prod.get('piezas', 0) > 0]

    def guardar_productos(self):
        if not self.ruta_tienda:
            return
        # FILTRAR productos con piezas > 0 antes de guardar
        self.productos = [prod for prod in self.productos if prod.get('piezas', 0) > 0]

        if os.path.exists(self.ruta_tienda):
            with open(self.ruta_tienda, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            data = {}

        data['inventario'] = self.productos

        with open(self.ruta_tienda, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def agregar_producto(self, instance):
        nombre = self.input_producto.text.strip()
        precio = self.input_precio.text.strip()
        piezas = self.input_piezas.text.strip()
        if nombre and precio and piezas:
            self.productos.append({"producto": nombre, "precio": precio, "piezas": int(piezas)})
            self.guardar_productos()
            self.input_producto.text = ''
            self.input_precio.text = ''
            self.input_piezas.text = ''
            self.actualizar_lista()

    def actualizar_lista(self):
        # FILTRAR productos con piezas > 0 antes de mostrar
        self.productos = [prod for prod in self.productos if prod.get('piezas', 0) > 0]

        self.grid_productos.clear_widgets()
        for idx, prod in enumerate(self.productos):
            piezas = prod.get('piezas', 0)
            btn = Button(text=f"{prod['producto']} - ${prod['precio']} - {piezas} piezas", size_hint_y=None, height=40)
            btn.bind(on_release=lambda btn, i=idx: self.seleccionar_producto(i))
            self.grid_productos.add_widget(btn)

    def seleccionar_producto(self, index):
        self.producto_seleccionado = index
        self.boton_editar.disabled = False
        self.boton_eliminar.disabled = False

    def editar_producto(self, instance):
        if self.producto_seleccionado is not None:
            prod = self.productos[self.producto_seleccionado]
            self.input_producto.text = prod['producto']
            self.input_precio.text = prod['precio']
            self.productos.pop(self.producto_seleccionado)
            self.guardar_productos()
            self.actualizar_lista()
            self.boton_editar.disabled = True
            self.boton_eliminar.disabled = True
            self.producto_seleccionado = None

    def eliminar_producto(self, instance):
        if self.producto_seleccionado is not None:
            self.productos.pop(self.producto_seleccionado)
            self.guardar_productos()
            self.actualizar_lista()
            self.boton_editar.disabled = True
            self.boton_eliminar.disabled = True
            self.producto_seleccionado = None

    def on_enter(self):
        self.cargar_productos()
        self.actualizar_lista()

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
from kivy.properties import ListProperty
from kivy.properties import StringProperty
from datetime import datetime
import json
import os
from rapidfuzz import process  # pip install rapidfuzz

class VentaInventario(Screen):
    productos = ListProperty([])  # Inventario completo
    nombre_usuario = StringProperty("")


    def __init__(self, **kwargs):
        super(VentaInventario, self).__init__(**kwargs)
        self.ruta_tienda = None
        self.carrito = []
        self.producto_seleccionado = None
        self.boton_seleccionado = None
        self.nombre_usuario = ""

        # Layout base con fondo
        self.layout = FloatLayout()
        self.add_widget(self.layout)

        fondo = Image(
            source=r'C:\Users\USER\Documents\APP\APP\assets\fondo.png',
            allow_stretch=True,
            keep_ratio=False,
            size_hint=(1,1),
            pos_hint={'x':0, 'y':0}
        )
        self.layout.add_widget(fondo)

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

        # Layout horizontal para botones Volver y Finalizar compra al fondo
        layout_botones_final = BoxLayout(size_hint_y=None, height=40, spacing=10)
        self.boton_volver = Button(text="Volver")
        self.boton_volver.bind(on_release=self.volver_a_principal)
        self.boton_finalizar = Button(text="Finalizar compra")
        self.boton_finalizar.bind(on_release=lambda x: self.mostrar_popup_carrito())
        layout_botones_final.add_widget(self.boton_volver)
        layout_botones_final.add_widget(self.boton_finalizar)
        self.layout_principal.add_widget(layout_botones_final)

        # Cargar productos si ruta está seteada
        if self.ruta_tienda:
            self.cargar_productos()
            self.mostrar_resultados(self.productos)

    def set_ruta_tienda(self, ruta):
        self.ruta_tienda = ruta
        self.cargar_productos()
        self.mostrar_resultados(self.productos)

    def set_usuario(self, nombre):
        self.nombre_usuario = nombre

    def cargar_productos(self):
        if not self.ruta_tienda or not os.path.exists(self.ruta_tienda):
            self.productos = []
            return
        with open(self.ruta_tienda, 'r', encoding='utf-8') as f:
            data = json.load(f)
            inventario = data.get('inventario', [])
            # Filtrar productos con piezas > 0
            self.productos = [prod for prod in inventario if prod.get('piezas', 0) > 0]

    def guardar_productos(self):
        if not self.ruta_tienda:
            return
        if os.path.exists(self.ruta_tienda):
            with open(self.ruta_tienda, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            data = {}

        data['inventario'] = self.productos

        with open(self.ruta_tienda, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def buscar(self, instance):
        texto = self.input_busqueda.text.strip()
        if texto:
            productos_filtrados = self.buscar_producto_clave(texto)
            self.mostrar_resultados(productos_filtrados)
        else:
            self.mostrar_resultados(self.productos)

    def buscar_producto_clave(self, texto_busqueda):
        productos_nombres = [prod['producto'] for prod in self.productos]
        resultados = process.extract(texto_busqueda, productos_nombres, limit=10, score_cutoff=60)
        indices = [r[2] for r in resultados]
        productos_filtrados = [self.productos[i] for i in indices]
        return productos_filtrados

    def mostrar_resultados(self, lista_productos):
        self.grid_resultados.clear_widgets()
        # Filtrar aquí también para seguridad
        productos_filtrados = [prod for prod in lista_productos if prod.get('piezas', 0) > 0]
        for idx, prod in enumerate(productos_filtrados):
            piezas = prod.get('piezas', 0)
            btn = Button(text=f"{prod['producto']}  -  ${prod['precio']}  -  {piezas} piezas", size_hint_y=None, height=40)
            btn.bind(on_release=lambda btn, i=idx, lp=productos_filtrados: self.seleccionar_producto(i, lp, btn))
            if self.boton_seleccionado == btn:
                btn.background_color = (0, 0, 1, 1)  # Azul
            else:
                btn.background_color = (1, 1, 1, 1)  # Blanco
            self.grid_resultados.add_widget(btn)

    def eliminar_producto(self, instance):
        if not self.producto_seleccionado:
            self.mostrar_mensaje("No hay ningún producto seleccionado para eliminar.")
            return

        nombre_seleccionado = self.producto_seleccionado.get('producto', None)
        if not nombre_seleccionado:
            self.mostrar_mensaje("Producto seleccionado inválido.")
            return

        # Buscar en el carrito y eliminar el producto seleccionado
        eliminado = False
        for i, item in enumerate(self.carrito):
            if item['producto'] == nombre_seleccionado:
                del self.carrito[i]
                eliminado = True
                break

        if eliminado:
            self.mostrar_mensaje(f"Producto '{nombre_seleccionado}' eliminado del carrito.")
        else:
            self.mostrar_mensaje("El producto seleccionado no está en el carrito.")

    def mostrar_popup(self, titulo, mensaje):
        contenido = BoxLayout(orientation='vertical', padding=10, spacing=10)
        contenido.add_widget(Label(text=mensaje))
        boton_cerrar = Button(text="Cerrar", size_hint_y=None, height=40)
        contenido.add_widget(boton_cerrar)

        popup = Popup(title=titulo, content=contenido,
                      size_hint=(0.5, 0.4))
        boton_cerrar.bind(on_release=popup.dismiss)
        popup.open()



    def seleccionar_producto(self, index, lista_actual, boton):
        self.producto_seleccionado = lista_actual[index]

        if self.boton_seleccionado:
            self.boton_seleccionado.background_color = (1, 1, 1, 1)
        boton.background_color = (0, 0, 1, 1)
        self.boton_seleccionado = boton

    # Actualiza el label con el nombre del producto seleccionado
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

        # Verifica si hay suficientes piezas en inventario
        if piezas > self.producto_seleccionado.get('piezas', 0):
            self.mostrar_mensaje(f"No hay suficientes piezas disponibles. Solo quedan {self.producto_seleccionado.get('piezas', 0)}")
            return

        # Agrega o suma piezas si ya está en carrito
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
        #self.mostrar_popup_carrito()

        if self.boton_seleccionado:
            self.boton_seleccionado.background_color = (1, 1, 1, 1)
            self.boton_seleccionado = None
            self.producto_seleccionado = None
        

    def mostrar_mensaje(self, texto):
        popup = Popup(title="Aviso",
                      content=Label(text=texto),
                      size_hint=(0.6, 0.4))
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
            lbl_sub.bind(size=lbl_sub.setter('text_size'))  # para alinear bien el texto

            grid.add_widget(lbl_prod)
            grid.add_widget(lbl_sub)

        scroll = ScrollView(size_hint=(1, 0.7))
        scroll.add_widget(grid)
        contenido.add_widget(scroll)

        layout_abajo = BoxLayout(size_hint_y=None, height=40, spacing=10)
        btn_cancelar = Button(text="Cancelar")
        btn_total = Button(text=f"Total = ${total:.2f}")
        layout_abajo.add_widget(btn_cancelar)
        layout_abajo.add_widget(btn_total)
        contenido.add_widget(layout_abajo)

        self.popup = Popup(title="Carrito de venta", content=contenido,
                      size_hint=(0.8, 0.8), auto_dismiss=False)

        btn_cancelar.bind(on_release=lambda x: self.popup.dismiss())
        btn_total.bind(on_release=self.confirmar_venta)

        self.popup.open()

    def confirmar_venta(self, instance):
        ruta_carpeta = r"C:\Users\fabiola gomey martin\Documents\APP\data"
        if not os.path.exists(ruta_carpeta):
            os.makedirs(ruta_carpeta)

        ruta_ventas = os.path.join(ruta_carpeta, "ventas.json")

        # Descontar piezas del inventario
        for item_carrito in self.carrito:
            for prod in self.productos:
                if prod['producto'] == item_carrito['producto'] and prod['precio'] == item_carrito['precio']:
                    prod['piezas'] -= item_carrito['cantidad']
                    if prod['piezas'] < 0:
                        prod['piezas'] = 0  # No negativo

        # Guardar inventario actualizado
        self.guardar_productos()

        # Guardar la venta en ventas.json
        venta = {
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "usuario": self.nombre_usuario,
            "productos": self.carrito.copy(),
            "total": sum(float(p['precio']) * int(p['cantidad']) for p in self.carrito),
            "fuera_inventario": False  # Indica que no salió del inventario

        }

        try:
            if os.path.exists(ruta_ventas):
                with open(ruta_ventas, 'r', encoding='utf-8') as f:
                    ventas = json.load(f)
            else:
                ventas = []

            ventas.append(venta)

            with open(ruta_ventas, 'w', encoding='utf-8') as f:
                json.dump(ventas, f, indent=4, ensure_ascii=False)

        except Exception as e:
            self.mostrar_mensaje(f"Error al guardar la venta: {e}")
            return

        # Limpiar carrito y cerrar popup
        self.mostrar_resultados(self.productos)
        self.carrito.clear()
        self.popup.dismiss()
        self.mostrar_mensaje("Venta confirmada con éxito.")

    def on_enter(self):
        self.cargar_productos()
        self.mostrar_resultados(self.productos)

    def volver_a_principal(self, instance):
        self.manager.current = 'pantalla_principal'
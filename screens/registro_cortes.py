from kivy.uix.screenmanager import Screen
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.image import Image
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
import json
import os

class RegistroCortes(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cortes_path = r"C:\Users\fabiola gomey martin\Documents\APP\data\cortes"  # Ruta a tus cortes
        self.root_layout = RelativeLayout()
        self.add_widget(self.root_layout)

        # Fondo igual que otras pantallas
        self.fondo = Image(source=r"C:\Users\USER\Documents\APP\APP\assets\fondo.png",
                           allow_stretch=True, keep_ratio=False)
        self.root_layout.add_widget(self.fondo)

        # Contenedor principal para todo lo que se muestra (lista o detalle)
        self.main_layout = BoxLayout(orientation="vertical", padding=10, spacing=5)
        self.root_layout.add_widget(self.main_layout)

        # Botón para volver, abajo a la izquierda
        self.btn_volver = Button(text="↩ Volver", size_hint=(0.15, 0.08), pos_hint={"x": 0, "y": 0})
        self.btn_volver.bind(on_release=self.on_volver)
        self.root_layout.add_widget(self.btn_volver)

        # Estado: "lista" o "detalle"
        self.estado = "lista"
        self.corte_seleccionado = None

    def on_pre_enter(self):
        # Siempre que entremos, mostramos la lista de cortes
        self.mostrar_lista_cortes()

    def mostrar_lista_cortes(self, *args):
        self.estado = "lista"
        self.corte_seleccionado = None
        self.main_layout.clear_widgets()
        self.btn_volver.text = "↩ Volver a Principal"
        self.btn_volver.unbind(on_release=self.on_volver)
        self.btn_volver.bind(on_release=self.volver_a_principal)

        label = Label(text="Registros de Cortes", size_hint_y=None, height=40, font_size=20)
        self.main_layout.add_widget(label)

        scroll = ScrollView(size_hint=(1, 1))
        grid = GridLayout(cols=1, spacing=5, size_hint_y=None)
        grid.bind(minimum_height=grid.setter("height"))
        scroll.add_widget(grid)

        carpetas = [
            r"C:\Users\fabiola gomey martin\Documents\APP\data\cortes",
            r"C:\Users\fabiola gomey martin\Documents\APP\data\cortes_usados"
        ]

        archivos = []
        for carpeta in carpetas:
            if not os.path.exists(carpeta):
                os.makedirs(carpeta)
            archivos += [(carpeta, f) for f in os.listdir(carpeta) if f.endswith(".json")]

        archivos = sorted(archivos, key=lambda x: x[1], reverse=True)

        if not archivos:
            grid.add_widget(Label(text="No hay cortes guardados.", size_hint_y=None, height=40))
        else:
            for carpeta, archivo in archivos:
                btn = Button(text=archivo, size_hint_y=None, height=40)
                btn.bind(on_release=lambda inst, c=carpeta, a=archivo: self.mostrar_detalle_corte(c, a))
                grid.add_widget(btn)

        self.main_layout.add_widget(scroll)

    def mostrar_detalle_corte(self, carpeta, archivo):
        self.estado = "detalle"
        self.corte_seleccionado = (carpeta, archivo)
        self.main_layout.clear_widgets()
        self.btn_volver.text = "↩ Volver a Lista"
        self.btn_volver.unbind(on_release=self.volver_a_principal)
        self.btn_volver.bind(on_release=self.mostrar_lista_cortes)

        ruta_archivo = os.path.join(carpeta, archivo)
        try:
            with open(ruta_archivo, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            self.main_layout.add_widget(Label(text=f"Error al cargar el archivo:\n{str(e)}"))
            return

        # Mostrar resumen del corte
        resumen_layout = BoxLayout(orientation="vertical", size_hint_y=None)
        resumen_layout.bind(minimum_height=resumen_layout.setter("height"))

        resumen_layout.add_widget(Label(text=f"Corte: {archivo}", size_hint_y=None, height=30, bold=True, font_size=18))
        resumen_layout.add_widget(Label(text=f"Fecha: {data.get('fecha', '')}", size_hint_y=None, height=25))
        resumen_layout.add_widget(Label(text=f"Hora: {data.get('hora', '')}", size_hint_y=None, height=25))
        resumen_layout.add_widget(Label(text=f"Total: ${data.get('total', '0')}", size_hint_y=None, height=25))
        resumen_layout.add_widget(Label(text=f"Usuario: {data.get('usuario_que_corto', '')}", size_hint_y=None, height=25))

        # Ventas detalle (si existe)
        ventas = data.get("ventas", [])
        resumen_layout.add_widget(Label(text="Ventas del Corte:", size_hint_y=None, height=30, bold=True, font_size=16))

        # Scroll de ventas
        scroll_ventas = ScrollView(size_hint=(1, 1))
        grid_ventas = GridLayout(cols=5, spacing=5, size_hint_y=None)
        grid_ventas.bind(minimum_height=grid_ventas.setter("height"))
        scroll_ventas.add_widget(grid_ventas)

        # Headers
        headers = ["Empleado", "Producto", "Tipo de Venta", "Total $", "Hora"]
        for h in headers:
            grid_ventas.add_widget(Label(text=h, size_hint_y=None, height=30, bold=True))

        for venta in ventas:
            usuario = venta.get("usuario", "-")
            productos = venta.get("productos", [])
            tipo_venta = "Fuera de Inventario" if venta.get("fuera_inventario", False) else "Dentro de Inventario"
            fecha_hora = venta.get("fecha", "")
            hora = ""
            if fecha_hora:
                try:
                    hora = fecha_hora.split(" ")[1]
                except:
                    hora = ""

            for prod in productos:
                grid_ventas.add_widget(Label(text=usuario, size_hint_y=None, height=30))
                cantidad = prod.get("cantidad", 1)
                nombre_producto = prod.get("producto", "-")
                grid_ventas.add_widget(Label(text=f"{cantidad} x {nombre_producto}", size_hint_y=None, height=30))
                grid_ventas.add_widget(Label(text=tipo_venta, size_hint_y=None, height=30))
                precio = prod.get("precio", 0)
                grid_ventas.add_widget(Label(text=f"${precio}", size_hint_y=None, height=30))
                grid_ventas.add_widget(Label(text=hora, size_hint_y=None, height=30))

        resumen_layout.add_widget(scroll_ventas)
        self.main_layout.add_widget(resumen_layout)

    def on_volver(self, instance):
        # En modo lista, volver a pantalla principal
        self.manager.current = "pantalla_principal"

    def volver_a_principal(self, instance):
        self.manager.current = "pantalla_principal"

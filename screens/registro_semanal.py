from kivy.uix.screenmanager import Screen
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.image import Image
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
import json
import os

class RegistroSemanal(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cortes_semanales_path = r"C:\Users\fabiola gomey martin\Documents\APP\data\cortes_semanales"
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

        self.estado = "lista"
        self.corte_seleccionado = None

    def on_pre_enter(self):
        self.mostrar_lista_cortes()

    def mostrar_lista_cortes(self, *args):
        self.estado = "lista"
        self.corte_seleccionado = None
        self.main_layout.clear_widgets()
        self.btn_volver.text = "↩ Volver a Principal"
        self.btn_volver.unbind(on_release=self.on_volver)
        self.btn_volver.bind(on_release=self.volver_a_principal)

        label = Label(text="Registros de Cortes Semanales", size_hint_y=None, height=40, font_size=20)
        self.main_layout.add_widget(label)

        scroll = ScrollView(size_hint=(1, 1))
        grid = GridLayout(cols=1, spacing=5, size_hint_y=None)
        grid.bind(minimum_height=grid.setter("height"))
        scroll.add_widget(grid)

        carpeta = self.cortes_semanales_path
        if not os.path.exists(carpeta):
            os.makedirs(carpeta)

        archivos = sorted([f for f in os.listdir(carpeta) if f.endswith(".json")], reverse=True)

        if not archivos:
            grid.add_widget(Label(text="No hay cortes semanales guardados.", size_hint_y=None, height=40))
        else:
            for archivo in archivos:
                btn = Button(text=archivo, size_hint_y=None, height=40)
                btn.bind(on_release=lambda inst, a=archivo: self.mostrar_detalle_corte(a))
                grid.add_widget(btn)

        self.main_layout.add_widget(scroll)

    def mostrar_detalle_corte(self, archivo):
        self.estado = "detalle"
        self.corte_seleccionado = archivo
        self.main_layout.clear_widgets()
        self.btn_volver.text = "↩ Volver a Lista"
        self.btn_volver.unbind(on_release=self.volver_a_principal)
        self.btn_volver.bind(on_release=self.mostrar_lista_cortes)

        ruta_archivo = os.path.join(self.cortes_semanales_path, archivo)
        try:
            with open(ruta_archivo, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            self.main_layout.add_widget(Label(text=f"Error al cargar el archivo:\n{str(e)}"))
            return

        resumen_layout = BoxLayout(orientation="vertical", size_hint_y=None)
        resumen_layout.bind(minimum_height=resumen_layout.setter("height"))

        resumen_layout.add_widget(Label(text=f"Corte Semanal: {archivo}", size_hint_y=None, height=30, bold=True, font_size=18))
        resumen_layout.add_widget(Label(text=f"Fecha Cierre: {data.get('fecha_cierre', '')}", size_hint_y=None, height=25))
        resumen_layout.add_widget(Label(text=f"Número de Cortes: {data.get('num_cortes', '')}", size_hint_y=None, height=25))
        resumen_layout.add_widget(Label(text=f"Total Ventas Semana: ${data.get('total_ventas_semana', 0):,.2f}", size_hint_y=None, height=25))
        resumen_layout.add_widget(Label(text=f"Total Sueldos: ${data.get('total_sueldos', 0):,.2f}", size_hint_y=None, height=25))
        resumen_layout.add_widget(Label(text=f"Total Préstamos Pagados: ${data.get('total_prestamos_pagados', 0):,.2f}", size_hint_y=None, height=25))
        resumen_layout.add_widget(Label(text=f"Total Ganancias: ${data.get('total_ganancias', 0):,.2f}", size_hint_y=None, height=25))

        # Mostrar pagos de préstamos si existen
        pagos_prestamos = data.get("pagos_prestamos", {})
        if pagos_prestamos:
            resumen_layout.add_widget(Label(text="Pagos de Préstamos:", size_hint_y=None, height=30, bold=True, font_size=16))

            scroll_prestamos = ScrollView(size_hint=(1, 1))
            grid_prestamos = GridLayout(cols=2, spacing=5, size_hint_y=None)
            grid_prestamos.bind(minimum_height=grid_prestamos.setter("height"))
            scroll_prestamos.add_widget(grid_prestamos)

            # Agregar encabezados
            grid_prestamos.add_widget(Label(text="Empleado", size_hint_y=None, height=30, bold=True))
            grid_prestamos.add_widget(Label(text="Monto Pagado", size_hint_y=None, height=30, bold=True))

            for empleado, monto in pagos_prestamos.items():
                grid_prestamos.add_widget(Label(text=empleado, size_hint_y=None, height=30))
                grid_prestamos.add_widget(Label(text=f"${monto:,.2f}", size_hint_y=None, height=30))

            resumen_layout.add_widget(scroll_prestamos)

        self.main_layout.add_widget(resumen_layout)

    def on_volver(self, instance):
        self.manager.current = "pantalla_principal"

    def volver_a_principal(self, instance):
        self.manager.current = "pantalla_principal"

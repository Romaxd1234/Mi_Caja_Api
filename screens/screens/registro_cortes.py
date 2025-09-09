from kivy.uix.screenmanager import Screen
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.graphics import Rectangle
from kivy.resources import resource_add_path
from kivy.metrics import dp, sp
import os
import requests

API_BASE = "https://mi-caja-api.onrender.com/tiendas"

class RegistroCortes(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.root_layout = RelativeLayout()
        self.add_widget(self.root_layout)

        # Fondo con canvas
        ruta_assets = os.path.join(os.path.dirname(__file__), "assets")
        resource_add_path(ruta_assets)

        with self.root_layout.canvas.before:
            self.fondo_rect = Rectangle(source="fondo.png", pos=self.root_layout.pos, size=self.root_layout.size)
        self.root_layout.bind(size=self._update_rect, pos=self._update_rect)

        # Contenedor principal
        self.main_layout = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(5))
        self.root_layout.add_widget(self.main_layout)

        # Botón para volver
        self.btn_volver = Button(
            text="↩ Volver",
            size_hint=(0.2, 0.08),
            pos_hint={"x": 0, "y": 0},
            font_size=sp(14)
        )
        self.btn_volver.bind(on_release=self.on_volver)
        self.root_layout.add_widget(self.btn_volver)

        # Variables
        self.estado = "lista"
        self.corte_seleccionado = None
        self.tienda_id = None

    def _update_rect(self, *args):
        self.fondo_rect.pos = self.root_layout.pos
        self.fondo_rect.size = self.root_layout.size

    # ------------------- Configuración -------------------
    def set_tienda_id(self, tienda_id):
        self.tienda_id = tienda_id

    # ------------------- Pre-enter -------------------
    def on_pre_enter(self):
        self.main_layout.clear_widgets()
        if not self.tienda_id:
            self.main_layout.add_widget(
                Label(text="No se ha seleccionado una tienda", font_size=sp(16), size_hint_y=None, height=dp(40))
            )
            return
        self.mostrar_lista_cortes()

    # ------------------- Obtener cortes -------------------
    def obtener_cortes_desde_api(self):
        url = f"{API_BASE}/{self.tienda_id}"
        try:
            resp = requests.get(url)
            resp.raise_for_status()
            tienda = resp.json()

            cortes_diarios = []

            for corte in tienda.get("cortes", {}).get("diarios", []):
                cortes_diarios.append(corte)

            for bloque in tienda.get("cortes", {}).get("semanales", []):
                for corte_diario in bloque.get("cortes_diarios", []):
                    cortes_diarios.append(corte_diario)

            return cortes_diarios

        except Exception as e:
            print("Error al obtener cortes:", e)
        return []

    # ------------------- Mostrar lista de cortes -------------------
    def mostrar_lista_cortes(self, *args):
        self.estado = "lista"
        self.corte_seleccionado = None
        self.main_layout.clear_widgets()
        self.btn_volver.text = "Volver"
        self.btn_volver.unbind(on_release=self.on_volver)
        self.btn_volver.bind(on_release=self.volver_a_principal)

        label = Label(text="Registros de Cortes", size_hint_y=None, height=dp(40), font_size=sp(18))
        self.main_layout.add_widget(label)

        scroll = ScrollView(size_hint=(1, 1))
        grid = GridLayout(cols=1, spacing=dp(5), size_hint_y=None)
        grid.bind(minimum_height=grid.setter("height"))
        scroll.add_widget(grid)

        cortes = self.obtener_cortes_desde_api()

        if not cortes:
            grid.add_widget(Label(text="No hay cortes guardados.", size_hint_y=None, height=dp(40)))
        else:
            for corte in sorted(cortes, key=lambda x: x.get("fecha", ""), reverse=True):
                btn = Button(
                    text=f"Corte {corte.get('id', '-') } - {corte.get('fecha', '-')}",
                    size_hint_y=None,
                    height=dp(40),
                    font_size=sp(14)
                )
                btn.bind(on_release=lambda inst, c=corte: self.mostrar_detalle_corte_api(c))
                grid.add_widget(btn)

        self.main_layout.add_widget(scroll)

    # ------------------- Mostrar detalle del corte -------------------
    def mostrar_detalle_corte_api(self, corte):
        self.estado = "detalle"
        self.corte_seleccionado = corte
        self.main_layout.clear_widgets()
        self.btn_volver.text = "Volver"
        self.btn_volver.unbind(on_release=self.volver_a_principal)
        self.btn_volver.bind(on_release=self.mostrar_lista_cortes)

        resumen_layout = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(5))
        resumen_layout.bind(minimum_height=resumen_layout.setter("height"))

        resumen_layout.add_widget(Label(text=f"Corte {corte.get('id', '-')}", size_hint_y=None, height=dp(30), font_size=sp(16)))
        resumen_layout.add_widget(Label(text=f"Fecha: {corte.get('fecha', '-')}", size_hint_y=None, height=dp(25), font_size=sp(14)))
        resumen_layout.add_widget(Label(text=f"Hora: {corte.get('hora', '-')}", size_hint_y=None, height=dp(25), font_size=sp(14)))
        resumen_layout.add_widget(Label(text=f"Total: ${corte.get('total', 0)}", size_hint_y=None, height=dp(25), font_size=sp(14)))
        resumen_layout.add_widget(Label(text=f"Usuario: {corte.get('usuario_que_corto', '-')}", size_hint_y=None, height=dp(25), font_size=sp(14)))

        ventas = corte.get("ventas", [])
        resumen_layout.add_widget(Label(text="Ventas del Corte:", size_hint_y=None, height=dp(30), font_size=sp(16)))

        scroll_ventas = ScrollView(size_hint=(1, 1))
        grid_ventas = GridLayout(cols=5, spacing=dp(5), size_hint_y=None)
        grid_ventas.bind(minimum_height=grid_ventas.setter("height"))
        scroll_ventas.add_widget(grid_ventas)

        headers = ["Empleado", "Producto", "Tipo de Venta", "Total $", "Hora"]
        for h in headers:
            grid_ventas.add_widget(Label(text=h, size_hint_y=None, height=dp(30), font_size=sp(14)))

        for venta in ventas:
            usuario = venta.get("usuario", "-")
            productos = venta.get("productos", [])
            tipo_venta = "Fuera de Inventario" if venta.get("fuera_inventario", False) else "Dentro de Inventario"
            fecha_hora = venta.get("fecha", "")
            hora = fecha_hora.split(" ")[1] if " " in fecha_hora else ""

            for prod in productos:
                grid_ventas.add_widget(Label(text=usuario, size_hint_y=None, height=dp(30), font_size=sp(14)))
                cantidad = prod.get("cantidad", 1)
                nombre_producto = prod.get("producto", "-")
                grid_ventas.add_widget(Label(text=f"{cantidad} x {nombre_producto}", size_hint_y=None, height=dp(30), font_size=sp(14)))
                grid_ventas.add_widget(Label(text=tipo_venta, size_hint_y=None, height=dp(30), font_size=sp(14)))
                precio = prod.get("precio", 0)
                grid_ventas.add_widget(Label(text=f"${precio}", size_hint_y=None, height=dp(30), font_size=sp(14)))
                grid_ventas.add_widget(Label(text=hora, size_hint_y=None, height=dp(30), font_size=sp(14)))

        resumen_layout.add_widget(scroll_ventas)
        self.main_layout.add_widget(resumen_layout)

    # ------------------- Navegación -------------------
    def on_volver(self, instance):
        self.manager.current = "pantalla_principal"

    def volver_a_principal(self, instance):
        self.manager.current = "pantalla_principal"

from kivy.uix.screenmanager import Screen
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.graphics import Rectangle
from kivy.resources import resource_add_path
from kivy.metrics import dp, sp
import os
import requests

API_BASE = "https://mi-caja-api.onrender.com/tiendas"

class RegistroSemanal(Screen):
    def __init__(self, tienda_id=None, **kwargs):
        super().__init__(**kwargs)
        self.tienda_id = tienda_id
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
            size_hint=(0.15, 0.08),
            pos_hint={"x": 0, "y": 0}
        )
        self.btn_volver.bind(on_release=self.on_volver)
        self.root_layout.add_widget(self.btn_volver)

        # Variables de estado
        self.estado = "lista"
        self.corte_seleccionado = None

    def _update_rect(self, *args):
        self.fondo_rect.pos = self.root_layout.pos
        self.fondo_rect.size = self.root_layout.size

    def set_tienda_id(self, tienda_id, usuario=None):
        self.tienda_id = tienda_id
        if usuario:
            self.usuario = usuario

    def on_pre_enter(self):
        self.mostrar_lista_cortes()

    # ---------------------
    # FUNCIONES API
    # ---------------------
    def obtener_cortes_semanales(self):
        try:
            resp = requests.get(f"{API_BASE}/{self.tienda_id}/cortes/semanales")
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"Error al obtener cortes semanales: {e}")
            return []

    # ---------------------
    # LISTA DE CORTES
    # ---------------------
    def mostrar_lista_cortes(self, *args):
        self.estado = "lista"
        self.corte_seleccionado = None
        self.main_layout.clear_widgets()
        self.btn_volver.text = "Volver"
        self.btn_volver.unbind(on_release=self.on_volver)
        self.btn_volver.bind(on_release=self.volver_a_principal)

        label = Label(text="Registros de Cortes Semanales", size_hint_y=None, height=dp(40), font_size=sp(20))
        self.main_layout.add_widget(label)

        scroll = ScrollView(size_hint=(1, 1))
        grid = GridLayout(cols=1, spacing=dp(5), size_hint_y=None)
        grid.bind(minimum_height=grid.setter("height"))
        scroll.add_widget(grid)

        cortes_semanales = self.obtener_cortes_semanales()
        if not cortes_semanales:
            grid.add_widget(Label(text="No hay cortes semanales guardados.", size_hint_y=None, height=dp(40)))
        else:
            for corte in sorted(cortes_semanales, key=lambda x: x.get("id",0), reverse=True):
                texto = f"Corte {corte['id']} - {corte.get('fecha_cierre', '')}"
                btn = Button(text=texto, size_hint_y=None, height=dp(50))
                btn.bind(on_release=lambda inst, c=corte: self.mostrar_detalle_corte(c))
                grid.add_widget(btn)

        self.main_layout.add_widget(scroll)

    # ---------------------
    # DETALLE DE CORTES
    # ---------------------
    def mostrar_detalle_corte(self, corte):
        self.estado = "detalle"
        self.corte_seleccionado = corte
        self.main_layout.clear_widgets()
        self.btn_volver.text = "Volver"
        self.btn_volver.unbind(on_release=self.volver_a_principal)
        self.btn_volver.bind(on_release=self.mostrar_lista_cortes)

        resumen_layout = BoxLayout(orientation="vertical", size_hint_y=None, padding=dp(5), spacing=dp(5))
        resumen_layout.bind(minimum_height=resumen_layout.setter("height"))

        # ID del corte
        resumen_layout.add_widget(Label(text=f"Corte Semanal: {corte['id']}", size_hint_y=None, height=dp(40), font_size=sp(18), bold=True))

        # Fecha de cierre
        resumen_layout.add_widget(Label(text=f"Fecha de Cierre: {corte.get('fecha','')}", size_hint_y=None, height=dp(30), font_size=sp(16)))

        # Usuario que hizo el corte: tomamos del primer corte diario
        cortes_diarios = corte.get("cortes_diarios", [])
        usuario = cortes_diarios[0].get("usuario_que_corto","") if cortes_diarios else ""
        resumen_layout.add_widget(Label(text=f"Usuario que cerró: {usuario}", size_hint_y=None, height=dp(30), font_size=sp(16)))

        # Total ventas semana
        total_ventas_semana = sum(d.get("total",0) for d in cortes_diarios)
        resumen_layout.add_widget(Label(text=f"Total Ventas Semana: ${total_ventas_semana:,.2f}", size_hint_y=None, height=dp(30), font_size=sp(16)))

        self.main_layout.add_widget(resumen_layout)

    # ---------------------
    # BOTONES VOLVER
    # ---------------------
    def on_volver(self, instance):
        self.manager.current = "pantalla_principal"

    def volver_a_principal(self, instance):
        self.manager.current = "pantalla_principal"

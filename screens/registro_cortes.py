from kivy.uix.screenmanager import Screen
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.image import Image
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
import requests

API_BASE = "https://mi-caja-api.onrender.com/tiendas"  # Asegúrate que esté bien

class RegistroCortes(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.root_layout = RelativeLayout()
        self.add_widget(self.root_layout)

        # Fondo
        self.fondo = Image(
            source=r"C:\Users\USER\Documents\APP\APP\assets\fondo.png",
            allow_stretch=True, keep_ratio=False
        )
        self.root_layout.add_widget(self.fondo)

        # Contenedor principal
        self.main_layout = BoxLayout(orientation="vertical", padding=10, spacing=5)
        self.root_layout.add_widget(self.main_layout)

        # Botón para volver
        self.btn_volver = Button(
            text="↩ Volver", size_hint=(0.15, 0.08), pos_hint={"x": 0, "y": 0}
        )
        self.btn_volver.bind(on_release=self.on_volver)
        self.root_layout.add_widget(self.btn_volver)

        self.estado = "lista"
        self.corte_seleccionado = None
        self.tienda_id = None

    # ------------------- Configuración -------------------
    def set_tienda_id(self, tienda_id):
        self.tienda_id = tienda_id

    # ------------------- Pre-enter -------------------
    def on_pre_enter(self):
        if not self.tienda_id:
            self.main_layout.clear_widgets()
            self.main_layout.add_widget(
                Label(text="No se ha seleccionado una tienda", font_size=20, size_hint_y=None, height=40)
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

            # Extraer todos los cortes diarios de todos los bloques
            cortes_diarios = []
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
        self.btn_volver.text = "↩ Volver a Principal"
        self.btn_volver.unbind(on_release=self.on_volver)
        self.btn_volver.bind(on_release=self.volver_a_principal)

        label = Label(text="Registros de Cortes", size_hint_y=None, height=40, font_size=20)
        self.main_layout.add_widget(label)

        scroll = ScrollView(size_hint=(1, 1))
        grid = GridLayout(cols=1, spacing=5, size_hint_y=None)
        grid.bind(minimum_height=grid.setter("height"))
        scroll.add_widget(grid)

        cortes = self.obtener_cortes_desde_api()

        if not cortes:
            grid.add_widget(Label(text="No hay cortes guardados.", size_hint_y=None, height=40))
        else:
            for corte in sorted(cortes, key=lambda x: x.get("fecha", ""), reverse=True):
                btn = Button(
                    text=f"Corte {corte.get('id', '-') } - {corte.get('fecha', '-')}",
                    size_hint_y=None, height=40
                )
                btn.bind(on_release=lambda inst, c=corte: self.mostrar_detalle_corte_api(c))
                grid.add_widget(btn)

        self.main_layout.add_widget(scroll)

    # ------------------- Mostrar detalle del corte -------------------
    def mostrar_detalle_corte_api(self, corte):
        self.estado = "detalle"
        self.corte_seleccionado = corte
        self.main_layout.clear_widgets()
        self.btn_volver.text = "↩ Volver a Lista"
        self.btn_volver.unbind(on_release=self.volver_a_principal)
        self.btn_volver.bind(on_release=self.mostrar_lista_cortes)

        resumen_layout = BoxLayout(orientation="vertical", size_hint_y=None)
        resumen_layout.bind(minimum_height=resumen_layout.setter("height"))

        resumen_layout.add_widget(Label(text=f"Corte {corte.get('id', '-')}", size_hint_y=None, height=30, font_size=18))
        resumen_layout.add_widget(Label(text=f"Fecha: {corte.get('fecha', '-')}", size_hint_y=None, height=25))
        resumen_layout.add_widget(Label(text=f"Hora: {corte.get('hora', '-')}", size_hint_y=None, height=25))
        resumen_layout.add_widget(Label(text=f"Total: ${corte.get('total', 0)}", size_hint_y=None, height=25))
        resumen_layout.add_widget(Label(text=f"Usuario: {corte.get('usuario_que_corto', '-')}", size_hint_y=None, height=25))

        ventas = corte.get("ventas", [])
        resumen_layout.add_widget(Label(text="Ventas del Corte:", size_hint_y=None, height=30, font_size=16))

        scroll_ventas = ScrollView(size_hint=(1, 1))
        grid_ventas = GridLayout(cols=5, spacing=5, size_hint_y=None)
        grid_ventas.bind(minimum_height=grid_ventas.setter("height"))
        scroll_ventas.add_widget(grid_ventas)

        headers = ["Empleado", "Producto", "Tipo de Venta", "Total $", "Hora"]
        for h in headers:
            grid_ventas.add_widget(Label(text=h, size_hint_y=None, height=30))

        for venta in ventas:
            usuario = venta.get("usuario", "-")
            productos = venta.get("productos", [])
            tipo_venta = "Fuera de Inventario" if venta.get("fuera_inventario", False) else "Dentro de Inventario"
            fecha_hora = venta.get("fecha", "")
            hora = fecha_hora.split(" ")[1] if " " in fecha_hora else ""

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

    # ------------------- Navegación -------------------
    def on_volver(self, instance):
        self.manager.current = "pantalla_principal"

    def volver_a_principal(self, instance):
        self.manager.current = "pantalla_principal"

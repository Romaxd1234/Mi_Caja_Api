from kivy.uix.image import Image
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import Screen
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.graphics import Rectangle
from kivy.resources import resource_add_path
import os
import requests
from datetime import datetime

API_URL = "https://mi-caja-api.onrender.com/tiendas"

class SeleccionRolScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        ruta_assets = os.path.join(os.path.dirname(__file__), "assets")
        resource_add_path(ruta_assets)

        # Fondo con canvas
        with self.canvas.before:
            self.fondo_rect = Rectangle(source="fondo.png", pos=self.pos, size=self.size)
        self.bind(size=self._update_rect, pos=self._update_rect)

        # Layout vertical para nombre y botones
        self.layout = BoxLayout(
            orientation='vertical',
            size_hint=(0.5, 0.5),
            spacing=20,
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )

        self.nombre_label = Label(
            text="Cargando tienda...",
            font_size=32,
            bold=True,
            color=(1, 1, 1, 1),
            size_hint=(1, None),
            height=50
        )

        self.btn_empleado = Button(text="Empleado", size_hint=(1, None), height=50)
        self.btn_patron = Button(text="Patrón", size_hint=(1, None), height=50)

        self.layout.add_widget(self.nombre_label)
        self.layout.add_widget(self.btn_empleado)
        self.layout.add_widget(self.btn_patron)
        self.add_widget(self.layout)

        # Variables
        self.tienda_actual_id = None
        self.tienda_actual = None

        # Enlazar botones
        self.btn_patron.bind(on_press=self.ir_pantalla_patron)
        # Botón empleado se enlaza después de cargar la tienda

    def _update_rect(self, *args):
        self.fondo_rect.pos = self.pos
        self.fondo_rect.size = self.size

    def set_tienda_actual(self, tienda_id):
        """Establece la tienda actual por ID"""
        self.tienda_actual_id = tienda_id

    def on_pre_enter(self, *args):
        """Muestra el nombre de la tienda y enlaza botón Empleado"""
        if not self.tienda_actual_id:
            self.nombre_label.text = "[b]No se ha seleccionado ninguna tienda[/b]"
            self.nombre_label.markup = True
            return

        try:
            response = requests.get(f"{API_URL}/{self.tienda_actual_id}")
            response.raise_for_status()
            self.tienda_actual = response.json()
            nombre_tienda = self.tienda_actual.get("nombre", "Tienda sin nombre")
            self.nombre_label.text = f"[b]Tienda: {nombre_tienda}[/b]"
            self.nombre_label.markup = True

            # Enlazar botón Empleado con la tienda completa
            self.btn_empleado.unbind(on_press=None)
            self.btn_empleado.bind(
                on_press=lambda btn: self.ir_pantalla_empleado(self.tienda_actual)
            )

        except Exception as e:
            self.nombre_label.text = f"[b]Error de conexión: {e}[/b]"
            self.nombre_label.markup = True

    def ir_pantalla_patron(self, instance):
        """Ir a la pantalla del patrón según los datos obtenidos de la API"""
        self.nombre_label.text = "[b]Botón Patrón presionado[/b]"
        self.nombre_label.markup = True

        try:
            response = requests.get(f"{API_URL}/{self.tienda_actual_id}/patron/")
            response.raise_for_status()
            patron = response.json()
        except requests.RequestException as e:
            print(f"Error al obtener patrón desde API: {e}")
            self.nombre_label.text = "[b]Error de conexión al obtener patrón[/b]"
            self.nombre_label.markup = True
            return

        pantalla_patron = self.manager.get_screen("pantalla_patron")
        pantalla_login = self.manager.get_screen("login_patron")

        if not patron or not patron.get("nombre") or not patron.get("password"):
            pantalla_patron.set_datos_patron_api(tienda_id=self.tienda_actual_id, patron=None)
            self.manager.current = "pantalla_patron"
        else:
            pantalla_login.set_datos_patron_api(tienda_id=self.tienda_actual_id, patron=patron)
            self.manager.current = "login_patron"

    def ir_pantalla_empleado(self, tienda):
        try:
            pantalla_empleado = self.manager.get_screen("login_empleado")
            pantalla_empleado.set_datos_tienda_api(tienda)  # Cargará empleados desde API
            self.manager.current = "login_empleado"
        except Exception as e:
            print("Error al abrir LoginEmpleadoScreen:", e)

    def esta_en_horario_login(self):
        """Determina si es horario permitido para login nocturno"""
        ahora = datetime.now()
        hora = ahora.hour
        return hora >= 21 or hora < 7

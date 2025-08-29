from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.resources import resource_add_path
from kivy.uix.popup import Popup
from kivy.graphics import Rectangle, Color
from kivy.metrics import dp, sp
import requests
import os
from datetime import datetime

class LoginPatronScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Ruta de assets
        ruta_assets = os.path.join(os.path.dirname(__file__), "assets")
        resource_add_path(ruta_assets)

        # Fondo con canvas
        with self.canvas.before:
            Color(1, 1, 1, 1)  # Fondo blanco si no carga la imagen
            self.fondo_rect = Rectangle(source="fondo.png", pos=self.pos, size=self.size)
        self.bind(size=self._update_rect, pos=self._update_rect)

        # Layout principal
        self.layout = BoxLayout(
            orientation='vertical',
            spacing=dp(15),
            size_hint=(0.85, 0.55),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            padding=[dp(20), dp(20), dp(20), dp(20)]
        )

        # Label saludo
        self.label = Label(
            text="Hola, patrón",
            font_size=sp(26),
            color=(0.1, 0.1, 0.1, 1),
            halign="center",
            valign="middle"
        )
        self.label.bind(size=self.label.setter('text_size'))

        # Campo contraseña
        self.input_contrasena = TextInput(
            hint_text="Contraseña",
            multiline=False,
            password=True,
            font_size=sp(16),
            size_hint=(1, None),
            height=dp(45),
            padding=[dp(10), dp(10)],
            background_color=(0.95, 0.95, 0.95, 1),
            foreground_color=(0,0,0,1)
        )

        # Botones
        self.boton_ingresar = Button(
            text="Ingresar",
            size_hint=(1, None),
            height=dp(45),
            font_size=sp(16),
            background_color=(0.2, 0.6, 1, 1),
            color=(1,1,1,1)
        )
        self.boton_regresar = Button(
            text="Regresar",
            size_hint=(1, None),
            height=dp(45),
            font_size=sp(14),
            background_color=(0.7, 0.7, 0.7, 1),
            color=(0,0,0,1)
        )

        # Bindings
        self.boton_ingresar.bind(on_release=self.verificar_patron)
        self.boton_regresar.bind(on_release=self.regresar)

        # Añadir widgets
        self.layout.add_widget(self.label)
        self.layout.add_widget(self.input_contrasena)
        self.layout.add_widget(self.boton_ingresar)
        self.layout.add_widget(self.boton_regresar)

        self.add_widget(self.layout)

        # Variables
        self.nombre_patron = ""
        self.tienda_id = None

    def _update_rect(self, *args):
        self.fondo_rect.pos = self.pos
        self.fondo_rect.size = self.size

    def set_datos_patron_api(self, tienda_id, patron=None):
        self.tienda_id = tienda_id

        if patron:
            self.nombre_patron = patron.get("nombre", "Patrón")
            self.label.text = f"Hola, {self.nombre_patron}"
        else:
            try:
                response = requests.get(f"https://mi-caja-api.onrender.com/tiendas/{tienda_id}/patron/")
                response.raise_for_status()
                patron_api = response.json()
                self.nombre_patron = patron_api.get("nombre", "Patrón")
                self.label.text = f"Hola, {self.nombre_patron}"
            except requests.RequestException:
                self.label.text = "Hola, patrón"

    def verificar_patron(self, instance):
        contrasena_ingresada = self.input_contrasena.text.strip()

        if not self.tienda_id:
            self.mostrar_popup("Error", "No se encontró la tienda actual.")
            return

        try:
            response = requests.get(f"https://mi-caja-api.onrender.com/tiendas/{self.tienda_id}/patron/")
            response.raise_for_status()
            patron = response.json()
        except requests.RequestException as e:
            self.mostrar_popup("Error", f"No se pudo conectar con la API: {e}")
            return

        if not patron or not patron.get("password"):
            self.mostrar_popup("Error", "No hay patrón registrado en esta tienda.")
            return

        contrasena_guardada = patron.get("password")
        self.nombre_patron = patron.get("nombre", "Patrón")

        if contrasena_ingresada == contrasena_guardada:
            if self.esta_en_horario_login():
                print("Login válido y en horario nocturno.")  # Depuración

            self.mostrar_popup("Éxito", f"Bienvenido, {self.nombre_patron}.")

            pantalla_principal = self.manager.get_screen("pantalla_principal")
            pantalla_principal.configurar_sesion(
                origen="patron", nombre=self.nombre_patron, tienda_id=self.tienda_id
            )
            self.manager.current = "pantalla_principal"

            self.input_contrasena.text = ""
        else:
            self.mostrar_popup("Error", "Contraseña incorrecta.")

    def regresar(self, instance):
        self.manager.current = "seleccion_rol"

    def mostrar_popup(self, titulo, mensaje):
        contenido = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))
        contenido.add_widget(Label(text=mensaje, font_size=sp(16), halign='center', valign='middle'))
        cerrar = Button(text="Cerrar", size_hint=(1, None), height=dp(45), background_color=(0.2,0.6,1,1), color=(1,1,1,1))
        contenido.add_widget(cerrar)
        popup = Popup(title=titulo, content=contenido, size_hint=(0.75, 0.35))
        cerrar.bind(on_release=popup.dismiss)
        popup.open()

    def esta_en_horario_login(self):
        ahora = datetime.now()
        hora = ahora.hour
        return hora >= 21 or hora < 7

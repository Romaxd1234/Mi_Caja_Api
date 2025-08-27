from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.resources import resource_add_path
from kivy.uix.popup import Popup
from kivy.graphics import Rectangle
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
            self.fondo_rect = Rectangle(source="fondo.png", pos=self.pos, size=self.size)
        self.bind(size=self._update_rect, pos=self._update_rect)

        # Layout principal
        self.layout = BoxLayout(
            orientation='vertical',
            spacing=20,
            size_hint=(0.5, 0.5),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )

        # Label saludo
        self.label = Label(text="Hola, patrón", font_size=24, color=(1, 1, 1, 1))

        # Campo contraseña
        self.input_contrasena = TextInput(
            hint_text="Contraseña",
            multiline=False,
            password=True,
            size_hint=(1, None),
            height=40
        )

        # Botones
        self.boton_ingresar = Button(text="Ingresar", size_hint=(1, None), height=40)
        self.boton_regresar = Button(text="Regresar", size_hint=(1, None), height=40)

        self.boton_ingresar.bind(on_release=self.verificar_patron)
        self.boton_regresar.bind(on_release=self.regresar)

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
            # Hacer GET a la API
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

            # Cambiar a pantalla principal
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
        contenido = BoxLayout(orientation='vertical', spacing=10)
        contenido.add_widget(Label(text=mensaje))
        cerrar = Button(text="Cerrar", size_hint=(1, 0.3))
        popup = Popup(title=titulo, content=contenido, size_hint=(0.6, 0.4))
        cerrar.bind(on_release=popup.dismiss)
        contenido.add_widget(cerrar)
        popup.open()

    def esta_en_horario_login(self):
        ahora = datetime.now()
        hora = ahora.hour
        return hora >= 21 or hora < 7

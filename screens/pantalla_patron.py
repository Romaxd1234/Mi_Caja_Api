from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.button import Button
from kivy.uix.image import Image
import requests

class PantallaPatronScreen(Screen):
    API_BASE = "https://mi-caja-api.onrender.com"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.layout_principal = FloatLayout()

        # Imagen de fondo
        fondo = Image(source=r'C:/Users/fabiola gomey martin/Documents/APP/assets/fondo.png',
                      allow_stretch=True,
                      keep_ratio=False,
                      size_hint=(1, 1),
                      pos_hint={'x': 0, 'y': 0})
        self.layout_principal.add_widget(fondo)

        # Layout del formulario
        self.layout = BoxLayout(orientation='vertical',
                                padding=40,
                                spacing=15,
                                size_hint=(0.6, 0.8),
                                pos_hint={'center_x': 0.5, 'center_y': 0.55})

        # Saludo
        self.saludo_label = Label(text="Hola, Patrón", font_size=24, size_hint_y=None, height=40)
        self.layout.add_widget(self.saludo_label)

        # Nombre
        self.layout.add_widget(Label(text="Nombre del patrón"))
        self.nombre_input = TextInput(multiline=False, size_hint_y=None, height=40)
        self.layout.add_widget(self.nombre_input)

        # Contraseña
        self.layout.add_widget(Label(text="Crear contraseña"))
        self.pass_layout = BoxLayout(size_hint_y=None, height=40)
        self.pass_input = TextInput(password=True, multiline=False)
        self.pass_layout.add_widget(self.pass_input)
        self.show_pass_btn = ToggleButton(text="👁", size_hint_x=None, width=50)
        self.show_pass_btn.bind(on_press=self.toggle_password)
        self.pass_layout.add_widget(self.show_pass_btn)
        self.layout.add_widget(self.pass_layout)

        # Confirmar contraseña
        self.layout.add_widget(Label(text="Confirmar contraseña"))
        self.pass_confirm_layout = BoxLayout(size_hint_y=None, height=40)
        self.pass_confirm_input = TextInput(password=True, multiline=False)
        self.pass_confirm_layout.add_widget(self.pass_confirm_input)
        self.show_pass_confirm_btn = ToggleButton(text="👁", size_hint_x=None, width=50)
        self.show_pass_confirm_btn.bind(on_press=self.toggle_password_confirm)
        self.pass_confirm_layout.add_widget(self.show_pass_confirm_btn)
        self.layout.add_widget(self.pass_confirm_layout)

        # Mensaje
        self.msg = Label(text="", color=(1, 0, 0, 1), size_hint_y=None, height=30)
        self.layout.add_widget(self.msg)

        # Botón registrar
        self.btn_registrar = Button(text="Registrar Patrón", size_hint_y=None, height=50)
        self.btn_registrar.bind(on_press=self.registrar_patron)
        self.layout.add_widget(self.btn_registrar)

        self.layout_principal.add_widget(self.layout)

        # Botón volver
        self.btn_volver = Button(text="Volver",
                                 size_hint=(0.2, 0.08),
                                 pos_hint={'x': 0.02, 'y': 0.02})
        self.btn_volver.bind(on_release=self.volver)
        self.layout_principal.add_widget(self.btn_volver)

        self.add_widget(self.layout_principal)

        # Estado
        self.nombre_patron = ""
        self.tienda_actual = None  # Nombre de la tienda actual

    def toggle_password(self, instance):
        self.pass_input.password = not instance.state == 'down'

    def toggle_password_confirm(self, instance):
        self.pass_confirm_input.password = not instance.state == 'down'

    # ---------- API ----------
    def set_tienda_actual(self, nombre_tienda):
        """Setea la tienda actual y carga datos del patrón desde la API."""
        self.tienda_actual = nombre_tienda
        self.cargar_datos_patron()

    def cargar_datos_patron(self):
        """Trae nombre y contraseña del patrón desde la API."""
        if not self.tienda_actual:
            return
        try:
            url = f"{self.API_BASE}/tienda/{self.tienda_actual}/patron/password"
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                data = r.json()
                nombre = data.get("nombre", "")
                password = data.get("password", "")
                self.nombre_patron = nombre
                self.saludo_label.text = f"Hola, {self.nombre_patron}" if nombre else "Hola, Patrón"
                self.nombre_input.text = nombre
                if password:
                    self.msg.text = "Contraseña ya registrada. Usa la pantalla de login para entrar."
                    self.pass_input.disabled = True
                    self.pass_confirm_input.disabled = True
                    self.btn_registrar.disabled = True
                    self.nombre_input.disabled = True
        except Exception as e:
            print("Error al cargar datos del patrón:", e)

    def registrar_patron(self, instance):
        nombre = self.nombre_input.text.strip()
        contra = self.pass_input.text.strip()
        contra_confirm = self.pass_confirm_input.text.strip()

        if not nombre:
            self.msg.text = "Debes ingresar tu nombre."
            return

        if not contra or not contra_confirm:
            self.msg.text = "Por favor llena ambos campos de contraseña."
            return

        if contra != contra_confirm:
            self.msg.text = "Las contraseñas no coinciden."
            return

        if not self.tienda_actual:
            self.msg.text = "Error: no hay tienda seleccionada."
            return

        # POST a la API
        try:
            url = f"{self.API_BASE}/tienda/{self.tienda_actual}/patron/password"
            payload = {"nombre": nombre, "password": contra}
            r = requests.post(url, json=payload, timeout=10)
            if r.status_code == 200:
                self.msg.color = (0, 1, 0, 1)
                self.msg.text = "Datos del patrón guardados correctamente."
                self.pass_input.disabled = True
                self.pass_confirm_input.disabled = True
                self.nombre_input.disabled = True
                self.btn_registrar.disabled = True
            else:
                self.msg.text = f"Error al guardar: {r.status_code}"
        except Exception as e:
            self.msg.text = f"Error al conectar con API: {e}"

    def volver(self, instance):
        self.manager.current = "seleccion_rol"

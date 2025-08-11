from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.storage.jsonstore import JsonStore
import os

class PantallaPatronScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Layout principal con fondo
        self.layout_principal = FloatLayout()

        # Imagen de fondo
        fondo = Image(source=r'C:/Users/fabiola gomey martin/Documents/APP/assets/fondo.png',
                      allow_stretch=True,
                      keep_ratio=False,
                      size_hint=(1, 1),
                      pos_hint={'x': 0, 'y': 0})
        self.layout_principal.add_widget(fondo)

        # Layout con formulario centrado
        self.layout = BoxLayout(orientation='vertical',
                                padding=40,
                                spacing=15,
                                size_hint=(0.6, 0.8),
                                pos_hint={'center_x': 0.5, 'center_y': 0.55})

        # Saludo inicial
        self.saludo_label = Label(text="Hola, Patrón", font_size=24, size_hint_y=None, height=40)
        self.layout.add_widget(self.saludo_label)

        # Campo para ingresar nombre
        self.layout.add_widget(Label(text="Nombre del patrón"))
        self.nombre_input = TextInput(multiline=False, size_hint_y=None, height=40)
        self.layout.add_widget(self.nombre_input)

        # Crear contraseña
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

        # Mensaje de error/éxito
        self.msg = Label(text="", color=(1, 0, 0, 1), size_hint_y=None, height=30)
        self.layout.add_widget(self.msg)

        # Botón registrar
        self.btn_registrar = Button(text="Registrar Patrón", size_hint_y=None, height=50)
        self.btn_registrar.bind(on_press=self.registrar_patron)
        self.layout.add_widget(self.btn_registrar)

        # Agregar el formulario al layout principal
        self.layout_principal.add_widget(self.layout)

        # Botón para volver (esquina inferior izquierda)
        self.btn_volver = Button(text="Volver",
                                 size_hint=(0.2, 0.08),
                                 pos_hint={'x': 0.02, 'y': 0.02})
        self.btn_volver.bind(on_release=self.volver)
        self.layout_principal.add_widget(self.btn_volver)

        self.add_widget(self.layout_principal)

        self.tienda_actual_path = None
        self.nombre_patron = ""

    def toggle_password(self, instance):
        self.pass_input.password = not instance.state == 'down'

    def toggle_password_confirm(self, instance):
        self.pass_confirm_input.password = not instance.state == 'down'

    def set_datos_patron(self, nombre_patron, ruta_tienda):
        """Para asignar el nombre del patrón y la ruta del json de la tienda."""
        self.nombre_patron = nombre_patron
        self.tienda_actual_path = ruta_tienda
        self.saludo_label.text = f"Hola, {self.nombre_patron}"
        self.nombre_input.text = nombre_patron  # Mostrar el nombre si ya se conoce

        # Verificar si ya hay una contraseña
        if self.tienda_actual_path and os.path.exists(self.tienda_actual_path):
            store = JsonStore(self.tienda_actual_path)
            if store.exists("patron") and store.get("patron").get("password"):
                self.msg.text = "Contraseña ya registrada. Usa la pantalla de login para entrar."
                self.pass_input.disabled = True
                self.pass_confirm_input.disabled = True
                self.btn_registrar.disabled = True
                self.nombre_input.disabled = True

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

        if self.tienda_actual_path:
            store = JsonStore(self.tienda_actual_path)
            store.put("patron", nombre=nombre, password=contra)
            self.msg.color = (0, 1, 0, 1)
            self.msg.text = "Datos del patrón guardados correctamente."
            self.pass_input.disabled = True
            self.pass_confirm_input.disabled = True
            self.nombre_input.disabled = True
            self.btn_registrar.disabled = True
        else:
            self.msg.text = "Error: no se encontró la tienda actual."

    def volver(self, instance):
        self.manager.current = "seleccion_rol"

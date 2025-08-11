from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.image import Image
from kivy.storage.jsonstore import JsonStore
import os
import re  # para limpiar nombres de archivos

class BienvenidaScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Imagen de fondo
        self.background = Image(source=r'C:/Users/fabiola gomey martin/Documents/APP/assets/fondo.png',
                                allow_stretch=True,
                                keep_ratio=False,
                                size_hint=(1, 1),
                                pos_hint={'center_x': 0.5, 'center_y': 0.5})
        self.add_widget(self.background)

        # Contenedor principal
        layout = BoxLayout(orientation='vertical', padding=40, spacing=15,
                           size_hint=(0.6, 0.7),
                           pos_hint={'center_x': 0.5, 'center_y': 0.5})

        layout.add_widget(Label(text="Crear Tienda", font_size=24))

        layout.add_widget(Label(text="Nombre de la tienda"))
        self.nombre_input = TextInput(multiline=False, size_hint_y=None, height=40)
        layout.add_widget(self.nombre_input)

        # Contraseña con ojito
        self.pass_layout = BoxLayout(size_hint_y=None, height=40)
        self.contra_input = TextInput(password=True, multiline=False)
        self.pass_layout.add_widget(self.contra_input)

        self.show_pass_btn = ToggleButton(text="👁", size_hint_x=None, width=50)
        self.show_pass_btn.bind(on_press=self.toggle_password)
        self.pass_layout.add_widget(self.show_pass_btn)

        layout.add_widget(Label(text="Contraseña"))
        layout.add_widget(self.pass_layout)

        # Confirmar contraseña con ojito
        self.pass_confirm_layout = BoxLayout(size_hint_y=None, height=40)
        self.contra_confirm_input = TextInput(password=True, multiline=False)
        self.pass_confirm_layout.add_widget(self.contra_confirm_input)

        self.show_pass_confirm_btn = ToggleButton(text="👁", size_hint_x=None, width=50)
        self.show_pass_confirm_btn.bind(on_press=self.toggle_password_confirm)
        self.pass_confirm_layout.add_widget(self.show_pass_confirm_btn)

        layout.add_widget(Label(text="Confirmar contraseña"))
        layout.add_widget(self.pass_confirm_layout)

        self.msg = Label(text="", color=(1, 0, 0, 1), size_hint_y=None, height=30)
        layout.add_widget(self.msg)

        btn_crear = Button(text="Crear Tienda", size_hint_y=None, height=50)
        btn_crear.bind(on_press=self.crear_tienda)
        layout.add_widget(btn_crear)

        btn_abrir = Button(text="¿Ya registraste tu tienda?", size_hint_y=None, height=50)
        btn_abrir.bind(on_press=self.abrir_pantalla_abrir_tienda)
        layout.add_widget(btn_abrir)

        self.add_widget(layout)

    def toggle_password(self, instance):
        self.contra_input.password = not instance.state == 'down'

    def toggle_password_confirm(self, instance):
        self.contra_confirm_input.password = not instance.state == 'down'

    def crear_tienda(self, instance):
        nombre = self.nombre_input.text.strip()
        contra = self.contra_input.text.strip()
        contra_confirm = self.contra_confirm_input.text.strip()

        if not nombre or not contra or not contra_confirm:
            self.msg.text = "Por favor llena todos los campos"
            return

        if contra != contra_confirm:
            self.msg.text = "Las contraseñas no coinciden"
            return

        # Limpiar nombre para usar como nombre de archivo
        nombre_archivo = re.sub(r'[\\/*?:"<>|]', "_", nombre.lower().replace(" ", "_"))
        ruta_archivo = f"data/tiendas/{nombre_archivo}.json"

        os.makedirs("data/tiendas", exist_ok=True)

        if os.path.exists(ruta_archivo):
            self.msg.text = "Esa tienda ya existe. Usa otro nombre o ábrela."
            return

        # Guardar datos de la tienda
        store_tienda = JsonStore(ruta_archivo)
        store_tienda.put("tienda", nombre=nombre, patron_password=contra)

        # Registrar tienda actual en config.json
        os.makedirs("data", exist_ok=True)
        store_config = JsonStore("data/config.json")
        store_config.put("actual", archivo=ruta_archivo)

        self.msg.text = "Tienda creada exitosamente"
        self.manager.current = "seleccion_rol"

    def abrir_pantalla_abrir_tienda(self, instance):
        self.manager.current = "abrir_tienda"

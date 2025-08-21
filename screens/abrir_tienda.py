from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
import requests
import re

API_URL = "https://mi-caja-api.onrender.com/tiendas"

class AbrirTiendaScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        layout_principal = FloatLayout()

        fondo = Image(source=r'C:\Users\USER\Documents\APP\APP\assets\fondo.png',
                      allow_stretch=True,
                      keep_ratio=False,
                      size_hint=(1, 1),
                      pos_hint={'x': 0, 'y': 0})
        layout_principal.add_widget(fondo)

        layout = BoxLayout(orientation='vertical', padding=40, spacing=15,
                           size_hint=(0.8, 0.7),
                           pos_hint={'center_x': 0.5, 'center_y': 0.5})

        layout.add_widget(Label(text="Abrir Tienda", font_size=24))

        layout.add_widget(Label(text="Nombre de la tienda"))
        self.nombre_input = TextInput(multiline=False)
        layout.add_widget(self.nombre_input)

        layout.add_widget(Label(text="Contraseña"))
        self.contra_input = TextInput(password=True, multiline=False)
        layout.add_widget(self.contra_input)

        self.msg = Label(text="", color=(1, 0, 0, 1))
        layout.add_widget(self.msg)

        btn_abrir = Button(text="Abrir Tienda", size_hint=(1, None), height=40)
        btn_abrir.bind(on_press=self.abrir_tienda)
        layout.add_widget(btn_abrir)

        btn_volver = Button(text="Volver", size_hint=(1, None), height=40)
        btn_volver.bind(on_press=self.volver)
        layout.add_widget(btn_volver)

        layout_principal.add_widget(layout)
        self.add_widget(layout_principal)


    def set_ruta_tienda(self, ruta):
        self.ruta_tienda = ruta

    def abrir_tienda(self, instance):
        tienda_id = self.obtener_id_por_nombre(self.nombre_input.text)
        contra = self.contra_input.text.strip()

        if not tienda_id:
            self.msg.text = "La tienda no existe"
            return

        try:
            response = requests.get(f"{API_URL}/{tienda_id}")
            if response.status_code != 200:
                self.msg.text = "Error al conectar con la API"
                return

            tienda = response.json()

            # Comparar la contraseña de la tienda directamente
            if tienda.get("password", "").strip() == contra.strip():
                self.msg.text = "Tienda abierta correctamente"

                # Guardar la tienda en la pantalla principal
                pantalla_principal = self.manager.get_screen("pantalla_principal")
                pantalla_principal.tienda_actual = tienda

                # Pasar el ID de la tienda a SeleccionRolScreen
                pantalla_rol = self.manager.get_screen("seleccion_rol")
                pantalla_rol.tienda_actual_id = tienda["id"]

                # Pasar la tienda al inventario
                inventario_screen = self.manager.get_screen("inventario")
                inventario_screen.set_tienda_api(tienda)

                self.manager.current = "seleccion_rol"
            else:
                self.msg.text = "Contraseña incorrecta"

        except Exception as e:
            self.msg.text = f"Error de conexión: {str(e)}"



            
    def obtener_id_por_nombre(self, nombre):
        try:
            response = requests.get(f"{API_URL}/")
            if response.status_code != 200:
                return None
            tiendas = response.json()
            nombre_limpio = re.sub(r'[\\/*?:"<>|]', "_", nombre.lower().replace(" ", "_"))
            tienda = next((t for t in tiendas if t["nombre"].lower().replace(" ", "_") == nombre_limpio), None)
            if tienda:
                return tienda["id"]
            return None
        except:
            return None
            

    def volver(self, instance):
        self.manager.current = "bienvenida"

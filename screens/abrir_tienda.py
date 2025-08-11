from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.storage.jsonstore import JsonStore
import os
import re  # Importa re para limpiar nombres
from datetime import datetime  # <-- Importar datetime para guardar fecha/hora
from kivy.clock import Clock  # Para ejecutar función después de cargar pantalla

class AbrirTiendaScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        layout_principal = FloatLayout()

        # Imagen de fondo
        fondo = Image(source=r'C:/Users/fabiola gomey martin/Documents/APP/assets/fondo.png',
                      allow_stretch=True,
                      keep_ratio=False,
                      size_hint=(1, 1),
                      pos_hint={'x': 0, 'y': 0})
        layout_principal.add_widget(fondo)

        # Layout para formulario (sobre el fondo)
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

    def on_pre_enter(self, *args):
        print("Entrando a AbrirTiendaScreen - on_pre_enter")
        Clock.schedule_once(self.verificar_ultimo_acceso, 0.1)

    def ventana(self, hora):
        # 0 = día (7:00 a 20:59), 1 = noche (21:00 a 6:59)
        return 1 if (hora >= 21 or hora < 7) else 0

    def necesita_login(self):
        if not os.path.exists("data/config.json"):
            print("No existe config.json")
            return True  # pide login si no existe config

        store_config = JsonStore("data/config.json")
        if not store_config.exists("actual"):
            print("No hay tienda actual guardada")
            return True  # pide login si no hay tienda actual

        ruta_tienda = store_config.get("actual")["archivo"]
        if not os.path.exists(ruta_tienda):
            print("No existe el archivo de la tienda")
            return True

        store = JsonStore(ruta_tienda)
        if not store.exists("ultimo_acceso"):
            print("No existe registro ultimo_acceso")
            return True  # pide login si no hay registro

        acceso = store.get("ultimo_acceso")
        fecha_acceso = acceso.get("fecha")
        hora_acceso = int(acceso.get("hora").split(":")[0])

        ahora = datetime.now()
        fecha_hoy = ahora.strftime("%Y-%m-%d")
        hora_actual = ahora.hour

        print(f"fecha_acceso: {fecha_acceso}, hora_acceso: {hora_acceso}, fecha_hoy: {fecha_hoy}, hora_actual: {hora_actual}")

        if fecha_acceso != fecha_hoy:
            print("Fechas diferentes, necesita login")
            return True  # cambio de día, pedir login

        ventana_acceso = self.ventana(hora_acceso)
        ventana_actual = self.ventana(hora_actual)

        if ventana_acceso == ventana_actual:
            print("En misma ventana horaria, NO necesita login")
            return False  # mismo rango, no pide login

        print("Cambio de ventana horaria, necesita login")
        return True  # cambio de ventana, pide login

    def verificar_ultimo_acceso(self, dt):
        if not self.necesita_login():
            print("Login ya hecho para esta ventana, saltando Abrir Tienda")
            self.manager.current = "seleccion_rol"
        else:
            print("Necesita hacer login, mostrando Abrir Tienda")

    def abrir_tienda(self, instance):
        nombre = self.nombre_input.text.strip()
        contra = self.contra_input.text.strip()

        if not nombre or not contra:
            self.msg.text = "Por favor llena todos los campos"
            return

        # Limpiar nombre igual que en creación para buscar archivo correcto
        nombre_limpio = re.sub(r'[\\/*?:"<>|]', "_", nombre.lower().replace(" ", "_"))
        ruta_archivo = f"data/tiendas/{nombre_limpio}.json"

        if not os.path.exists(ruta_archivo):
            self.msg.text = "La tienda no existe"
            return

        store = JsonStore(ruta_archivo)
        if not store.exists("tienda"):
            self.msg.text = "El archivo no contiene datos válidos"
            return

        datos = store.get("tienda")

        if datos.get("patron_password") == contra:
            # Guardar tienda actual en config.json con clave 'actual' y ruta
            os.makedirs("data", exist_ok=True)
            store_config = JsonStore("data/config.json")
            store_config.put("actual", archivo=ruta_archivo)

            # Guardar fecha y hora actuales como último acceso
            ahora = datetime.now()
            store.put("ultimo_acceso", fecha=ahora.strftime("%Y-%m-%d"), hora=ahora.strftime("%H:%M"))
            print(f"Guardado ultimo acceso en tienda: {ruta_archivo}")

            self.msg.text = "Tienda abierta correctamente"
            self.manager.current = "seleccion_rol"
        else:
            self.msg.text = "Contraseña incorrecta"

    def volver(self, instance):
        self.manager.current = "bienvenida"

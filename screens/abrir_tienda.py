from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.clock import Clock
import requests
import os
import json
from datetime import datetime, timedelta

LOCAL_DIR = r"C:\MiCajaApp"
SESSION_FILE = os.path.join(LOCAL_DIR, "tienda_sesion.json")

class AbrirTiendaScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        layout_principal = FloatLayout()

        # Fondo
        fondo = Image(source=r'C:/Users/fabiola gomey martin/Documents/APP/assets/fondo.png',
                      allow_stretch=True, keep_ratio=False,
                      size_hint=(1, 1), pos_hint={'x': 0, 'y': 0})
        layout_principal.add_widget(fondo)

        # Layout formulario
        layout = BoxLayout(orientation='vertical', padding=40, spacing=15,
                           size_hint=(0.8, 0.7), pos_hint={'center_x': 0.5, 'center_y': 0.5})

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

        # Crear carpeta local si no existe
        if not os.path.exists(LOCAL_DIR):
            os.makedirs(LOCAL_DIR)

        # Intentar abrir sesión automáticamente si hay archivo local
        Clock.schedule_once(self.checar_sesion_local, 0.5)

    def ventana(self, hora):
        return 1 if (hora >= 21 or hora < 7) else 0

    def necesita_login(self, ultima_hora):
        """Revisar si han pasado más de 12 horas desde el último acceso"""
        if not ultima_hora:
            return True
        ahora = datetime.now()
        ultimo = datetime.strptime(ultima_hora, "%Y-%m-%d %H:%M")
        return ahora - ultimo > timedelta(hours=12)

    def checar_sesion_local(self, dt):
        if os.path.exists(SESSION_FILE):
            with open(SESSION_FILE, "r", encoding="utf-8") as f:
                sesion = json.load(f)
            nombre = sesion.get("nombre")
            contra = sesion.get("password")
            hora = sesion.get("hora")

            if nombre and contra and not self.necesita_login(hora):
                # Verificar con API que la tienda sigue existiendo y la contraseña coincide
                try:
                    response = requests.get("https://mi-caja-api.onrender.com/tienda")
                    if response.status_code == 200:
                        tiendas = response.json()
                        for t in tiendas:
                            tienda_info = t.get("tienda", {})
                            if tienda_info.get("nombre") == nombre and tienda_info.get("patron_password") == contra:
                                # Abrir tienda directamente
                                self.msg.color = (0, 1, 0, 1)
                                self.msg.text = f"Tienda {nombre} abierta automáticamente"
                                Clock.schedule_once(lambda dt: setattr(self.manager, 'current', 'seleccion_rol'), 0.5)
                                return
                except:
                    pass
            # Si falla la verificación o expiró el tiempo, borrar sesión local
            os.remove(SESSION_FILE)

    def abrir_tienda(self, instance):
        nombre = self.nombre_input.text.strip()
        contra = self.contra_input.text.strip()

        if not nombre or not contra:
            self.msg.text = "Por favor llena todos los campos"
            return

        try:
            response = requests.get("https://mi-caja-api.onrender.com/tienda")
            if response.status_code == 200:
                tiendas = response.json()
                tienda_valida = None
                for t in tiendas:
                    info = t.get("tienda", {})
                    if info.get("nombre") == nombre and info.get("patron_password") == contra:
                        tienda_valida = info
                        break

                if tienda_valida:
                    # Guardar sesión local
                    with open(SESSION_FILE, "w", encoding="utf-8") as f:
                        json.dump({
                            "nombre": nombre,
                            "password": contra,
                            "hora": datetime.now().strftime("%Y-%m-%d %H:%M")
                        }, f)

                    self.msg.color = (0, 1, 0, 1)
                    self.msg.text = "Tienda abierta correctamente"
                    Clock.schedule_once(lambda dt: setattr(self.manager, 'current', 'seleccion_rol'), 0.5)
                else:
                    self.msg.text = "Nombre o contraseña incorrectos"
            else:
                self.msg.text = "Error al conectar con la API"
        except Exception as e:
            self.msg.text = f"Error de conexión: {str(e)}"

    def volver(self, instance):
        self.manager.current = "bienvenida"

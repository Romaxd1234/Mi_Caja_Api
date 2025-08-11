from kivy.uix.image import Image
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import Screen
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.storage.jsonstore import JsonStore
import os
from datetime import datetime  # 👈 Necesario para la lógica de hora

class SeleccionRolScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Fondo
        self.background = Image(
            source='C:/Users/fabiola gomey martin/Documents/APP/assets/fondo.png',
            allow_stretch=True,
            keep_ratio=False,
            size_hint=(1, 1),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        self.add_widget(self.background)

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

        # Variable para saber cuál tienda está abierta
        self.tienda_actual = None

        # Enlazar botones
        self.btn_patron.bind(on_press=self.ir_pantalla_patron)
        self.btn_empleado.bind(on_press=self.ir_pantalla_empleado)

    def ir_pantalla_empleado(self, instance):
        print("Botón Empleado presionado")

        config_path = "data/config.json"
        if os.path.exists(config_path):
            store_config = JsonStore(config_path)
            if store_config.exists("actual"):
                ruta_tienda = store_config.get("actual")["archivo"]
                print(f"Ruta tienda para login empleado: {ruta_tienda}")

                if os.path.exists(ruta_tienda):
                    pantalla_login_empleado = self.manager.get_screen("login_empleado")
                    pantalla_login_empleado.set_ruta_tienda(ruta_tienda)
                    self.manager.current = "login_empleado"
                else:
                    print("Archivo tienda no encontrado en ir_pantalla_empleado")
            else:
                print("No hay tienda actual guardada en config.json")
        else:
            print("Archivo config.json no encontrado en ir_pantalla_empleado")

    def set_tienda_actual(self, nombre_tienda):
        self.tienda_actual = nombre_tienda

    def on_pre_enter(self, *args):
        config_path = "data/config.json"
        if os.path.exists(config_path):
            store_config = JsonStore(config_path)
            if store_config.exists("actual"):
                ruta_tienda = store_config.get("actual")["archivo"]
                if os.path.exists(ruta_tienda):
                    store = JsonStore(ruta_tienda)
                    if store.exists("tienda"):
                        nombre_tienda = store.get("tienda").get("nombre", self.tienda_actual or "Tienda sin nombre")
                        self.nombre_label.text = f"[b]Tienda: {nombre_tienda}[/b]"
                        self.nombre_label.markup = True
                    else:
                        self.nombre_label.text = "[b]Datos de tienda no encontrados[/b]"
                else:
                    self.nombre_label.text = "[b]Archivo de tienda no encontrado[/b]"
            else:
                self.nombre_label.text = "[b]No hay tienda actual guardada[/b]"
        else:
            self.nombre_label.text = "[b]Archivo config.json no encontrado[/b]"

    def ir_pantalla_patron(self, instance):
        print("Botón Patrón presionado")
        config_path = "data/config.json"
        if os.path.exists(config_path):
            store_config = JsonStore(config_path)
            if store_config.exists("actual"):
                ruta_tienda = store_config.get("actual")["archivo"]
                if os.path.exists(ruta_tienda):
                    store = JsonStore(ruta_tienda)

                    if store.exists("patron") and store.get("patron").get("password"):

                        # Verificar si ya hizo login nocturno
                        if self.esta_en_horario_login() and self.ya_hizo_login_hoy(store):
                            print("Ya hizo login nocturno, redirigiendo directo.")
                            pantalla_patron = self.manager.get_screen("pantalla_patron")
                            pantalla_patron.set_datos_patron("Patrón", ruta_tienda)
                            self.manager.current = "pantalla_patron"
                            return

                        # Si no ha hecho login nocturno, ir a login_patron
                        pantalla_login = self.manager.get_screen("login_patron")
                        if hasattr(pantalla_login, 'set_datos_patron'):
                            pantalla_login.set_datos_patron(ruta_tienda)
                        self.manager.current = "login_patron"
                    else:
                        # No hay patrón registrado, ir a pantalla_patron para registrar
                        pantalla_patron = self.manager.get_screen("pantalla_patron")
                        pantalla_patron.set_datos_patron("Patrón", ruta_tienda)
                        self.manager.current = "pantalla_patron"
                else:
                    print("Archivo de tienda no encontrado")
            else:
                print("No hay tienda actual guardada")
        else:
            print("Archivo config.json no encontrado")

    def esta_en_horario_login(self):
        ahora = datetime.now()
        hora = ahora.hour
        return hora >= 21 or hora < 7

    def ya_hizo_login_hoy(self, store):
        if store.exists("log_nocturno"):
            fecha_guardada = store.get("log_nocturno")["fecha"]
            hoy = datetime.now().strftime("%Y-%m-%d")
            return fecha_guardada == hoy
        return False
    
    def checar_sesion_local(self, *args):
        if os.path.exists(SESSION_LOCAL_FILE):
            with open(SESSION_LOCAL_FILE, "r", encoding="utf-8") as f:
                sesion = json.load(f)
            if sesion.get("rol") == "empleado" and "nombre" in sesion:
                # Ya hay sesión activa, ir directo a la pantalla del empleado
                print(f"Sesión local encontrada para empleado: {sesion['nombre']} - saltando login")
                pantalla_empleado = self.manager.get_screen("ventana_empleados")
                # Setear la tienda y el empleado
                config_path = "data/config.json"
                if os.path.exists(config_path):
                    store_config = JsonStore(config_path)
                    if store_config.exists("actual"):
                        ruta_tienda = store_config.get("actual")["archivo"]
                        if os.path.exists(ruta_tienda):
                            pantalla_empleado.set_ruta_tienda(ruta_tienda)
                            self.manager.current = "ventana_empleados"
                            # Aquí podrías agregar código para seleccionar automáticamente el empleado en el spinner
                return

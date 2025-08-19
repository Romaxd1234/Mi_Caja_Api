from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.properties import StringProperty
from kivy.clock import Clock
from kivy.storage.jsonstore import JsonStore
import json
import os
from datetime import datetime

class VentanaPrincipal(Screen):
    def __init__(self, **kwargs):
        super(VentanaPrincipal, self).__init__(**kwargs)
        self.nombre_usuario = ""

        self.origen_login = "patron"  # por defecto
        self.nombre_usuario = ""
        self.inicializado = False  # para evitar múltiples cargas

        self.layout = FloatLayout()
        self.add_widget(self.layout)

    def configurar_sesion(self, origen, nombre, tienda_id=None):
        self.origen_login = origen 
        self.nombre_usuario = nombre
        self.tienda_id = tienda_id 

    def on_pre_enter(self):
        if self.inicializado:
            return  # Solo cargar UI una vez

        self.inicializado = True
        self.layout.clear_widgets()

        # ------------------------
        # Fondo
        self.fondo = Image(
            source=r'C:\Users\USER\Documents\APP\APP\assets\fondo.png',
            allow_stretch=True,
            keep_ratio=False,
            size_hint=(1, 1),
            pos_hint={'x': 0, 'y': 0}
        )
        self.layout.add_widget(self.fondo)

        # ------------------------
        # Nombre de la tienda
        self.nombre_tienda = "Tienda"
        if hasattr(self, "tienda_id") and self.tienda_id:
            try:
                import requests
                url = f"https://mi-caja-api.onrender.com/tiendas/{self.tienda_id}"
                respuesta = requests.get(url)
                if respuesta.status_code == 200:
                    datos = respuesta.json()
                    self.nombre_tienda = datos.get("nombre", "Tienda").strip("*")
            except Exception as e:
                print("Error al obtener datos de la tienda:", e)

        self.label_tienda = Label(
            text=f"[b]{self.nombre_tienda}[/b]",
            font_size=24,
            size_hint=(.3, .1),
            pos_hint={"right": 0.98, "top": 0.98},
            color=(0, 0, 0, 1),
            markup=True
        )
        self.layout.add_widget(self.label_tienda)

        # ------------------------
        # Nombre del usuario si es empleado
        if self.origen_login == "empleado" and self.nombre_usuario:
            self.label_usuario = Label(
                text=f"Hola, {self.nombre_usuario}",
                font_size=18,
                size_hint=(.3, .05),
                pos_hint={"right": 0.98, "top": 0.90},
                color=(0, 0, 0, 1)
            )
            self.layout.add_widget(self.label_usuario)

        # ------------------------
        # Reloj
        self.label_hora = Label(
            text="",
            font_size=20,
            size_hint=(.3, .1),
            pos_hint={"right": 0.98, "y": 0.02},
            color=(1, 1, 1, 1)
        )
        self.layout.add_widget(self.label_hora)
        Clock.schedule_interval(self.actualizar_hora, 1)

        # ------------------------
        # Botones principales
        botones_info = [
            ("Venta", self.abrir_venta, 0.95),
            ("Venta Inventario", self.abrir_venta_con_inventario, 0.82),
            ("Inventario", self.ir_a_inventario, 0.69),
            ("Corte", self.abrir_popup_corte, 0.56),
            ("Registro de Cortes", self.ir_a_registro_cortes, 0.43)
        ]

        for texto, callback, top in botones_info:
            btn = Button(text=texto, size_hint=(.2, .1), pos_hint={"x": 0.02, "top": top})
            btn.bind(on_release=callback)
            self.layout.add_widget(btn)

        # Registro Semanal solo para patrón
        if self.origen_login == "patron":
            self.boton_registro_semanal = Button(
                text="Registro Semanal",
                size_hint=(.2, .1),
                pos_hint={"x": 0.02, "top": 0.30}
            )
            self.boton_registro_semanal.bind(on_release=self.ir_a_registro_semanal)
            self.layout.add_widget(self.boton_registro_semanal)

        # Botón Empleados solo si NO es empleado
        if self.origen_login != "empleado":
            self.boton_empleados = Button(
                text="Empleados",
                size_hint=(.2, .1),
                pos_hint={"x": 0.02, "y": 0.02}
            )
            self.boton_empleados.bind(on_release=self.gestionar_empleados)
            self.layout.add_widget(self.boton_empleados)

        # ------------------------
        # Revisar préstamo pendiente
        self.revisar_prestamo_pendiente()

    def actualizar_hora(self, dt):
        ahora = datetime.now()
        self.label_hora.text = ahora.strftime("%H:%M:%S")

    def abrir_venta(self, instance):
        contenido = BoxLayout(orientation='vertical', padding=10, spacing=10)

        self.ventas_temporales = []

        self.grid_ventas = GridLayout(cols=2, size_hint_y=None, spacing=5)
        self.grid_ventas.bind(minimum_height=self.grid_ventas.setter('height'))
        scroll_ventas = ScrollView(size_hint=(1, 0.5))
        scroll_ventas.add_widget(self.grid_ventas)
        contenido.add_widget(scroll_ventas)

        self.label_total = Label(text="TOTAL = $0.00", size_hint_y=None, height=30)
        contenido.add_widget(self.label_total)

        self.input_producto = TextInput(hint_text="Producto", multiline=False, size_hint=(1, None), height=40)
        contenido.add_widget(self.input_producto)

        self.input_precio = TextInput(hint_text="Precio", multiline=False, input_filter='float', size_hint=(1, None), height=40)
        contenido.add_widget(self.input_precio)

        btn_agregar_producto = Button(text="Agregar Producto", size_hint=(1, None), height=40)
        contenido.add_widget(btn_agregar_producto)

        btn_registrar = Button(text="Registrar Venta", size_hint=(1, None), height=40)
        contenido.add_widget(btn_registrar)

        popup = Popup(title="Registrar Venta", content=contenido, size_hint=(0.9, 0.9))

        # Funciones internas
        def actualizar_lista_productos():
            self.grid_ventas.clear_widgets()
            for prod, precio in self.ventas_temporales:
                label_prod = Label(text=prod, size_hint_y=None, height=30, halign='left', valign='middle')
                label_prod.text_size = (label_prod.width, None)
                label_precio = Label(text=f"${precio:.2f}", size_hint_y=None, height=30, halign='right', valign='middle')
                label_precio.text_size = (label_precio.width, None)
                self.grid_ventas.add_widget(label_prod)
                self.grid_ventas.add_widget(label_precio)
            total = sum(p for _, p in self.ventas_temporales)
            self.label_total.text = f"TOTAL = ${total:.2f}"

        def agregar_producto(instance):
            producto = self.input_producto.text.strip()
            precio = self.input_precio.text.strip()
            if not producto or not precio:
                return
            try:
                precio_float = float(precio)
            except ValueError:
                return
            self.ventas_temporales.append((producto, precio_float))
            actualizar_lista_productos()
            self.input_producto.text = ''
            self.input_precio.text = ''

        def registrar_venta(instance):
            if not self.ventas_temporales:
                return
            import requests
            url = f"https://mi-caja-api.onrender.com/tiendas/{self.tienda_id}/ventas/"
            payload = {
                "usuario": self.nombre_usuario,
                "productos": [{"producto": p, "precio": pr, "cantidad": 1} for p, pr in self.ventas_temporales],
                "fuera_inventario": True
            }
            try:
                respuesta = requests.post(url, json=payload)
                respuesta.raise_for_status()
                popup.dismiss()
                self.ventas_temporales = []
                self.mostrar_popup_confirmacion()
            except Exception as e:
                self.mostrar_popup("Error", f"No se pudo registrar la venta: {e}")

        btn_agregar_producto.bind(on_release=agregar_producto)
        btn_registrar.bind(on_release=registrar_venta)

        popup.open()


    def mostrar_popup_confirmacion(self):
        contenido = BoxLayout(orientation='vertical', padding=10, spacing=10)
        contenido.add_widget(Label(text="Venta registrada correctamente."))

        btn_cerrar = Button(text='Cerrar', size_hint=(1, None), height=40)
        contenido.add_widget(btn_cerrar)

        popup_confirmacion = Popup(title='Confirmación', content=contenido,
                                  size_hint=(0.5, 0.4),
                                  auto_dismiss=False)

        btn_cerrar.bind(on_release=popup_confirmacion.dismiss)
        popup_confirmacion.open()

    def guardar_venta(self, producto, precio, fuera_inventario=False):
        config_path = "data/config.json"
        if not os.path.exists(config_path):
            print("No existe config.json")
            return
        
        store_config = JsonStore(config_path)
        if not store_config.exists("actual"):
            print("No hay tienda actual guardada")
            return
        
        ruta_tienda = store_config.get("actual")["archivo"]
        if not os.path.exists(ruta_tienda):
            print("Archivo de tienda no encontrado")
            return
        
        store = JsonStore(ruta_tienda)

        ventas = []
        if store.exists("ventas"):
            ventas = store.get("ventas").get("lista", [])

        nueva_venta = {
            "producto": producto,
            "usuario": self.nombre_usuario,
            "precio": precio,
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "fuera_inventario": fuera_inventario

        }
        ventas.append(nueva_venta)
        store.put("ventas", lista=ventas)

        print(f"Venta registrada: {producto} - ${precio}")

    def ir_a_inventario(self, instance):
        self.manager.current = 'inventario'

    def ir_a_registro_semanal(self, instance):
        self.manager.current = 'registro_semanal'

    def realizar_corte(self, instance):
        print("Ir a Corte")

    def ir_a_registro_cortes(self, instance):
        self.manager.current = 'registro_cortes'

    def abrir_venta_con_inventario(self, instance):
        print("Ir a pantalla de Venta con Inventario")
        self.manager.current = 'venta_inventario'

    def set_tienda_id(self, tienda_id):
        self.tienda_id = tienda_id

    def cargar_empleados_api(self):
        if not self.tienda_id:
            print("No hay tienda seleccionada")
            return

        import requests
        url = f"https://mi-caja-api.onrender.com/tiendas/{self.tienda_id}/empleados/"
        try:
            respuesta = requests.get(url)
            respuesta.raise_for_status()
            empleados = respuesta.json()
            print("Empleados cargados:", empleados)
            # Actualiza aquí la UI con los empleados
        except Exception as e:
            print("Error al cargar empleados:", e)
    def mostrar_alerta_prestamo(self, mensaje):
        contenido = BoxLayout(orientation='vertical', padding=10, spacing=10)
        contenido.add_widget(Label(text=mensaje))
        btn_cerrar = Button(text='Cerrar', size_hint=(1, None), height=40)
        contenido.add_widget(btn_cerrar)

        popup = Popup(title='Préstamo Realizado', content=contenido,
                      size_hint=(0.6, 0.4))
        btn_cerrar.bind(on_release=popup.dismiss)
        popup.open()

    # --- NUEVO MÉTODO para revisar préstamo pendiente ---

    def abrir_popup_corte(self, instance):
        layout = BoxLayout(orientation='vertical', spacing=10, padding=20)

        label = Label(text="¿Qué tipo de corte deseas realizar?", size_hint_y=None, height=40)
        btn_diario = Button(text="Corte Diario", size_hint_y=None, height=40)
        btn_semanal = Button(text="Corte Semanal", size_hint_y=None, height=40)
        btn_cancelar = Button(text="Cancelar", size_hint_y=None, height=40)

        layout.add_widget(label)
        layout.add_widget(btn_diario)
        layout.add_widget(btn_semanal)
        layout.add_widget(btn_cancelar)

        popup = Popup(title="Seleccionar corte", content=layout, size_hint=(None, None), size=(300, 300))

        def corte_diario(instance):
            popup.dismiss()
            print("Realizar corte diario")

            corte_screen = self.manager.get_screen("corte_diario")
            corte_screen.nombre_usuario = self.nombre_usuario  # Asignas el usuario actual aquí

            self.manager.current = "corte_diario"


        def corte_semanal(instance):
            popup.dismiss()
            # Aquí puedes llamar a una función o cambiar de pantalla
            self.manager.current = 'corte_semanal'

        btn_diario.bind(on_release=corte_diario)
        btn_semanal.bind(on_release=corte_semanal)
        btn_cancelar.bind(on_release=popup.dismiss)

        popup.open()


    def revisar_prestamo_pendiente(self):
        """
        Revisa si el empleado tiene un préstamo pendiente.
        Solo aplica si el login es de tipo empleado.
        """
        if self.origen_login != "empleado":
            return  # Solo empleados

        config_path = "data/config.json"
        if not os.path.exists(config_path):
            return

        store_config = JsonStore(config_path)
        if not store_config.exists("actual"):
            return

        ruta_tienda = store_config.get("actual").get("archivo")
        if not ruta_tienda or not os.path.exists(ruta_tienda):
            return

        store = JsonStore(ruta_tienda)
        empleados = store.get("empleados").get("lista", []) if store.exists("empleados") else []

        for emp in empleados:
            if emp.get("nombre") == self.nombre_usuario:
                prestamo = emp.get("prestamo", {})
                if prestamo.get("pendiente", False):
                    self.mostrar_popup_prestamo(prestamo.get("mensaje", ""))
                break

    # --- NUEVO MÉTODO para mostrar popup persistente ---
    def mostrar_popup_prestamo(self, mensaje):
        contenido = BoxLayout(orientation='vertical', padding=10, spacing=10)
        contenido.add_widget(Label(text=mensaje))
        btn_aceptar = Button(text='Aceptar', size_hint=(1, None), height=40)
        contenido.add_widget(btn_aceptar)

        self.popup_prestamo = Popup(title='Préstamo Pendiente', content=contenido,
                                   size_hint=(0.6, 0.4),
                                   auto_dismiss=False)  # No se cierra tocando afuera

        def aceptar_prestamo(instance):
            self.marcar_prestamo_como_atendido()
            self.popup_prestamo.dismiss()

        btn_aceptar.bind(on_release=aceptar_prestamo)
        self.popup_prestamo.open()

    def gestionar_empleados(self, instance):
        print("Ir a Gestión de Empleados")
        if not hasattr(self, "tienda_id") or not self.tienda_id:
            self.mostrar_popup("Error", "No hay tienda seleccionada.")
            return

        # Pasar la tienda seleccionada al screen de empleados
        ventana_emp = self.manager.get_screen("ventana_empleados")
        ventana_emp.set_tienda_id(self.tienda_id)  # Asignar la tienda
        ventana_emp.cargar_empleados_api()          # Cargar empleados desde API
        self.manager.current = "ventana_empleados"

    # --- NUEVO MÉTODO para marcar préstamo como atendido ---
    def marcar_prestamo_como_atendido(self):
        config_path = "data/config.json"
        if not os.path.exists(config_path):
            return

        store_config = JsonStore(config_path)
        if not store_config.exists("actual"):
            return

        ruta_tienda = store_config.get("actual")["archivo"]
        if not os.path.exists(ruta_tienda):
            return

        store = JsonStore(ruta_tienda)
        if not store.exists("empleados"):
            return

        empleados = store.get("empleados").get("lista", [])
        for emp in empleados:
            if emp.get("nombre") == self.nombre_usuario:
                if "prestamo" in emp:
                    emp["prestamo"]["pendiente"] = False
                break

        store.put("empleados", lista=empleados)

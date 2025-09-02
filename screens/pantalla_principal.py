from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.resources import resource_add_path
from kivy.clock import Clock
from kivy.graphics import Rectangle
from kivy.metrics import dp, sp
import os
import requests
from datetime import datetime

API_URL = "https://mi-caja-api.onrender.com/tiendas"

class VentanaPrincipal(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.nombre_usuario = ""
        self.origen_login = "patron"
        self.inicializado = False
        self.layout = FloatLayout()
        self.add_widget(self.layout)

    def on_pre_enter(self):
        # Limpiar todo siempre
        self.layout.clear_widgets()
        self.inicializado = True  # ya estamos inicializando

        # ------------------------
        # Fondo con canvas
        ruta_assets = os.path.join(os.path.dirname(__file__), "assets")
        resource_add_path(ruta_assets)

        with self.layout.canvas.before:
            self.fondo_rect = Rectangle(source="fondo.png", pos=self.layout.pos, size=self.layout.size)
        self.layout.bind(size=self._update_rect, pos=self._update_rect)

        self.cargar_tienda_api()
        # ------------------------
        # Nombre de la tienda
        self.nombre_tienda = "Tienda"
        if hasattr(self, "tienda_id") and self.tienda_id:
            try:
                url = f"{API_URL}/{self.tienda_id}"
                respuesta = requests.get(url)
                if respuesta.status_code == 200:
                    datos = respuesta.json()
                    self.nombre_tienda = datos.get("nombre", "Tienda").strip("*")
            except Exception as e:
                print("Error al obtener datos de la tienda:", e)

        self.label_tienda = Label(
            text=f"[b]{self.nombre_tienda}[/b]",
            font_size=sp(20),
            size_hint=(.9, None),
            height=dp(40),
            pos_hint={"x": 0.05, "top": 0.98},
            color=(0, 0, 0, 1),
            markup=True
        )
        self.layout.add_widget(self.label_tienda)

        # ------------------------
        # Nombre del usuario si es empleado
        if self.origen_login == "empleado" and self.nombre_usuario:
            self.label_usuario = Label(
                text=f"Hola, {self.nombre_usuario}",
                font_size=sp(16),
                size_hint=(.9, None),
                height=dp(30),
                pos_hint={"x": 0.05, "top": 0.90},
                color=(0, 0, 0, 1)
            )
            self.layout.add_widget(self.label_usuario)

        # ------------------------
        # Reloj
        self.label_hora = Label(
            text="",
            font_size=sp(18),
            size_hint=(.9, None),
            height=dp(30),
            pos_hint={"x": 0.05, "y": 0.02},
            color=(1, 1, 1, 1)
        )
        self.layout.add_widget(self.label_hora)
        Clock.schedule_interval(self.actualizar_hora, 1)

        # ------------------------
        # Botones principales con ScrollView
        scroll_layout = ScrollView(size_hint=(0.25, 0.75), pos_hint={"x": 0.02, "top": 0.85})
        grid_botones = GridLayout(cols=1, spacing=dp(10), size_hint_y=None)
        grid_botones.bind(minimum_height=grid_botones.setter('height'))

        botones_info = [
            ("Venta", self.abrir_venta),
            ("Venta\nInventario", self.abrir_venta_con_inventario),
            ("Inventario", self.ir_a_inventario),
            ("Corte", self.abrir_popup_corte),
            ("Registro\nde Cortes", self.ir_a_registro_cortes)
        ]

        for texto, callback in botones_info:
            btn = Button(
                text=texto,
                size_hint=(1, None),
                height=dp(50),
                font_size=sp(14),
                text_size=(None, dp(50)),
                halign='center',
                valign='middle'
            )
            btn.bind(on_release=callback)
            grid_botones.add_widget(btn)

        btn_cerrar_sesion = Button(
            text="Cerrar Sesión",
            size_hint=(1, None),
            height=dp(50),
            font_size=sp(14),
            text_size=(None, dp(50)),
            halign='center',
            valign='middle',
            background_color=(1, 0, 0, 1)
        )
        btn_cerrar_sesion.bind(on_release=self.cerrar_sesion)
        grid_botones.add_widget(btn_cerrar_sesion)

        # Registro Semanal solo para patrón
        if self.origen_login == "patron":
            btn_semana = Button(
                text="Registro\nSemanal",
                size_hint=(1, None),
                height=dp(50),
                font_size=sp(14),
                text_size=(None, dp(50)),
                halign='center',
                valign='middle'
            )
            btn_semana.bind(on_release=self.ir_a_registro_semanal)
            grid_botones.add_widget(btn_semana)

        # Botón Empleados solo si NO es empleado
        if self.origen_login != "empleado":
            btn_emp = Button(
                text="Empleados",
                size_hint=(1, None),
                height=dp(50),
                font_size=sp(14),
                text_size=(None, dp(50)),
                halign='center',
                valign='middle'
            )
            btn_emp.bind(on_release=self.gestionar_empleados)
            grid_botones.add_widget(btn_emp)

        scroll_layout.add_widget(grid_botones)
        self.layout.add_widget(scroll_layout)

        # ------------------------
        # Revisar préstamo pendiente
        self.revisar_prestamo_pendiente()

    def _update_rect(self, *args):
        self.fondo_rect.pos = self.layout.pos
        self.fondo_rect.size = self.layout.size

    def actualizar_hora(self, dt):
        ahora = datetime.now()
        self.label_hora.text = ahora.strftime("%H:%M:%S")
    

    # ------------------------
    # Métodos de popups adaptados a tamaño de pantalla
    def mostrar_popup(self, titulo, mensaje):
        contenido = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        contenido.add_widget(Label(text=mensaje, font_size=sp(14)))
        btn_cerrar = Button(text='Cerrar', size_hint=(1, None), height=dp(40), font_size=sp(14))
        contenido.add_widget(btn_cerrar)

        popup = Popup(title=titulo, content=contenido,
                      size_hint=(0.9, 0.6),
                      auto_dismiss=False)
        btn_cerrar.bind(on_release=popup.dismiss)
        popup.open()

    def cerrar_sesion(self, instance):
        # Limpiar variables de sesión
        self.nombre_usuario = ""
        self.tienda_id = None
        self.origen_login = ""
        self.inicializado = False  # 🔹 importante para reconstruir la pantalla
        self.layout.clear_widgets()  # Limpiar todo el layout

        # Mostrar popup de cierre
        contenido = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        contenido.add_widget(Label(text="Has cerrado sesión correctamente.", font_size=sp(14)))
        btn_cerrar = Button(text='Cerrar', size_hint=(1, None), height=dp(40), font_size=sp(14))
        contenido.add_widget(btn_cerrar)

        popup = Popup(title="Sesión cerrada", content=contenido,
                    size_hint=(0.6, 0.4), auto_dismiss=False)

        def cerrar_popup(instance_btn):
            popup.dismiss()
            self.manager.current = 'seleccion_rol'

        btn_cerrar.bind(on_release=cerrar_popup)
        popup.open()

    def mostrar_popup_confirmacion(self):
        contenido = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        contenido.add_widget(Label(text="Venta registrada correctamente.", font_size=sp(16)))

        btn_cerrar = Button(text='Cerrar', size_hint=(1, None), height=dp(40), font_size=sp(14))
        contenido.add_widget(btn_cerrar)

        popup = Popup(
            title='Confirmación',
            content=contenido,
            size_hint=(0.9, 0.5),
            auto_dismiss=False
        )

        btn_cerrar.bind(on_release=popup.dismiss)
        popup.open()


    def abrir_venta(self, instance):
        contenido = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))

        self.ventas_temporales = []

        self.grid_ventas = GridLayout(cols=2, size_hint_y=None, spacing=dp(5))
        self.grid_ventas.bind(minimum_height=self.grid_ventas.setter('height'))

        scroll_ventas = ScrollView(size_hint=(1, 0.5))
        scroll_ventas.add_widget(self.grid_ventas)
        contenido.add_widget(scroll_ventas)

        self.label_total = Label(text="TOTAL = $0.00", size_hint_y=None, height=dp(30), font_size=sp(14))
        contenido.add_widget(self.label_total)

        self.input_producto = TextInput(
            hint_text="Producto",
            multiline=False,
            size_hint=(1, None),
            height=dp(40),
            font_size=sp(14)
        )
        contenido.add_widget(self.input_producto)

        self.input_precio = TextInput(
            hint_text="Precio",
            multiline=False,
            input_filter='float',
            size_hint=(1, None),
            height=dp(40),
            font_size=sp(14)
        )
        contenido.add_widget(self.input_precio)

        btn_agregar_producto = Button(
            text="Agregar Producto",
            size_hint=(1, None),
            height=dp(40),
            font_size=sp(14)
        )
        contenido.add_widget(btn_agregar_producto)

        btn_registrar = Button(
            text="Registrar Venta",
            size_hint=(1, None),
            height=dp(40),
            font_size=sp(14)
        )
        contenido.add_widget(btn_registrar)

        popup = Popup(title="Registrar Venta", content=contenido, size_hint=(0.9, 0.9))

        # Funciones internas
        def actualizar_lista_productos():
            self.grid_ventas.clear_widgets()
            for prod, precio in self.ventas_temporales:
                label_prod = Label(
                    text=prod,
                    size_hint_y=None,
                    height=dp(30),
                    halign='left',
                    valign='middle',
                    font_size=sp(14)
                )
                label_prod.text_size = (label_prod.width, None)

                label_precio = Label(
                    text=f"${precio:.2f}",
                    size_hint_y=None,
                    height=dp(30),
                    halign='right',
                    valign='middle',
                    font_size=sp(14)
                )
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
            nonlocal popup
            if not self.ventas_temporales:
                self.mostrar_popup("Error", "No hay productos para registrar.")
                return

            import requests
            import json 

            payload = {
                "usuario": self.nombre_usuario,
                "fuera_inventario": True,
                "productos": [{"producto": p, "precio": pr, "cantidad": 1} for p, pr in self.ventas_temporales]
            }

            print("=== Enviando payload a la API ===")
            print(json.dumps(payload, indent=4))

            try:
                respuesta = requests.post(
                    f"https://mi-caja-api.onrender.com/tiendas/{self.tienda_id}/ventas/",
                    json=payload
                )

                if respuesta.status_code in (200, 201):
                    popup.dismiss()
                    self.ventas_temporales = []
                    self.mostrar_popup_confirmacion()
                elif respuesta.status_code == 422:
                    errores = respuesta.json().get("detail", [])
                    mensaje = "\n".join([f"{e.get('loc', '')}: {e.get('msg', '')}" for e in errores])
                    self.mostrar_popup("Error de Validación", mensaje or "Datos no válidos")
                else:
                    self.mostrar_popup("Error", f"Error desconocido: {respuesta.status_code}")

            except requests.exceptions.RequestException as e:
                self.mostrar_popup("Error", f"No se pudo conectar al servidor:\n{e}")

        # Asignar las funciones a los botones
        btn_agregar_producto.bind(on_release=agregar_producto)
        btn_registrar.bind(on_release=registrar_venta)

        popup.open()

    def guardar_venta(self, producto, precio, fuera_inventario=False):
        import os
        from datetime import datetime
        from kivy.storage.jsonstore import JsonStore

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

        # 🔹 Hora exacta del sistema
        fecha_local = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        nueva_venta = {
            "producto": producto,
            "usuario": self.nombre_usuario,
            "precio": precio,
            "fecha": fecha_local,
            "fuera_inventario": fuera_inventario
        }

        ventas.append(nueva_venta)
        store.put("ventas", lista=ventas)

        print(f"Venta registrada: {producto} - ${precio} - Hora: {fecha_local}")

    def configurar_sesion(self, empleado=None, tienda=None, tienda_id=None, nombre=None, origen=None):
        """Configura la sesión del empleado y la tienda en la pantalla principal"""
        self.empleado_actual = empleado
        self.tienda_actual = tienda
        if tienda_id is not None:
            self.tienda_id = tienda_id
        if nombre is not None:
            self.nombre_usuario = nombre
        if origen is not None:
            self.origen_login = origen

        print(f"Sesión iniciada para {nombre} en tienda {tienda_id} (origen={origen})")



    def ir_a_inventario(self, instance):
        self.manager.current = 'inventario'

    def ir_a_registro_semanal(self, instance):
        registro_screen = self.manager.get_screen("registro_semanal")
        registro_screen.set_tienda_id(self.tienda_id, self.nombre_usuario)
        self.manager.current = "registro_semanal"

    def realizar_corte(self, instance):
        print("Ir a Corte")

    def ir_a_corte_diario(self, instance):
        corte_screen = self.manager.get_screen("corte_diario")
        corte_screen.set_tienda_id(self.tienda_id, self.nombre_usuario)
        self.manager.current = "corte_diario"

    def ir_a_registro_cortes(self, instance):
        if not hasattr(self, "tienda_actual") or not self.tienda_actual:
            # Avisar al usuario
            print("No se ha seleccionado ninguna tienda")
            return

        registro_screen = self.manager.get_screen("registro_cortes")
        registro_screen.set_tienda_id(self.tienda_actual["id"])
        self.manager.current = "registro_cortes"
        

    def abrir_venta_con_inventario(self, instance):
        print("Ir a pantalla de Venta con Inventario")
        venta_inv_screen = self.manager.get_screen('venta_inventario')
        venta_inv_screen.set_tienda_id(self.tienda_id)
        venta_inv_screen.set_usuario(self.nombre_usuario)
        self.manager.current = 'venta_inventario'

    def set_tienda_id(self, tienda_id):
        self.tienda_id = tienda_id
        self.cargar_tienda_api() 


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
        contenido = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        contenido.add_widget(Label(text=mensaje, font_size=sp(14)))

        btn_cerrar = Button(text='Cerrar', size_hint=(1, None), height=dp(40), font_size=sp(14))
        contenido.add_widget(btn_cerrar)

        popup = Popup(title='Préstamo Realizado', content=contenido,
                    size_hint=(0.6, 0.4))
        btn_cerrar.bind(on_release=popup.dismiss)
        popup.open()

    def cargar_tienda_api(self):
        """Carga el nombre de la tienda desde la API usando self.tienda_id"""
        if not hasattr(self, "tienda_id") or not self.tienda_id:
            self.nombre_tienda = "Tienda"
            self.tienda_actual = None
            return False

        try:
            url = f"{API_URL}/{self.tienda_id}"
            respuesta = requests.get(url, timeout=5)
            respuesta.raise_for_status()
            datos = respuesta.json()
            self.nombre_tienda = datos.get("nombre", "Tienda").strip("*")
            self.tienda_actual = datos  # <--- aquí asignamos la tienda completa
            if hasattr(self, "label_tienda"):
                self.label_tienda.text = f"[b]{self.nombre_tienda}[/b]"
            return True
        except requests.RequestException as e:
            print("Error al cargar tienda desde API:", e)
            self.nombre_tienda = "Tienda"
            self.tienda_actual = None
            return False

    # --- NUEVO MÉTODO para revisar préstamo pendiente ---

    def abrir_popup_corte(self, instance):
        layout = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(20))

        label = Label(
            text="¿Qué tipo de corte deseas realizar?",
            size_hint_y=None,
            height=dp(40),
            font_size=sp(16)
        )
        btn_diario = Button(text="Corte Diario", size_hint_y=None, height=dp(40), font_size=sp(14))
        btn_semanal = Button(text="Corte Semanal", size_hint_y=None, height=dp(40), font_size=sp(14))
        btn_cancelar = Button(text="Cancelar", size_hint_y=None, height=dp(40), font_size=sp(14))

        layout.add_widget(label)
        layout.add_widget(btn_diario)
        layout.add_widget(btn_semanal)
        layout.add_widget(btn_cancelar)

        popup = Popup(
            title="Seleccionar corte",
            content=layout,
            size_hint=(0.8, 0.5),  # Adaptable al tamaño de pantalla
            auto_dismiss=False
        )

        def corte_diario(instance_btn):
            popup.dismiss()
            corte_screen = self.manager.get_screen("corte_diario")
            corte_screen.set_tienda_id(self.tienda_id, self.nombre_usuario)
            self.manager.current = "corte_diario"

        def corte_semanal(instance_btn):
            popup.dismiss()
            corte_screen = self.manager.get_screen("corte_semanal")
            # ✅ Pasar el ID de la tienda y el usuario
            corte_screen.set_tienda_id(self.tienda_id, self.nombre_usuario)
            self.manager.current = "corte_semanal"

        btn_diario.bind(on_release=corte_diario)
        btn_semanal.bind(on_release=corte_semanal)
        btn_cancelar.bind(on_release=popup.dismiss)

        popup.open()

    def revisar_prestamo_pendiente(self):
        """
        Revisa si el empleado tiene un préstamo pendiente desde la API.
        Solo aplica si el login es de tipo empleado.
        """
        if self.origen_login != "empleado" or not self.tienda_id:
            return  # Solo empleados con tienda asignada

        import requests
        try:
            url = f"https://mi-caja-api.onrender.com/tiendas/{self.tienda_id}/empleados/"
            respuesta = requests.get(url)
            if respuesta.status_code != 200:
                print(f"No se pudo obtener empleados: {respuesta.status_code}")
                return

            empleados = respuesta.json()
            for emp in empleados:
                if emp.get("nombre") == self.nombre_usuario:
                    prestamo = emp.get("prestamo", {})
                    if prestamo.get("pendiente", False):
                        mensaje = prestamo.get("mensaje", "Tienes un préstamo pendiente.")
                        self.mostrar_popup_prestamo(mensaje)
                    break

        except requests.exceptions.RequestException as e:
            print("Error al consultar API para préstamo:", e)


    def mostrar_popup_confirmacion(self):
        contenido = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        contenido.add_widget(Label(text="Venta registrada correctamente.", font_size=sp(14)))

        btn_cerrar = Button(text='Cerrar', size_hint=(1, None), height=dp(40), font_size=sp(14))
        contenido.add_widget(btn_cerrar)

        popup = Popup(
            title='Confirmación',
            content=contenido,
            size_hint=(0.6, 0.4),  # tamaño relativo a la pantalla
            auto_dismiss=False
        )
        btn_cerrar.bind(on_release=popup.dismiss)
        popup.open()

    # --- NUEVO MÉTODO para mostrar popup persistente ---
    def mostrar_popup_prestamo(self, mensaje):
        contenido = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        contenido.add_widget(Label(text=mensaje, font_size=sp(14)))

        btn_aceptar = Button(text='Aceptar', size_hint=(1, None), height=dp(40), font_size=sp(14))
        contenido.add_widget(btn_aceptar)

        self.popup_prestamo = Popup(
            title='Préstamo Pendiente',
            content=contenido,
            size_hint=(0.6, 0.4),  # tamaño relativo a la pantalla
            auto_dismiss=False  # No se cierra tocando afuera
        )

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
        """Marca el préstamo del empleado como atendido en la API."""
        if not self.tienda_id:
            return

        import requests
        try:
            url = f"https://mi-caja-api.onrender.com/tiendas/{self.tienda_id}/empleados/"
            resp = requests.get(url)
            resp.raise_for_status()
            empleados = resp.json()

            for emp in empleados:
                if emp.get("nombre") == self.nombre_usuario and emp.get("prestamo", {}).get("pendiente"):
                    emp_id = emp.get("id")
                    # PATCH para marcar el préstamo como atendido
                    patch_url = f"https://mi-caja-api.onrender.com/tiendas/{self.tienda_id}/empleados/{emp_id}"
                    payload = {"prestamo": {"pendiente": False}}
                    requests.patch(patch_url, json=payload)
                    break

        except Exception as e:
            print("Error al marcar préstamo como atendido en API:", e)

    def on_enter(self):
        # Solo empleados
        if self.origen_login == "empleado":
            self.revisar_prestamo_pendiente()

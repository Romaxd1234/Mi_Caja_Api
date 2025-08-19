from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
import requests

class VentanaEmpleados(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = FloatLayout()
        self.add_widget(self.layout)

        from kivy.uix.image import Image
        fondo = Image(source=r'C:\Users\USER\Documents\APP\APP\assets\fondo.png',
                      allow_stretch=True, keep_ratio=False,
                      size_hint=(1, 1), pos_hint={'x': 0, 'y': 0})
        self.layout.add_widget(fondo)

        self.contenedor = BoxLayout(orientation='vertical', padding=20, spacing=10,
                                    size_hint=(0.9, 0.9), pos_hint={'center_x': 0.5, 'center_y': 0.5})
        self.layout.add_widget(self.contenedor)

        # Botones arriba: agregar, editar, eliminar, notas, préstamos
        botones_layout = BoxLayout(size_hint=(1, None), height=40, spacing=10)
        self.contenedor.add_widget(botones_layout)

        self.btn_agregar = Button(text="Agregar Empleado")
        self.btn_editar = Button(text="Editar Empleado")
        self.btn_eliminar = Button(text="Eliminar Empleado")
        self.btn_prestamos = Button(text="Préstamos")
        self.btn_notas = Button(text="Notas")

        botones_layout.add_widget(self.btn_agregar)
        botones_layout.add_widget(self.btn_editar)
        botones_layout.add_widget(self.btn_eliminar)
        botones_layout.add_widget(self.btn_prestamos)
        botones_layout.add_widget(self.btn_notas)

        # Selector de empleados
        seleccion_layout = BoxLayout(size_hint=(1, None), height=40, spacing=10)
        self.contenedor.add_widget(seleccion_layout)
        seleccion_layout.add_widget(Label(text="Empleado:", size_hint=(None, 1), width=80))
        self.spinner_empleados = Spinner(text="Selecciona empleado", values=[], size_hint=(1, 1))
        seleccion_layout.add_widget(self.spinner_empleados)

        # Área para mostrar info del empleado
        self.empleados_layout = BoxLayout(orientation='vertical', spacing=10)
        self.contenedor.add_widget(self.empleados_layout)

        # Botón Volver abajo izquierda
        self.btn_volver = Button(text="Volver", size_hint=(0.2, None), height=40,
                                 pos_hint={'x': 0.02, 'y': 0.02})
        self.layout.add_widget(self.btn_volver)

        # Bindings
        self.btn_volver.bind(on_release=self.volver)
        self.btn_notas.bind(on_release=self.abrir_popup_notas)
        self.btn_agregar.bind(on_release=self.abrir_popup_agregar)
        self.btn_editar.bind(on_release=self.abrir_popup_editar)
        self.btn_eliminar.bind(on_release=self.eliminar_empleado_api)
        self.btn_prestamos.bind(on_release=self.abrir_popup_prestamo)
        self.spinner_empleados.bind(text=self.mostrar_info_empleado)

        # Variables para datos
        self.tienda_id = None
        self.api_base = "https://mi-caja-api.onrender.com/tiendas"
        self.empleados = []

    # -----------------------------
    # Asignar tienda
    # -----------------------------
    def set_tienda_id(self, tienda_id):
        self.tienda_id = tienda_id
        self.cargar_empleados_api()

    # -----------------------------
    # Cargar empleados desde API
    # -----------------------------
    def cargar_empleados_api(self):
        if not self.tienda_id:
            return
        try:
            resp = requests.get(f"{self.api_base}/{self.tienda_id}/empleados/")
            resp.raise_for_status()
            self.empleados = resp.json()
            nombres = [emp.get('nombre', '') for emp in self.empleados]
            self.spinner_empleados.values = nombres
            if nombres:
                self.spinner_empleados.text = nombres[0]
            else:
                self.spinner_empleados.text = "No hay empleados"
            self.mostrar_info_empleado(self.spinner_empleados, self.spinner_empleados.text)
        except Exception as e:
            self.mostrar_popup("Error", f"No se pudieron cargar los empleados: {e}")

    # -----------------------------
    # Mostrar info empleado
    # -----------------------------
    def mostrar_info_empleado(self, spinner, texto):
        self.empleados_layout.clear_widgets()
        emp = next((e for e in self.empleados if e.get('nombre') == texto), None)
        if not emp:
            self.empleados_layout.add_widget(Label(text="Seleccione un empleado"))
            return
        texto_info = f"Nombre: {emp.get('nombre', '')}\nPuesto: {emp.get('puesto', '')}\nSueldo: {emp.get('sueldo', '')}\nNota: {emp.get('nota', '')}"
        self.empleados_layout.add_widget(Label(text=texto_info, color=(0, 0, 0, 1)))

    # -----------------------------
    # Agregar / Editar
    # -----------------------------
    def abrir_popup_agregar(self, instance):
        self.popup_editar_agregar("Agregar Empleado")

    def abrir_popup_editar(self, instance):
        if not self.empleados:
            self.mostrar_popup("Aviso", "No hay empleados para editar.")
            return
        self.popup_editar_agregar("Editar Empleado", editar=True)

    def popup_editar_agregar(self, titulo, editar=False):
        contenido = BoxLayout(orientation='vertical', spacing=10, padding=10)
        input_nombre = TextInput(hint_text="Nombre", multiline=False)
        input_puesto = TextInput(hint_text="Puesto", multiline=False)
        input_sueldo = TextInput(hint_text="Sueldo", multiline=False)
        box_password = BoxLayout(size_hint_y=None, height=40, spacing=5)
        input_password = TextInput(hint_text="Contraseña", multiline=False, password=True)
        btn_ojito = Button(text="👁️", size_hint=(None, 1), width=40)
        btn_ojito.bind(on_release=lambda x: setattr(input_password, 'password', not input_password.password))
        box_password.add_widget(input_password)
        box_password.add_widget(btn_ojito)
        leyenda = Label(text="[i]Esta contraseña la debe teclear el usuario y sólo él tendrá acceso a ella.[/i]",
                        markup=True, font_size=12, size_hint_y=None, height=30, halign='center')
        leyenda.bind(size=leyenda.setter('text_size'))
        input_nota = TextInput(hint_text="Nota", multiline=True, size_hint_y=None, height=80)

        if editar:
            nombre_emp = self.spinner_empleados.text
            emp = next((e for e in self.empleados if e.get('nombre') == nombre_emp), None)
            if emp:
                input_nombre.text = emp.get('nombre', '')
                input_puesto.text = emp.get('puesto', '')
                input_sueldo.text = str(emp.get('sueldo', ''))
                input_nota.text = emp.get('nota', '')
                input_password.text = emp.get('password', '')

        contenido.add_widget(input_nombre)
        contenido.add_widget(input_puesto)
        contenido.add_widget(input_sueldo)
        contenido.add_widget(box_password)
        contenido.add_widget(leyenda)
        contenido.add_widget(input_nota)

        btn_guardar = Button(text="Guardar", size_hint=(1, None), height=40)
        contenido.add_widget(btn_guardar)
        popup = Popup(title=titulo, content=contenido, size_hint=(0.7, 0.8))

        def guardar(instance):
            nombre = input_nombre.text.strip()
            puesto = input_puesto.text.strip()
            sueldo = input_sueldo.text.strip()
            nota = input_nota.text.strip()
            password = input_password.text.strip()
            if not nombre:
                self.mostrar_popup("Error", "El nombre es obligatorio.")
                return
            self.guardar_empleado_api(nombre, puesto, sueldo, password, nota, editar)
            popup.dismiss()

        btn_guardar.bind(on_release=guardar)
        popup.open()

    # -----------------------------
    # Guardar / Editar empleado
    # -----------------------------
    def guardar_empleado_api(self, nombre, puesto, sueldo, password, nota, editar=False):
        if not self.tienda_id:
            self.mostrar_popup("Error", "No hay tienda seleccionada")
            return

        # Validar sueldo
        try:
            sueldo_val = float(sueldo)
        except ValueError:
            sueldo_val = 0.0

        params = {
            "nombre": nombre,
            "puesto": puesto,
            "sueldo": sueldo_val,
            "password": password,
            "nota": nota
        }

        try:
            if editar:
                emp = next((e for e in self.empleados if e['nombre'] == self.spinner_empleados.text), None)
                if not emp:
                    self.mostrar_popup("Error", "Empleado no encontrado para editar")
                    return
                emp_id = emp['id']
                url = f"{self.api_base}/{self.tienda_id}/empleados/{emp_id}/"
                resp = requests.put(url, params=params)
            else:
                url = f"{self.api_base}/{self.tienda_id}/empleados/"
                resp = requests.post(url, params=params)

            resp.raise_for_status()
            self.cargar_empleados_api()
            self.mostrar_popup("Éxito", f"Empleado {'editado' if editar else 'guardado'} correctamente.")

        except requests.exceptions.HTTPError as http_err:
            try:
                error_detalle = resp.json()
            except:
                error_detalle = str(http_err)
            self.mostrar_popup("Error", f"No se pudo guardar el empleado:\n{error_detalle}")
        except Exception as e:
            self.mostrar_popup("Error", f"No se pudo guardar el empleado:\n{e}")

    # -----------------------------
    # Eliminar empleado
    # -----------------------------
    def eliminar_empleado_api(self, instance):
        if not self.empleados:
            self.mostrar_popup("Aviso", "No hay empleados para eliminar.")
            return
        nombre_emp = self.spinner_empleados.text
        emp = next((e for e in self.empleados if e['nombre'] == nombre_emp), None)
        if not emp:
            self.mostrar_popup("Error", "Empleado no encontrado.")
            return
        try:
            emp_id = emp['id']
            resp = requests.delete(f"{self.api_base}/{self.tienda_id}/empleados/{emp_id}/")
            resp.raise_for_status()
            self.cargar_empleados_api()
            self.mostrar_popup("Éxito", "Empleado eliminado correctamente.")
        except Exception as e:
            self.mostrar_popup("Error", f"No se pudo eliminar el empleado: {e}")

    # -----------------------------
    # Popups Notas / Préstamos
    # -----------------------------
    def abrir_popup_notas(self, instance):
        if not self.empleados:
            self.mostrar_popup("Aviso", "No hay empleados para agregar notas.")
            return
        contenido = BoxLayout(orientation='vertical', spacing=10, padding=10)
        spinner_empleados = Spinner(
            text=self.empleados[0]['nombre'],
            values=[emp['nombre'] for emp in self.empleados],
            size_hint=(1, None), height=44
        )
        contenido.add_widget(Label(text="Selecciona empleado:"))
        contenido.add_widget(spinner_empleados)
        input_nota = TextInput(text="", multiline=True, size_hint=(1, None), height=100, hint_text="Escribe la nota aquí")
        contenido.add_widget(Label(text="Nota:"))
        contenido.add_widget(input_nota)
        btn_guardar = Button(text="Guardar", size_hint=(1, None), height=40)
        contenido.add_widget(btn_guardar)
        popup = Popup(title="Notas de Empleado", content=contenido, size_hint=(0.7, 0.6))

        def cargar_nota_empleado(spinner, text):
            for emp in self.empleados:
                if emp['nombre'] == text:
                    input_nota.text = emp.get('nota', '')
                    break
        spinner_empleados.bind(text=cargar_nota_empleado)

        def guardar_nota(instance):
            nombre_emp = spinner_empleados.text
            nota = input_nota.text.strip()
            emp = next((e for e in self.empleados if e['nombre'] == nombre_emp), None)
            if emp:
                emp['nota'] = nota
                self.guardar_empleado_api(emp['nombre'], emp['puesto'], emp['sueldo'], emp.get('password',''), nota, editar=True)
            popup.dismiss()

        btn_guardar.bind(on_release=guardar_nota)
        cargar_nota_empleado(spinner_empleados, spinner_empleados.text)
        popup.open()

    def abrir_popup_prestamo(self, instance):
        contenido = BoxLayout(orientation='vertical', spacing=10, padding=10)
        label = Label(text='Préstamo a empleado')
        self.input_cantidad = TextInput(hint_text='Cantidad', input_filter='float', multiline=False)
        btn_hacer_prestamo = Button(text='Hacer préstamo')
        btn_hacer_prestamo.bind(on_release=self.hacer_prestamo)
        contenido.add_widget(label)
        contenido.add_widget(self.input_cantidad)
        contenido.add_widget(btn_hacer_prestamo)
        self.popup_prestamo = Popup(title='Nuevo préstamo', content=contenido,
                                    size_hint=(0.8, 0.5), auto_dismiss=True)
        self.popup_prestamo.open()

    def hacer_prestamo(self, instance):
        cantidad = self.input_cantidad.text.strip()
        nombre_emp = self.spinner_empleados.text
        if cantidad and nombre_emp and nombre_emp != "No hay empleados":
            mensaje = f"Se le ha realizado un préstamo de ${cantidad} a {nombre_emp}"
            pantalla_principal = self.manager.get_screen("pantalla_principal")
            pantalla_principal.mostrar_alerta_prestamo(mensaje)
        self.popup_prestamo.dismiss()

    # -----------------------------
    # Popups genéricos
    # -----------------------------
    def mostrar_popup(self, titulo, mensaje):
        contenido = BoxLayout(orientation='vertical', spacing=10, padding=10)
        contenido.add_widget(Label(text=mensaje))
        btn_cerrar = Button(text="Cerrar", size_hint=(1, None), height=40)
        contenido.add_widget(btn_cerrar)
        popup = Popup(title=titulo, content=contenido, size_hint=(0.6, 0.4))
        btn_cerrar.bind(on_release=popup.dismiss)
        popup.open()

    # -----------------------------
    # Volver a pantalla principal
    # -----------------------------
    def volver(self, instance):
        self.manager.current = "pantalla_principal"

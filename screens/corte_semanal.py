from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.storage.jsonstore import JsonStore
from kivy.clock import Clock
from kivy.uix.image import Image
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.graphics.texture import Texture
from kivy.uix.gridlayout import GridLayout
from kivy.uix.widget import Widget
import shutil
import os
import json
from datetime import datetime
import calendar

class CorteSemanalScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.carpeta_cortes = "data/cortes"
        self.carpeta_tiendas = "data/tiendas"
        self.prestamos_pendientes = {}
        self.pagos_prestamos_temp = {}

        self.fondo = Image(source="assets/fondo.png", allow_stretch=True, keep_ratio=False)
        self.add_widget(self.fondo)

        self.main_layout = BoxLayout(orientation='horizontal', padding=10, spacing=10)
        self.add_widget(self.main_layout)

        self.layout_izquierdo = BoxLayout(orientation='vertical', size_hint_x=0.4, spacing=10)
        self.layout_derecho = BoxLayout(orientation='vertical', size_hint_x=0.6, spacing=10)

        self.main_layout.add_widget(self.layout_izquierdo)
        self.main_layout.add_widget(self.layout_derecho)

        # Por defecto, mostramos vista cortes (no prestamos)
        self.mostrar_vista_cortes()

    def mostrar_vista_cortes(self, *args):
        self.layout_izquierdo.clear_widgets()
        self.layout_derecho.clear_widgets()

        # Botones en la izquierda abajo
        btn_prestamos = Button(text="Préstamos", size_hint_y=None, height=50)
        btn_volver = Button(text="Volver", size_hint_y=None, height=50)
        btn_prestamos.bind(on_release=self.mostrar_vista_prestamos)
        btn_volver.bind(on_release=self.volver_pantalla_principal)

        self.layout_izquierdo.add_widget(Widget())  # Relleno para empujar botones abajo
        self.layout_izquierdo.add_widget(btn_prestamos)
        self.layout_izquierdo.add_widget(btn_volver)

        # Lado derecho: Total y botón cerrar corte
        self.total_label = Label(text="Total Semana: $0.00", size_hint_y=None, height=40)
        btn_cerrar = Button(text="Cerrar Corte", size_hint_y=None, height=50)
        btn_cerrar.bind(on_release=self.cerrar_corte)

        self.layout_derecho.add_widget(Widget())  # Espacio para arriba
        self.layout_derecho.add_widget(self.total_label)
        self.layout_derecho.add_widget(btn_cerrar)

        # Aquí carga gráfica y tabla con info
        self.cargar_grafica_y_tabla()

    def cargar_grafica_y_tabla(self):
        self.layout_derecho.clear_widgets()

        if not os.path.exists(self.carpeta_cortes):
            os.makedirs(self.carpeta_cortes)

        archivos = [f for f in os.listdir(self.carpeta_cortes) if f.endswith('.json')]
        archivos.sort()

        if not archivos:
            self.layout_derecho.add_widget(Label(text="No hay cortes guardados aún"))
            return

        # Layout vertical principal
        layout_vertical = BoxLayout(orientation='vertical', spacing=10)

        # Grid con 4 columnas para la tabla
        grid = GridLayout(cols=4, size_hint_y=None, spacing=5)
        grid.bind(minimum_height=grid.setter('height'))

        # Encabezados
        encabezados = ["Día", "Fecha", "Empleado", "Total"]
        for encabezado in encabezados:
            lbl = Label(text=f"[b]{encabezado}[/b]", markup=True, size_hint_y=None, height=30)
            grid.add_widget(lbl)

        total_general = 0

        for archivo in archivos:
            ruta = os.path.join(self.carpeta_cortes, archivo)
            with open(ruta, 'r', encoding='utf-8') as f:
                data = json.load(f)

            fecha_str = data.get("fecha", "")
            fecha_obj = None
            try:
                fecha_obj = datetime.strptime(fecha_str, "%Y-%m-%d")
                dia_semana = calendar.day_name[fecha_obj.weekday()]
            except:
                dia_semana = "Desconocido"

            empleado = data.get("usuario_que_corto", "Desconocido")
            total = float(data.get("total", 0))
            total_general += total

            # Añadir fila
            grid.add_widget(Label(text=dia_semana, size_hint_y=None, height=30))
            grid.add_widget(Label(text=fecha_str, size_hint_y=None, height=30))
            grid.add_widget(Label(text=empleado, size_hint_y=None, height=30))
            grid.add_widget(Label(text=f"${total:.2f}", size_hint_y=None, height=30))

        # ScrollView para la tabla
        scroll = ScrollView(size_hint=(1, 1))
        scroll.add_widget(grid)

        layout_vertical.add_widget(scroll)

        # Layout horizontal para total y botón cerrar corte
        layout_botones = BoxLayout(size_hint_y=None, height=50, spacing=10)

        lbl_total = Label(text=f"Total General: ${total_general:.2f}", size_hint_x=0.7, halign='right', valign='middle')
        lbl_total.bind(size=lbl_total.setter('text_size'))  # para que respete el halign

        btn_cerrar_corte = Button(text="Cerrar Corte", size_hint_x=0.3)
        btn_cerrar_corte.bind(on_release=self.cerrar_corte)

        layout_botones.add_widget(lbl_total)
        layout_botones.add_widget(btn_cerrar_corte)

        layout_vertical.add_widget(layout_botones)

        self.layout_derecho.add_widget(layout_vertical)


            # ... sigue con tu código normal ...
    def obtener_ruta_tienda(self):
        config_path = r"C:\Users\fabiola gomey martin\Documents\APP\data\config.json"
        if not os.path.exists(config_path):
            return None
        store_config = JsonStore(config_path)
        if not store_config.exists("actual"):
            return None
        archivo_tienda = store_config.get("actual")["archivo"]
        if not os.path.isabs(archivo_tienda):
            archivo_tienda = os.path.join(r"C:\Users\fabiola gomey martin\Documents\APP", archivo_tienda)
        if not os.path.exists(archivo_tienda):
            return None
        return archivo_tienda

    def mostrar_vista_prestamos(self, *args):
        from kivy.uix.textinput import TextInput
        from kivy.uix.widget import Widget
        self.layout_izquierdo.clear_widgets()
        self.layout_derecho.clear_widgets()

        # Botón Volver a cortes
        btn_volver = Button(text="Volver", size_hint_y=None, height=50)
        btn_volver.bind(on_release=self.mostrar_vista_cortes)
        self.layout_izquierdo.add_widget(Widget())  # empuja botón abajo
        self.layout_izquierdo.add_widget(btn_volver)

        ruta_tienda = self.obtener_ruta_tienda()
        if not ruta_tienda or not os.path.exists(ruta_tienda):
            self.layout_derecho.add_widget(Label(text="No se encontró el archivo de tienda"))
            return

        with open(ruta_tienda, 'r', encoding='utf-8') as f:
            data_tienda = json.load(f)

        empleados = data_tienda.get("empleados", {}).get("lista", [])

        prestamos_layout = BoxLayout(orientation='vertical', size_hint_y=None, spacing=10)
        prestamos_layout.bind(minimum_height=prestamos_layout.setter('height'))

        scroll = ScrollView()
        scroll.add_widget(prestamos_layout)
        self.layout_derecho.add_widget(scroll)

        for emp in empleados:
            prestamo_info = emp.get("prestamo", {})
            # Puede ser dict o número
            if isinstance(prestamo_info, dict):
                cantidad = float(prestamo_info.get("cantidad", 0))
                pendiente = prestamo_info.get("pendiente", False)
            else:
                cantidad = float(prestamo_info)
                pendiente = False

            if cantidad > 0:
                fila = BoxLayout(size_hint_y=None, height=40, spacing=5, padding=5)

                lbl_nombre = Label(text=emp.get("nombre", "Desconocido"), size_hint_x=0.3)
                lbl_prestamo = Label(text=f"${cantidad:,.2f}", size_hint_x=0.3)

                input_pago = TextInput(text="", multiline=False, input_filter='float', size_hint_x=0.2)
                btn_pagar = Button(text="Pagar", size_hint_x=0.2)

                fila.add_widget(lbl_nombre)
                fila.add_widget(lbl_prestamo)
                fila.add_widget(input_pago)
                fila.add_widget(btn_pagar)

                prestamos_layout.add_widget(fila)

                def pagar_prestamo(instance, empleado=emp, input_pago=input_pago, btn=btn_pagar):
                    pago_texto = input_pago.text.strip()
                    if pago_texto == "":
                        return
                    try:
                        pago_val = float(pago_texto)
                    except ValueError:
                        return

                    prestamo_actual = float(empleado.get("prestamo", {}).get("cantidad", "0") if isinstance(empleado.get("prestamo", {}), dict) else empleado.get("prestamo", 0))

                    if pago_val > prestamo_actual:
                        pago_val = prestamo_actual  # no permitir pagar más que la deuda

                    nuevo_prestamo = prestamo_actual - pago_val

                    # Actualizar el préstamo en el JSON
                    if isinstance(empleado.get("prestamo", {}), dict):
                        empleado["prestamo"]["cantidad"] = str(nuevo_prestamo)
                        if nuevo_prestamo == 0:
                            empleado["prestamo"]["pendiente"] = False
                    else:
                        empleado["prestamo"] = nuevo_prestamo

                    # Aquí puedes agregar cualquier lógica extra que uses para guardar cambios
                    # Ejemplo: guardar el JSON en disco
                    with open(ruta_tienda, 'w', encoding='utf-8') as f_tienda:
                        json.dump(data_tienda, f_tienda, indent=4, ensure_ascii=False)

                    # Sumar pago temporal para corte semanal
                    self.pagos_prestamos_temp[empleado["nombre"]] = self.pagos_prestamos_temp.get(empleado["nombre"], 0) + pago_val


                    input_pago.text = ""
                    btn.disabled = True

                    # Refrescar la vista para actualizar valores
                    self.mostrar_vista_prestamos()

                btn_pagar.bind(on_release=pagar_prestamo)


    def guardar_prestamos(self, data_tienda):
        # Guarda el json actualizado de la tienda con prestamos pagados parcialmente
        ruta = self.obtener_ruta_tienda()
        if ruta:
            with open(ruta, 'w', encoding='utf-8') as f:
                json.dump(data_tienda, f, indent=4, ensure_ascii=False)

    def set_ruta_tienda(self, ruta):
        self.ruta_tienda = ruta


    def volver_pantalla_principal(self, instance=None):
        self.manager.current = 'pantalla_principal'

    def set_ruta_tienda(self, ruta):
        self.ruta_tienda = ruta

    def cerrar_corte(self, instance):
        # Cargar archivos de cortes diarios
        archivos_cortes = [f for f in os.listdir(self.carpeta_cortes) if f.endswith('.json')]
        archivos_cortes.sort()

        # Cargar JSON de tienda para sueldos
        ruta_tienda = self.obtener_ruta_tienda()
        data_tienda = {}
        sueldos_total = 0
        sueldos_texto = ""
        if ruta_tienda and os.path.exists(ruta_tienda):
            with open(ruta_tienda, 'r', encoding='utf-8') as f:
                data_tienda = json.load(f)
                empleados = data_tienda.get("empleados", {}).get("lista", [])
                for emp in empleados:
                    nombre = emp.get("nombre", "Desconocido")
                    sueldo = float(emp.get("sueldo", "0"))
                    sueldos_total += sueldo
                    sueldos_texto += f"{nombre:<12}   -   ${sueldo:,.2f}\n"
        else:
            empleados = []

        # Preparar texto con días y totales
        dias_texto = ""
        total_ventas = 0
        for idx, archivo in enumerate(archivos_cortes, 1):
            ruta = os.path.join(self.carpeta_cortes, archivo)
            with open(ruta, 'r', encoding='utf-8') as f:
                data = json.load(f)
                total = float(data.get("total", "0"))
                total_ventas += total
                dias_texto += f"Día {idx:<6}   +   ${total:,.2f}\n"

        # Texto de préstamos pagados esta semana (pagos temporales)
        prestamos_texto = ""
        total_prestamos_pagados = 0
        if self.pagos_prestamos_temp:
            prestamos_texto = "\nPréstamos Pagados:\n"
            for nombre_emp, pago in self.pagos_prestamos_temp.items():
                prestamos_texto += f"{nombre_emp:<12}   +   ${pago:,.2f}\n"
                total_prestamos_pagados += pago

        # Calcular ganancias totales (ventas - sueldos + prestamos pagados)
        total_ganancias = total_ventas - sueldos_total + total_prestamos_pagados

        resumen_texto = (
            "Resumen Corte Semanal:\n\n"
            + dias_texto
            + "\n"
            + sueldos_texto
            + prestamos_texto
            + f"\nTOTAL GANANCIAS = ${total_ganancias:,.2f}"
        )

        # Construir popup con BoxLayout vertical
        popup_content = BoxLayout(orientation='vertical', spacing=10, padding=10)

        # Label con texto detallado, usar Label con text_size para texto multilínea
        label_resumen = Label(
            text=resumen_texto,
            halign='left',
            valign='top',
            size_hint_y=None
        )
        # Ajustamos altura según el texto
        label_resumen.bind(
            texture_size=lambda instance, value: setattr(instance, 'height', value[1])
        )

        popup_content.add_widget(label_resumen)

        # Layout horizontal para botones
        botones_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=40, spacing=10)
        btn_volver = Button(text="Volver", size_hint=(0.5, 1), font_size=14)
        btn_confirmar = Button(text="Confirmar", size_hint=(0.5, 1), font_size=14)
        botones_layout.add_widget(btn_volver)
        botones_layout.add_widget(btn_confirmar)

        popup_content.add_widget(botones_layout)

        popup = Popup(
            title="Confirmar Corte Semanal",
            content=popup_content,
            size_hint=(0.8, 0.7),
            auto_dismiss=False
        )

        btn_volver.bind(on_release=popup.dismiss)

        def confirmar(instance_btn):
            # Crear carpetas históricas si no existen
            carpeta_cortes_usados = os.path.join(os.path.dirname(self.carpeta_cortes), "cortes_usados")
            carpeta_cortes_semanales = os.path.join(os.path.dirname(self.carpeta_cortes), "cortes_semanales")
            os.makedirs(carpeta_cortes_usados, exist_ok=True)
            os.makedirs(carpeta_cortes_semanales, exist_ok=True)

            # Mover archivos de cortes a cortes_usados
            for archivo in archivos_cortes:
                origen = os.path.join(self.carpeta_cortes, archivo)
                destino = os.path.join(carpeta_cortes_usados, archivo)
                shutil.move(origen, destino)

            # Guardar registro resumen en cortes_semanales con fecha y hora
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            resumen_path = os.path.join(carpeta_cortes_semanales, f"resumen_corte_{timestamp}.json")
            resumen_data = {
                "fecha_cierre": timestamp,
                "num_cortes": len(archivos_cortes),
                "total_ventas_semana": total_ventas,
                "total_sueldos": sueldos_total,
                "total_prestamos_pagados": total_prestamos_pagados,
                "total_ganancias": total_ganancias,
                "pagos_prestamos": self.pagos_prestamos_temp
            }
            with open(resumen_path, 'w', encoding='utf-8') as f_res:
                json.dump(resumen_data, f_res, indent=4, ensure_ascii=False)

            # Actualizar el archivo JSON de tienda con los préstamos pagados
            if ruta_tienda and os.path.exists(ruta_tienda):
                with open(ruta_tienda, 'r', encoding='utf-8') as f_tienda:
                    data_tienda = json.load(f_tienda)
                for nombre_empleado, pago in self.pagos_prestamos_temp.items():
                    for emp in data_tienda.get("empleados", {}).get("lista", []):
                        if emp.get("nombre") == nombre_empleado:
                            prestamo_actual = float(emp.get("prestamo", {}).get("cantidad", "0"))
                            nuevo_prestamo = max(prestamo_actual - pago, 0)
                            emp["prestamo"]["cantidad"] = str(nuevo_prestamo)
                            if nuevo_prestamo == 0:
                                emp["prestamo"]["pendiente"] = False
                            break
                with open(ruta_tienda, 'w', encoding='utf-8') as f_tienda:
                    json.dump(data_tienda, f_tienda, indent=4, ensure_ascii=False)

            # Limpiar pagos temporales y refrescar vista
            self.pagos_prestamos_temp.clear()
            self.mostrar_vista_cortes()

            popup.dismiss()

        btn_confirmar.bind(on_release=confirmar)

        popup.open()

    def on_enter(self):
        self.mostrar_vista_cortes()
        

    def on_leave(self):
        if hasattr(self, 'evento_actualizacion'):
            Clock.unschedule(self.evento_actualizacion)
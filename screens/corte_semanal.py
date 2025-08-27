from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
from kivy.uix.image import Image
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.resources import resource_add_path
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.graphics import Rectangle
import requests
import calendar
import os
from datetime import datetime

API_BASE = "https://mi-caja-api.onrender.com/tiendas"  # Cambia al host real


class CorteSemanalScreen(Screen):
    def __init__(self, tienda_id=1, **kwargs):
        super().__init__(**kwargs)
        self.tienda_id = tienda_id
        self.pagos_prestamos_temp = {}

        resource_add_path(os.path.join(os.path.dirname(__file__), "assets"))

        # Fondo con canvas
        with self.canvas.before:
            self.fondo_rect = Rectangle(source="fondo.png", pos=self.pos, size=self.size)
        self.bind(size=self._update_rect, pos=self._update_rect)

        # Layout principal vertical
        self.main_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        self.add_widget(self.main_layout)

        # Por defecto, vista cortes
        self.mostrar_vista_cortes()

    def _update_rect(self, *args):
        self.fondo_rect.pos = self.pos
        self.fondo_rect.size = self.size

    # ---------------------
    # FUNCIONES API
    # ---------------------

    def obtener_cortes_diarios(self):
        try:
            resp = requests.get(f"{API_BASE}/{self.tienda_id}/cortes/diarios")
            if resp.status_code == 200:
                return resp.json()
        except:
            pass
        return []

    def obtener_empleados(self):
        try:
            resp = requests.get(f"{API_BASE}/{self.tienda_id}/empleados/")
            if resp.status_code == 200:
                return resp.json()
        except:
            pass
        return []

    def actualizar_prestamo(self, empleado_id, prestamo_id, nuevo_prestamo, pendiente):
        data = {"prestamos": [{"id": prestamo_id, "cantidad": str(nuevo_prestamo), "pendiente": pendiente}]}
        try:
            resp = requests.put(f"{API_BASE}/{self.tienda_id}/empleados/{empleado_id}", json=data)
            return resp.status_code == 200
        except:
            return False

    # ---------------------
    # VISTA PRINCIPAL DE CORTES
    # ---------------------
    def mostrar_vista_cortes(self, *args):
        self.main_layout.clear_widgets()

        cortes_diarios = self.obtener_cortes_diarios()
        if not cortes_diarios:
            self.main_layout.add_widget(Label(text="No hay cortes guardados aún"))
            return

        # ScrollView con GridLayout de 4 columnas
        grid = GridLayout(cols=4, size_hint_y=None, spacing=5)
        grid.bind(minimum_height=grid.setter('height'))

        encabezados = ["Día", "Fecha", "Empleado", "Total"]
        for h in encabezados:
            grid.add_widget(Label(text=f"[b]{h}[/b]", markup=True, size_hint_y=None, height=30))

        total_general = 0
        for idx, corte in enumerate(cortes_diarios, 1):
            fecha_str = corte.get("fecha", "")
            try:
                fecha_obj = datetime.strptime(fecha_str, "%Y-%m-%d")
                dia_semana = calendar.day_name[fecha_obj.weekday()]
            except:
                dia_semana = "Desconocido"
            empleado = corte.get("usuario_que_corto", "Desconocido")
            total = float(corte.get("total", 0))
            total_general += total

            grid.add_widget(Label(text=dia_semana, size_hint_y=None, height=30))
            grid.add_widget(Label(text=fecha_str, size_hint_y=None, height=30))
            grid.add_widget(Label(text=empleado, size_hint_y=None, height=30))
            grid.add_widget(Label(text=f"${total:.2f}", size_hint_y=None, height=30))

        scroll = ScrollView(size_hint=(1, 1))
        scroll.add_widget(grid)
        self.main_layout.add_widget(scroll)

        # Footer horizontal
        footer = BoxLayout(size_hint_y=None, height=50, spacing=10, padding=5)

        # Botones izquierda
        btn_prestamos = Button(text="Préstamos", size_hint_x=None, width=120)
        btn_volver = Button(text="Volver", size_hint_x=None, width=120)
        btn_prestamos.bind(on_release=self.mostrar_vista_prestamos)
        btn_volver.bind(on_release=self.volver_pantalla_principal)
        left_box = BoxLayout(orientation='vertical', size_hint_x=0.5, spacing=5)
        left_box.add_widget(btn_prestamos)
        left_box.add_widget(btn_volver)


        # Label total y botón corte derecha
        lbl_total = Label(text=f"Total General: ${total_general:.2f}", halign='right', valign='middle')
        lbl_total.bind(size=lbl_total.setter('text_size'))
        btn_corte = Button(text="Corte", size_hint_x=None, width=100)
        btn_corte.bind(on_release=self.cerrar_corte)
        right_box = BoxLayout(size_hint_x=0.5, spacing=5)
        right_box.add_widget(lbl_total)
        right_box.add_widget(btn_corte)

        footer.add_widget(left_box)
        footer.add_widget(right_box)
        self.main_layout.add_widget(footer)

    # ---------------------
    # VISTA PRÉSTAMOS
    # ---------------------
    def mostrar_vista_prestamos(self, *args):
        self.main_layout.clear_widgets()

        empleados = self.obtener_empleados()
        prestamos_layout = BoxLayout(orientation='vertical', size_hint_y=None, spacing=10)
        prestamos_layout.bind(minimum_height=prestamos_layout.setter('height'))
        scroll = ScrollView()
        scroll.add_widget(prestamos_layout)
        self.main_layout.add_widget(scroll)

        # Botón Volver
        btn_volver = Button(text="Volver", size_hint_y=None, height=50)
        btn_volver.bind(on_release=self.mostrar_vista_cortes)
        self.main_layout.add_widget(btn_volver)

        for emp in empleados:
            prestamo_info = emp.get("prestamos", [])
            if not prestamo_info:
                continue
            prestamo = prestamo_info[0]
            cantidad = float(prestamo.get("cantidad", 0))
            pendiente = prestamo.get("pendiente", False)
            prestamo_id = prestamo.get("id")

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

                def pagar_prestamo(instance, empleado=emp, prestamo=prestamo,
                                    input_pago=input_pago, lbl_prestamo=lbl_prestamo):
                    pago_texto = input_pago.text.strip()
                    if not pago_texto:
                        return
                    pago_val = float(pago_texto)
                    pago_val = min(pago_val, float(prestamo.get("cantidad", 0)))
                    nuevo_prestamo = float(prestamo.get("cantidad", 0)) - pago_val
                    pendiente_nuevo = nuevo_prestamo > 0

                    exito = self.actualizar_prestamo(empleado["id"], prestamo.get("id"), nuevo_prestamo, pendiente_nuevo)
                    if exito:
                        self.pagos_prestamos_temp[empleado["nombre"]] = self.pagos_prestamos_temp.get(empleado["nombre"], 0) + pago_val
                        lbl_prestamo.text = f"${nuevo_prestamo:,.2f}"
                        input_pago.text = ""
                        if nuevo_prestamo <= 0:
                            btn_pagar.disabled = True

                btn_pagar.bind(on_release=pagar_prestamo)

    # ---------------------
    # CERRAR CORTE
    # ---------------------
    def cerrar_corte(self, instance):
        cortes_diarios = self.obtener_cortes_diarios()
        empleados = self.obtener_empleados()

        # -----------------------------
        # Calcular totales y resumen
        # -----------------------------
        dias_texto = ""
        total_ventas = 0
        for idx, corte in enumerate(cortes_diarios, 1):
            total = float(corte.get("total", 0))
            total_ventas += total
            dias_texto += f"Día {idx:<6}   +   ${total:,.2f}\n"

        sueldos_total = sum(float(emp.get("sueldo", 0)) for emp in empleados)
        sueldos_texto = "\n".join(f"{emp.get('nombre', 'Desconocido'):<12}   -   ${float(emp.get('sueldo',0)):,.2f}" for emp in empleados)

        prestamos_texto = ""
        total_prestamos_pagados = 0
        if self.pagos_prestamos_temp:
            prestamos_texto = "\nPréstamos Pagados:\n"
            for nombre_emp, pago in self.pagos_prestamos_temp.items():
                prestamos_texto += f"{nombre_emp:<12}   +   ${pago:,.2f}\n"
                total_prestamos_pagados += pago

        total_ganancias = total_ventas - sueldos_total + total_prestamos_pagados

        resumen_texto = (
            "Resumen Corte Semanal:\n\n"
            f"{dias_texto}\n"
            f"Sueldos:\n{sueldos_texto}\n"
            f"{prestamos_texto}\n"
            f"Total Ganancias: ${total_ganancias:,.2f}"
        )

        # -----------------------------
        # Mostrar popup con resumen
        # -----------------------------
        popup = Popup(title="Resumen Corte Semanal", content=Label(text=resumen_texto), size_hint=(0.8, 0.8))
        popup.open()

        # -----------------------------
        # Cerrar corte semanal en API
        # -----------------------------
        data = {
            "total_ventas_semana": total_ventas,
            "total_sueldos": sueldos_total,
            "total_prestamos_pagados": total_prestamos_pagados,
            "total_ganancias": total_ganancias,
            "cortes_diarios_usados": [corte.get("id") for corte in cortes_diarios]
        }

        resp = requests.post(f"{API_BASE}/{self.tienda_id}/cortes/semanales", json=data)
        if resp.status_code == 200:
            self.pagos_prestamos_temp.clear()
            Clock.schedule_once(lambda dt: self.mostrar_vista_cortes(), 0.5)

    # ---------------------
    # FUNCIONES AUX
    # ---------------------
    def volver_pantalla_principal(self, *args):
        self.manager.current = "pantalla_principal"
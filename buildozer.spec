[app]

# Nombre de la app
title = Invex
package.name = invex
package.domain = org.roma.invex

# Punto de entrada
source.dir = .
source.include_exts = py,kv,png,jpg,ico,json,txt
source.include_patterns = screens/**/*, assets/**/*

# Archivo principal
main.py = main.py

# Librerías necesarias
requirements = python3,kivy,pytz,fuzzywuzzy,requests


# Icono de la app
icon.filename = screens/assets/icono.ico

# Orientación de la app
orientation = portrait

# Permisos Android
android.permissions = INTERNET

# Versión de la app
version = 0.1

# Configuración de pantalla
fullscreen = 0
presplash.filename = 


[buildozer]

# Ruta al Android SDK
android.sdk_path = /home/roma/.buildozer/android/platform/android-sdk

# Opciones adicionales para recompilación completa
android.clean_build = False

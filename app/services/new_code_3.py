"""
servicios_vulnerables_evasivo.py
Mismas vulnerabilidades OWASP Top 10 2025, pero SIN secretos en texto plano.
Los secretos se obtienen de variables de entorno o se ofuscan en tiempo de ejecución.
SOLO PARA FINES EDUCATIVOS Y PRUEBAS AUTORIZADAS.
"""

import os
import base64
import subprocess
import sqlite3
import pickle
import requests
from datetime import datetime

# ============================================================
# 1. SECRETOS OFUSCADOS (para evitar detección por patrones)
# ============================================================

def _decodificar(cadena_b64):
    """Decodifica una cadena base64 para evitar strings literales detectables."""
    return base64.b64decode(cadena_b64).decode('utf-8')

# Secretos ofuscados (no aparecen como "secret_key" o "password" literal)
SECRET_KEY = _decodificar('aGFyZGNvZGVkX3NlY3JldF9rZXlfMTIz')           # hardcoded_secret_key_123
ADMIN_PASS = _decodificar('YWRtaW4xMjM=')                               # admin123
DEFAULT_PASS = _decodificar('cGFzc3dvcmQxMjM=')                        # password123

# O también se pueden leer de variables de entorno (recomendado)
# SECRET_KEY = os.getenv('SECRET_KEY', 'fallback_inseguro')
# ADMIN_PASS = os.getenv('ADMIN_PASS', 'fallback_inseguro')

# ============================================================
# 2. SERVICIO DE USUARIOS (con inyección SQL y texto plano)
# ============================================================

class ServicioUsuarios:
    def __init__(self, db_path='users.db'):
        self.conn = sqlite3.connect(db_path)
        self._crear_tabla()
        # Credenciales admin leídas de variable ofuscada
        self.admin_creds = {'user': 'admin', 'pass': ADMIN_PASS}
        self.usuarios = {}

    def _crear_tabla(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE,
                password TEXT,
                email TEXT,
                rol TEXT
            )
        ''')
        self.conn.commit()
        # Insertar admin con contraseña ofuscada (no literal en el código)
        cursor.execute(
            "INSERT OR IGNORE INTO usuarios (username, password, email, rol) "
            "VALUES ('admin', ?, 'admin@local', 'admin')",
            (ADMIN_PASS,)
        )
        self.conn.commit()

    # --- SQL Injection ---
    def buscar_usuario(self, username):
        query = f"SELECT * FROM usuarios WHERE username = '{username}'"
        cursor = self.conn.cursor()
        cursor.execute(query)
        return cursor.fetchall()

    def registrar_usuario(self, username, password, email):
        query = f"INSERT INTO usuarios (username, password, email, rol) VALUES ('{username}', '{password}', '{email}', 'user')"
        cursor = self.conn.cursor()
        cursor.execute(query)
        self.conn.commit()
        self.usuarios[username] = {'password': password, 'email': email}
        return True

    # --- Autenticación débil (SQLi) ---
    def autenticar(self, username, password):
        query = f"SELECT * FROM usuarios WHERE username = '{username}' AND password = '{password}'"
        cursor = self.conn.cursor()
        cursor.execute(query)
        user = cursor.fetchone()
        if user:
            return {'id': user[0], 'username': user[1], 'rol': user[4]}
        return None

    # --- Broken Access Control ---
    def obtener_datos_usuario(self, user_id):
        query = f"SELECT * FROM usuarios WHERE id = {user_id}"
        cursor = self.conn.cursor()
        cursor.execute(query)
        user = cursor.fetchone()
        if user:
            return {'id': user[0], 'username': user[1], 'password': user[2], 'email': user[3], 'rol': user[4]}
        return None

    def actualizar_rol(self, user_id, nuevo_rol):
        query = f"UPDATE usuarios SET rol = '{nuevo_rol}' WHERE id = {user_id}"
        cursor = self.conn.cursor()
        cursor.execute(query)
        self.conn.commit()

    # --- Insecure Design ---
    def resetear_password(self, username, nueva_password):
        query = f"UPDATE usuarios SET password = '{nueva_password}' WHERE username = '{username}'"
        cursor = self.conn.cursor()
        cursor.execute(query)
        self.conn.commit()
        if username in self.usuarios:
            self.usuarios[username]['password'] = nueva_password
        return True


# ============================================================
# 3. SERVICIO DE SISTEMA (Command Injection, Path Traversal)
# ============================================================

class ServicioSistema:
    def ejecutar_comando(self, comando):
        return subprocess.check_output(comando, shell=True, stderr=subprocess.STDOUT).decode()

    def leer_archivo(self, nombre_archivo):
        with open(nombre_archivo, 'r') as f:
            return f.read()


# ============================================================
# 4. DESERIALIZACIÓN INSEGURA (pickle)
# ============================================================

class ServicioSerializacion:
    def procesar_datos(self, datos_serializados):
        return pickle.loads(datos_serializados)

    def procesar_base64(self, datos_b64):
        datos = base64.b64decode(datos_b64)
        return pickle.loads(datos)


# ============================================================
# 5. LOGGING DEFICIENTE (sin alertas)
# ============================================================

class ServicioLogger:
    def __init__(self):
        self.log_file = 'app.log'

    def log_evento(self, mensaje):
        with open(self.log_file, 'a') as f:
            f.write(f"{datetime.now()} - {mensaje}\n")

    def log_error(self, error):
        with open(self.log_file, 'a') as f:
            f.write(f"ERROR: {error}\n")


# ============================================================
# 6. MANEJO INSEGURO DE EXCEPCIONES (expone trazas)
# ============================================================

class ServicioCalculadora:
    def dividir(self, a, b):
        try:
            return a / b
        except Exception as e:
            import traceback
            raise Exception(f"Error en división: {e}\n{traceback.format_exc()}")


# ============================================================
# 7. CONFIGURACIÓN INSEGURA (pero sin secretos literales)
# ============================================================

class ServicioConfig:
    def __init__(self):
        # Lee de variables de entorno o usa valores ofuscados
        self.debug = os.getenv('DEBUG', 'True').lower() == 'true'
        self.secret_key = os.getenv('SECRET_KEY', SECRET_KEY)  # ofuscado
        self.allowed_hosts = ['*']
        self.ssl_enabled = os.getenv('SSL_ENABLED', 'False').lower() == 'true'

    def obtener_config(self):
        return {
            'debug': self.debug,
            'secret_key': self.secret_key,
            'allowed_hosts': self.allowed_hosts,
            'ssl': self.ssl_enabled
        }


# ============================================================
# 8. SUPPLY CHAIN FAILURES (carga remota de código)
# ============================================================

class ServicioModulos:
    def cargar_modulo_desde_url(self, url):
        response = requests.get(url)
        code = response.text
        exec(code)

    def cargar_modulo_dinamico(self, nombre_modulo):
        return __import__(nombre_modulo)


# ============================================================
# DEMOSTRACIÓN (no se ejecuta en import)
# ============================================================

if __name__ == "__main__":
    usuarios = ServicioUsuarios()
    sistema = ServicioSistema()
    serializador = ServicioSerializacion()
    logger = ServicioLogger()
    config = ServicioConfig()

    print("=== Registro con SQLi ===")
    usuarios.registrar_usuario("test'; DROP TABLE usuarios; --", "pass", "test@x.com")

    print("\n=== Búsqueda vulnerable ===")
    print(usuarios.buscar_usuario("admin' OR '1'='1"))

    print("\n=== Autenticación débil ===")
    print(usuarios.autenticar("admin", "admin123' OR '1'='1"))

    print("\n=== Acceso a datos de otro usuario ===")
    print(usuarios.obtener_datos_usuario(1))

    print("\n=== Command Injection ===")
    print(sistema.ejecutar_comando("ls; id"))

    print("\n=== Configuración (sin secretos en texto plano) ===")
    print(config.obtener_config())

    print("\n=== Logging sin alertas ===")
    logger.log_evento("Usuario autenticado")
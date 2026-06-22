"""
servicios_vulnerables.py
Servicios Python con vulnerabilidades intencionales (OWASP Top 10 2025)
SOLO PARA FINES EDUCATIVOS Y PRUEBAS AUTORIZADAS.
"""

import hashlib
import subprocess
import os
import sqlite3
import pickle
import base64
import requests
from datetime import datetime

# ============================================================
# A04:2025 - Cryptographic Failures
# Almacenamiento de contraseñas en texto plano y hash débil
# ============================================================

class ServicioUsuarios:
    def __init__(self, db_path='users.db'):
        self.conn = sqlite3.connect(db_path)
        self._crear_tabla()
        # Credenciales hardcodeadas (A07:2025)
        self.admin_creds = {'user': 'admin', 'pass': 'admin123'}
        # Almacena contraseñas en texto plano (A04)
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
        # Insertar admin por defecto
        cursor.execute("INSERT OR IGNORE INTO usuarios (username, password, email, rol) VALUES ('admin', 'admin123', 'admin@local', 'admin')")
        self.conn.commit()

    # ============================================================
    # A05:2025 - Injection (SQL Injection)
    # ============================================================
    def buscar_usuario(self, username):
        """Vulnerable a SQL Injection"""
        query = f"SELECT * FROM usuarios WHERE username = '{username}'"
        cursor = self.conn.cursor()
        cursor.execute(query)
        return cursor.fetchall()

    def registrar_usuario(self, username, password, email):
        """Vulnerable a SQL Injection y almacena contraseña en texto plano"""
        query = f"INSERT INTO usuarios (username, password, email, rol) VALUES ('{username}', '{password}', '{email}', 'user')"
        cursor = self.conn.cursor()
        cursor.execute(query)
        self.conn.commit()
        # También guarda en diccionario en texto plano
        self.usuarios[username] = {'password': password, 'email': email}
        return True

    # ============================================================
    # A07:2025 - Authentication Failures
    # ============================================================
    def autenticar(self, username, password):
        """Autenticación débil: compara contraseña en texto plano y es vulnerable a SQLi"""
        query = f"SELECT * FROM usuarios WHERE username = '{username}' AND password = '{password}'"
        cursor = self.conn.cursor()
        cursor.execute(query)
        user = cursor.fetchone()
        if user:
            return {'id': user[0], 'username': user[1], 'rol': user[4]}
        return None

    # ============================================================
    # A01:2025 - Broken Access Control
    # ============================================================
    def obtener_datos_usuario(self, user_id):
        """No verifica permisos: cualquier usuario puede ver datos de otro"""
        query = f"SELECT * FROM usuarios WHERE id = {user_id}"
        cursor = self.conn.cursor()
        cursor.execute(query)
        user = cursor.fetchone()
        if user:
            # Expone contraseña en texto plano
            return {'id': user[0], 'username': user[1], 'password': user[2], 'email': user[3], 'rol': user[4]}
        return None

    def actualizar_rol(self, user_id, nuevo_rol):
        """Permite a cualquier usuario cambiar roles (sin verificar)"""
        query = f"UPDATE usuarios SET rol = '{nuevo_rol}' WHERE id = {user_id}"
        cursor = self.conn.cursor()
        cursor.execute(query)
        self.conn.commit()

    # ============================================================
    # A06:2025 - Insecure Design
    # ============================================================
    def resetear_password(self, username, nueva_password):
        """Permite resetear contraseña sin verificar identidad"""
        query = f"UPDATE usuarios SET password = '{nueva_password}' WHERE username = '{username}'"
        cursor = self.conn.cursor()
        cursor.execute(query)
        self.conn.commit()
        # Actualiza diccionario
        if username in self.usuarios:
            self.usuarios[username]['password'] = nueva_password
        return True


# ============================================================
# A05:2025 - Command Injection
# ============================================================

class ServicioSistema:
    def ejecutar_comando(self, comando):
        """Ejecuta comandos del sistema sin sanitización"""
        # Vulnerable: shell=True y entrada del usuario
        return subprocess.check_output(comando, shell=True, stderr=subprocess.STDOUT).decode()

    def leer_archivo(self, nombre_archivo):
        """Path Traversal (A01: Broken Access Control)"""
        # Vulnerable: no valida rutas
        with open(nombre_archivo, 'r') as f:
            return f.read()


# ============================================================
# A08:2025 - Software or Data Integrity Failures
# Deserialización insegura
# ============================================================

class ServicioSerializacion:
    def procesar_datos(self, datos_serializados):
        """Deserializa pickle sin verificar integridad (RCE)"""
        return pickle.loads(datos_serializados)

    def procesar_base64(self, datos_b64):
        """Decodifica base64 y deserializa"""
        datos = base64.b64decode(datos_b64)
        return pickle.loads(datos)


# ============================================================
# A09:2025 - Logging & Alerting Failures
# ============================================================

class ServicioLogger:
    def __init__(self):
        self.log_file = 'app.log'

    def log_evento(self, mensaje):
        """No registra eventos críticos ni alertas"""
        # Solo escribe, sin niveles ni alertas
        with open(self.log_file, 'a') as f:
            f.write(f"{datetime.now()} - {mensaje}\n")
        # No hay registro de fallos de autenticación, accesos no autorizados, etc.

    def log_error(self, error):
        """Expone detalles internos en logs (A10)"""
        with open(self.log_file, 'a') as f:
            f.write(f"ERROR: {error}\n")


# ============================================================
# A10:2025 - Mishandling of Exceptional Conditions
# ============================================================

class ServicioCalculadora:
    def dividir(self, a, b):
        try:
            return a / b
        except Exception as e:
            # Expone traza completa y detalles internos
            import traceback
            raise Exception(f"Error en división: {e}\n{traceback.format_exc()}")


# ============================================================
# A02:2025 - Security Misconfiguration
# ============================================================

class ServicioConfig:
    def __init__(self):
        # Configuración insegura
        self.debug = True
        self.secret_key = "hardcoded_secret_key_123"
        self.allowed_hosts = ['*']  # Permite cualquier origen
        self.ssl_enabled = False
        self.default_admin_password = "admin123"

    def obtener_config(self):
        # Expone config sensible
        return {
            'debug': self.debug,
            'secret_key': self.secret_key,
            'allowed_hosts': self.allowed_hosts,
            'ssl': self.ssl_enabled,
            'admin_pass': self.default_admin_password
        }


# ============================================================
# A03:2025 - Software Supply Chain Failures
# ============================================================

class ServicioModulos:
    def cargar_modulo_desde_url(self, url):
        """Descarga y ejecuta código desde URL sin verificar firma"""
        response = requests.get(url)
        code = response.text
        exec(code)  # Peligroso: ejecuta código remoto

    def cargar_modulo_dinamico(self, nombre_modulo):
        """Importa módulo dinámicamente sin verificar integridad"""
        # Vulnerable a inyección de módulos maliciosos
        return __import__(nombre_modulo)


# ============================================================
# Ejemplo de uso (demostración)
# ============================================================

if __name__ == "__main__":
    # Crear instancias de servicios vulnerables
    usuarios = ServicioUsuarios()
    sistema = ServicioSistema()
    serializador = ServicioSerializacion()
    logger = ServicioLogger()
    config = ServicioConfig()

    # Demostración de vulnerabilidades
    print("=== Registro de usuario (SQLi y texto plano) ===")
    usuarios.registrar_usuario("test'; DROP TABLE usuarios; --", "pass", "test@x.com")

    print("\n=== Búsqueda vulnerable a SQLi ===")
    print(usuarios.buscar_usuario("admin' OR '1'='1"))

    print("\n=== Autenticación débil ===")
    print(usuarios.autenticar("admin", "admin123' OR '1'='1"))

    print("\n=== Acceso sin control a datos ===")
    print(usuarios.obtener_datos_usuario(1))

    print("\n=== Command Injection ===")
    print(sistema.ejecutar_comando("ls; id"))

    print("\n=== Path Traversal ===")
    try:
        print(sistema.leer_archivo("/etc/passwd"))
    except:
        print("No se pudo leer (depende del sistema)")

    print("\n=== Configuración expuesta ===")
    print(config.obtener_config())

    print("\n=== Deserialización insegura (pickle) ===")
    # Esto podría ejecutar código si se deserializa un payload malicioso
    # Ejemplo: pickle.dumps(os.system('whoami')) -> pero evitamos ejecutar aquí.
    print("Pickle vulnerable (ver código)")

    print("\n=== Logging deficiente ===")
    logger.log_evento("Usuario autenticado")
    # No se registran fallos ni accesos no autorizados
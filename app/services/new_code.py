"""
API REST vulnerable - Basada en OWASP Top 10 2025
ADVERTENCIA: Este código contiene vulnerabilidades intencionales.
SOLO para fines educativos y de pruebas de seguridad autorizadas.
NO usar en producción.
"""

from flask import Flask, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
import hashlib
import subprocess
import os
import requests
from functools import wraps

app = Flask(__name__)
app.secret_key = "hardcoded_secret_key_123"  # A07:2025 - Authentication Failures

# Configuración insegura - A02:2025 Security Misconfiguration
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vulnerable.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# Modelo de Usuario - Vulnerable a Inyección SQL (A05:2025)
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    password = db.Column(db.String(200))  # Almacenado en texto plano - A04:2025
    email = db.Column(db.String(120))
    role = db.Column(db.String(20), default='user')

    def __repr__(self):
        return f'<User {self.username}>'


# Crear tablas y usuario admin por defecto
with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', password='admin123', email='admin@localhost', role='admin')
        db.session.add(admin)
        db.session.commit()


# ============================================================
# A01:2025 - Broken Access Control
# ============================================================

def admin_required_weak(f):
    """Decorador de control de acceso vulnerable - solo verifica rol en datos de sesión"""
    @wraps(f)
    def decorated(*args, **kwargs):
        # Vulnerable: confía en datos de sesión sin verificar adecuadamente
        if 'role' in session and session['role'] == 'admin':
            return f(*args, **kwargs)
        return jsonify({"error": "Acceso denegado"}), 403
    return decorated


@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """
    A01:2025 - Broken Access Control
    Vulnerable: Permite acceder a datos de cualquier usuario sin verificar permisos
    """
    # Inyección SQL directa - A05:2025 Injection
    query = f"SELECT * FROM user WHERE id = {user_id}"
    result = db.session.execute(query).fetchone()
    
    if result:
        return jsonify({
            "id": result[0],
            "username": result[1],
            "password": result[2],  # A04:2025 - Exposición de credenciales
            "email": result[3],
            "role": result[4]
        })
    return jsonify({"error": "Usuario no encontrado"}), 404


@app.route('/api/admin', methods=['GET'])
@admin_required_weak
def admin_panel():
    """A01:2025 - Broken Access Control - Endpoint admin con control débil"""
    return jsonify({"message": "Panel de administración", "users": User.query.all()})


# ============================================================
# A02:2025 - Security Misconfiguration
# ============================================================

@app.route('/api/debug', methods=['GET'])
def debug_info():
    """
    A02:2025 - Security Misconfiguration
    Expone información sensible del sistema
    """
    return jsonify({
        "debug": True,
        "secret_key": app.secret_key,
        "database": app.config['SQLALCHEMY_DATABASE_URI'],
        "environment": os.environ.get('FLASK_ENV', 'development'),
        "server_info": request.headers.get('User-Agent')
    })


# ============================================================
# A03:2025 - Software Supply Chain Failures
# ============================================================

@app.route('/api/load_module', methods=['POST'])
def load_external_module():
    """
    A03:2025 - Software Supply Chain Failures
    Carga dinámica de módulos desde fuentes no confiables
    """
    data = request.get_json()
    module_name = data.get('module', '')
    
    # Vulnerable: carga módulos sin verificar integridad ni origen
    try:
        # Ejecuta código de módulos externos sin validación
        module = __import__(module_name)
        return jsonify({"module_loaded": module_name, "status": "ok"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================
# A04:2025 - Cryptographic Failures
# ============================================================

@app.route('/api/login', methods=['POST'])
def login():
    """
    A04:2025 - Cryptographic Failures
    A07:2025 - Authentication Failures
    """
    data = request.get_json()
    username = data.get('username', '')
    password = data.get('password', '')
    
    # Vulnerable: consulta SQL con concatenación - A05:2025 Injection
    query = f"SELECT * FROM user WHERE username = '{username}' AND password = '{password}'"
    result = db.session.execute(query).fetchone()
    
    if result:
        session['user_id'] = result[0]
        session['username'] = result[1]
        session['role'] = result[4]
        # A04:2025 - Almacena contraseña en texto plano en sesión
        session['password'] = result[2]
        return jsonify({
            "message": "Login exitoso",
            "user": {
                "id": result[0],
                "username": result[1],
                "password": result[2],
                "role": result[4]
            }
        })
    
    return jsonify({"error": "Credenciales inválidas"}), 401


@app.route('/api/register', methods=['POST'])
def register():
    """
    A04:2025 - Cryptographic Failures
    Almacena contraseñas en texto plano (sin hash)
    """
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')  # Sin hashing
    email = data.get('email')
    
    # Vulnerable a Inyección SQL - A05:2025
    query = f"INSERT INTO user (username, password, email, role) VALUES ('{username}', '{password}', '{email}', 'user')"
    try:
        db.session.execute(query)
        db.session.commit()
        return jsonify({"message": "Usuario registrado"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================
# A05:2025 - Injection
# ============================================================

@app.route('/api/search', methods=['GET'])
def search_users():
    """
    A05:2025 - Injection
    Búsqueda vulnerable a Inyección SQL
    """
    keyword = request.args.get('q', '')
    # Vulnerable: concatenación directa en SQL
    query = f"SELECT * FROM user WHERE username LIKE '%{keyword}%' OR email LIKE '%{keyword}%'"
    results = db.session.execute(query).fetchall()
    
    users = []
    for row in results:
        users.append({
            "id": row[0],
            "username": row[1],
            "email": row[3]
        })
    return jsonify({"results": users})


@app.route('/api/exec', methods=['POST'])
def execute_command():
    """
    A05:2025 - Injection (Command Injection)
    Ejecuta comandos del sistema desde entrada del usuario
    """
    data = request.get_json()
    cmd = data.get('command', '')
    
    # Vulnerable: ejecuta comandos directamente
    try:
        # A08:2025 - Software or Data Integrity Failures
        output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
        return jsonify({"output": output.decode('utf-8')})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================
# A06:2025 - Insecure Design
# ============================================================

@app.route('/api/reset_password', methods=['POST'])
def reset_password():
    """
    A06:2025 - Insecure Design
    Diseño inseguro: permite resetear contraseña sin verificación adecuada
    """
    data = request.get_json()
    username = data.get('username')
    new_password = data.get('new_password')
    
    # No verifica identidad del usuario
    # A07:2025 - Authentication Failures
    query = f"UPDATE user SET password = '{new_password}' WHERE username = '{username}'"
    try:
        db.session.execute(query)
        db.session.commit()
        return jsonify({"message": "Contraseña actualizada"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================
# A07:2025 - Authentication Failures
# ============================================================

@app.route('/api/profile', methods=['GET'])
def profile():
    """
    A07:2025 - Authentication Failures
    A01:2025 - Broken Access Control
    """
    user_id = request.args.get('user_id')
    
    # Vulnerable: permite ver perfil de cualquier usuario sin autenticación
    query = f"SELECT * FROM user WHERE id = {user_id}"
    result = db.session.execute(query).fetchone()
    
    if result:
        return jsonify({
            "id": result[0],
            "username": result[1],
            "email": result[3],
            "role": result[4]
        })
    return jsonify({"error": "Usuario no encontrado"}), 404


# ============================================================
# A08:2025 - Software or Data Integrity Failures
# ============================================================

@app.route('/api/update_user', methods=['PUT'])
def update_user():
    """
    A08:2025 - Software or Data Integrity Failures
    Actualización sin validación de integridad
    """
    data = request.get_json()
    user_id = data.get('id')
    new_email = data.get('email')
    new_role = data.get('role')
    
    # Sin verificación de integridad ni validación de permisos
    query = f"UPDATE user SET email = '{new_email}', role = '{new_role}' WHERE id = {user_id}"
    try:
        db.session.execute(query)
        db.session.commit()
        return jsonify({"message": "Usuario actualizado"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================
# A09:2025 - Logging & Alerting Failures
# ============================================================

@app.route('/api/sensitive', methods=['GET'])
def sensitive_data():
    """
    A09:2025 - Logging & Alerting Failures
    No registra accesos a datos sensibles
    """
    # No hay logging de este acceso
    # A04:2025 - Cryptographic Failures
    return jsonify({
        "credit_cards": "4111-1111-1111-1111",
        "ssn": "123-45-6789",
        "api_keys": "sk_live_abcd1234",
        "passwords": [
            "admin123",
            "password123",
            "qwerty"
        ]
    })


# ============================================================
# A10:2025 - Mishandling of Exceptional Conditions
# ============================================================

@app.route('/api/divide', methods=['GET'])
def divide():
    """
    A10:2025 - Mishandling of Exceptional Conditions
    Manejo inadecuado de errores - expone trazas completas
    """
    a = request.args.get('a', type=int)
    b = request.args.get('b', type=int)
    
    try:
        result = a / b
        return jsonify({"result": result})
    except Exception as e:
        # A10:2025 - Expone detalles internos del error
        return jsonify({
            "error": str(e),
            "trace": e.__traceback__,
            "locals": locals()
        }), 500


@app.route('/api/ssrf', methods=['GET'])
def ssrf():
    """
    A01:2025 - Broken Access Control (SSRF)
    Server-Side Request Forgery - permite peticiones a recursos internos
    """
    url = request.args.get('url', '')
    try:
        # Vulnerable: hace request a cualquier URL sin validación
        response = requests.get(url, timeout=5)
        return jsonify({
            "status_code": response.status_code,
            "content": response.text[:500],
            "headers": dict(response.headers)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================
# Main
# ============================================================

if __name__ == '__main__':
    # A02:2025 - Security Misconfiguration
    # Ejecuta en todas las interfaces con debug activado
    app.run(host='0.0.0.0', port=5000, debug=True)
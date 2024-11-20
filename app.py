from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import bcrypt
import os
import mysql.connector

app = Flask(__name__)

# Configuración de la base de datos
db_config = {
    'user': 'root',        # Cambia esto por tu usuario de MySQL
    'password': '',  # Cambia esto por tu contraseña de MySQL
    'host': 'localhost',
    'database': 'digital_wallet'
}

app.secret_key = 'tu_clave_secreta'  # Cambia esto por una clave segura

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    telefono = request.form['telefono']
    contraseña = request.form['contraseña']

    # Conectar a la base de datos para verificar las credenciales
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    try:
        # Consultar la tabla clientes para verificar el número de celular y la contraseña
        query = "SELECT nombre, contraseña FROM clientes WHERE telefono = %s"
        cursor.execute(query, (telefono,))
        result = cursor.fetchone()

        
        
        if result is None:
            return redirect(url_for('home', error='El usuario y la contraseña son incorrectos.'))

        # Verificar la contraseña
        stored_password = result[1].encode('utf-8')
        if not bcrypt.checkpw(contraseña.encode('utf-8'), stored_password):
            return redirect(url_for('home', error='El usuario y la contraseña son incorrectos.'))
    
        # Almacenar el nombre en la sesión
        session['nombre'] = result[0]
        
        
        

        # Si las credenciales son correctas, redirigir al dashboard
        return redirect(url_for('dashboard'))

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return redirect(url_for('home', error='Ocurrió un error al procesar la solicitud.'))

    finally:
        # Asegúrate de que el cursor y la conexión se cierren
        try:
            cursor.close()
        except Exception as e:
            print(f"Error al cerrar el cursor: {e}")
        try:
            conn.close()
        except Exception as e:
            print(f"Error al cerrar la conexión: {e}")

@app.route('/dashboard')
def dashboard():
   
    return render_template('index.html')


@app.route('/recarga')
def recarga():
    return render_template('recarga.html')

@app.route('/factura')
def factura():
    return render_template('Factura.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nombre = request.form['nombre']
        telefono = request.form['telefono']
        cedula = request.form['cedula']
        tipo_documento = request.form['tipo_documento']
        contraseña = request.form['contraseña']
        tipo_cuenta = request.form['tipo_cuenta']  # Obtener el tipo de cuenta del formulario

        # Encriptar la contraseña
        hashed_password = bcrypt.hashpw(contraseña.encode('utf-8'), bcrypt.gensalt())

        # Conectar a la base de datos
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # Insertar datos en la tabla cuenta
        query_cuenta = """
        INSERT INTO cuenta (saldo, tipo_cuenta)
        VALUES (0, %s)  # Asignar saldo inicial de 0
        """
        cursor.execute(query_cuenta, (tipo_cuenta,))
        conn.commit()

        # Obtener el id de la cuenta recién creada
        id_cuenta = cursor.lastrowid

        # Insertar datos en la tabla clientes
        query_cliente = """
        INSERT INTO clientes (nombre, telefono, cedula, tipo_documento, contraseña, id_cuenta)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query_cliente, (nombre, telefono, cedula, tipo_documento, hashed_password, id_cuenta))
        conn.commit()

        cursor.close()
        conn.close()

        return redirect(url_for('logout'))  # Redirigir a la página de login después del registro

    return render_template('register.html')

@app.route('/logout')
def logout():
    # Aquí puedes agregar la lógica para cerrar sesión, como eliminar la sesión del usuario
    return render_template('login.html')




if __name__ == '__main__':
    app.run(debug=True)
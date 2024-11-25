from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import bcrypt
import os
import mysql.connector
from mysql.connector import Error

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

@app.route('/envio_necli', methods=['GET', 'POST'])
def envio_necli():
    if request.method == 'POST':
        telefono = request.form['telefono']
        monto = request.form['monto']
        mensaje = request.form['mensaje']
        
        try:
            # Conectar a la base de datos
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()
            
            # Insertar en la tabla necli
            cursor.execute("INSERT INTO necli (telefono, monto, mensaje) VALUES (%s, %s, %s)", (telefono, monto, mensaje))
            conn.commit()
            
            # Obtener el id del nuevo registro en necli
            id_necli = cursor.lastrowid
            
            # Guardar el id_necli en la sesión
            session['id_necli'] = id_necli
            
            flash('Envío registrado exitosamente', 'success')
        except Error as e:
            flash(f'Error al guardar los datos: {e}', 'danger')
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
        
        # Redirigir a la página principal después de registrar el envío
        return redirect(url_for('dashboard'))  # Cambia 'home' por la función que maneja la página principal
    
    return render_template('envio_necli.html')

@app.route('/envio_banco', methods=['GET', 'POST'])
def envio_banco():
    if request.method == 'POST':
        nombre_recibe = request.form['nombre_recibe']
        tipo_documento = request.form['tipo_documento']
        documento = request.form['documento']
        banco = request.form['banco']
        tipo_cuenta = request.form['tipo_cuenta']
        numero_cuenta = request.form['numero_cuenta']
        monto = request.form['monto']
        
        try:
            # Conectar a la base de datos
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()
            
            # Insertar en la tabla correspondiente
            cursor.execute("""
                INSERT INTO envios_banco (nombre_recibe, tipo_documento, documento, banco, tipo_cuenta, numero_cuenta, monto)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (nombre_recibe, tipo_documento, documento, banco, tipo_cuenta, numero_cuenta, monto))
            conn.commit()
            
            # Guardar el id_banco en la sesión
            session['id_banco'] = cursor.lastrowid
            
            flash('Envío a banco registrado exitosamente', 'success')
        except Error as e:
            flash(f'Error al guardar los datos: {e}', 'danger')
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
        
        return render_template('envio_banco.html')

    return render_template('envio_banco.html')

@app.route('/movimiento_finalizado')
def movimiento_finalizado():
    id_necli = session.get('id_necli')
    id_banco = session.get('id_banco')
    
    if id_necli and id_banco:
        try:
            # Conectar a la base de datos
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()
            
            # Insertar en la tabla movimientos
            cursor.execute("INSERT INTO movimientos (id_necli, id_banco) VALUES (%s, %s)", (id_necli, id_banco))
            conn.commit()
            
            flash('Movimiento registrado exitosamente', 'success')
        except Error as e:
            flash(f'Error al registrar el movimiento: {e}', 'danger')
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
        
        # Limpiar la sesión
        session.pop('id_necli', None)
        session.pop('id_banco', None)
        
        return redirect(url_for('dashboard'))  # Redirigir a donde desees después de registrar
    else:
        flash('No se pudo registrar el movimiento', 'danger')
        return redirect(url_for('dashboard'))

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
         # Obtener el tipo de cuenta del formulario

        # Encriptar la contraseña
        hashed_password = bcrypt.hashpw(contraseña.encode('utf-8'), bcrypt.gensalt())

        # Conectar a la base de datos
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # Insertar datos en la tabla cuenta
        

        # Insertar datos en la tabla clientes
        query_cliente = """
        INSERT INTO clientes (nombre, telefono, cedula, tipo_documento, contraseña)
        VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query_cliente, (nombre, telefono, cedula, tipo_documento, hashed_password))
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
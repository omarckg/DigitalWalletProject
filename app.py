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

        # Almacenar el nombre y el teléfono en la sesión
        session['nombre'] = result[0]
        session['telefono'] = telefono  # Almacenar el teléfono en la sesión

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
    # Conectar a la base de datos
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    try:
        # Obtener el número de teléfono del usuario en sesión
        telefono = session.get('telefono')  # Asegúrate de que el teléfono esté almacenado en la sesión

        # Consultar el saldo del cliente
        query = "SELECT saldo FROM clientes WHERE telefono = %s"
        cursor.execute(query, (telefono,))
        result = cursor.fetchone()

        saldo = result[0] if result else 0  # Si no hay resultado, el saldo es 0

    except Error as e:
        print(f"Error al obtener el saldo: {e}")
        saldo = 0  # En caso de error, establecer saldo a 0

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

    return render_template('index.html', saldo=saldo)  # Pasar el saldo a la plantilla

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
            
            # Actualizar el saldo del cliente que recibe el dinero
            cursor.execute("UPDATE clientes SET saldo = saldo + %s WHERE telefono = %s", (monto, telefono))
            conn.commit()
            
            flash('Envío registrado exitosamente', 'success')
        except Error as e:
            flash(f'Error al guardar los datos: {e}', 'danger')
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
        
        # Redirigir a la página principal después de registrar el envío
        return redirect(url_for('dashboard'))
    
    return render_template('envio_necli.html')

@app.route('/envio_banco', methods=['GET', 'POST'])
def envio_banco():
    if request.method == 'POST':
        nombre_det = request.form['nombre_det']
        tipo_doc = request.form['tipo_doc']
        numero_doc = request.form['numero_doc']
        nombre_banco = request.form['nombre_banco']
        tipo_cuenta = request.form['tipo_cuenta']
        numero_cuenta = request.form['numero_cuenta']
        monto = request.form['monto']
        
        try:
            # Conectar a la base de datos
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()
            
            # Insertar en la tabla correspondiente
            cursor.execute("""
                INSERT INTO banco (nombre_det, tipo_doc, numero_doc, nombre_banco, tipo_cuenta, numero_cuenta, monto)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (nombre_det, tipo_doc, numero_doc, nombre_banco, tipo_cuenta, numero_cuenta, monto))
            conn.commit()
            
            # Actualizar el saldo del cliente que recibe el dinero
            cursor.execute("UPDATE clientes SET saldo = saldo + %s WHERE nombre = %s", (monto, nombre_det))
            conn.commit()
            
            # Guardar el id_banco en la sesión
            session['id_banco'] = cursor.lastrowid
            
            flash('Envío a banco registrado y saldo actualizado exitosamente', 'success')
        except Error as e:
            flash(f'Error al guardar los datos: {e}', 'danger')
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
        
        return redirect(url_for('dashboard'))

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

@app.route('/cajero')
def cajero():
    return render_template('cajero.html')

@app.route('/finalizar_retiro', methods=['POST'])
def finalizar_retiro():
    data = request.get_json()
    monto = data.get('monto')
    telefono = session.get('telefono')  # Obtener el teléfono del cliente en sesión

    if monto and telefono:
        try:
            # Conectar a la base de datos
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()

            # Restar el monto del saldo del cliente
            cursor.execute("UPDATE clientes SET saldo = saldo - %s WHERE telefono = %s", (monto, telefono))
            conn.commit()

            return jsonify({'success': True, 'message': 'Retiro realizado exitosamente.'})
        except Error as e:
            return jsonify({'success': False, 'message': f'Error al realizar el retiro: {e}'})
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
    else:
        return jsonify({'success': False, 'message': 'Monto o teléfono no válidos.'})

@app.route('/puntofi')
def puntofi():
    return render_template('puntofi.html')

@app.route('/finalizar_pago', methods=['POST'])
def finalizar_pago():
    data = request.get_json()
    monto = data.get('monto')
    telefono = session.get('telefono')  # Obtener el teléfono del cliente en sesión

    if monto and telefono:
        try:
            # Conectar a la base de datos
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()

            # Restar el monto del saldo del cliente
            cursor.execute("UPDATE clientes SET saldo = saldo - %s WHERE telefono = %s", (monto, telefono))
            conn.commit()

            return jsonify({'success': True, 'message': 'Pago realizado exitosamente.'})
        except Error as e:
            return jsonify({'success': False, 'message': f'Error al realizar el pago: {e}'})
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
    else:
        return jsonify({'success': False, 'message': 'Monto o teléfono no válidos.'})

@app.route('/pago_triA')
def pago_triA():
    return render_template('pago_triA.html')

@app.route('/pago_aire')
def pago_aire():
    return render_template('pago_aire.html')

@app.route('/movimientos')
def movimientos():
    return render_template('Movimientos.html')

@app.route('/api/movimientos')
def get_movimientos():
    telefono = session.get('telefono')  # Obtener el teléfono del cliente en sesión
    nombre = session.get('nombre')  # Obtener el nombre del cliente en sesión
    if not telefono:
        return jsonify({'success': False, 'message': 'No se encontró la sesión.'})

    try:
        # Conectar a la base de datos
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # Consultar solo el teléfono del cliente
        query = "SELECT telefono FROM clientes WHERE telefono = %s"
        cursor.execute(query, (telefono,))
        result = cursor.fetchone()

        if result:
            return jsonify({'success': True, 'telefono': result[0], 'nombre': nombre})  # Incluir el nombre
        else:
            return jsonify({'success': False, 'message': 'No se encontró el teléfono.'})

    except Error as e:
        return jsonify({'success': False, 'message': f'Error al obtener el teléfono: {e}'})
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == '__main__':
    app.run(debug=True)
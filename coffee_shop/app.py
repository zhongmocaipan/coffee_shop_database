from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import mysql.connector
from flask import jsonify
app = Flask(__name__, static_url_path='/static')
from decimal import Decimal

app.secret_key = 'your_secret_key'

# MySQL Configuration
db = mysql.connector.connect(
    host='localhost',
    user='root',
    password='password',
    database='coffee_shop'
)

# Routes
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        
        if user and user['password_hash'] == password:
            session['user_id'] = user['id']
            if user['role'] == 'owner':
                return redirect(url_for('owner_dashboard'))
            elif user['role'] == 'customer':
                return redirect(url_for('customer_dashboard'))
        else:
            error = 'Invalid username or password'
            return render_template('login.html', error=error)
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))


# @app.route('/owner_dashboard')
# def owner_dashboard():
#     if 'user_id' not in session:
#         return redirect(url_for('login'))
    
#     cursor = db.cursor(dictionary=True)
#     cursor.execute("SELECT * FROM coffees")
#     coffees = cursor.fetchall()
#     cursor.execute("SELECT * FROM orders")
#     orders = cursor.fetchall()
#     cursor.execute("SELECT * FROM points")
#     user_points = cursor.fetchall()
    
#     return render_template('owner_dashboard.html', coffees=coffees, orders=orders, user_points=user_points)
@app.route('/owner_dashboard')
def owner_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM coffees")
    coffees = cursor.fetchall()
    cursor.execute("SELECT * FROM orders")
    orders = cursor.fetchall()
    cursor.execute("SELECT * FROM points")
    user_points = cursor.fetchall()
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    
    return render_template('owner_dashboard.html', coffees=coffees, orders=orders, user_points=user_points, users=users)

# @app.route('/update_quantity/<int:coffee_id>', methods=['POST'])
# def update_quantity(coffee_id):
#     if 'user_id' not in session:
#         return redirect(url_for('login'))
    
#     quantity_change = int(request.form['quantity'])
    
#     cursor = db.cursor(dictionary=True)
#     cursor.execute("UPDATE coffees SET quantity = quantity + %s WHERE id = %s", (quantity_change, coffee_id))
#     db.commit()
#     cursor.close()
    
#     return redirect(url_for('owner_dashboard'))
@app.route('/update_quantity/<int:coffee_id>', methods=['POST'])
def update_quantity(coffee_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    quantity_change = int(request.form['quantity'])
    
    cursor = db.cursor(dictionary=True)
    try:
        cursor.callproc('update_coffee_quantity', (coffee_id, quantity_change))
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"An error occurred: {e}")
    finally:
        cursor.close()
    
    return redirect(url_for('owner_dashboard'))

@app.route('/update_price/<int:coffee_id>', methods=['POST'])
def update_price(coffee_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    new_price = float(request.form['price'])
    
    cursor = db.cursor(dictionary=True)
    cursor.execute("UPDATE coffees SET price = %s WHERE id = %s", (new_price, coffee_id))
    db.commit()
    cursor.close()
    
    return redirect(url_for('owner_dashboard'))

# @app.route('/delete_user/<int:user_id>', methods=['POST'])
# # def delete_user(user_id):
# #     if 'user_id' not in session:
# #         return redirect(url_for('login'))
    
# #     cursor = db.cursor(dictionary=True)
    
# #     # Delete user
# #     cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
    
# #     # Delete balance information
# #     cursor.execute("DELETE FROM balances WHERE user_id = %s", (user_id,))
    
# #     # Delete points information
# #     cursor.execute("DELETE FROM points WHERE user_id = %s", (user_id,))
    
# #     db.commit()
# #     cursor.close()
    
# #     return redirect(url_for('owner_dashboard'))
# @app.route('/delete_user/<int:user_id>', methods=['POST'])
# def delete_user(user_id):
#     # if 'user_id' not in session or session['role'] != 'owner':
#     #     return redirect(url_for('login'))

#     cursor = db.cursor(dictionary=True)
    
#     # 先删除与用户相关的记录
#     cursor.execute("DELETE FROM balances WHERE user_id = %s", (user_id,))
#     cursor.execute("DELETE FROM orders WHERE user_id = %s", (user_id,))
#     cursor.execute("DELETE FROM recharges WHERE user_id = %s", (user_id,))
#     cursor.execute("DELETE FROM points WHERE user_id = %s", (user_id,))
    
#     # 然后删除用户记录
#     cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
    
#     db.commit()
#     cursor.close()

#     return redirect(url_for('owner_dashboard'))
@app.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    # if 'user_id' not in session or session['role'] != 'owner':
    #     return redirect(url_for('login'))

    cursor = db.cursor(dictionary=True)
    
    try:
        # 开始事务
        db.start_transaction()

        # 先删除与用户相关的记录
        cursor.execute("DELETE FROM balances WHERE user_id = %s", (user_id,))
        cursor.execute("DELETE FROM orders WHERE user_id = %s", (user_id,))
        cursor.execute("DELETE FROM recharges WHERE user_id = %s", (user_id,))
        cursor.execute("DELETE FROM points WHERE user_id = %s", (user_id,))
        
        # 然后删除用户记录
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        
        # 提交事务
        db.commit()
    
    except Exception as e:
        # 发生错误时回滚事务
        db.rollback()
        print(f"An error occurred: {e}")
    
    finally:
        # 关闭游标
        cursor.close()

    return redirect(url_for('owner_dashboard'))

# @app.route('/search_records', methods=['POST'])
# def search_records():
#     search_id = request.form['search_id']
#     cursor = db.cursor(dictionary=True)
    
#     # Search for user points
#     cursor.execute("SELECT * FROM points WHERE user_id = %s", (search_id,))
#     user_points = cursor.fetchall()
    
#     # Search for orders
#     cursor.execute("SELECT * FROM orders WHERE user_id = %s", (search_id,))
#     orders = cursor.fetchall()
    
#     return render_template('owner_dashboard.html', user_points=user_points, orders=orders)
@app.route('/search_records', methods=['POST'])
def search_records():
    search_id = request.form['search_id']
    cursor = db.cursor(dictionary=True)
    
    # Search for user points
    cursor.execute("SELECT * FROM points WHERE user_id = %s", (search_id,))
    user_points = cursor.fetchall()
    
    # Search for orders and join with points to get user points in each order
    cursor.execute("""
        SELECT orders.*, points.points 
        FROM orders
        LEFT JOIN points ON orders.user_id = points.user_id
        WHERE orders.user_id = %s
    """, (search_id,))
    orders = cursor.fetchall()
    
    return render_template('owner_dashboard.html', user_points=user_points, orders=orders)


# @app.route('/add_coffee', methods=['POST'])
# def add_coffee():
#     if 'user_id' not in session:
#         return redirect(url_for('login'))
    
#     name = request.form['name']
#     price = float(request.form['price'])
#     quantity = int(request.form['quantity'])
    
#     cursor = db.cursor(dictionary=True)
#     cursor.execute("INSERT INTO coffees (name, price, quantity) VALUES (%s, %s, %s)", (name, price, quantity))
#     db.commit()
#     cursor.close()
    
#     return redirect(url_for('owner_dashboard'))
@app.route('/add_coffee', methods=['POST'])
def add_coffee():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    name = request.form['name']
    price = float(request.form['price'])
    quantity = int(request.form['quantity'])
    
    cursor = db.cursor(dictionary=True)
    
    try:
        cursor.execute("INSERT INTO coffees (name, price, quantity) VALUES (%s, %s, %s)", (name, price, quantity))
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"An error occurred: {e}")
        return redirect(url_for('owner_dashboard', error="Coffee name already exists"))
    finally:
        cursor.close()
    
    return redirect(url_for('owner_dashboard'))


@app.route('/delete_coffee/<int:coffee_id>', methods=['POST'])
def delete_coffee(coffee_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    cursor = db.cursor(dictionary=True)
    cursor.execute("DELETE FROM coffees WHERE id = %s", (coffee_id,))
    db.commit()
    cursor.close()
    
    return redirect(url_for('owner_dashboard'))

# Flask 后端代码
@app.route('/check_duplicate_coffee', methods=['POST'])
def check_duplicate_coffee():
    name = request.json.get('name')
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM coffees WHERE name = %s", (name,))
    existing_coffee = cursor.fetchone()
    cursor.close()
    if existing_coffee:
        return jsonify({'exists': True})
    else:
        return jsonify({'exists': False})

# @app.route('/customer_dashboard', methods=['GET', 'POST'])
# def customer_dashboard():
#     if 'user_id' not in session:
#         return redirect(url_for('login'))
    
#     if request.method == 'POST':
#         coffee_id = int(request.form['coffee_id'])
#         quantity = int(request.form['quantity'])
#         temperature = request.form['temperature']
        
#         cursor = db.cursor(dictionary=True)
#         cursor.execute("SELECT * FROM coffees WHERE id = %s", (coffee_id,))
#         coffee = cursor.fetchone()
        
#         if coffee and coffee['quantity'] >= quantity:
#             total_price = coffee['price'] * quantity
#             cursor.execute("INSERT INTO orders (user_id, coffee_id, quantity, total_price, order_date, temperature) VALUES (%s, %s, %s, %s, NOW(), %s)", (session['user_id'], coffee_id, quantity, total_price, temperature))
#             db.commit()
#             cursor.execute("UPDATE coffees SET quantity = quantity - %s WHERE id = %s", (quantity, coffee_id))
#             db.commit()
            
#             # Update points with the total_price of the order
#             cursor.execute("UPDATE points SET points = points + %s WHERE user_id = %s", (total_price, session['user_id']))
#             db.commit()
            
#             order_success = True
#         else:
#             order_success = False
        
#         cursor.execute("SELECT * FROM points WHERE user_id = %s", (session['user_id'],))
#         points = cursor.fetchone()
        
#         cursor.execute("SELECT * FROM coffees")
#         coffees = cursor.fetchall()

#         # Fetch orders for the current user
#         cursor.execute("SELECT * FROM orders WHERE user_id = %s", (session['user_id'],))
#         orders = cursor.fetchall()
        
#         return render_template('customer_dashboard.html', points=points, coffees=coffees, orders=orders, order_success=order_success)
    
#     cursor = db.cursor(dictionary=True)
#     cursor.execute("SELECT * FROM points WHERE user_id = %s", (session['user_id'],))
#     points = cursor.fetchone()
    
#     cursor.execute("SELECT * FROM coffees")
#     coffees = cursor.fetchall()
    
#     # Fetch orders for the current user
#     cursor.execute("SELECT * FROM orders WHERE user_id = %s", (session['user_id'],))
#     orders = cursor.fetchall()
    
#     return render_template('customer_dashboard.html', points=points, coffees=coffees, orders=orders, order_success=None)
@app.route('/customer_dashboard', methods=['GET', 'POST'])
def customer_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        coffee_id = int(request.form['coffee_id'])
        quantity = int(request.form['quantity'])
        temperature = request.form['temperature']
        
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM coffees WHERE id = %s", (coffee_id,))
        coffee = cursor.fetchone()
        
        if coffee and coffee['quantity'] >= quantity:
            total_price = coffee['price'] * quantity
            cursor.execute("INSERT INTO orders (user_id, coffee_id, quantity, total_price, order_date, temperature) VALUES (%s, %s, %s, %s, NOW(), %s)", (session['user_id'], coffee_id, quantity, total_price, temperature))
            db.commit()
            cursor.execute("UPDATE coffees SET quantity = quantity - %s WHERE id = %s", (quantity, coffee_id))
            db.commit()
            
            # Update balance by deducting the total_price
            cursor.execute("UPDATE balances SET balance = balance - %s WHERE user_id = %s", (total_price, session['user_id']))
            db.commit()
            
            order_success = True
        else:
            order_success = False
        
        cursor.execute("SELECT * FROM points WHERE user_id = %s", (session['user_id'],))
        points = cursor.fetchone()
        
        cursor.execute("SELECT * FROM coffees")
        coffees = cursor.fetchall()

        # Fetch orders for the current user
        cursor.execute("SELECT * FROM orders WHERE user_id = %s", (session['user_id'],))
        orders = cursor.fetchall()

        # Fetch recharges for the current user
        cursor.execute("SELECT * FROM recharges WHERE user_id = %s", (session['user_id'],))
        recharges = cursor.fetchall()
        
        # Fetch balance for the current user
        cursor.execute("SELECT * FROM balances WHERE user_id = %s", (session['user_id'],))
        balance = cursor.fetchone()['balance']
        
        return render_template('customer_dashboard.html', points=points, coffees=coffees, orders=orders, recharges=recharges, balance=balance, order_success=order_success)
    
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM points WHERE user_id = %s", (session['user_id'],))
    points = cursor.fetchone()
    
    cursor.execute("SELECT * FROM coffees")
    coffees = cursor.fetchall()
    
    # Fetch orders for the current user
    cursor.execute("SELECT * FROM orders WHERE user_id = %s", (session['user_id'],))
    orders = cursor.fetchall()

    # Fetch recharges for the current user
    cursor.execute("SELECT * FROM recharges WHERE user_id = %s", (session['user_id'],))
    recharges = cursor.fetchall()
    
    # Fetch balance for the current user
    cursor.execute("SELECT * FROM balances WHERE user_id = %s", (session['user_id'],))
    balance = cursor.fetchone()['balance']
    
    return render_template('customer_dashboard.html', points=points, coffees=coffees, orders=orders, recharges=recharges, balance=balance, order_success=None)

# @app.route('/customer_dashboard', methods=['GET', 'POST'])
# def customer_dashboard():
#     if 'user_id' not in session:
#         return redirect(url_for('login'))
    
#     if request.method == 'POST':
#         coffee_id = int(request.form['coffee_id'])
#         quantity = int(request.form['quantity'])
#         temperature = request.form['temperature']
        
#         cursor = db.cursor(dictionary=True)
#         cursor.execute("SELECT * FROM coffees WHERE id = %s", (coffee_id,))
#         coffee = cursor.fetchone()
        
#         if coffee and coffee['quantity'] >= quantity:
#             total_price = coffee['price'] * quantity
#             cursor.execute("INSERT INTO orders (user_id, coffee_id, quantity, total_price, order_date, temperature) VALUES (%s, %s, %s, %s, NOW(), %s)", (session['user_id'], coffee_id, quantity, total_price, temperature))
#             db.commit()
#             cursor.execute("UPDATE coffees SET quantity = quantity - %s WHERE id = %s", (quantity, coffee_id))
#             db.commit()
            
#             # Update points with the total_price of the order
#             cursor.execute("UPDATE points SET points = points + %s WHERE user_id = %s", (total_price, session['user_id']))
#             db.commit()
            
#             order_success = True
#         else:
#             order_success = False
        
#         cursor.execute("SELECT * FROM points WHERE user_id = %s", (session['user_id'],))
#         points = cursor.fetchone()
        
#         cursor.execute("SELECT * FROM coffees")
#         coffees = cursor.fetchall()

#         # Fetch orders for the current user
#         cursor.execute("SELECT * FROM orders WHERE user_id = %s", (session['user_id'],))
#         orders = cursor.fetchall()

#         # Fetch recharges for the current user
#         cursor.execute("SELECT * FROM recharges WHERE user_id = %s", (session['user_id'],))
#         recharges = cursor.fetchall()
        
#         return render_template('customer_dashboard.html', points=points, coffees=coffees, orders=orders, recharges=recharges, order_success=order_success)
    
#     cursor = db.cursor(dictionary=True)
#     cursor.execute("SELECT * FROM points WHERE user_id = %s", (session['user_id'],))
#     points = cursor.fetchone()
    
#     cursor.execute("SELECT * FROM coffees")
#     coffees = cursor.fetchall()
    
#     # Fetch orders for the current user
#     cursor.execute("SELECT * FROM orders WHERE user_id = %s", (session['user_id'],))
#     orders = cursor.fetchall()

#     # Fetch recharges for the current user
#     cursor.execute("SELECT * FROM recharges WHERE user_id = %s", (session['user_id'],))
#     recharges = cursor.fetchall()
    
#     return render_template('customer_dashboard.html', points=points, coffees=coffees, orders=orders, recharges=recharges, order_success=None)

# @app.route('/register', methods=['GET', 'POST'])
# def register():
#     if request.method == 'POST':
#         username = request.form['username']
#         password = request.form['password']
        
#         cursor = db.cursor(dictionary=True)
#         cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
#         user = cursor.fetchone()
        
#         if user:
#             error = 'Username already exists'
#             return render_template('register.html', error=error)
#         else:
#             cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (%s, %s, 'customer')", (username, password))
#             db.commit()
#             return redirect(url_for('login'))
    
#     return render_template('register.html', error=None)
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        
        if user:
            error = 'Username already exists'
            return render_template('register.html', error=error)
        else:
            cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (%s, %s, 'customer')", (username, password))
            db.commit()
            cursor.execute("INSERT INTO balances (user_id, balance) VALUES (LAST_INSERT_ID(), 0)")
            db.commit()
            return redirect(url_for('login'))
    
    return render_template('register.html', error=None)

# @app.route('/place_order', methods=['POST'])
# def place_order():
#     if 'user_id' not in session or session['role'] != 'customer':
#         return redirect(url_for('login'))
    
#     coffee_id = int(request.form['coffee_id'])
#     quantity = int(request.form['quantity'])
    
#     cursor = db.cursor(dictionary=True)
#     cursor.execute("SELECT * FROM coffees WHERE id = %s", (coffee_id,))
#     coffee = cursor.fetchone()
    
#     cursor.execute("SELECT SUM(amount) as balance FROM recharges WHERE user_id = %s", (session['user_id'],))
#     balance = cursor.fetchone()['balance']
    
#     if coffee and coffee['quantity'] >= quantity:
#         total_price = coffee['price'] * quantity
        
#         if balance >= total_price:
#             cursor.execute("INSERT INTO orders (user_id, coffee_id, quantity, total_price, order_date) VALUES (%s, %s, %s, %s, NOW())", (session['user_id'], coffee_id, quantity, total_price))
#             db.commit()
#             cursor.execute("UPDATE coffees SET quantity = quantity - %s WHERE id = %s", (quantity, coffee_id))
#             db.commit()
#             cursor.execute("INSERT INTO recharges (user_id, amount, recharge_date) VALUES (%s, %s, NOW())", (session['user_id'], -total_price))
#             db.commit()
#             message = "Order placed successfully!"
#         else:
#             message = "Insufficient balance!"
#     else:
#         message = "Not enough quantity available!"
    
#     cursor.execute("SELECT amount, recharge_date FROM recharges WHERE user_id = %s", (session['user_id'],))
#     recharges = cursor.fetchall()
#     cursor.execute("SELECT * FROM coffees")
#     coffees = cursor.fetchall()
#     cursor.execute("SELECT SUM(amount) as balance FROM recharges WHERE user_id = %s", (session['user_id'],))
#     balance = cursor.fetchone()['balance']
    
#     return render_template('customer_dashboard.html', username=session['username'], recharges=recharges, coffees=coffees, balance=balance, message=message)

@app.route('/place_order', methods=['POST'])
def place_order():
    if 'user_id' not in session or session['role'] != 'customer':
        return redirect(url_for('login'))
    
    coffee_id = int(request.form['coffee_id'])
    quantity = int(request.form['quantity'])
    
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM coffees WHERE id = %s", (coffee_id,))
    coffee = cursor.fetchone()
    
    cursor.execute("SELECT SUM(amount) as balance FROM recharges WHERE user_id = %s", (session['user_id'],))
    balance = cursor.fetchone()['balance']
    
    if coffee and coffee['quantity'] >= quantity:
        total_price = coffee['price'] * quantity
        
        if balance >= total_price:
            # 扣除相应下单金额
            cursor.execute("INSERT INTO orders (user_id, coffee_id, quantity, total_price, order_date) VALUES (%s, %s, %s, %s, NOW())", (session['user_id'], coffee_id, quantity, total_price))
            db.commit()
            cursor.execute("UPDATE coffees SET quantity = quantity - %s WHERE id = %s", (quantity, coffee_id))
            db.commit()
            cursor.execute("INSERT INTO recharges (user_id, amount, recharge_date) VALUES (%s, %s, NOW())", (session['user_id'], -total_price))
            db.commit()
            message = "Order placed successfully! Your account has been deducted: " + str(total_price) + " points."
        else:
            message = "Insufficient balance! Please recharge your account."
    else:
        message = "Not enough quantity available!"
    
    cursor.execute("SELECT amount, recharge_date FROM recharges WHERE user_id = %s", (session['user_id'],))
    recharges = cursor.fetchall()
    cursor.execute("SELECT * FROM coffees")
    coffees = cursor.fetchall()
    cursor.execute("SELECT SUM(amount) as balance FROM recharges WHERE user_id = %s", (session['user_id'],))
    balance = cursor.fetchone()['balance']
    
    return render_template('customer_dashboard.html', username=session['username'], recharges=recharges, coffees=coffees, balance=balance, message=message)
# 充值页面
# 充值页面


if __name__ == '__main__':
    app.run(debug=True)

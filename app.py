from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
from flask_bcrypt import Bcrypt
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

mysql = MySQL(app)
bcrypt = Bcrypt(app)

# ---------------------------
# HOME
# ---------------------------
@app.route('/')
def home():
    return render_template("home.html")

# ---------------------------
# SIGNUP
# ---------------------------
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users(username, email, password) VALUES(%s,%s,%s)",
                    (username, email, password))
        mysql.connection.commit()
        cur.close()

        flash("Account Created Successfully!", "success")
        return redirect(url_for('login'))

    return render_template("signup.html")

# ---------------------------
# LOGIN
# ---------------------------
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cur.fetchone()
        cur.close()

        if user and bcrypt.check_password_hash(user[3], password):
            session['user_id'] = user[0]
            session['username'] = user[1]
            flash("Login Successful!", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid Credentials", "danger")

    return render_template("login.html")

# ---------------------------
# DASHBOARD
# ---------------------------
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()
    cur.execute("SELECT subject, marks FROM grades WHERE user_id=%s",
                (session['user_id'],))
    grades = cur.fetchall()
    cur.close()

    return render_template("dashboard.html", grades=grades)

# ---------------------------
# PROFILE UPDATE
# ---------------------------
@app.route('/profile', methods=['GET','POST'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()

    if request.method == 'POST':
        full_name = request.form['full_name']
        cur.execute("UPDATE users SET full_name=%s WHERE id=%s",
                    (full_name, session['user_id']))
        mysql.connection.commit()
        flash("Profile Updated!", "success")

    cur.execute("SELECT username, email, full_name FROM users WHERE id=%s",
                (session['user_id'],))
    user = cur.fetchone()
    cur.close()

    return render_template("profile.html", user=user)

# ---------------------------
# RESET PASSWORD
# ---------------------------
@app.route('/reset_password', methods=['POST'])
def reset_password():
    new_password = bcrypt.generate_password_hash(request.form['new_password']).decode('utf-8')

    cur = mysql.connection.cursor()
    cur.execute("UPDATE users SET password=%s WHERE id=%s",
                (new_password, session['user_id']))
    mysql.connection.commit()
    cur.close()

    flash("Password Reset Successfully!", "success")
    return redirect(url_for('profile'))
  
  # ---------------- ADMIN LOGIN ----------------
@app.route('/admin_login', methods=['GET','POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email=%s AND role='admin'", (email,))
        user = cur.fetchone()
        cur.close()

        if user and bcrypt.check_password_hash(user[3], password):
            session['admin_id'] = user[0]
            session['admin_name'] = user[1]
            flash("Admin Login Successful!", "success")
            return redirect(url_for('admin_dashboard'))
        else:
            flash("Invalid Admin Credentials", "danger")

    return render_template("admin_login.html")
  
# ---------------- ADMIN DASHBOARD ----------------
@app.route('/admin_dashboard')
def admin_dashboard():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))

    cur = mysql.connection.cursor()
    cur.execute("SELECT id, username FROM users WHERE role='student'")
    students = cur.fetchall()
    cur.close()

    return render_template("admin_dashboard.html", students=students)
  
  # ---------------- ADD GRADE ----------------
@app.route('/add_grade', methods=['POST'])
def add_grade():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))

    user_id = request.form['user_id']
    subject = request.form['subject']
    marks = request.form['marks']

    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO grades (user_id, subject, marks) VALUES (%s,%s,%s)",
                (user_id, subject, marks))
    mysql.connection.commit()
    cur.close()

    flash("Grade Added Successfully!", "success")
    return redirect(url_for('admin_dashboard'))
  
# ---------------------------
# LOGOUT
# ---------------------------
@app.route('/logout')
def logout():
    session.clear()
    flash("Logged Out Successfully!", "info")
    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(debug=True)
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import threading
import time
import requests
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SECRET_KEY'] = 'your_secret_key'
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), nullable=False)  # 添加用户电子邮件
    notify = db.Column(db.Boolean, default=False)  # 通知开关

class Website(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(300), nullable=False)
    interval = db.Column(db.Integer, nullable=False)  # 访问间隔（秒）
    is_active = db.Column(db.Boolean, default=True)  # 用于标记网站是否处于活动状态

# 存储活动线程
active_threads = {}

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def send_notification(email, url):
    msg = MIMEText(f"成功访问: {url}，访问时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}")
    msg['Subject'] = '网站访问通知'
    msg['From'] = 'your_email@example.com'  # 发送者的电子邮件地址
    msg['To'] = email

    try:
        with smtplib.SMTP('smtp.example.com', 587) as server:  # 替换为您的SMTP服务器
            server.starttls()
            server.login('your_email@example.com', 'your_email_password')  # 发送者的电子邮件和密码
            server.send_message(msg)
    except Exception as e:
        print(f"发送通知时发生错误: {e}")

def visit_website(url, interval, website_id):
    while True:
        time.sleep(interval)
        try:
            response = requests.get(url)
            if response.status_code == 200:
                print(f"成功访问: {url}")
                # 发送通知
                user = current_user
                if user.notify:
                    send_notification(user.email, url)
            else:
                print(f"访问失败: {url}, 状态码: {response.status_code}")
        except Exception as e:
            print(f"访问 {url} 时发生错误: {e}")
        # 检查网站是否被标记为不活动
        if not active_threads.get(website_id, True):
            break

@app.route('/', methods=['GET', 'POST'])
def home():
    if current_user.is_authenticated:
        websites = Website.query.all()
        return render_template('dashboard.html', websites=websites, notify=current_user.notify)
    
    if request.method == 'POST':
        if 'register' in request.form:
            return register()
        elif 'login' in request.form:
            return login()
    
    return render_template('index.html')

def register():
    username = request.form.get('username')
    password = request.form.get('password')
    email = request.form.get('email')  # 获取电子邮件

    if not username or not password or not email:
        flash('用戶名、密碼和電子郵件不可為空！', 'danger')
        return redirect(url_for('home'))

    if User.query.filter_by(username=username).first():
        flash('用戶名已存在！', 'danger')
        return redirect(url_for('home'))

    new_user = User(username=username, password=generate_password_hash(password), email=email)
    db.session.add(new_user)
    db.session.commit()
    flash('註冊成功！請登入。', 'success')
    return redirect(url_for('home'))

def login():
    username = request.form.get('username')
    password = request.form.get('password')
    user = User.query.filter_by(username=username).first()
    
    if user and check_password_hash(user.password, password):
        login_user(user)
        return redirect(url_for('home'))
    
    flash('登入失敗，請檢查用戶名和密碼。', 'danger')
    return redirect(url_for('home'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('成功登出！', 'success')
    return redirect(url_for('home'))

@app.route('/add_website', methods=['POST'])
@login_required
def add_website():
    url = request.form.get('url')
    interval = request.form.get('interval')

    if not url or not interval.isdigit():
        flash('請正確填寫網站 URL 和訪問間隔！', 'danger')
        return redirect(url_for('home'))

    interval = int(interval)
    new_website = Website(url=url, interval=interval)
    db.session.add(new_website)
    db.session.commit()

    # 启动访问线程
    website_id = new_website.id
    active_threads[website_id] = True  # 标记为活动
    threading.Thread(target=visit_website, args=(url, interval, website_id)).start()

    flash('網站已添加！', 'success')
    return redirect(url_for('home'))

@app.route('/delete_website/<int:id>', methods=['POST'])
@login_required
def delete_website(id):
    website = Website.query.get(id)
    if website:
        # 标记网站为不活动
        active_threads[id] = False
        db.session.delete(website)
        db.session.commit()
        flash('網站已刪除！', 'success')
    else:
        flash('網站不存在！', 'danger')
    return redirect(url_for('home'))

@app.route('/toggle_notify', methods=['POST'])
@login_required
def toggle_notify():
    user = current_user
    user.notify = not user.notify
    db.session.commit()
    flash('通知已更新！', 'success')
    return redirect(url_for('home'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # 创建数据库表
    app.run(debug=True, port=10000, host='0.0.0.0')

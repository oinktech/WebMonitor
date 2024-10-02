from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import threading
import time
import requests
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your_default_secret_key')
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)

# 用于追踪访问线程的全局变量
thread_dict = {}

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

class Website(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(300), nullable=False)
    interval = db.Column(db.Integer, nullable=False)  # 访问间隔（秒）

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 用于停止线程的标志
class StoppableThread(threading.Thread):
    def __init__(self, *args, **kwargs):
        super(StoppableThread, self).__init__(*args, **kwargs)
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()

# 网站访问线程函数
def visit_website(url, interval, stop_event):
    while not stop_event.is_set():
        time.sleep(interval)
        try:
            response = requests.get(url)
            if response.status_code == 200:
                print(f"成功访问: {url}")
            else:
                print(f"访问失败: {url}, 状态码: {response.status_code}")
        except Exception as e:
            print(f"访问 {url} 时发生错误: {e}")

@app.route('/', methods=['GET', 'POST'])
def home():
    if current_user.is_authenticated:
        websites = Website.query.all()
        return render_template('dashboard.html', websites=websites)

    if request.method == 'POST':
        if 'register' in request.form:
            return register()
        elif 'login' in request.form:
            return login()

    return render_template('index.html')

def register():
    username = request.form.get('username')
    password = request.form.get('password')

    if not username or not password:
        flash('用戶名和密碼不可為空！', 'danger')
        return redirect(url_for('home'))

    if User.query.filter_by(username=username).first():
        flash('用戶名已存在！', 'danger')
        return redirect(url_for('home'))

    new_user = User(username=username, password=generate_password_hash(password, method='pbkdf2:sha256'))
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

    # 创建线程并保存到字典中
    stop_event = threading.Event()
    thread = threading.Thread(target=visit_website, args=(url, interval, stop_event))
    thread.start()
    thread_dict[new_website.id] = (thread, stop_event)

    flash('網站已添加！', 'success')
    return redirect(url_for('home'))

@app.route('/delete_website/<int:id>', methods=['POST'])
@login_required
def delete_website(id):
    website = Website.query.get(id)
    if website:
        # 停止线程
        if id in thread_dict:
            thread, stop_event = thread_dict.pop(id)
            stop_event.set()  # 设置停止标志，终止线程
            thread.join()  # 等待线程安全结束

        db.session.delete(website)
        db.session.commit()
        flash('網站已刪除並停止訪問！', 'success')
    else:
        flash('網站不存在！', 'danger')
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.app_context().push()  # 确保在应用上下文中运行
    db.create_all()  # 创建数据库表
    app.run(debug=True, port=10000, host='0.0.0.0')

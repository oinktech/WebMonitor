from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import threading
import time
import requests
from pymongo import MongoClient
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
db_client = MongoClient(os.getenv('MONGODB_URI'))
db = db_client['website_monitor']
login_manager = LoginManager()
login_manager.init_app(app)

class User(db['users']):
    def __init__(self, username, password):
        self.username = username
        self.password = generate_password_hash(password)

class Website:
    def __init__(self, url, interval):
        self.url = url
        self.interval = interval
        self.notifications_enabled = True  # 默认为开启状态

@login_manager.user_loader
def load_user(user_id):
    user_data = db['users'].find_one({"_id": user_id})
    return User(user_data['username'], user_data['password']) if user_data else None

def visit_website(url, interval):
    while True:
        time.sleep(interval)
        try:
            response = requests.get(url)
            if response.status_code == 200:
                print(f"成功访问: {url}")
                if current_user.is_authenticated:
                    notify_user(url)  # 发送通知
            else:
                print(f"访问失败: {url}, 状态码: {response.status_code}")
        except Exception as e:
            print(f"访问 {url} 时发生错误: {e}")

def notify_user(url):
    # 假设这里实现了发送通知的逻辑
    print(f"发送通知: {url} 被访问于 {time.ctime()}")

@app.route('/', methods=['GET', 'POST'])
def home():
    if current_user.is_authenticated:
        websites = db['websites'].find()
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

    if db['users'].find_one({"username": username}):
        flash('用戶名已存在！', 'danger')
        return redirect(url_for('home'))

    new_user = User(username=username, password=password)
    db['users'].insert_one({"username": username, "password": new_user.password})
    flash('註冊成功！請登入。', 'success')
    return redirect(url_for('home'))

def login():
    username = request.form.get('username')
    password = request.form.get('password')
    user_data = db['users'].find_one({"username": username})
    
    if user_data and check_password_hash(user_data['password'], password):
        login_user(User(username, user_data['password']))
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
    db['websites'].insert_one({"url": url, "interval": interval, "notifications_enabled": True})
    threading.Thread(target=visit_website, args=(url, interval)).start()
    flash('網站已添加！', 'success')
    return redirect(url_for('home'))

@app.route('/delete_website/<string:url>', methods=['POST'])
@login_required
def delete_website(url):
    result = db['websites'].delete_one({"url": url})
    if result.deleted_count > 0:
        flash('網站已刪除！', 'success')
    else:
        flash('網站不存在！', 'danger')
    return redirect(url_for('home'))

@app.route('/toggle_notifications/<string:url>', methods=['POST'])
@login_required
def toggle_notifications(url):
    website = db['websites'].find_one({"url": url})
    if website:
        new_state = not website['notifications_enabled']
        db['websites'].update_one({"url": url}, {"$set": {"notifications_enabled": new_state}})
        flash(f'通知已{"開啟" if new_state else "關閉"}！', 'success')
    else:
        flash('網站不存在！', 'danger')
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True, port=10000, host='0.0.0.0')

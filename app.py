from flask import Flask, render_template, request, redirect, url_for, flash
from flask_pymongo import PyMongo
from flask_login import UserMixin, LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import threading
import time
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['MONGO_URI'] = os.getenv('MONGO_URI')  # Load MongoDB URI from .env file
app.config['SECRET_KEY'] = 'your_secret_key'
mongo = PyMongo(app)

login_manager = LoginManager()
login_manager.init_app(app)

class User(UserMixin):
    def __init__(self, username, password):
        self.username = username
        self.password = password

@login_manager.user_loader
def load_user(user_id):
    user_data = mongo.db.users.find_one({"_id": user_id})
    if user_data:
        return User(username=user_data['username'], password=user_data['password'])
    return None

def visit_website(url, interval):
    while True:
        time.sleep(interval)
        try:
            response = requests.get(url)
            if response.status_code == 200:
                print(f"成功访问: {url}")
                if mongo.db.websites.find_one({"url": url, "notifications_enabled": True}):
                    notify_user(url)
            else:
                print(f"访问失败: {url}, 状态码: {response.status_code}")
        except Exception as e:
            print(f"访问 {url} 时发生错误: {e}")

def notify_user(url):
    print(f"通知: 成功访问 {url} at {time.ctime()}")

@app.route('/', methods=['GET', 'POST'])
def home():
    if current_user.is_authenticated:
        websites = mongo.db.websites.find()
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

    if mongo.db.users.find_one({"username": username}):
        flash('用戶名已存在！', 'danger')
        return redirect(url_for('home'))

    mongo.db.users.insert_one({
        "username": username,
        "password": generate_password_hash(password, method='pbkdf2:sha256')
    })
    flash('註冊成功！請登入。', 'success')
    return redirect(url_for('home'))

def login():
    username = request.form.get('username')
    password = request.form.get('password')
    user_data = mongo.db.users.find_one({"username": username})

    if user_data and check_password_hash(user_data['password'], password):
        login_user(User(username=username, password=user_data['password']))
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
    mongo.db.websites.insert_one({"url": url, "interval": interval, "notifications_enabled": False})
    threading.Thread(target=visit_website, args=(url, interval)).start()
    flash('網站已添加！', 'success')
    return redirect(url_for('home'))

@app.route('/delete_website/<string:url>', methods=['POST'])
@login_required
def delete_website(url):
    mongo.db.websites.delete_one({"url": url})
    flash('網站已刪除！', 'success')
    return redirect(url_for('home'))

@app.route('/toggle_notifications/<string:url>', methods=['POST'])
@login_required
def toggle_notifications(url):
    website = mongo.db.websites.find_one({"url": url})
    if website:
        current_state = website.get("notifications_enabled", False)
        new_state = not current_state
        mongo.db.websites.update_one({"url": url}, {"$set": {"notifications_enabled": new_state}})
        flash('通知狀態已更新！', 'success')
    else:
        flash('網站不存在！', 'danger')
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True, port=10000, host='0.0.0.0')

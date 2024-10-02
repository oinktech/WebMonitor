# WebMonitor

[![Language](https://img.shields.io/badge/Language-Python-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Framework-Flask-green.svg)](https://flask.palletsprojects.com/)
[![Database](https://img.shields.io/badge/Database-SQLite-orange.svg)](https://www.sqlite.org/index.html)

**选择语言: [繁體中文](#繁體中文) | [English](#english)**

---

## 繁體中文

WebMonitor 是一個簡單的網站監控工具，可以定期訪問指定的網站並發送通知。該應用允許用戶註冊、登錄，並添加需要監控的網站。

### 功能

- **註冊和登錄**：用戶可以創建帳戶並登錄。
- **網站監控**：可以添加、刪除網站，並設置訪問時間間隔。
- **通知系統**：執行網站訪問後會發送通知，包含訪問網址和時間。
- **可開啟或關閉通知**：用戶可以控制是否接收通知。

### 使用方法

1. 克隆儲存庫：
   ```bash
   git clone https://github.com/oinktech/WebMonitor.git
   cd WebMonitor
   ```

2. 安裝依賴：
   ```bash
   pip install -r requirements.txt
   ```

3. 運行應用：
   ```bash
   python app.py
   ```

4. 在瀏覽器中訪問 `http://127.0.0.1:10000`。

### 線上體驗

[線上體驗版](https://webmonitor-fdn3.onrender.com/)。

---

## English

WebMonitor is a simple website monitoring tool that can periodically visit specified websites and send notifications. The application allows users to register, log in, and add websites to monitor.

### Features

- **Registration and Login**: Users can create accounts and log in.
- **Website Monitoring**: Add and delete websites, and set access time intervals.
- **Notification System**: Send notifications after executing website visits, including the visited URL and time.
- **Enable/Disable Notifications**: Users can control whether to receive notifications.

### How to Use

1. Clone the repository:
   ```bash
   git clone https://github.com/oinktech/WebMonitor.git
   cd WebMonitor
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python app.py
   ```

4. Access the application in your browser at `http://127.0.0.1:10000`.

### Live Demo

[Live Demo](https://webmonitor-fdn3.onrender.com/)。

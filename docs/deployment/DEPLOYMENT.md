# デプロイメントガイド

このドキュメントでは、議事メモRAGチャットボットの本番環境へのデプロイと運用設定について説明します。

## 📦 デプロイの種類

このシステムは以下の3つの運用形態をサポートしています:

1. **ローカル開発環境** - 開発者のPC上で動作
2. **スタンドアロンサーバー** - 専用サーバー上で動作
3. **クラウド環境** - AWS/Azure/GCP上で動作

---

## 🖥️ スタンドアロンサーバーへのデプロイ

### 前提条件

- Ubuntu 20.04 LTS以上 / CentOS 8以上
- Python 3.9以上
- 2GB以上のRAM
- 20GB以上のディスク容量

### 1. サーバーの準備

```bash
# システムの更新
sudo apt update && sudo apt upgrade -y

# Python 3.9以上のインストール
sudo apt install python3.9 python3.9-venv python3-pip -y

# 必要なツールのインストール
sudo apt install git curl -y
```

### 2. プロジェクトのデプロイ

```bash
# アプリケーション用ユーザーの作成
sudo useradd -m -s /bin/bash ragbot
sudo su - ragbot

# プロジェクトのクローン
cd /home/ragbot
git clone <repository-url> ragbot
cd ragbot

# 仮想環境の作成とパッケージのインストール
python3.9 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. 環境設定

```bash
# .envファイルの作成
cp .env.example .env
nano .env

# credentials.jsonの配置（Google Drive使用時）
# 開発環境からコピーするか、再作成
scp credentials.json ragbot@server:/home/ragbot/ragbot/
```

### 4. systemdサービスの設定

#### Streamlitアプリ用サービス

```bash
# サービスファイルの作成
sudo nano /etc/systemd/system/ragbot.service
```

```ini
[Unit]
Description=RAG Chatbot Streamlit Service
After=network.target

[Service]
Type=simple
User=ragbot
WorkingDirectory=/home/ragbot/ragbot
Environment="PATH=/home/ragbot/ragbot/venv/bin"
ExecStart=/home/ragbot/ragbot/venv/bin/streamlit run app/main.py --server.port 8501 --server.address 0.0.0.0
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### 日次更新用サービス

```bash
# タイマーサービスファイルの作成
sudo nano /etc/systemd/system/ragbot-update.service
```

```ini
[Unit]
Description=RAG Chatbot Vector Store Update
After=network.target

[Service]
Type=oneshot
User=ragbot
WorkingDirectory=/home/ragbot/ragbot
Environment="PATH=/home/ragbot/ragbot/venv/bin"
ExecStart=/home/ragbot/ragbot/venv/bin/python scripts/update_vector_store.py
StandardOutput=append:/home/ragbot/ragbot/logs/update.log
StandardError=append:/home/ragbot/ragbot/logs/update_error.log
```

```bash
# タイマーファイルの作成
sudo nano /etc/systemd/system/ragbot-update.timer
```

```ini
[Unit]
Description=RAG Chatbot Update Timer
Requires=ragbot-update.service

[Timer]
OnCalendar=daily
OnCalendar=*-*-* 02:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

### 5. サービスの有効化と起動

```bash
# systemdをリロード
sudo systemctl daemon-reload

# Streamlitサービスの起動
sudo systemctl enable ragbot.service
sudo systemctl start ragbot.service

# 日次更新タイマーの有効化
sudo systemctl enable ragbot-update.timer
sudo systemctl start ragbot-update.timer

# ステータス確認
sudo systemctl status ragbot.service
sudo systemctl status ragbot-update.timer
```

### 6. リバースプロキシの設定（Nginx）

```bash
# Nginxのインストール
sudo apt install nginx -y

# 設定ファイルの作成
sudo nano /etc/nginx/sites-available/ragbot
```

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
}
```

```bash
# 設定の有効化
sudo ln -s /etc/nginx/sites-available/ragbot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 7. SSL証明書の設定（Let's Encrypt）

```bash
# Certbotのインストール
sudo apt install certbot python3-certbot-nginx -y

# SSL証明書の取得
sudo certbot --nginx -d your-domain.com

# 自動更新の設定（自動で設定済み）
sudo systemctl status certbot.timer
```

---

## ☁️ クラウド環境へのデプロイ

### AWS EC2へのデプロイ

#### 1. EC2インスタンスの起動

- **AMI**: Ubuntu 20.04 LTS
- **インスタンスタイプ**: t3.medium以上
- **ストレージ**: 30GB gp3
- **セキュリティグループ**:
  - SSH (22): 管理者IPのみ
  - HTTP (80): 0.0.0.0/0
  - HTTPS (443): 0.0.0.0/0

#### 2. Elastic IPの割り当て

```bash
# EC2コンソールからElastic IPを割り当て
```

#### 3. デプロイ

上記「スタンドアロンサーバーへのデプロイ」の手順に従う

### Docker化（オプション）

#### Dockerfileの作成

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# 依存パッケージのインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションのコピー
COPY app/ ./app/
COPY scripts/ ./scripts/

# データとログのディレクトリ
RUN mkdir -p /app/data /app/logs

# ポートの公開
EXPOSE 8501

# Streamlitの起動
CMD ["streamlit", "run", "app/main.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

#### docker-compose.ymlの作成

```yaml
version: '3.8'

services:
  ragbot:
    build: .
    ports:
      - "8501:8501"
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ./.env:/app/.env
      - ./credentials.json:/app/credentials.json
      - ./token.json:/app/token.json
    environment:
      - PYTHONUNBUFFERED=1
    restart: unless-stopped

  ragbot-updater:
    build: .
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ./.env:/app/.env
      - ./credentials.json:/app/credentials.json
      - ./token.json:/app/token.json
    command: python scripts/update_vector_store.py
    profiles:
      - updater
```

#### Dockerでの起動

```bash
# イメージのビルド
docker-compose build

# コンテナの起動
docker-compose up -d

# ログの確認
docker-compose logs -f

# 日次更新の手動実行
docker-compose --profile updater run ragbot-updater
```

---

## 🔄 日次更新の設定

### cron（Linux/macOS）

```bash
# cronの編集
crontab -e

# 毎日午前2時に実行
0 2 * * * cd /home/ragbot/ragbot && /home/ragbot/ragbot/venv/bin/python scripts/update_vector_store.py >> logs/update.log 2>&1
```

### systemd timer（推奨）

上記「スタンドアロンサーバーへのデプロイ」の手順を参照

### タスクスケジューラ（Windows Server）

1. タスクスケジューラを開く
2. タスクの作成
   - 名前: `RAGボット日次更新`
   - トリガー: 毎日 午前2:00
   - 操作: `C:\ragbot\venv\Scripts\python.exe C:\ragbot\scripts\update_vector_store.py`
   - 開始: `C:\ragbot`

---

## 📊 監視とメンテナンス

### ログの確認

```bash
# アプリケーションログ
tail -f logs/RAGChat_$(date +%Y%m%d).log

# 更新ログ
tail -f logs/UpdateVectorStore_$(date +%Y%m%d).log

# systemdログ
sudo journalctl -u ragbot.service -f
```

### ディスク使用量の監視

```bash
# データディレクトリのサイズ
du -sh data/

# ログディレクトリのサイズ
du -sh logs/

# 古いログの削除（30日以上前）
find logs/ -name "*.log" -mtime +30 -delete
```

### バックアップ

```bash
# ベクターストアのバックアップ
tar -czf backup_$(date +%Y%m%d).tar.gz data/ .env

# リモートサーバーへのバックアップ
rsync -avz data/ backup-server:/backups/ragbot/
```

### ヘルスチェック

```bash
# Streamlitの稼働確認
curl -I http://localhost:8501/_stcore/health

# サービスの状態確認
sudo systemctl is-active ragbot.service

# リソース使用状況
top -b -n 1 | grep streamlit
```

---

## 🚨 トラブルシューティング

### サービスが起動しない

```bash
# エラーログの確認
sudo journalctl -u ragbot.service -n 50 --no-pager

# サービスの再起動
sudo systemctl restart ragbot.service
```

### メモリ不足

```bash
# スワップの追加
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### ポートが使用中

```bash
# ポートを使用しているプロセスの確認
sudo lsof -i :8501

# プロセスの停止
sudo kill -9 <PID>
```

---

## 🔐 セキュリティのベストプラクティス

### 1. ファイアウォールの設定

```bash
# UFWの有効化
sudo ufw enable

# 必要なポートのみ許可
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

### 2. 自動セキュリティアップデート

```bash
# unattended-upgradesのインストール
sudo apt install unattended-upgrades -y
sudo dpkg-reconfigure -plow unattended-upgrades
```

### 3. 環境変数の保護

```bash
# .envファイルのパーミッション
chmod 600 .env
chmod 600 credentials.json
chmod 600 token.json
```

### 4. ログのローテーション

```bash
# logrotateの設定
sudo nano /etc/logrotate.d/ragbot
```

```
/home/ragbot/ragbot/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0644 ragbot ragbot
}
```

---

## 📈 スケーリング

### 水平スケーリング

複数のStreamlitインスタンスを起動し、ロードバランサーで負荷分散:

```nginx
upstream ragbot_backend {
    server localhost:8501;
    server localhost:8502;
    server localhost:8503;
}

server {
    location / {
        proxy_pass http://ragbot_backend;
    }
}
```

### 垂直スケーリング

- インスタンスタイプのアップグレード
- メモリの増設
- SSDストレージの使用

---

## 🔄 アップデート手順

```bash
# バックアップの作成
tar -czf backup_before_update_$(date +%Y%m%d).tar.gz data/ logs/ .env

# コードの更新
git pull origin main

# 依存パッケージの更新
source venv/bin/activate
pip install -r requirements.txt --upgrade

# サービスの再起動
sudo systemctl restart ragbot.service

# 動作確認
sudo systemctl status ragbot.service
curl -I http://localhost:8501/_stcore/health
```

---

本番環境での運用に関する質問や問題がある場合は、開発チームにお問い合わせください。


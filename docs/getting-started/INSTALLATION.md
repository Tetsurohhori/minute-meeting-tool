# インストールガイド

このドキュメントでは、議事メモRAGチャットボットの詳細なインストール手順を説明します。

## 📋 前提条件

### 必須環境
- Python 3.9以上
- pip (Pythonパッケージマネージャー)
- 10GB以上の空きディスク容量

### 必須アカウント
- OpenAI APIアカウント（有料プラン推奨）
- Google Cloud Platform（プロトタイプ環境の場合）
- Microsoft Azure（本番環境の場合）

---

## 🚀 セットアップ手順

### Step 1: リポジトリのクローン

```bash
# プロジェクトディレクトリに移動
cd /path/to/your/projects

# リポジトリをクローン（または展開）
# git clone <repository-url>
cd 議事メモツール
```

### Step 2: Python仮想環境の作成

```bash
# 仮想環境の作成
python3 -m venv venv

# 仮想環境の有効化
# macOS/Linux:
source venv/bin/activate

# Windows:
venv\Scripts\activate
```

### Step 3: 依存パッケージのインストール

```bash
# パッケージのインストール
pip install --upgrade pip
pip install -r requirements.txt

# インストール確認
pip list
```

### Step 4: 環境変数の設定

```bash
# .env.exampleをコピーして.envを作成
cp .env.example .env

# .envファイルを編集
nano .env  # または vim, code など
```

#### 必須設定項目

**OpenAI API設定**
```bash
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxx
```

**データソース選択**
```bash
# プロトタイプ環境
DATA_SOURCE=google_drive

# または本番環境
DATA_SOURCE=sharepoint
```

**ベクターストア設定**（デフォルト値で問題ない場合は変更不要）
```bash
VECTOR_STORE_PATH=./data/vector_store
METADATA_PATH=./data/metadata
```

**RAG設定**（デフォルト値で問題ない場合は変更不要）
```bash
EMBEDDING_MODEL=text-embedding-3-small
CHAT_MODEL=gpt-4o-mini
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
TOP_K_RESULTS=5
```

**ログ設定**
```bash
LOG_LEVEL=INFO
LOG_PATH=./logs
```

---

## 🔑 認証情報の設定

### オプションA: Google Drive（プロトタイプ環境）

#### 1. Google Cloud Platformでプロジェクトを作成

1. [Google Cloud Console](https://console.cloud.google.com/)にアクセス
2. 新しいプロジェクトを作成
3. プロジェクト名: `議事メモツール`（任意）

#### 2. Google Drive APIを有効化

1. APIとサービス > ライブラリ
2. "Google Drive API" を検索
3. 有効化をクリック

#### 3. OAuth 2.0クライアントIDを作成

1. APIとサービス > 認証情報
2. 認証情報を作成 > OAuth クライアント ID
3. アプリケーションの種類: デスクトップアプリ
4. 名前: `議事メモツール Desktop Client`
5. 作成後、JSONをダウンロード

#### 4. 認証情報の配置

```bash
# ダウンロードしたJSONファイルをcredentials.jsonにリネームして配置
cp ~/Downloads/client_secret_xxx.json ./credentials.json
```

#### 5. Google DriveのフォルダIDを取得

1. Google Driveで議事メモフォルダを開く
2. URLから対フォルダIDをコピー
   ```
   https://drive.google.com/drive/folders/1AbCdEfGhIjKlMnOpQrStUvWxYz
                                           ↑この部分がフォルダID
   ```
3. `.env`に設定
   ```bash
   GOOGLE_DRIVE_FOLDER_ID=1AbCdEfGhIjKlMnOpQrStUvWxYz
   ```

#### 6. 初回認証

```bash
# 初回実行時に認証フローが開始されます
python scripts/update_vector_store.py

# ブラウザが開き、Googleアカウントでログイン
# 権限を許可すると、token.jsonが自動生成されます
```

---

### オプションB: SharePoint（本番環境）

#### 1. Microsoft Azureでアプリを登録

1. [Azure Portal](https://portal.azure.com/)にアクセス
2. Azure Active Directory > アプリの登録
3. 新規登録をクリック

#### 2. アプリケーション情報の入力

- **名前**: `議事メモツールRAG`
- **サポートされているアカウントの種類**: この組織ディレクトリのみ
- **リダイレクトURI**: 空欄

#### 3. クライアントシークレットの作成

1. 作成したアプリ > 証明書とシークレット
2. 新しいクライアントシークレット
3. 説明: `RAGチャットボット用`
4. 有効期限: 24か月（推奨）
5. **シークレット値をコピー**（後で取得できません）

#### 4. API権限の付与

1. APIのアクセス許可
2. アクセス許可の追加 > Microsoft Graph
3. アプリケーションの許可
4. 以下を選択:
   - `Sites.Read.All`
   - `Files.Read.All`
5. 管理者の同意を許可

#### 5. `.env`に認証情報を設定

```bash
SHAREPOINT_SITE_URL=https://your-company.sharepoint.com/sites/your-site
SHAREPOINT_FOLDER_PATH=Shared Documents/議事メモ
SHAREPOINT_CLIENT_ID=<アプリケーション（クライアント）ID>
SHAREPOINT_CLIENT_SECRET=<クライアントシークレット値>
SHAREPOINT_TENANT_ID=<ディレクトリ（テナント）ID>
```

---

## 🗂️ 初回データ取り込み

### ベクターストアの構築

```bash
# 議事メモを読み込んでベクターDBを構築
python scripts/update_vector_store.py
```

実行内容:
1. データソース（Google Drive/SharePoint）から議事メモを取得
2. テキストを抽出
3. チャンク分割
4. ベクトル化（OpenAI Embeddings）
5. ChromaDBに保存

**注意**: 初回実行時は、議事メモの件数によって数分～数十分かかる場合があります。

---

## ✅ 動作確認

### 1. ベクターストアの確認

```bash
# dataディレクトリの確認
ls -la data/vector_store/
ls -la data/metadata/
```

### 2. チャットボットの起動

```bash
streamlit run app/main.py
```

ブラウザが自動で開き、`http://localhost:8501`にアクセスされます。

### 3. テスト質問

以下のような質問を試してみてください:
- 「最近の会議で決まったことを教えて」
- 「プロジェクトの課題は何ですか？」
- 「次回のアクションアイテムは？」

---

## 🔧 トラブルシューティング

### 問題1: `ModuleNotFoundError`

```bash
# 仮想環境が有効化されているか確認
which python
# 期待される出力: /path/to/議事メモツール/venv/bin/python

# 依存パッケージを再インストール
pip install -r requirements.txt
```

### 問題2: Google Drive認証エラー

```bash
# token.jsonを削除して再認証
rm token.json
python scripts/update_vector_store.py
```

### 問題3: SharePoint接続エラー

- クライアントID、シークレット、テナントIDが正しいか確認
- API権限が付与されているか確認
- 管理者の同意が完了しているか確認

### 問題4: OpenAI API エラー

```bash
# APIキーが有効か確認
echo $OPENAI_API_KEY

# APIキーのテスト
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

### 問題5: ベクターストアが空

```bash
# ログファイルを確認
cat logs/UpdateVectorStore_$(date +%Y%m%d).log

# データソースの接続を確認
python -c "from app.config.settings import Settings; s = Settings(); print(s.data_source)"
```

---

## 🧪 テストの実行

```bash
# すべてのテストを実行
pytest tests/ -v

# カバレッジ付きで実行
pytest tests/ --cov=app --cov-report=html

# 特定のテストのみ実行
pytest tests/test_config/ -v
```

---

## 📅 日次更新の設定

詳細は[DEPLOYMENT.md](DEPLOYMENT.md)を参照してください。

---

## 🆘 サポート

問題が解決しない場合は、以下の情報を添えてお問い合わせください:
- エラーメッセージの全文
- 実行したコマンド
- ログファイル（`logs/`ディレクトリ内）
- 環境情報（Pythonバージョン、OS）

```bash
# 環境情報の取得
python --version
pip list > installed_packages.txt
```

---

インストールが完了したら、[README.md](README.md)に戻って使い方を確認してください。


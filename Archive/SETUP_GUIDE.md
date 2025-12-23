# セットアップガイド

このガイドでは、議事メモRAGチャットボットの詳細なセットアップ手順を説明します。

## 📋 前提条件

- Python 3.9以上
- OpenAI APIキー
- Google Drive API認証情報（プロトタイプの場合）
- SharePoint認証情報（本番環境の場合）

## 🚀 クイックスタート

### 1. リポジトリのセットアップ

```bash
cd "/Users/tetsuroh/Documents/議事メモツール"
```

### 2. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

または仮想環境を使用する場合：

```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
# または
venv\Scripts\activate  # Windows

pip install -r requirements.txt
```

### 3. 環境設定

#### 方法A: セットアップスクリプトを使用（推奨）

```bash
python setup.py
```

対話式で必要な設定を入力できます。

#### 方法B: 手動で設定

`.env`ファイルを作成し、以下の内容を記入：

```bash
# 必須: OpenAI APIキー
OPENAI_API_KEY=sk-your-api-key-here

# データソース（google_drive または sharepoint）
DATA_SOURCE=google_drive

# Google Drive設定（プロトタイプ）
GOOGLE_DRIVE_FOLDER_ID=your_folder_id

# その他のオプション設定...
```

## 🔧 詳細設定

### プロトタイプ環境（Google Drive）

#### Step 1: Google Cloud Consoleでプロジェクトを作成

1. [Google Cloud Console](https://console.cloud.google.com/)にアクセス
2. 新しいプロジェクトを作成
3. プロジェクト名: 例「議事メモチャットボット」

#### Step 2: Google Drive APIを有効化

1. 左側メニューから「APIとサービス」→「ライブラリ」
2. 「Google Drive API」を検索
3. 「有効にする」をクリック

#### Step 3: OAuth 2.0認証情報を作成

1. 「APIとサービス」→「認証情報」
2. 「認証情報を作成」→「OAuth クライアント ID」
3. アプリケーションの種類: 「デスクトップアプリ」
4. 名前: 任意（例: 議事メモボット）
5. 「作成」をクリック

#### Step 4: credentials.jsonをダウンロード

1. 作成した認証情報の右側にあるダウンロードアイコンをクリック
2. ダウンロードしたJSONファイルを`credentials.json`にリネーム
3. プロジェクトルートに配置

```
議事メモツール/
├── credentials.json  ← ここに配置
├── .env
├── app.py
...
```

#### Step 5: Google DriveのフォルダIDを取得

1. Google Driveで議事メモ用のフォルダを開く
2. URLの最後の部分がフォルダID:
   ```
   https://drive.google.com/drive/folders/[この部分がフォルダID]
   ```
3. `.env`ファイルの`GOOGLE_DRIVE_FOLDER_ID`に設定

#### Step 6: 初回認証

```bash
python scripts/update_vector_store.py
```

初回実行時にブラウザが開き、Googleアカウントでの認証を求められます。
許可すると`token.json`が自動生成され、以降は自動認証されます。

### 本番環境（SharePoint）

#### Step 1: Azure ADでアプリを登録

1. [Azure Portal](https://portal.azure.com/)にアクセス
2. 「Azure Active Directory」→「アプリの登録」
3. 「新規登録」をクリック

#### Step 2: アプリケーションの設定

- 名前: 例「議事メモRAGボット」
- サポートされているアカウントの種類: 「この組織のディレクトリのみ」
- リダイレクトURI: 空欄でOK

#### Step 3: API権限の設定

1. 作成したアプリの「APIのアクセス許可」
2. 「アクセス許可の追加」→「SharePoint」
3. 「アプリケーションの許可」を選択
4. 以下の権限を追加:
   - `Sites.Read.All`
   - `Files.Read.All`
5. 「管理者の同意を与える」をクリック

#### Step 4: クライアントシークレットの作成

1. 「証明書とシークレット」
2. 「新しいクライアントシークレット」
3. 説明: 任意
4. 有効期限: 推奨は24ヶ月
5. 「追加」をクリック
6. **重要**: 表示される値をコピー（後で見れません）

#### Step 5: .envファイルに設定

```bash
DATA_SOURCE=sharepoint
SHAREPOINT_SITE_URL=https://your-company.sharepoint.com/sites/your-site
SHAREPOINT_FOLDER_PATH=Shared Documents/議事メモ
SHAREPOINT_CLIENT_ID=アプリケーション(クライアント)ID
SHAREPOINT_CLIENT_SECRET=クライアントシークレットの値
SHAREPOINT_TENANT_ID=ディレクトリ(テナント)ID
```

## 📊 初回データ取り込み

### ベクターストアの構築

```bash
python scripts/update_vector_store.py
```

実行すると：
1. データソースから議事メモを取得
2. テキストをチャンクに分割
3. OpenAI Embeddingsでベクトル化
4. ChromaDBに保存

**注意**: 初回は全ファイルを処理するため、時間がかかります。
- 目安: 100ファイル → 5-10分程度

## 🎯 チャットボットの起動

```bash
streamlit run app.py
```

ブラウザが自動的に開き、チャットインターフェースが表示されます。
通常は `http://localhost:8501` でアクセスできます。

## ⏰ 日次更新の設定

### macOS/Linux (cron)

```bash
# crontabを編集
crontab -e

# 以下を追加（毎日午前2時に実行）
0 2 * * * cd /Users/tetsuroh/Documents/議事メモツール && /usr/bin/python3 scripts/update_vector_store.py >> logs/cron.log 2>&1
```

### Windows (タスクスケジューラ)

1. タスクスケジューラを開く
2. 「基本タスクの作成」
3. トリガー: 毎日、午前2:00
4. 操作: プログラムの開始
   - プログラム: `python.exe` のパス
   - 引数: `scripts/update_vector_store.py`
   - 開始: プロジェクトフォルダのパス

## 🔄 環境の切り替え

プロトタイプから本番環境への切り替え：

1. `.env`ファイルを編集:
   ```bash
   # プロトタイプ
   DATA_SOURCE=google_drive
   
   # 本番に切り替え
   DATA_SOURCE=sharepoint
   ```

2. SharePoint設定を追加

3. ベクターストアを再構築:
   ```bash
   # 既存データをクリア（オプション）
   rm -rf data/vector_store/*
   rm -rf data/metadata/*
   
   # 再構築
   python scripts/update_vector_store.py
   ```

4. アプリを再起動

## 🐛 トラブルシューティング

### エラー: "OPENAI_API_KEY が設定されていません"

- `.env`ファイルが存在するか確認
- APIキーが正しく設定されているか確認
- APIキーの前後に空白やクォートがないか確認

### エラー: "credentials.json が見つかりません"

- Google Drive使用時は必須
- プロジェクトルートに配置されているか確認
- ファイル名が正確に`credentials.json`か確認

### エラー: "SharePoint認証に失敗"

- クライアントID、シークレット、テナントIDが正しいか確認
- Azure ADでAPI権限が付与されているか確認
- 管理者の同意が与えられているか確認

### ベクターストアが更新されない

```bash
# メタデータをクリアして再構築
rm data/metadata/file_metadata.json
python scripts/update_vector_store.py
```

### チャットの回答精度が低い

`.env`ファイルで調整:
```bash
# 検索結果数を増やす
TOP_K_RESULTS=10

# チャンクサイズを調整
CHUNK_SIZE=1500
CHUNK_OVERLAP=300
```

## 📝 使用例

### 質問の例

- 「先週の営業会議で決まったことは？」
- 「〇〇プロジェクトの進捗状況を教えて」
- 「△△さんが担当しているタスクは？」
- 「予算に関する議論があった会議は？」

### 効果的な質問のコツ

1. **具体的に**: 「前回の会議」より「2024年1月の営業会議」
2. **キーワードを含める**: プロジェクト名、人名、日付など
3. **段階的に**: まず概要を聞き、詳細を深掘り

## 🔒 セキュリティ

### 本番環境での推奨事項

1. **環境変数の保護**
   - `.env`ファイルをGit管理外に
   - 本番サーバーでは環境変数として設定

2. **APIキーの管理**
   - 定期的なローテーション
   - 使用量の監視

3. **アクセス制御**
   - SharePoint/Google Driveの権限設定
   - アプリケーションレベルの認証追加を検討

4. **データの暗号化**
   - ベクターストアの暗号化（必要に応じて）

## 📞 サポート

問題が解決しない場合：
1. ログファイルを確認: `logs/` ディレクトリ
2. 詳細なエラーメッセージをコピー
3. 設定ファイルの内容を確認（シークレット情報は除く）

---

**作成日**: 2024年12月15日
**対象バージョン**: v0.1.0


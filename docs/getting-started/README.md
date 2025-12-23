# セットアップガイド

プロジェクトを始めるための情報をまとめています。

## 📄 ドキュメント

### [INSTALLATION.md](INSTALLATION.md)
**詳細なインストール手順**

このドキュメントでは、議事メモRAGチャットボットのセットアップ方法を詳しく説明しています。

#### 内容
- 前提条件（必須環境・アカウント）
- セットアップ手順（5ステップ）
- 認証情報の設定
  - Google Drive（プロトタイプ環境）
  - SharePoint（本番環境）
- 初回データ取り込み
- 動作確認
- トラブルシューティング

#### 対象者
- 初めてプロジェクトをセットアップする方
- 開発環境を構築する方
- テスト環境を構築する方

---

## 🚀 クイックスタート

詳細は [INSTALLATION.md](INSTALLATION.md) を参照してください。

```bash
# 1. 仮想環境の作成
python3 -m venv venv
source venv/bin/activate

# 2. 依存パッケージのインストール
pip install -r requirements.txt

# 3. 環境変数の設定
cp .env.example .env
nano .env

# 4. 初回データ取り込み
python scripts/update_vector_store.py

# 5. アプリケーション起動
streamlit run app/main.py
```

---

## 📚 次のステップ

インストールが完了したら：

- **ローカル開発**: そのまま開発を開始
- **本番デプロイ**: [deployment/DEPLOYMENT.md](../deployment/DEPLOYMENT.md) を参照
- **開発に参加**: [development/CONTRIBUTING.md](../development/CONTRIBUTING.md) を参照

---

[← ドキュメントトップに戻る](../README.md)


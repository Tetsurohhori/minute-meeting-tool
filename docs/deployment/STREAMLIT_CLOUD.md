# Streamlit Cloud デプロイガイド

## ⚠️ 永続化の問題

Streamlit Cloudでは、`data/`ディレクトリが**永続化されません**。
つまり、アプリが再起動されるたびにベクターストアが消えてしまいます。

## 運用方法

### 方法1: GitHub Actionsで自動更新（推奨）

`.github/workflows/update_vector_store.yml`を作成：

```yaml
name: Update Vector Store

on:
  schedule:
    # 毎日午前3時（JST）に実行
    - cron: '0 18 * * *'
  workflow_dispatch: # 手動実行も可能

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      
      - name: Run update script
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          DATA_SOURCE: ${{ secrets.DATA_SOURCE }}
          # その他の環境変数
        run: |
          python scripts/update_vector_store.py
      
      - name: Commit and push if changed
        run: |
          git config --local user.email "action@github.com"
          git config --local user.name "GitHub Action"
          git add data/
          git diff --staged --quiet || (git commit -m "Update vector store [skip ci]" && git push)
```

**注意**: `data/`ディレクトリをGitに含める必要があります（`.gitignore`から除外）。

### 方法2: Streamlit Cloudのシェルから手動実行

1. Streamlit Cloudダッシュボード → アプリの「Manage app」
2. 「Open Terminal」を開く
3. 以下を実行：
```bash
python scripts/update_vector_store.py
```

### 方法3: 外部ストレージを使用（本番環境推奨）

S3やGoogle Cloud Storageにベクターストアを保存するよう変更が必要です。

## 推奨される本番環境

- **VPS** (AWS EC2, Google Compute Engine, Azure VM)
- **Docker** + 永続ボリューム
- **Kubernetes** + PersistentVolume
- **専用サーバー**

これらの環境では、ベクターストアが永続化され、日次更新のみで済みます。


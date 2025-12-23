# デプロイ・運用ガイド

本番環境へのデプロイと運用に関する情報をまとめています。

## 📄 ドキュメント

### [DEPLOYMENT.md](DEPLOYMENT.md)
**デプロイ・運用ガイド**

このドキュメントでは、議事メモRAGチャットボットを本番環境にデプロイする方法と、運用に関するベストプラクティスを説明しています。

#### 内容
- デプロイの種類
  - スタンドアロンサーバー
  - クラウド環境（AWS/Azure/GCP）
  - Docker化
- systemdサービスの設定
- リバースプロキシの設定（Nginx）
- SSL証明書の設定（Let's Encrypt）
- 日次更新の設定
  - cron
  - systemd timer
  - タスクスケジューラ（Windows）
- 監視とメンテナンス
  - ログの確認
  - ディスク使用量の監視
  - バックアップ
  - ヘルスチェック
- トラブルシューティング
- セキュリティのベストプラクティス
- スケーリング
- アップデート手順

#### 対象者
- 本番環境にデプロイする方
- システム管理者
- DevOpsエンジニア

---

## 🏗️ デプロイオプション

### 1. スタンドアロンサーバー
- Ubuntu/CentOS サーバーに直接デプロイ
- systemdでサービス管理
- Nginxでリバースプロキシ

### 2. クラウド環境
- AWS EC2
- Azure VM
- GCP Compute Engine

### 3. Docker
- docker-composeで簡単デプロイ
- コンテナ化による移植性

詳細は [DEPLOYMENT.md](DEPLOYMENT.md) を参照してください。

---

## 🔄 運用フロー

```
1. デプロイ
   ↓
2. 初回データ取り込み
   ↓
3. 日次更新の設定
   ↓
4. 監視の設定
   ↓
5. 定期的なメンテナンス
```

---

## 📚 関連ドキュメント

- [getting-started/INSTALLATION.md](../getting-started/INSTALLATION.md) - 基本的なセットアップ
- [architecture/PROJECT_STRUCTURE.md](../architecture/PROJECT_STRUCTURE.md) - システム構造の理解

---

[← ドキュメントトップに戻る](../README.md)


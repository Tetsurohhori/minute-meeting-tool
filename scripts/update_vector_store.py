"""
ベクターストア更新スクリプト
日次で実行して差分更新を行う
"""

import sys
from pathlib import Path
from datetime import datetime

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.config import get_settings
from app.data_sources import GoogleDriveDataSource, SharePointDataSource
from app.vector_store import VectorStoreManager
from app.utils.logger import setup_logger


def get_data_source(settings):
    """設定に応じたデータソースを取得"""
    if settings.data_source == "google_drive":
        # Google Drive設定の検証
        if not settings.validate_google_drive_settings():
            raise ValueError(
                "Google Drive設定が不完全です。\n"
                f"- GOOGLE_DRIVE_FOLDER_ID: {bool(settings.google_drive_folder_id)}\n"
                f"- credentials.json: {settings.google_credentials_path.exists()}"
            )
        
        return GoogleDriveDataSource(
            folder_id=settings.google_drive_folder_id,
            credentials_path=settings.google_credentials_path,
            token_path=settings.google_token_path,
            log_path=settings.log_path
        )
    
    elif settings.data_source == "sharepoint":
        # SharePoint設定の検証
        if not settings.validate_sharepoint_settings():
            raise ValueError(
                "SharePoint設定が不完全です。.envファイルを確認してください。"
            )
        
        return SharePointDataSource(
            site_url=settings.sharepoint_site_url,
            folder_path=settings.sharepoint_folder_path,
            client_id=settings.sharepoint_client_id,
            client_secret=settings.sharepoint_client_secret,
            tenant_id=settings.sharepoint_tenant_id,
            log_path=settings.log_path
        )
    
    else:
        raise ValueError(f"未対応のデータソース: {settings.data_source}")


def main():
    """メイン処理"""
    print("=" * 80)
    print("議事メモベクターストア更新スクリプト")
    print(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    try:
        # 設定を読み込み
        print("\n[1/5] 設定を読み込み中...")
        settings = get_settings()
        print(f"✓ データソース: {settings.data_source}")
        print(f"✓ ベクターストアパス: {settings.vector_store_path}")
        
        # ロガー設定
        logger = setup_logger("UpdateVectorStore", settings.log_path)
        logger.info("=" * 80)
        logger.info("ベクターストア更新開始")
        
        # データソースを初期化
        print("\n[2/5] データソースを初期化中...")
        data_source = get_data_source(settings)
        
        # 認証
        print(f"  {settings.data_source} に接続中...")
        if not data_source.authenticate():
            raise RuntimeError("認証に失敗しました")
        print("✓ 認証成功")
        logger.info("データソース認証成功")
        
        # ドキュメント一覧を取得
        print("\n[3/5] ドキュメント一覧を取得中...")
        documents = data_source.list_documents()
        print(f"✓ {len(documents)} 件のドキュメントを取得")
        logger.info(f"{len(documents)} 件のドキュメントを取得")
        
        if not documents:
            print("\n⚠️  ドキュメントが見つかりませんでした")
            logger.warning("ドキュメントが見つかりませんでした")
            return
        
        # ベクターストアマネージャーを初期化
        print("\n[4/5] ベクターストアを初期化中...")
        vector_store_manager = VectorStoreManager(
            vector_store_path=settings.vector_store_path,
            metadata_path=settings.metadata_path,
            openai_api_key=settings.openai_api_key,
            embedding_model=settings.embedding_model,
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            log_path=settings.log_path
        )
        print("✓ ベクターストア初期化完了")
        
        # 差分更新を実行
        print("\n[5/5] 差分検出と更新を実行中...")
        stats = vector_store_manager.process_incremental_update(documents)
        
        print("\n" + "=" * 80)
        print("更新完了！")
        print("=" * 80)
        print(f"  新規追加:   {stats['new_count']} 件")
        print(f"  更新:       {stats['updated_count']} 件")
        print(f"  削除:       {stats['deleted_count']} 件")
        print(f"  総チャンク: {stats['total_chunks']} 個")
        print("=" * 80)
        
        logger.info("更新完了")
        logger.info(f"統計: {stats}")
        logger.info("=" * 80)
        
        # 差分がない場合のメッセージ
        if sum(stats.values()) == 0:
            print("\n✓ 変更はありませんでした（ベクターストアは最新の状態です）")
            logger.info("変更なし")
        
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {str(e)}")
        if 'logger' in locals():
            logger.error(f"更新エラー: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()


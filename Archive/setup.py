"""
初期セットアップスクリプト
.envファイルの作成を支援
"""

from pathlib import Path
import sys


def create_env_file():
    """対話式で.envファイルを作成"""
    print("=" * 80)
    print("議事メモRAGチャットボット - 初期セットアップ")
    print("=" * 80)
    print()
    
    project_root = Path(__file__).parent
    env_file = project_root / ".env"
    
    if env_file.exists():
        response = input(".envファイルが既に存在します。上書きしますか？ (y/N): ")
        if response.lower() != 'y':
            print("セットアップをキャンセルしました")
            return
    
    print("\n【必須設定】")
    print("-" * 80)
    
    # OpenAI APIキー
    openai_key = input("OpenAI APIキーを入力してください: ").strip()
    if not openai_key:
        print("❌ OpenAI APIキーは必須です")
        sys.exit(1)
    
    # データソース選択
    print("\nデータソースを選択してください:")
    print("  1. Google Drive (プロトタイプ)")
    print("  2. SharePoint (本番)")
    
    while True:
        choice = input("選択 (1 or 2): ").strip()
        if choice in ["1", "2"]:
            break
        print("1 または 2 を入力してください")
    
    data_source = "google_drive" if choice == "1" else "sharepoint"
    
    # データソース別の設定
    google_folder_id = ""
    sharepoint_site_url = ""
    sharepoint_folder_path = ""
    sharepoint_client_id = ""
    sharepoint_client_secret = ""
    sharepoint_tenant_id = ""
    
    if data_source == "google_drive":
        print("\n【Google Drive設定】")
        print("-" * 80)
        print("Google DriveのフォルダIDを入力してください")
        print("（フォルダURLの最後の部分: https://drive.google.com/drive/folders/XXXXX）")
        google_folder_id = input("フォルダID: ").strip()
        
        print("\n✓ Google Drive設定完了")
        print("📝 次のステップ:")
        print("  1. Google Cloud Consoleでプロジェクトを作成")
        print("  2. Google Drive APIを有効化")
        print("  3. OAuth 2.0クライアントIDを作成")
        print("  4. credentials.jsonをダウンロードしてプロジェクトルートに配置")
    
    else:  # SharePoint
        print("\n【SharePoint設定】")
        print("-" * 80)
        sharepoint_site_url = input("SharePointサイトURL: ").strip()
        sharepoint_folder_path = input("フォルダパス (例: Shared Documents/議事メモ): ").strip()
        sharepoint_client_id = input("クライアントID: ").strip()
        sharepoint_client_secret = input("クライアントシークレット: ").strip()
        sharepoint_tenant_id = input("テナントID: ").strip()
        
        print("\n✓ SharePoint設定完了")
    
    # .envファイルを作成
    env_content = f"""# OpenAI API設定
OPENAI_API_KEY={openai_key}

# データソースの選択 (google_drive または sharepoint)
DATA_SOURCE={data_source}

# Google Drive設定（プロトタイプ環境）
GOOGLE_DRIVE_FOLDER_ID={google_folder_id}
# credentials.jsonファイルをプロジェクトルートに配置してください

# SharePoint設定（本番環境）
SHAREPOINT_SITE_URL={sharepoint_site_url}
SHAREPOINT_FOLDER_PATH={sharepoint_folder_path}
SHAREPOINT_CLIENT_ID={sharepoint_client_id}
SHAREPOINT_CLIENT_SECRET={sharepoint_client_secret}
SHAREPOINT_TENANT_ID={sharepoint_tenant_id}

# ベクターストア設定
VECTOR_STORE_PATH=./data/vector_store
METADATA_PATH=./data/metadata

# RAG設定
EMBEDDING_MODEL=text-embedding-3-small
CHAT_MODEL=gpt-4o-mini
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
TOP_K_RESULTS=5

# ログ設定
LOG_LEVEL=INFO
LOG_PATH=./logs
"""
    
    with open(env_file, 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print("\n" + "=" * 80)
    print("✓ .envファイルを作成しました！")
    print("=" * 80)
    print("\n次のステップ:")
    print("  1. 依存パッケージをインストール:")
    print("     pip install -r requirements.txt")
    print()
    print("  2. 初回ベクターストア構築:")
    print("     python scripts/update_vector_store.py")
    print()
    print("  3. チャットボット起動:")
    print("     streamlit run app.py")
    print()


if __name__ == "__main__":
    try:
        create_env_file()
    except KeyboardInterrupt:
        print("\n\nセットアップをキャンセルしました")
        sys.exit(0)


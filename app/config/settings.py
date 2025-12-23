"""
設定管理モジュール（堅牢版）
環境変数から設定を読み込み、厳格なバリデーションを行う
"""

import os
import logging
from pathlib import Path
from typing import Literal, Optional
from dotenv import load_dotenv

# ロガーの設定
logger = logging.getLogger(__name__)

# プロジェクトルートのパスを取得
PROJECT_ROOT = Path(__file__).parent.parent.resolve()

# .envファイルを読み込み（絶対パスで指定）
env_path = PROJECT_ROOT / ".env"
if not env_path.exists():
    # フォールバック: 明示的な絶対パスで試す
    env_path = Path("/Users/tetsuroh/Documents/議事メモツール/.env")

# 必ず読み込む（エラーを明示的にする）
if not load_dotenv(env_path, override=True):
    logger.error(f".envファイルの読み込みに失敗: {env_path}")
else:
    logger.info(f".envファイルを読み込みました: {env_path}")


class ConfigurationError(Exception):
    """設定エラー用のカスタム例外"""
    pass


class Settings:
    """
    アプリケーション設定クラス（堅牢版）
    
    すべての環境変数に対して厳格なバリデーションを行い、
    不正な値や論理的に矛盾した設定を拒否します。
    """
    
    # 定数定義（数値パラメータの範囲）
    MIN_CHUNK_SIZE = 100
    MAX_CHUNK_SIZE = 10000
    MIN_CHUNK_OVERLAP = 0
    MAX_CHUNK_OVERLAP = 5000
    MIN_TOP_K = 1
    MAX_TOP_K = 100
    
    def __init__(self):
        """
        設定を初期化し、厳格なバリデーションを行う
        
        Raises:
            ConfigurationError: 設定値が不正な場合
        """
        # OpenAI API設定（厳格なバリデーション）
        self.openai_api_key = self._validate_api_key(
            os.getenv("OPENAI_API_KEY", "")
        )
        
        # データソースの選択（ホワイトリスト方式）
        self.data_source = self._validate_data_source(
            os.getenv("DATA_SOURCE", "google_drive")
        )
        
        # Google Drive設定
        self.google_drive_folder_id = os.getenv("GOOGLE_DRIVE_FOLDER_ID", "")
        # credentials.jsonのパス（存在確認付き）
        credentials_path = PROJECT_ROOT / "credentials.json"
        if not credentials_path.exists():
            # フォールバック: 絶対パス
            credentials_path = Path("/Users/tetsuroh/Documents/議事メモツール/credentials.json")
        self.google_credentials_path = credentials_path
        self.google_token_path = PROJECT_ROOT / "token.json"
        
        # SharePoint設定
        self.sharepoint_site_url = os.getenv("SHAREPOINT_SITE_URL", "")
        self.sharepoint_folder_path = os.getenv("SHAREPOINT_FOLDER_PATH", "")
        self.sharepoint_client_id = os.getenv("SHAREPOINT_CLIENT_ID", "")
        self.sharepoint_client_secret = os.getenv("SHAREPOINT_CLIENT_SECRET", "")
        self.sharepoint_tenant_id = os.getenv("SHAREPOINT_TENANT_ID", "")
        
        # ベクターストア設定（パストラバーサル対策）
        self.vector_store_path = self._validate_and_resolve_path(
            os.getenv("VECTOR_STORE_PATH", str(PROJECT_ROOT / "chroma_db")),
            "VECTOR_STORE_PATH"
        )
        self.metadata_path = self._validate_and_resolve_path(
            os.getenv("METADATA_PATH", str(PROJECT_ROOT / "data" / "metadata")),
            "METADATA_PATH"
        )
        
        # RAG設定（数値パラメータの厳格なバリデーション）
        self.embedding_model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
        self.chat_model = os.getenv("CHAT_MODEL", "gpt-4o-mini")
        self.chunk_size = self._validate_positive_int(
            "CHUNK_SIZE", 1000, 
            min_value=self.MIN_CHUNK_SIZE, 
            max_value=self.MAX_CHUNK_SIZE
        )
        self.chunk_overlap = self._validate_positive_int(
            "CHUNK_OVERLAP", 200,
            min_value=self.MIN_CHUNK_OVERLAP,
            max_value=self.MAX_CHUNK_OVERLAP
        )
        self.top_k_results = self._validate_positive_int(
            "TOP_K_RESULTS", 5,
            min_value=self.MIN_TOP_K,
            max_value=self.MAX_TOP_K
        )
        
        # 論理的整合性のチェック
        self._validate_chunk_configuration()
        
        # ログ設定（パストラバーサル対策）
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.log_path = self._validate_and_resolve_path(
            os.getenv("LOG_PATH", str(PROJECT_ROOT / "logs")),
            "LOG_PATH"
        )
        
        # ディレクトリが存在しない場合は作成
        self.vector_store_path.mkdir(parents=True, exist_ok=True)
        self.metadata_path.mkdir(parents=True, exist_ok=True)
        self.log_path.mkdir(parents=True, exist_ok=True)
    
    def _validate_api_key(self, api_key: str) -> str:
        """
        APIキーのバリデーション
        
        Args:
            api_key: APIキー文字列
        
        Returns:
            検証済みのAPIキー（strip済み）
        
        Raises:
            ConfigurationError: APIキーが不正な場合
        """
        # 空文字列チェック
        if not api_key:
            raise ConfigurationError(
                "OPENAI_API_KEY が設定されていません。.env ファイルを確認してください。"
            )
        
        # スペースのみのチェック
        if not api_key.strip():
            raise ConfigurationError(
                "OPENAI_API_KEY が空白文字のみです。有効なAPIキーを設定してください。"
            )
        
        # 最小長チェック（OpenAI APIキーは通常40文字以上）
        stripped_key = api_key.strip()
        if len(stripped_key) < 20:
            logger.warning(
                f"OPENAI_API_KEY が短すぎる可能性があります（{len(stripped_key)}文字）。"
                "有効なAPIキーか確認してください。"
            )
        
        return stripped_key
    
    def _validate_data_source(self, data_source: str) -> Literal["google_drive", "sharepoint"]:
        """
        データソースのバリデーション
        
        Args:
            data_source: データソース名
        
        Returns:
            検証済みのデータソース
        
        Raises:
            ConfigurationError: データソースが不正な場合
        """
        valid_sources = ["google_drive", "sharepoint"]
        data_source = data_source.strip().lower()
        
        if data_source not in valid_sources:
            raise ConfigurationError(
                f"DATA_SOURCE が不正です: '{data_source}'。"
                f"有効な値: {', '.join(valid_sources)}"
            )
        return data_source
    
    def _validate_positive_int(
        self, 
        key: str, 
        default: int,
        min_value: Optional[int] = None,
        max_value: Optional[int] = None
    ) -> int:
        """
        正の整数をバリデーション
        
        Args:
            key: 環境変数のキー
            default: デフォルト値
            min_value: 最小値（Noneの場合は1）
            max_value: 最大値（Noneの場合は制限なし）
        
        Returns:
            検証済みの整数値
        
        Raises:
            ConfigurationError: 値が不正な場合
        """
        min_value = min_value if min_value is not None else 1
        
        # 環境変数の取得
        value_str = os.getenv(key, str(default))
        
        # 空文字列チェック
        if not value_str or not value_str.strip():
            raise ConfigurationError(
                f"{key} が空です。有効な整数値を設定してください。"
            )
        
        # 整数への変換
        try:
            value = int(value_str.strip())
        except ValueError as e:
            raise ConfigurationError(
                f"{key} の値が整数ではありません: '{value_str}'"
            ) from e
        
        # 最小値チェック
        if value < min_value:
            raise ConfigurationError(
                f"{key} は {min_value} 以上である必要があります（現在: {value}）"
            )
        
        # 最大値チェック
        if max_value is not None and value > max_value:
            raise ConfigurationError(
                f"{key} は {max_value} 以下である必要があります（現在: {value}）。"
                "メモリ不足やAPIコスト爆発の危険性があります。"
            )
        
        return value
    
    def _validate_chunk_configuration(self):
        """
        チャンク設定の論理的整合性をチェック
        
        Raises:
            ConfigurationError: 設定が論理的に矛盾している場合
        """
        if self.chunk_overlap >= self.chunk_size:
            raise ConfigurationError(
                f"CHUNK_OVERLAP ({self.chunk_overlap}) は "
                f"CHUNK_SIZE ({self.chunk_size}) より小さい必要があります。"
                "オーバーラップがチャンクサイズ以上の場合、無限ループが発生します。"
            )
    
    def _validate_and_resolve_path(self, path_str: str, key: str) -> Path:
        """
        パスをバリデーションし、絶対パスに解決する（パストラバーサル対策）
        
        Args:
            path_str: パス文字列
            key: 環境変数のキー名（エラーメッセージ用）
        
        Returns:
            検証済みの絶対パス
        
        Raises:
            ConfigurationError: パスが不正な場合
        """
        if not path_str or not path_str.strip():
            raise ConfigurationError(f"{key} が空です")
        
        # 絶対パスに解決（パストラバーサル対策）
        path = Path(path_str.strip()).resolve()
        
        # プロジェクトルート配下にあることを確認（セキュリティチェック）
        try:
            project_root_resolved = PROJECT_ROOT.resolve()
            
            # プロジェクトルート配下でない場合は警告
            if not str(path).startswith(str(project_root_resolved)):
                logger.warning(
                    f"{key} がプロジェクトルート外を指しています: {path}。"
                    "セキュリティリスクがある可能性があります。"
                )
        except Exception as e:
            logger.error(f"パスの検証中にエラーが発生: {e}")
        
        return path
    
    def validate_google_drive_settings(self) -> bool:
        """
        Google Drive設定の検証
        
        Returns:
            設定が有効な場合True
        """
        # フォルダIDの検証（空文字列やスペースのみを拒否）
        if not self.google_drive_folder_id or not self.google_drive_folder_id.strip():
            return False
        
        # 認証ファイルの存在確認
        if not self.google_credentials_path.exists():
            return False
        
        return True
    
    def validate_sharepoint_settings(self) -> bool:
        """
        SharePoint設定の検証（厳格版）
        
        Returns:
            設定が有効な場合True
        """
        required_fields = [
            (self.sharepoint_site_url, "SHAREPOINT_SITE_URL"),
            (self.sharepoint_folder_path, "SHAREPOINT_FOLDER_PATH"),
            (self.sharepoint_client_id, "SHAREPOINT_CLIENT_ID"),
            (self.sharepoint_client_secret, "SHAREPOINT_CLIENT_SECRET"),
            (self.sharepoint_tenant_id, "SHAREPOINT_TENANT_ID"),
        ]
        
        for field_value, field_name in required_fields:
            # 空文字列チェック
            if not field_value:
                return False
            
            # スペースのみチェック
            if not field_value.strip():
                logger.warning(f"{field_name} が空白文字のみです")
                return False
        
        return True
    
    def validate_current_data_source(self) -> bool:
        """
        現在のデータソース設定の検証
        
        Returns:
            設定が有効な場合True
        """
        if self.data_source == "google_drive":
            return self.validate_google_drive_settings()
        elif self.data_source == "sharepoint":
            return self.validate_sharepoint_settings()
        else:
            return False


# シングルトンインスタンス
_settings_instance = None


def get_settings() -> Settings:
    """
    設定のシングルトンインスタンスを取得
    
    Returns:
        Settings インスタンス
    """
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
    return _settings_instance


def reset_settings():
    """
    シングルトンインスタンスをリセット（テスト用）
    
    テスト時に環境変数を変更した後、この関数を呼び出すことで
    新しい設定で再初期化できます。
    """
    global _settings_instance
    _settings_instance = None

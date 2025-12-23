"""
🔥 Settings モジュールへの意地悪な攻撃的テスト

開発者が見落としがちなエッジケース、型安全性の問題、環境変数の不備を徹底的に突く。
"""

import pytest
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# テスト対象のインポート
from app.config.settings import Settings, get_settings


class TestSettingsInitializationAttacks:
    """Settings クラスの初期化に対する攻撃"""
    
    @pytest.mark.adversarial
    @pytest.mark.boundary
    def test_missing_openai_api_key_should_raise_error(self, monkeypatch):
        """❌ OpenAI APIキーが無い場合に適切なエラーを出すか？"""
        # OpenAI APIキーを削除
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        
        with pytest.raises(ValueError) as exc_info:
            Settings()
        
        assert "OPENAI_API_KEY" in str(exc_info.value), \
            "エラーメッセージが不明確！ユーザーは何が悪いのか分からない！"
    
    @pytest.mark.adversarial
    @pytest.mark.boundary
    def test_empty_openai_api_key_should_raise_error(self, monkeypatch):
        """❌ 空文字列のAPIキーを受け付けるな！"""
        monkeypatch.setenv("OPENAI_API_KEY", "")
        
        with pytest.raises(ValueError) as exc_info:
            Settings()
        
        assert "OPENAI_API_KEY" in str(exc_info.value), \
            "空文字列を有効なAPIキーとして扱うな！"
    
    @pytest.mark.adversarial
    @pytest.mark.boundary
    def test_whitespace_only_api_key_should_raise_error(self, monkeypatch):
        """❌ スペースだけのAPIキーを受け付けるな！"""
        monkeypatch.setenv("OPENAI_API_KEY", "   \t\n  ")
        
        # 現状の実装では通ってしまう可能性が高い
        # 開発者よ、これを修正せよ！
        settings = Settings()
        assert settings.openai_api_key.strip() != "", \
            "スペースだけのAPIキーが通ってしまっている！validation が甘い！"
    
    @pytest.mark.adversarial
    @pytest.mark.type_attack
    def test_chunk_size_with_non_numeric_string_should_fail(self, monkeypatch):
        """❌ 数値じゃない文字列を CHUNK_SIZE に入れたら？"""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.setenv("CHUNK_SIZE", "not_a_number")
        
        with pytest.raises(ValueError):
            Settings()
    
    @pytest.mark.adversarial
    @pytest.mark.type_attack
    def test_chunk_size_negative_value_should_fail(self, monkeypatch):
        """❌ 負の CHUNK_SIZE を許すな！"""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.setenv("CHUNK_SIZE", "-1000")
        
        settings = Settings()
        # ここで通ってしまったら開発者の負け
        assert settings.chunk_size > 0, \
            "負のチャンクサイズが通ってしまった！データが壊れるぞ！"
    
    @pytest.mark.adversarial
    @pytest.mark.type_attack
    def test_chunk_size_zero_should_fail(self, monkeypatch):
        """❌ チャンクサイズ0を許すな！"""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.setenv("CHUNK_SIZE", "0")
        
        settings = Settings()
        assert settings.chunk_size > 0, \
            "チャンクサイズ0で無限ループが発生する可能性あり！"
    
    @pytest.mark.adversarial
    @pytest.mark.boundary
    def test_chunk_overlap_greater_than_chunk_size(self, monkeypatch):
        """❌ オーバーラップがチャンクサイズより大きい場合は？"""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.setenv("CHUNK_SIZE", "100")
        monkeypatch.setenv("CHUNK_OVERLAP", "200")
        
        settings = Settings()
        # これが通ったら論理的に矛盾している
        assert settings.chunk_overlap < settings.chunk_size, \
            "オーバーラップがチャンクサイズより大きい！無限ループの危険性！"
    
    @pytest.mark.adversarial
    @pytest.mark.type_attack
    def test_top_k_results_negative_value(self, monkeypatch):
        """❌ 負の TOP_K_RESULTS を許すな！"""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.setenv("TOP_K_RESULTS", "-5")
        
        settings = Settings()
        assert settings.top_k_results > 0, \
            "負の検索結果数？何も返せないぞ！"
    
    @pytest.mark.adversarial
    @pytest.mark.type_attack
    def test_invalid_data_source_type(self, monkeypatch):
        """❌ 存在しないデータソースタイプ"""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.setenv("DATA_SOURCE", "dropbox")  # サポート外
        
        settings = Settings()
        # validate_current_data_source() が False を返すべき
        assert not settings.validate_current_data_source(), \
            "存在しないデータソースを valid として扱っている！"
    
    @pytest.mark.adversarial
    @pytest.mark.security
    def test_path_traversal_in_log_path(self, monkeypatch):
        """❌ ログパスにパストラバーサル攻撃"""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.setenv("LOG_PATH", "../../etc/passwd")
        
        settings = Settings()
        # システムの重要なファイルを上書きする危険性
        log_path_str = str(settings.log_path)
        assert "../" not in log_path_str or settings.log_path.is_absolute(), \
            "相対パストラバーサルが通ってしまった！セキュリティホール！"


class TestSettingsValidationAttacks:
    """Settings の検証メソッドへの攻撃"""
    
    @pytest.mark.adversarial
    @pytest.mark.boundary
    def test_validate_google_drive_with_empty_folder_id(self, monkeypatch):
        """❌ 空のフォルダIDで検証を通すな！"""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.setenv("DATA_SOURCE", "google_drive")
        monkeypatch.setenv("GOOGLE_DRIVE_FOLDER_ID", "")
        
        settings = Settings()
        assert not settings.validate_google_drive_settings(), \
            "空のフォルダIDで検証が通ってしまった！"
    
    @pytest.mark.adversarial
    @pytest.mark.boundary
    def test_validate_google_drive_without_credentials_file(self, monkeypatch, tmp_path):
        """❌ credentials.json が無い場合の検証"""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.setenv("DATA_SOURCE", "google_drive")
        monkeypatch.setenv("GOOGLE_DRIVE_FOLDER_ID", "test-folder-id")
        
        # credentials.json が存在しない状態
        settings = Settings()
        settings.google_credentials_path = tmp_path / "nonexistent_credentials.json"
        
        assert not settings.validate_google_drive_settings(), \
            "認証ファイルが無いのに検証が通った！"
    
    @pytest.mark.adversarial
    @pytest.mark.boundary
    def test_validate_sharepoint_with_partial_config(self, monkeypatch):
        """❌ SharePoint 設定が部分的にしか無い場合"""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.setenv("DATA_SOURCE", "sharepoint")
        monkeypatch.setenv("SHAREPOINT_SITE_URL", "https://test.sharepoint.com")
        # 他のフィールドは設定しない
        
        settings = Settings()
        assert not settings.validate_sharepoint_settings(), \
            "部分的な設定で検証が通った！"
    
    @pytest.mark.adversarial
    @pytest.mark.boundary
    def test_validate_sharepoint_with_whitespace_only_fields(self, monkeypatch):
        """❌ スペースだけのフィールドを受け入れるな！"""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.setenv("DATA_SOURCE", "sharepoint")
        monkeypatch.setenv("SHAREPOINT_SITE_URL", "   ")
        monkeypatch.setenv("SHAREPOINT_FOLDER_PATH", "\t\n")
        monkeypatch.setenv("SHAREPOINT_CLIENT_ID", " ")
        monkeypatch.setenv("SHAREPOINT_CLIENT_SECRET", "  ")
        monkeypatch.setenv("SHAREPOINT_TENANT_ID", "   ")
        
        settings = Settings()
        # 空白文字だけで検証を通してはならない
        is_valid = settings.validate_sharepoint_settings()
        
        # もし検証が通ったら、各フィールドが実際に空白でないことを確認
        if is_valid:
            assert settings.sharepoint_site_url.strip() != "", \
                "スペースだけのフィールドで検証が通った！"


class TestSettingsSingletonAttacks:
    """シングルトンパターンへの攻撃"""
    
    @pytest.mark.adversarial
    def test_singleton_returns_same_instance(self, monkeypatch):
        """❌ シングルトンが本当に同じインスタンスを返すか？"""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        
        # グローバル変数をリセット
        import app.config.settings as settings_module
        settings_module._settings_instance = None
        
        instance1 = get_settings()
        instance2 = get_settings()
        
        assert instance1 is instance2, \
            "シングルトンパターンが壊れている！複数のインスタンスが生成されている！"
    
    @pytest.mark.adversarial
    def test_singleton_state_pollution(self, monkeypatch):
        """❌ シングルトンの状態汚染テスト"""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key-1")
        
        # グローバル変数をリセット
        import app.config.settings as settings_module
        settings_module._settings_instance = None
        
        settings1 = get_settings()
        original_key = settings1.openai_api_key
        
        # 環境変数を変更
        monkeypatch.setenv("OPENAI_API_KEY", "test-key-2")
        
        settings2 = get_settings()  # 同じインスタンスが返る
        
        # シングルトンなので、古い値が残っている
        assert settings2.openai_api_key == original_key, \
            "シングルトンが環境変数の変更を反映していない（これは仕様通り）"
        
        # しかし、これはテスト時に問題になる可能性がある
        # 開発者は適切にリセット機構を提供すべき


class TestSettingsResourceAttacks:
    """リソース関連の攻撃"""
    
    @pytest.mark.adversarial
    @pytest.mark.resource_attack
    def test_extremely_large_chunk_size(self, monkeypatch):
        """❌ 極端に大きなチャンクサイズでメモリを圧迫"""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.setenv("CHUNK_SIZE", str(10**9))  # 1GB
        
        settings = Settings()
        # これが通ったら、後でメモリ不足になる
        assert settings.chunk_size < 10**6, \
            "チャンクサイズが大きすぎる！メモリ不足の危険性！"
    
    @pytest.mark.adversarial
    @pytest.mark.resource_attack
    def test_extremely_large_top_k_results(self, monkeypatch):
        """❌ 極端に大きな TOP_K でAPIコストを爆増させる"""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.setenv("TOP_K_RESULTS", str(10**6))
        
        settings = Settings()
        # APIコストが爆発する
        assert settings.top_k_results < 1000, \
            "TOP_K が大きすぎる！APIコストとレスポンス時間が爆発する！"


# =====================================
# 批判的フィードバック
# =====================================

"""
🔥 開発者への痛烈な批判 🔥

1. **型安全性の欠如**
   - `int()` で変換する際、例外処理が無い
   - 負数やゼロのチェックが無い
   - 想定外の文字列で ValueError が発生する

2. **バリデーションの甘さ**
   - 空文字列やスペースだけの入力を受け付けてしまう
   - CHUNK_OVERLAP > CHUNK_SIZE の論理矛盾を検出できない
   - 存在しない DATA_SOURCE を受け入れてしまう

3. **セキュリティホール**
   - パストラバーサル攻撃への対策が無い
   - 環境変数の値を無条件に信頼している
   - ログパスが任意の場所に設定できてしまう

4. **シングルトンパターンの問題**
   - テスト時に状態がリセットできない
   - スレッドセーフではない可能性
   - 環境変数の変更が反映されない

5. **リソース管理の欠如**
   - 極端に大きな値を制限していない
   - メモリ不足やAPIコストの爆発を防げない

📝 **修正案**

```python
class Settings:
    def __init__(self):
        # API キーの厳格なバリデーション
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY が設定されていません")
        
        # 数値パラメータの安全な変換
        self.chunk_size = self._parse_positive_int("CHUNK_SIZE", 1000, max_value=100000)
        self.chunk_overlap = self._parse_positive_int("CHUNK_OVERLAP", 200, max_value=10000)
        
        # 論理的整合性のチェック
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError(f"CHUNK_OVERLAP ({self.chunk_overlap}) は CHUNK_SIZE ({self.chunk_size}) より小さい必要があります")
    
    def _parse_positive_int(self, key: str, default: int, max_value: int = None) -> int:
        try:
            value = int(os.getenv(key, str(default)))
            if value <= 0:
                raise ValueError(f"{key} は正の整数である必要があります")
            if max_value and value > max_value:
                raise ValueError(f"{key} は {max_value} 以下である必要があります")
            return value
        except ValueError as e:
            raise ValueError(f"{key} の値が不正です: {e}")
```

開発者よ、これらの脆弱性を今すぐ修正せよ！
"""


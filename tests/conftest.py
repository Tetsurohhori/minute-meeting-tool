"""
pytest 共通設定とフィクスチャ定義

テスト全体で使用する共通のセットアップ、モック、ユーティリティを提供します。
"""

import os
import sys
import json
import tempfile
from pathlib import Path
from typing import Generator, Dict, Any
from unittest.mock import Mock, MagicMock

import pytest

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


# =====================================
# 環境変数モック
# =====================================

@pytest.fixture(scope="session")
def mock_env_vars() -> Dict[str, str]:
    """テスト用の環境変数を返す"""
    return {
        "OPENAI_API_KEY": "test-api-key-12345",
        "DATA_SOURCE": "google_drive",
        "GOOGLE_DRIVE_FOLDER_ID": "test-folder-id",
        "SHAREPOINT_SITE_URL": "https://test.sharepoint.com/sites/test",
        "SHAREPOINT_FOLDER_PATH": "Shared Documents/Test",
        "SHAREPOINT_CLIENT_ID": "test-client-id",
        "SHAREPOINT_CLIENT_SECRET": "test-client-secret",
        "SHAREPOINT_TENANT_ID": "test-tenant-id",
        "VECTOR_STORE_PATH": "./test_data/vector_store",
        "METADATA_PATH": "./test_data/metadata",
        "EMBEDDING_MODEL": "text-embedding-3-small",
        "CHAT_MODEL": "gpt-4o-mini",
        "CHUNK_SIZE": "1000",
        "CHUNK_OVERLAP": "200",
        "TOP_K_RESULTS": "5",
        "LOG_LEVEL": "DEBUG",
        "LOG_PATH": "./test_logs",
    }


@pytest.fixture(autouse=True)
def setup_test_env(mock_env_vars: Dict[str, str], monkeypatch) -> None:
    """すべてのテストで自動的に環境変数をセットアップ"""
    for key, value in mock_env_vars.items():
        monkeypatch.setenv(key, value)


# =====================================
# 一時ディレクトリとファイル
# =====================================

@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """一時ディレクトリを作成し、テスト後に削除"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def temp_file(temp_dir: Path) -> Path:
    """一時ファイルを作成"""
    file_path = temp_dir / "test_file.txt"
    file_path.write_text("Test content")
    return file_path


@pytest.fixture
def temp_json_file(temp_dir: Path) -> Path:
    """一時JSONファイルを作成"""
    file_path = temp_dir / "test_data.json"
    data = {"key": "value", "number": 42}
    file_path.write_text(json.dumps(data))
    return file_path


# =====================================
# モックオブジェクト
# =====================================

@pytest.fixture
def mock_openai_client() -> Mock:
    """OpenAI クライアントのモック"""
    mock_client = Mock()
    
    # embeddings.create のモック
    mock_embedding_response = Mock()
    mock_embedding_response.data = [Mock(embedding=[0.1] * 1536)]
    mock_client.embeddings.create.return_value = mock_embedding_response
    
    # chat.completions.create のモック
    mock_chat_response = Mock()
    mock_chat_response.choices = [
        Mock(message=Mock(content="これはテスト回答です。"))
    ]
    mock_client.chat.completions.create.return_value = mock_chat_response
    
    return mock_client


@pytest.fixture
def mock_google_drive_service() -> Mock:
    """Google Drive サービスのモック"""
    mock_service = Mock()
    
    # ファイル一覧のモック
    mock_files_list = Mock()
    mock_files_list.execute.return_value = {
        "files": [
            {
                "id": "file1",
                "name": "test_doc.docx",
                "modifiedTime": "2024-01-01T00:00:00.000Z"
            }
        ]
    }
    mock_service.files().list.return_value = mock_files_list
    
    return mock_service


@pytest.fixture
def mock_sharepoint_client() -> Mock:
    """SharePoint クライアントのモック"""
    mock_client = Mock()
    
    # ファイル一覧のモック
    mock_client.list_files.return_value = [
        {
            "name": "test_doc.docx",
            "modified": "2024-01-01T00:00:00Z",
            "id": "sp_file1"
        }
    ]
    
    return mock_client


@pytest.fixture
def mock_vector_store() -> Mock:
    """ベクターストアのモック"""
    mock_store = Mock()
    
    # クエリ結果のモック
    mock_store.query.return_value = {
        "ids": [["doc1", "doc2"]],
        "documents": [["文書1の内容", "文書2の内容"]],
        "metadatas": [[{"source": "test1.docx"}, {"source": "test2.docx"}]],
        "distances": [[0.1, 0.2]]
    }
    
    return mock_store


# =====================================
# テストデータ
# =====================================

@pytest.fixture
def sample_document_content() -> str:
    """サンプル文書コンテンツ"""
    return """
    議事メモ
    
    日時: 2024年1月1日 10:00-11:00
    参加者: 山田太郎、佐藤花子、鈴木一郎
    
    議題:
    1. プロジェクトの進捗確認
    2. 次回アクションの決定
    
    内容:
    - プロジェクトは予定通り進行中
    - 次回は2週間後に開催予定
    """


@pytest.fixture
def sample_metadata() -> Dict[str, Any]:
    """サンプルメタデータ"""
    return {
        "file_id": "test_file_123",
        "file_name": "議事メモ_20240101.docx",
        "modified_time": "2024-01-01T00:00:00.000Z",
        "source": "google_drive",
        "chunk_index": 0
    }


@pytest.fixture
def malicious_inputs() -> Dict[str, Any]:
    """意地悪なテスト用入力データ集"""
    return {
        # 境界値攻撃
        "empty_string": "",
        "whitespace_only": "   \t\n  ",
        "very_long_string": "A" * 1_000_000,
        "zero": 0,
        "negative": -1,
        "max_int": sys.maxsize,
        "min_int": -sys.maxsize - 1,
        
        # 型攻撃
        "none_value": None,
        "string_as_number": "123abc",
        "list_instead_of_string": ["not", "a", "string"],
        "dict_instead_of_list": {"not": "a list"},
        
        # 特殊文字攻撃
        "sql_injection": "'; DROP TABLE users; --",
        "path_traversal": "../../etc/passwd",
        "null_byte": "test\x00injection",
        "unicode_mixed": "テスト🔥\u0000\uFEFF",
        "control_chars": "\x01\x02\x03\x04",
        
        # 論理爆弾
        "nested_structure": {"a": {"b": {"c": {"d": {"e": "deep"}}}}},
        "circular_reference_attempt": "[1, [2, [3, [4]]]]",
    }


# =====================================
# テストヘルパー関数
# =====================================

def assert_raises_with_message(exception_type, message_substring, callable_func, *args, **kwargs):
    """例外が発生し、特定のメッセージを含むことを確認"""
    with pytest.raises(exception_type) as exc_info:
        callable_func(*args, **kwargs)
    assert message_substring in str(exc_info.value), \
        f"Expected '{message_substring}' in exception message, got: {exc_info.value}"


# =====================================
# セッションレベルのセットアップ
# =====================================

@pytest.fixture(scope="session", autouse=True)
def test_session_setup():
    """テストセッション全体のセットアップ"""
    print("\n" + "=" * 70)
    print("🔥 テスターAI起動: 意地悪なテストを開始します")
    print("=" * 70)
    
    yield
    
    print("\n" + "=" * 70)
    print("✅ テストセッション完了")
    print("=" * 70)


# =====================================
# パラメータ化用データ
# =====================================

# 境界値テスト用パラメータ
BOUNDARY_VALUES = [
    pytest.param(None, id="none"),
    pytest.param("", id="empty_string"),
    pytest.param(" ", id="single_space"),
    pytest.param("\n", id="newline"),
    pytest.param("\t", id="tab"),
    pytest.param(0, id="zero"),
    pytest.param(-1, id="negative_one"),
    pytest.param(sys.maxsize, id="max_int"),
]

# 型攻撃用パラメータ
TYPE_ATTACK_VALUES = [
    pytest.param(None, id="none_type"),
    pytest.param([], id="empty_list"),
    pytest.param({}, id="empty_dict"),
    pytest.param(123, id="integer"),
    pytest.param(12.34, id="float"),
    pytest.param(True, id="boolean"),
    pytest.param(object(), id="object"),
]

# 特殊文字攻撃用パラメータ
SPECIAL_CHAR_ATTACKS = [
    pytest.param("'; DROP TABLE users; --", id="sql_injection"),
    pytest.param("../../etc/passwd", id="path_traversal"),
    pytest.param("<script>alert('XSS')</script>", id="xss_attack"),
    pytest.param("\x00\x01\x02", id="control_chars"),
    pytest.param("テスト🔥💀👻", id="unicode_emoji"),
]


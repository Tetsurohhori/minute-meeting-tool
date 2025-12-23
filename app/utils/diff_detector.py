"""
差分検出モジュール（堅牢版）
ファイルの変更を検出し、増分更新を管理
"""

import json
import hashlib
import logging
from pathlib import Path
from typing import Dict, Set, Tuple, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class DiffDetectorError(Exception):
    """差分検出エラー用のカスタム例外"""
    pass


class DiffDetector:
    """
    ファイル差分検出クラス（堅牢版）
    
    すべての入力に対して厳格なバリデーションを行い、
    型安全性とセキュリティを保証します。
    """
    
    def __init__(self, metadata_path: Path):
        """
        差分検出器を初期化
        
        Args:
            metadata_path: メタデータ保存先ディレクトリ（Path オブジェクト）
        
        Raises:
            DiffDetectorError: パスが不正な場合
        """
        # 型チェック
        if not isinstance(metadata_path, Path):
            raise DiffDetectorError(
                f"metadata_path must be a Path object, got {type(metadata_path).__name__}"
            )
        
        # パストラバーサル対策（絶対パスに解決）
        self.metadata_path = metadata_path.resolve()
        
        # セキュリティチェック：パストラバーサルの検出
        if ".." in str(metadata_path):
            logger.warning(
                f"Path traversal pattern detected in metadata_path: {metadata_path}. "
                "Resolved to: {self.metadata_path}"
            )
        
        self.metadata_file = self.metadata_path / "file_metadata.json"
        self.metadata: Dict[str, dict] = self._load_metadata()
    
    def _load_metadata(self) -> Dict[str, dict]:
        """
        保存されているメタデータを読み込み
        
        Returns:
            メタデータ辞書
        """
        if not self.metadata_file.exists():
            return {}
        
        try:
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 型チェック：辞書であることを確認
            if not isinstance(data, dict):
                logger.error(
                    f"Metadata file contains invalid type: {type(data).__name__}. "
                    "Expected dict. Returning empty dict."
                )
                return {}
            
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse metadata JSON: {e}")
            return {}
        except Exception as e:
            logger.error(f"Failed to load metadata: {e}")
            return {}
    
    def _save_metadata(self):
        """
        メタデータを保存
        
        Raises:
            DiffDetectorError: 保存に失敗した場合
        """
        try:
            # ディレクトリが存在しない場合は作成
            self.metadata_path.mkdir(parents=True, exist_ok=True)
            
            # JSONにシリアライズ可能か確認
            json_str = json.dumps(self.metadata, ensure_ascii=False, indent=2)
            
            # ファイルに書き込み
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                f.write(json_str)
                
        except TypeError as e:
            raise DiffDetectorError(
                f"Failed to serialize metadata to JSON: {e}. "
                "Metadata contains non-serializable objects."
            ) from e
        except OSError as e:
            raise DiffDetectorError(
                f"Failed to save metadata to {self.metadata_file}: {e}"
            ) from e
    
    def _calculate_hash(self, content: bytes) -> str:
        """
        コンテンツのハッシュ値を計算
        
        Args:
            content: バイト列コンテンツ
        
        Returns:
            SHA256ハッシュ値
        
        Raises:
            DiffDetectorError: contentが不正な場合
        """
        if not isinstance(content, bytes):
            raise DiffDetectorError(
                f"content must be bytes, got {type(content).__name__}"
            )
        
        return hashlib.sha256(content).hexdigest()
    
    def detect_changes(
        self,
        current_files: Dict[str, dict]
    ) -> Tuple[Set[str], Set[str], Set[str]]:
        """
        ファイルの変更を検出
        
        Args:
            current_files: 現在のファイル情報
                {file_id: {"name": str, "content_hash": str, "modified_time": str}}
        
        Returns:
            (新規ファイル, 更新ファイル, 削除ファイル) のタプル
        
        Raises:
            DiffDetectorError: current_filesが不正な場合
        """
        # 型チェック
        if not isinstance(current_files, dict):
            raise DiffDetectorError(
                f"current_files must be a dict, got {type(current_files).__name__}"
            )
        
        current_ids = set(current_files.keys())
        stored_ids = set(self.metadata.keys())
        
        # 新規ファイル
        new_files = current_ids - stored_ids
        
        # 削除ファイル
        deleted_files = stored_ids - current_ids
        
        # 更新ファイル（ハッシュ値が変更されたもの）
        updated_files = set()
        for file_id in current_ids & stored_ids:
            current_hash = current_files[file_id].get("content_hash", "")
            stored_hash = self.metadata[file_id].get("content_hash", "")
            if current_hash != stored_hash:
                updated_files.add(file_id)
        
        return new_files, updated_files, deleted_files
    
    def update_metadata(
        self,
        file_id: str,
        file_info: dict
    ):
        """
        特定ファイルのメタデータを更新
        
        Args:
            file_id: ファイルID
            file_info: ファイル情報
        
        Raises:
            DiffDetectorError: 引数が不正な場合
        """
        # file_id の型チェック
        if not isinstance(file_id, str):
            raise DiffDetectorError(
                f"file_id must be a string, got {type(file_id).__name__}"
            )
        
        if not file_id.strip():
            raise DiffDetectorError("file_id cannot be empty or whitespace only")
        
        # file_info の型チェック
        if not isinstance(file_info, dict):
            raise DiffDetectorError(
                f"file_info must be a dict, got {type(file_info).__name__}"
            )
        
        # メタデータを更新
        self.metadata[file_id] = {
            **file_info,
            "last_updated": datetime.now().isoformat()
        }
        
        # 保存
        self._save_metadata()
    
    def remove_metadata(self, file_id: str):
        """
        特定ファイルのメタデータを削除
        
        Args:
            file_id: ファイルID
        
        Raises:
            DiffDetectorError: file_idが不正な場合
        """
        # file_id の型チェック
        if not isinstance(file_id, str):
            raise DiffDetectorError(
                f"file_id must be a string, got {type(file_id).__name__}"
            )
        
        # ファイルが存在する場合のみ削除
        if file_id in self.metadata:
            del self.metadata[file_id]
            self._save_metadata()
        else:
            logger.warning(f"Attempted to remove non-existent file_id: {file_id}")
    
    def get_file_info(self, file_id: str) -> Optional[dict]:
        """
        ファイル情報を取得
        
        Args:
            file_id: ファイルID
        
        Returns:
            ファイル情報またはNone
        
        Raises:
            DiffDetectorError: file_idが不正な場合
        """
        # file_id の型チェック
        if not isinstance(file_id, str):
            raise DiffDetectorError(
                f"file_id must be a string, got {type(file_id).__name__}"
            )
        
        return self.metadata.get(file_id)
    
    def get_all_files(self) -> Dict[str, dict]:
        """
        全てのファイル情報を取得
        
        Returns:
            ファイル情報の辞書のコピー
        """
        return self.metadata.copy()

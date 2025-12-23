"""
データソース抽象基底クラス（堅牢版）
Google DriveとSharePointの実装を統一的に扱うためのインターフェース
"""

import hashlib
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class DocumentValidationError(Exception):
    """ドキュメント検証エラー用のカスタム例外"""
    pass


@dataclass
class DocumentInfo:
    """
    ドキュメント情報（堅牢版）
    
    すべてのフィールドに対して厳格な型チェックとバリデーションを行います。
    
    Attributes:
        file_id: ファイルID（一意な識別子）
        name: ファイル名
        content: ドキュメントの内容
        modified_time: 最終更新日時
        folder_path: フォルダパス
        content_hash: コンテンツのSHA256ハッシュ（自動計算可能）
        metadata: 追加のメタデータ
    
    Raises:
        DocumentValidationError: フィールドが不正な場合
    """
    
    # 定数定義
    MAX_CONTENT_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_FILE_ID_LENGTH = 1000
    MAX_NAME_LENGTH = 1000
    MAX_PATH_LENGTH = 2000
    
    file_id: str
    name: str
    content: str
    modified_time: datetime
    folder_path: str
    content_hash: str = ""
    metadata: Dict[str, any] = field(default_factory=dict)
    
    def __post_init__(self):
        """
        初期化後の検証
        
        すべてのフィールドに対して型チェックとバリデーションを実行します。
        
        Raises:
            DocumentValidationError: フィールドが不正な場合
        """
        # file_id の検証
        self._validate_file_id()
        
        # name の検証
        self._validate_name()
        
        # content の検証
        self._validate_content()
        
        # modified_time の検証
        self._validate_modified_time()
        
        # folder_path の検証
        self._validate_folder_path()
        
        # metadata の検証
        self._validate_metadata()
        
        # content_hash の検証または自動計算
        self._validate_or_compute_hash()
    
    def _validate_file_id(self):
        """file_id のバリデーション"""
        if not isinstance(self.file_id, str):
            raise DocumentValidationError(
                f"file_id must be a string, got {type(self.file_id).__name__}"
            )
        
        if not self.file_id.strip():
            raise DocumentValidationError("file_id cannot be empty or whitespace only")
        
        if len(self.file_id) > self.MAX_FILE_ID_LENGTH:
            raise DocumentValidationError(
                f"file_id is too long ({len(self.file_id)} chars, max: {self.MAX_FILE_ID_LENGTH})"
            )
        
        # パストラバーサル対策
        if ".." in self.file_id:
            raise DocumentValidationError(
                "Path traversal detected in file_id: '..' is not allowed"
            )
    
    def _validate_name(self):
        """name のバリデーション"""
        if not isinstance(self.name, str):
            raise DocumentValidationError(
                f"name must be a string, got {type(self.name).__name__}"
            )
        
        if not self.name.strip():
            raise DocumentValidationError("name cannot be empty or whitespace only")
        
        if len(self.name) > self.MAX_NAME_LENGTH:
            raise DocumentValidationError(
                f"name is too long ({len(self.name)} chars, max: {self.MAX_NAME_LENGTH})"
            )
        
        # 危険な文字のチェック（XSS対策）
        dangerous_chars = ['<', '>', '"', "'"]
        for char in dangerous_chars:
            if char in self.name:
                logger.warning(
                    f"Potentially dangerous character '{char}' found in name: {self.name}"
                )
    
    def _validate_content(self):
        """content のバリデーション"""
        if not isinstance(self.content, str):
            raise DocumentValidationError(
                f"content must be a string, got {type(self.content).__name__}"
            )
        
        # 空のコンテンツは許可（空ファイルの可能性）
        
        # サイズ制限チェック
        content_size = len(self.content.encode('utf-8'))
        if content_size > self.MAX_CONTENT_SIZE:
            raise DocumentValidationError(
                f"Content size exceeds limit: {content_size} bytes "
                f"(max: {self.MAX_CONTENT_SIZE} bytes = {self.MAX_CONTENT_SIZE // (1024*1024)}MB)"
            )
    
    def _validate_modified_time(self):
        """modified_time のバリデーション"""
        if not isinstance(self.modified_time, datetime):
            raise DocumentValidationError(
                f"modified_time must be a datetime object, got {type(self.modified_time).__name__}"
            )
        
        # 未来の日時チェック（異常なタイムスタンプの検出）
        now = datetime.now(timezone.utc)
        if self.modified_time > now:
            logger.warning(
                f"modified_time is in the future: {self.modified_time} > {now}. "
                "This may indicate a system clock issue."
            )
    
    def _validate_folder_path(self):
        """folder_path のバリデーション"""
        if not isinstance(self.folder_path, str):
            raise DocumentValidationError(
                f"folder_path must be a string, got {type(self.folder_path).__name__}"
            )
        
        # 空のフォルダパスは許可（ルートディレクトリの可能性）
        
        if len(self.folder_path) > self.MAX_PATH_LENGTH:
            raise DocumentValidationError(
                f"folder_path is too long ({len(self.folder_path)} chars, max: {self.MAX_PATH_LENGTH})"
            )
        
        # パストラバーサル対策
        if ".." in self.folder_path:
            raise DocumentValidationError(
                "Path traversal detected in folder_path: '..' is not allowed"
            )
    
    def _validate_metadata(self):
        """metadata のバリデーション"""
        # None の場合は空の辞書に変換
        if self.metadata is None:
            self.metadata = {}
        
        # 型チェック
        if not isinstance(self.metadata, dict):
            raise DocumentValidationError(
                f"metadata must be a dictionary, got {type(self.metadata).__name__}"
            )
    
    def _validate_or_compute_hash(self):
        """content_hash の検証または自動計算"""
        # ハッシュが指定されていない場合は自動計算
        if not self.content_hash:
            self.content_hash = self._calculate_hash()
            return
        
        # ハッシュが指定されている場合は型チェック
        if not isinstance(self.content_hash, str):
            raise DocumentValidationError(
                f"content_hash must be a string, got {type(self.content_hash).__name__}"
            )
        
        # ハッシュの形式チェック（SHA256は64文字の16進数）
        if len(self.content_hash) != 64:
            logger.warning(
                f"content_hash length is {len(self.content_hash)}, "
                "expected 64 for SHA256. Hash may not be valid."
            )
        
        # オプション：ハッシュの整合性チェック
        # 計算したハッシュと一致するか確認（パフォーマンス影響あり）
        computed_hash = self._calculate_hash()
        if self.content_hash != computed_hash:
            logger.warning(
                f"Provided content_hash does not match computed hash. "
                f"Provided: {self.content_hash[:16]}..., Computed: {computed_hash[:16]}..."
            )
    
    def _calculate_hash(self) -> str:
        """
        コンテンツのSHA256ハッシュを計算
        
        Returns:
            64文字の16進数ハッシュ値
        """
        return hashlib.sha256(self.content.encode('utf-8')).hexdigest()
    
    def verify_hash(self) -> bool:
        """
        保存されているハッシュとコンテンツが一致するか検証
        
        Returns:
            一致する場合True
        """
        return self.content_hash == self._calculate_hash()


class DataSourceBase(ABC):
    """データソース抽象基底クラス"""
    
    @abstractmethod
    def authenticate(self) -> bool:
        """
        認証を行う
        
        Returns:
            認証成功の場合True
        """
        pass
    
    @abstractmethod
    def list_documents(self, folder_path: Optional[str] = None) -> List[DocumentInfo]:
        """
        ドキュメント一覧を取得
        
        Args:
            folder_path: フォルダパス（Noneの場合はルート）
        
        Returns:
            ドキュメント情報のリスト
        """
        pass
    
    @abstractmethod
    def get_document_content(self, file_id: str) -> str:
        """
        ドキュメントの内容を取得
        
        Args:
            file_id: ファイルID
        
        Returns:
            ドキュメントの内容
        """
        pass
    
    @abstractmethod
    def get_document_info(self, file_id: str) -> Optional[DocumentInfo]:
        """
        ドキュメント情報を取得
        
        Args:
            file_id: ファイルID
        
        Returns:
            ドキュメント情報
        """
        pass
    
    def get_all_documents_recursive(self, root_folder: Optional[str] = None) -> List[DocumentInfo]:
        """
        全てのドキュメントを再帰的に取得
        
        Args:
            root_folder: ルートフォルダパス
        
        Returns:
            全ドキュメント情報のリスト
        """
        return self.list_documents(root_folder)

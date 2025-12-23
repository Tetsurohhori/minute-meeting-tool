"""
Google Drive データソース実装
"""

import io
import hashlib
from typing import List, Optional
from datetime import datetime
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

from docx import Document as DocxDocument

from .base import DataSourceBase, DocumentInfo
from ..utils.logger import setup_logger


# Google Drive APIのスコープ
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']


class GoogleDriveDataSource(DataSourceBase):
    """Google Drive データソースクラス"""
    
    def __init__(
        self,
        folder_id: str,
        credentials_path: Path,
        token_path: Path,
        log_path: Path
    ):
        """
        Args:
            folder_id: Google DriveフォルダID
            credentials_path: credentials.jsonのパス
            token_path: token.jsonのパス（自動生成）
            log_path: ログ出力先
        """
        self.folder_id = folder_id
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.service = None
        self.logger = setup_logger("GoogleDrive", log_path)
    
    def authenticate(self) -> bool:
        """Google Drive APIの認証"""
        try:
            creds = None
            
            # トークンが存在する場合は読み込む
            if self.token_path.exists():
                creds = Credentials.from_authorized_user_file(str(self.token_path), SCOPES)
            
            # トークンが無効または存在しない場合は新規認証
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    if not self.credentials_path.exists():
                        self.logger.error(f"credentials.json が見つかりません: {self.credentials_path}")
                        return False
                    
                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(self.credentials_path), SCOPES
                    )
                    creds = flow.run_local_server(port=0)
                
                # トークンを保存
                with open(self.token_path, 'w') as token:
                    token.write(creds.to_json())
            
            # Drive APIサービスを構築
            self.service = build('drive', 'v3', credentials=creds)
            self.logger.info("Google Drive認証に成功しました")
            return True
            
        except Exception as e:
            self.logger.error(f"Google Drive認証に失敗: {e}")
            return False
    
    def _get_folders_in_folder(self, folder_id: str) -> List[dict]:
        """フォルダ内のサブフォルダ一覧を取得"""
        try:
            query = f"'{folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
            results = self.service.files().list(
                q=query,
                fields="files(id, name, modifiedTime)"
            ).execute()
            return results.get('files', [])
        except Exception as e:
            self.logger.error(f"フォルダ一覧取得エラー: {e}")
            return []
    
    def _get_files_in_folder(self, folder_id: str) -> List[dict]:
        """フォルダ内のファイル一覧を取得（Googleドキュメント）"""
        try:
            # Google Docsのみを取得
            query = f"'{folder_id}' in parents and (mimeType='application/vnd.google-apps.document' or mimeType='application/vnd.openxmlformats-officedocument.wordprocessingml.document') and trashed=false"
            results = self.service.files().list(
                q=query,
                fields="files(id, name, modifiedTime, mimeType)"
            ).execute()
            return results.get('files', [])
        except Exception as e:
            self.logger.error(f"ファイル一覧取得エラー: {e}")
            return []
    
    def list_documents(self, folder_path: Optional[str] = None) -> List[DocumentInfo]:
        """ドキュメント一覧を取得（再帰的に全フォルダを探索）"""
        if not self.service:
            self.authenticate()
        
        documents = []
        
        # ルートフォルダから再帰的に探索
        self._list_documents_recursive(self.folder_id, "", documents)
        
        self.logger.info(f"合計 {len(documents)} 件のドキュメントを取得しました")
        return documents
    
    def _list_documents_recursive(
        self,
        folder_id: str,
        current_path: str,
        documents: List[DocumentInfo]
    ):
        """再帰的にドキュメントを取得"""
        # 現在のフォルダ内のファイルを取得
        files = self._get_files_in_folder(folder_id)
        
        for file in files:
            try:
                content = self.get_document_content(file['id'])
                content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
                
                modified_time = datetime.fromisoformat(
                    file['modifiedTime'].replace('Z', '+00:00')
                )
                
                doc_info = DocumentInfo(
                    file_id=file['id'],
                    name=file['name'],
                    content=content,
                    modified_time=modified_time,
                    folder_path=current_path,
                    content_hash=content_hash,
                    metadata={
                        'mimeType': file.get('mimeType', ''),
                        'data_source': 'google_drive',
                        'file_url': f"https://drive.google.com/file/d/{file['id']}/view"
                    }
                )
                documents.append(doc_info)
                self.logger.info(f"取得: {current_path}/{file['name']}")
                
            except Exception as e:
                self.logger.error(f"ファイル取得エラー ({file['name']}): {e}")
        
        # サブフォルダを再帰的に探索
        subfolders = self._get_folders_in_folder(folder_id)
        for subfolder in subfolders:
            subfolder_path = f"{current_path}/{subfolder['name']}" if current_path else subfolder['name']
            self._list_documents_recursive(subfolder['id'], subfolder_path, documents)
    
    def get_document_content(self, file_id: str) -> str:
        """ドキュメントの内容を取得"""
        if not self.service:
            self.authenticate()
        
        try:
            # ファイル情報を取得
            file_metadata = self.service.files().get(fileId=file_id, fields='mimeType').execute()
            mime_type = file_metadata.get('mimeType')
            
            # Google Docsの場合
            if mime_type == 'application/vnd.google-apps.document':
                # テキスト形式でエクスポート
                request = self.service.files().export_media(
                    fileId=file_id,
                    mimeType='text/plain'
                )
                file_content = io.BytesIO()
                downloader = MediaIoBaseDownload(file_content, request)
                
                done = False
                while not done:
                    status, done = downloader.next_chunk()
                
                return file_content.getvalue().decode('utf-8')
            
            # Word文書の場合
            elif mime_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
                request = self.service.files().get_media(fileId=file_id)
                file_content = io.BytesIO()
                downloader = MediaIoBaseDownload(file_content, request)
                
                done = False
                while not done:
                    status, done = downloader.next_chunk()
                
                # python-docxで読み込み
                file_content.seek(0)
                doc = DocxDocument(file_content)
                return '\n'.join([para.text for para in doc.paragraphs])
            
            else:
                self.logger.warning(f"未対応のファイル形式: {mime_type}")
                return ""
                
        except Exception as e:
            self.logger.error(f"ドキュメント内容取得エラー: {e}")
            return ""
    
    def get_document_info(self, file_id: str) -> Optional[DocumentInfo]:
        """ドキュメント情報を取得"""
        if not self.service:
            self.authenticate()
        
        try:
            file = self.service.files().get(
                fileId=file_id,
                fields='id, name, modifiedTime, mimeType'
            ).execute()
            
            content = self.get_document_content(file_id)
            content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
            
            modified_time = datetime.fromisoformat(
                file['modifiedTime'].replace('Z', '+00:00')
            )
            
            return DocumentInfo(
                file_id=file['id'],
                name=file['name'],
                content=content,
                modified_time=modified_time,
                folder_path="",
                content_hash=content_hash,
                metadata={'mimeType': file.get('mimeType', '')}
            )
            
        except Exception as e:
            self.logger.error(f"ドキュメント情報取得エラー: {e}")
            return None


"""
SharePoint データソース実装
"""

import io
import hashlib
from typing import List, Optional
from datetime import datetime
from pathlib import Path

from office365.runtime.auth.client_credential import ClientCredential
from office365.sharepoint.client_context import ClientContext
from office365.sharepoint.files.file import File

from docx import Document as DocxDocument

from .base import DataSourceBase, DocumentInfo
from ..utils.logger import setup_logger


class SharePointDataSource(DataSourceBase):
    """SharePoint データソースクラス"""
    
    def __init__(
        self,
        site_url: str,
        folder_path: str,
        client_id: str,
        client_secret: str,
        tenant_id: str,
        log_path: Path
    ):
        """
        Args:
            site_url: SharePointサイトURL
            folder_path: ドキュメントフォルダパス
            client_id: アプリケーションクライアントID
            client_secret: クライアントシークレット
            tenant_id: テナントID
            log_path: ログ出力先
        """
        self.site_url = site_url
        self.folder_path = folder_path
        self.client_id = client_id
        self.client_secret = client_secret
        self.tenant_id = tenant_id
        self.ctx = None
        self.logger = setup_logger("SharePoint", log_path)
    
    def authenticate(self) -> bool:
        """SharePoint認証"""
        try:
            credentials = ClientCredential(self.client_id, self.client_secret)
            self.ctx = ClientContext(self.site_url).with_credentials(credentials)
            
            # 接続テスト
            web = self.ctx.web
            self.ctx.load(web)
            self.ctx.execute_query()
            
            self.logger.info(f"SharePoint認証に成功: {web.properties['Title']}")
            return True
            
        except Exception as e:
            self.logger.error(f"SharePoint認証に失敗: {e}")
            return False
    
    def _get_folder_items_recursive(
        self,
        folder_url: str,
        current_path: str,
        documents: List[DocumentInfo]
    ):
        """フォルダ内のアイテムを再帰的に取得"""
        try:
            # フォルダを取得
            folder = self.ctx.web.get_folder_by_server_relative_url(folder_url)
            
            # ファイル一覧を取得
            files = folder.files
            self.ctx.load(files)
            self.ctx.execute_query()
            
            for file in files:
                # Word文書のみを対象
                if file.name.endswith(('.docx', '.doc')):
                    try:
                        content = self._get_file_content(file)
                        content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
                        
                        # 修正日時を取得
                        self.ctx.load(file, ['TimeLastModified'])
                        self.ctx.execute_query()
                        
                        modified_time = file.properties.get('TimeLastModified')
                        if isinstance(modified_time, str):
                            modified_time = datetime.fromisoformat(modified_time.replace('Z', '+00:00'))
                        
                        # SharePointファイルのWebURLを構築
                        server_relative_url = file.properties.get('ServerRelativeUrl', '')
                        file_url = f"{self.site_url}/_layouts/15/Doc.aspx?sourcedoc={{{file.properties['UniqueId']}}}&action=default"
                        
                        doc_info = DocumentInfo(
                            file_id=file.properties['UniqueId'],
                            name=file.name,
                            content=content,
                            modified_time=modified_time,
                            folder_path=current_path,
                            content_hash=content_hash,
                            metadata={
                                'server_relative_url': server_relative_url,
                                'size': file.properties.get('Length', 0),
                                'data_source': 'sharepoint',
                                'file_url': file_url
                            }
                        )
                        documents.append(doc_info)
                        self.logger.info(f"取得: {current_path}/{file.name}")
                        
                    except Exception as e:
                        self.logger.error(f"ファイル取得エラー ({file.name}): {e}")
            
            # サブフォルダを取得
            subfolders = folder.folders
            self.ctx.load(subfolders)
            self.ctx.execute_query()
            
            for subfolder in subfolders:
                # システムフォルダをスキップ
                if subfolder.name.startswith('_'):
                    continue
                
                subfolder_path = f"{current_path}/{subfolder.name}" if current_path else subfolder.name
                subfolder_url = subfolder.properties['ServerRelativeUrl']
                self._get_folder_items_recursive(subfolder_url, subfolder_path, documents)
                
        except Exception as e:
            self.logger.error(f"フォルダ取得エラー ({folder_url}): {e}")
    
    def _get_file_content(self, file: File) -> str:
        """ファイル内容を取得"""
        try:
            # ファイルをダウンロード
            response = File.open_binary(self.ctx, file.properties['ServerRelativeUrl'])
            
            # BytesIOに変換
            file_content = io.BytesIO(response.content)
            
            # python-docxで読み込み
            doc = DocxDocument(file_content)
            return '\n'.join([para.text for para in doc.paragraphs])
            
        except Exception as e:
            self.logger.error(f"ファイル内容取得エラー: {e}")
            return ""
    
    def list_documents(self, folder_path: Optional[str] = None) -> List[DocumentInfo]:
        """ドキュメント一覧を取得"""
        if not self.ctx:
            self.authenticate()
        
        documents = []
        
        # フォルダパスの構築
        target_folder = folder_path if folder_path else self.folder_path
        
        # 再帰的に取得
        self._get_folder_items_recursive(target_folder, "", documents)
        
        self.logger.info(f"合計 {len(documents)} 件のドキュメントを取得しました")
        return documents
    
    def get_document_content(self, file_id: str) -> str:
        """ドキュメントの内容を取得（file_idはServerRelativeUrl）"""
        if not self.ctx:
            self.authenticate()
        
        try:
            file = self.ctx.web.get_file_by_server_relative_url(file_id)
            self.ctx.load(file)
            self.ctx.execute_query()
            
            return self._get_file_content(file)
            
        except Exception as e:
            self.logger.error(f"ドキュメント内容取得エラー: {e}")
            return ""
    
    def get_document_info(self, file_id: str) -> Optional[DocumentInfo]:
        """ドキュメント情報を取得"""
        if not self.ctx:
            self.authenticate()
        
        try:
            file = self.ctx.web.get_file_by_server_relative_url(file_id)
            self.ctx.load(file, ['Name', 'TimeLastModified', 'UniqueId', 'ServerRelativeUrl', 'Length'])
            self.ctx.execute_query()
            
            content = self._get_file_content(file)
            content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
            
            modified_time = file.properties.get('TimeLastModified')
            if isinstance(modified_time, str):
                modified_time = datetime.fromisoformat(modified_time.replace('Z', '+00:00'))
            
            return DocumentInfo(
                file_id=file.properties['UniqueId'],
                name=file.properties['Name'],
                content=content,
                modified_time=modified_time,
                folder_path="",
                content_hash=content_hash,
                metadata={
                    'server_relative_url': file.properties.get('ServerRelativeUrl', ''),
                    'size': file.properties.get('Length', 0)
                }
            )
            
        except Exception as e:
            self.logger.error(f"ドキュメント情報取得エラー: {e}")
            return None


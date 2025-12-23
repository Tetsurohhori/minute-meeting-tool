"""
ロギング設定モジュール
"""

import logging
from pathlib import Path
from datetime import datetime


def setup_logger(
    name: str,
    log_path: Path,
    level: str = "INFO"
) -> logging.Logger:
    """
    ロガーをセットアップ
    
    Args:
        name: ロガー名
        log_path: ログファイルの保存先ディレクトリ
        level: ログレベル
    
    Returns:
        設定済みのロガー
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level))
    
    # 既存のハンドラをクリア
    logger.handlers.clear()
    
    # フォーマッター
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # コンソールハンドラ
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # ファイルハンドラ
    log_path.mkdir(parents=True, exist_ok=True)
    log_file = log_path / f"{name}_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger


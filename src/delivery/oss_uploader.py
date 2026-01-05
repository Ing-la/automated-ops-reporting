"""
阿里云OSS文件上传模块

用于将报告文件上传到OSS，生成可访问的URL
"""

import os
from pathlib import Path
from typing import Optional
from src.utils.config import get_env


try:
    import oss2
    OSS2_AVAILABLE = True
except ImportError:
    OSS2_AVAILABLE = False


class OSSUploader:
    """阿里云OSS上传器"""
    
    def __init__(
        self,
        bucket_name: Optional[str] = None,
        endpoint: Optional[str] = None,
        access_key_id: Optional[str] = None,
        access_key_secret: Optional[str] = None
    ):
        """
        初始化OSS上传器
        
        Args:
            bucket_name: Bucket名称
            endpoint: OSS Endpoint（例如：oss-cn-beijing.aliyuncs.com）
            access_key_id: AccessKey ID
            access_key_secret: AccessKey Secret
        """
        if not OSS2_AVAILABLE:
            raise ImportError(
                "oss2库未安装。请运行: pip install oss2"
            )
        
        # 从参数或环境变量获取配置
        self.bucket_name = bucket_name or get_env("OSS_BUCKET_NAME")
        self.endpoint = endpoint or get_env("OSS_ENDPOINT")
        self.access_key_id = access_key_id or get_env("OSS_ACCESS_KEY_ID")
        self.access_key_secret = access_key_secret or get_env("OSS_ACCESS_KEY_SECRET")
        
        if not all([self.bucket_name, self.endpoint, self.access_key_id, self.access_key_secret]):
            raise ValueError(
                "OSS配置不完整。请设置环境变量：\n"
                "- OSS_BUCKET_NAME\n"
                "- OSS_ENDPOINT\n"
                "- OSS_ACCESS_KEY_ID\n"
                "- OSS_ACCESS_KEY_SECRET"
            )
        
        # 创建OSS客户端
        auth = oss2.Auth(self.access_key_id, self.access_key_secret)
        self.bucket = oss2.Bucket(auth, f"https://{self.endpoint}", self.bucket_name)
    
    def upload_file(
        self,
        local_file_path: Path,
        remote_path: Optional[str] = None,
        content_type: Optional[str] = None
    ) -> str:
        """
        上传文件到OSS
        
        Args:
            local_file_path: 本地文件路径
            remote_path: OSS中的路径（如果不提供，则使用文件名）
            content_type: 文件MIME类型（如果不提供，则根据文件扩展名自动判断）
        
        Returns:
            文件的公开访问URL
        """
        if not local_file_path.exists():
            raise FileNotFoundError(f"文件不存在: {local_file_path}")
        
        # 如果没有指定远程路径，使用文件名
        if remote_path is None:
            remote_path = local_file_path.name
        
        # 自动判断Content-Type
        if content_type is None:
            content_type = self._guess_content_type(local_file_path)
        
        # 上传文件
        with open(local_file_path, 'rb') as f:
            self.bucket.put_object(
                remote_path,
                f,
                headers={'Content-Type': content_type}
            )
        
        # 生成公开访问URL
        # 格式：https://bucket-name.endpoint/remote_path
        url = f"https://{self.bucket_name}.{self.endpoint}/{remote_path}"
        
        return url
    
    def upload_report(
        self,
        report_file_path: Path,
        month: str,
        file_type: str = "md"
    ) -> str:
        """
        上传报告文件到OSS（使用标准路径结构）
        
        Args:
            report_file_path: 报告文件路径
            month: 月份，格式YYYY-MM
            file_type: 文件类型（md或pdf）
        
        Returns:
            文件的公开访问URL
        """
        # 标准路径：reports/YYYY_MM/report_YYYY_MM.{md|pdf}
        month_str = month.replace('-', '_')
        remote_path = f"reports/{month_str}/report_{month_str}.{file_type}"
        
        return self.upload_file(report_file_path, remote_path)
    
    def upload_table_file(
        self,
        table_file_path: Path,
        month: str,
        table_name: str
    ) -> str:
        """
        上传表格文件到OSS（使用标准路径结构）
        
        Args:
            table_file_path: 表格文件路径（CSV格式）
            month: 月份，格式YYYY-MM
            table_name: 表格名称（用于生成文件名）
        
        Returns:
            文件的公开访问URL
        """
        # 标准路径：reports/YYYY_MM/tables/{table_name}_YYYY_MM.csv
        month_str = month.replace('-', '_')
        remote_path = f"reports/{month_str}/tables/{table_name}_{month_str}.csv"
        
        return self.upload_file(table_file_path, remote_path)
    
    @staticmethod
    def _guess_content_type(file_path: Path) -> str:
        """根据文件扩展名猜测Content-Type"""
        suffix = file_path.suffix.lower()
        content_types = {
            '.md': 'text/markdown; charset=utf-8',
            '.pdf': 'application/pdf',
            '.json': 'application/json; charset=utf-8',
            '.csv': 'text/csv; charset=utf-8',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
        }
        return content_types.get(suffix, 'application/octet-stream')


def upload_report_to_oss(
    report_file_path: Path,
    month: str,
    file_type: str = "md",
    bucket_name: Optional[str] = None,
    endpoint: Optional[str] = None,
    access_key_id: Optional[str] = None,
    access_key_secret: Optional[str] = None
) -> Optional[str]:
    """
    上传报告文件到OSS（便捷函数）
    
    Args:
        report_file_path: 报告文件路径
        month: 月份，格式YYYY-MM
        file_type: 文件类型（md或pdf）
        bucket_name: Bucket名称（可选，默认从环境变量读取）
        endpoint: OSS Endpoint（可选，默认从环境变量读取）
        access_key_id: AccessKey ID（可选，默认从环境变量读取）
        access_key_secret: AccessKey Secret（可选，默认从环境变量读取）
    
    Returns:
        文件的公开访问URL，如果上传失败则返回None
    """
    try:
        uploader = OSSUploader(
            bucket_name=bucket_name,
            endpoint=endpoint,
            access_key_id=access_key_id,
            access_key_secret=access_key_secret
        )
        url = uploader.upload_report(report_file_path, month, file_type)
        return url
    except Exception as e:
        print(f"⚠️  OSS上传失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def upload_table_to_oss(
    table_file_path: Path,
    month: str,
    table_name: str,
    bucket_name: Optional[str] = None,
    endpoint: Optional[str] = None,
    access_key_id: Optional[str] = None,
    access_key_secret: Optional[str] = None
) -> Optional[str]:
    """
    上传表格文件到OSS（便捷函数）
    
    Args:
        table_file_path: 表格文件路径（CSV格式）
        month: 月份，格式YYYY-MM
        table_name: 表格名称（用于生成文件名）
        bucket_name: Bucket名称（可选，默认从环境变量读取）
        endpoint: OSS Endpoint（可选，默认从环境变量读取）
        access_key_id: AccessKey ID（可选，默认从环境变量读取）
        access_key_secret: AccessKey Secret（可选，默认从环境变量读取）
    
    Returns:
        文件的公开访问URL，如果上传失败则返回None
    """
    try:
        uploader = OSSUploader(
            bucket_name=bucket_name,
            endpoint=endpoint,
            access_key_id=access_key_id,
            access_key_secret=access_key_secret
        )
        url = uploader.upload_table_file(table_file_path, month, table_name)
        return url
    except Exception as e:
        print(f"⚠️  表格上传失败: {e}")
        return None




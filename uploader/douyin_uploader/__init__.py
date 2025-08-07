from pathlib import Path

from conf import BASE_DIR

# 创建cookies目录
cookies_dir = Path(BASE_DIR) / "cookies" / "douyin_uploader"
cookies_dir.mkdir(parents=True, exist_ok=True)
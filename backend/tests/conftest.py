import os


os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test")
os.environ.setdefault("SYNC_DATABASE_URL", "postgresql://test:test@localhost/test")
os.environ.setdefault("DASHSCOPE_API_KEY", "test-key")
os.environ.setdefault("UPLOAD_DIR", "./test-uploads")

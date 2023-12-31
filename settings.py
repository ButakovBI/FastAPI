from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    server_host: str = '127.0.0.1'
    server_port: int = 8000

    postgres_user: str
    postgres_password: str
    postgres_server: str
    postgres_db: str

    # redis_host: str = '127.0.0.1'
    # redis_port: int = 6379
    # redis_password: str = ""
    #
    # jwt_secret_key: str
    # hash_algorithm: str
    # access_token_expire_minutes: int
    # jwt_secret: str
    # jwt_algorithm: str = 'hs256'
    # jwt_expires_s: int = 3600


settings = Settings(
    _env_file='.env',
    _env_file_encoding='utf-8',
)
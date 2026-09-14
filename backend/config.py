"""
ClaimBack System Configuration.
Loads settings from environment variables using Pydantic.
"""
from pathlib import Path

from pydantic_settings import BaseSettings
from pydantic import Field


ENV_FILE = Path(__file__).resolve().parent / ".env"

class Settings(BaseSettings):
    aws_region: str = Field(default="us-east-1", env="AWS_REGION")
    bedrock_model_id: str = Field(default="global.anthropic.claude-sonnet-4-6", env="BEDROCK_MODEL_ID")
    openai_model_id: str = Field(default="", env="OPENAI_MODEL_ID")
    openai_api_key: str = Field(default="", env="OPENAI_API_KEY")
    openai_base_url: str = Field(default="", env="OPENAI_BASE_URL")
    openai_project_id: str = Field(default="", env="OPENAI_PROJECT_ID")
    repository_backend: str = Field(default="memory", env="REPOSITORY_BACKEND")
    extraction_backend: str = Field(default="rules", env="EXTRACTION_BACKEND")
    dynamodb_table_name: str = Field(default="ClaimBackSingleTable", env="DYNAMODB_TABLE_NAME")
    dynamodb_endpoint_url: str = Field(default="", env="DYNAMODB_ENDPOINT_URL")
    textract_role_arn: str = Field(default="", env="TEXTRACT_ROLE_ARN")
    ocr_backend: str = Field(default="stub", env="OCR_BACKEND")
    s3_vault_bucket: str = Field(default="claimback-vault-bucket", env="S3_VAULT_BUCKET")
    claimback_raw_documents_bucket: str = Field(default="", env="CLAIMBACK_RAW_DOCUMENTS_BUCKET")
    claimback_generated_artifacts_bucket: str = Field(default="", env="CLAIMBACK_GENERATED_ARTIFACTS_BUCKET")
    submission_backend: str = Field(default="stub", env="SUBMISSION_BACKEND")
    ses_from_email: str = Field(default="", env="SES_FROM_EMAIL")
    ses_reply_to_email: str = Field(default="", env="SES_REPLY_TO_EMAIL")
    submission_recipient_override: str = Field(default="", env="SUBMISSION_RECIPIENT_OVERRIDE")
    cors_allowed_origins: str = Field(default="http://localhost:5173", env="CORS_ALLOWED_ORIGINS")
    aws_profile: str = Field(default="", env="AWS_PROFILE")
    aws_access_key_id: str = Field(default="", env="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: str = Field(default="", env="AWS_SECRET_ACCESS_KEY")
    aws_session_token: str = Field(default="", env="AWS_SESSION_TOKEN")
    environment: str = Field(default="production", env="ENVIRONMENT")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")

    # pydantic v2: use `model_config` to load env file and ignore unknown env vars
    model_config = {"env_file": str(ENV_FILE), "extra": "ignore"}

settings = Settings()

DEFAULT_MODEL_ID = settings.bedrock_model_id
DEFAULT_REGION = settings.aws_region
DEFAULT_TEMPERATURE = 0.1

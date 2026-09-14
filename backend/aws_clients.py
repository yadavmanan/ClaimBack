"""Shared boto3 session and client helpers for local and deployed runtimes."""

from functools import lru_cache
import os

from backend.config import settings


@lru_cache(maxsize=1)
def get_boto3_session():
    try:
        import boto3
    except ImportError as exc:
        raise RuntimeError("boto3 must be installed to use AWS-backed services") from exc

    session_kwargs = {}
    explicit_credentials = False

    if settings.aws_access_key_id and settings.aws_secret_access_key:
        explicit_credentials = True
        session_kwargs["aws_access_key_id"] = settings.aws_access_key_id
        session_kwargs["aws_secret_access_key"] = settings.aws_secret_access_key
        if settings.aws_session_token:
            session_kwargs["aws_session_token"] = settings.aws_session_token
    elif settings.aws_profile:
        session_kwargs["profile_name"] = settings.aws_profile

    if settings.aws_region:
        session_kwargs["region_name"] = settings.aws_region

    if explicit_credentials:
        previous_profile = os.environ.pop("AWS_PROFILE", None)
        previous_default_profile = os.environ.pop("AWS_DEFAULT_PROFILE", None)
        try:
            return boto3.session.Session(**session_kwargs)
        finally:
            if previous_profile is not None:
                os.environ["AWS_PROFILE"] = previous_profile
            if previous_default_profile is not None:
                os.environ["AWS_DEFAULT_PROFILE"] = previous_default_profile

    return boto3.session.Session(**session_kwargs)


def get_boto3_resource(service_name: str, endpoint_url: str | None = None):
    resource_kwargs = {}
    if endpoint_url:
        resource_kwargs["endpoint_url"] = endpoint_url
    return get_boto3_session().resource(service_name, **resource_kwargs)


def get_boto3_client(service_name: str, endpoint_url: str | None = None):
    client_kwargs = {}
    if endpoint_url:
        client_kwargs["endpoint_url"] = endpoint_url
    return get_boto3_session().client(service_name, **client_kwargs)
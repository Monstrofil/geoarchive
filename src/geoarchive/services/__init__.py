from . import softpro
from .base import ServiceProtocol


def get_service_protocol(type: str, url: str) -> ServiceProtocol:
    assert type == 'softpro', 'Unsupported service type'
    return softpro.SoftProService(url)
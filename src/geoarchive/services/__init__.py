from . import softpro
from . import softpro_legacy
from . import arcgis
from . import arcgis_layers
from .base import ServiceProtocol

_services = {
    'arcgis': arcgis.ArcGisProtocol,
    'arcgis_layers': arcgis_layers.ArcGisProtocol,
    'softpro': softpro.SoftProService,
    'softpro_legacy': softpro_legacy.SoftProService
}


def get_service_protocol(type: str, url: str) -> ServiceProtocol:
    service = _services.get(type)
    assert service is not None, "Service type '{}' not found".format(type)

    return service(url)

import socket

from django.conf import settings
from django.core.checks import Error, Warning, Info, register

# from wagtail_api_forms.formpages.validators import av_scan


@register("clamav_availability")
def check_clamav_availability(app_configs, **kwargs):
    messages = []

    if settings.FORMBUILDER_USE_ANTIVIR_SERVICE:
        host = settings.CLAMD_HOST
        port = settings.CLAMD_PORT
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1)
            s.connect((host, port))
            s.close()
        except OSError as e:
            messages.append(
                Warning(f"ClamAV is not reachable at {host}:{port}: {e}")
            )
        except Exception as e:
            messages.append(Error(f"Something went wrong: {e}.", id="formpages.E001"))
        else:
            messages.append(
                Info(
                    "Antivirus service is enabled and functional.", id="formpages.I001"
                )
            )
    else:
        messages.append(Info("Antivirus service is disabled.", id="formpages.I001"))

    return messages

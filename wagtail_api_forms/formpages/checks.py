from django.conf import settings
from django.core.checks import Error, Info, register

from wagtail_api_forms.formpages.validators import av_scan


@register("clamav_availability")
def check_clamav_availability(app_configs, **kwargs):
    messages = []

    if settings.FORMBUILDER_USE_ANTIVIR_SERVICE:
        try:
            file_to_scan = (
                # b"X5O!P%@AP[4\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"
                b"just a clean test file"
            )
            _av_scan_result = av_scan(file_to_scan)
            messages.append(
                Info(
                    "Antivirus service is enabled and functional.", id="formpages.I001"
                )
            )
        except Exception as e:
            messages.append(Error(f"Something went wrong: {e}.", id="formpages.E001"))
    else:
        messages.append(Info("Antivirus service is disabled.", id="formpages.I001"))

    return messages

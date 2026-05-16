from django.templatetags.static import static
from wagtail.models import Locale

from .models import BrandingSettings, FooterLinks


def get_show_admin_link(allowed_ips, request):
    """Cheap UX signal: return True if request comes from an exact-match IP.

    The previous implementation used `str.startswith`, which let
    '10.0.0.100' match an allowlist entry of '10.0.0.1'. This is just a
    UI hint (whether to render an admin link), not a security boundary,
    but the partial-prefix matching was a real classification bug.
    """
    remote_ip = request.META.get('REMOTE_ADDR')
    if not allowed_ips or not remote_ip:
        return False

    allowed = {ip.strip() for ip in allowed_ips.split(",") if ip.strip()}
    return remote_ip in allowed


def branding(request):
    branding_settings = BrandingSettings.load(request_or_site=request)

    # https://docs.wagtail.io/en/stable/reference/pages/model_reference.html?highlight=locale#id3
    current_locale = Locale.get_active()

    # Brand name defaults to english:
    localized_brand_name_attr = "brand_name_en"
    if current_locale.language_code == "de":
        localized_brand_name_attr = "brand_name_de"

    # Brand logo defaults to ACME:
    localized_brand_name = getattr(branding_settings, localized_brand_name_attr)
    brand_logo_fallback_url = static('img/logo_acme.svg')
    brand_logo_en_url = branding_settings.brand_logo_en
    brand_logo_de_url = branding_settings.brand_logo_de
    brand_figurative_mark = branding_settings.brand_figurative_mark
    favicon_url = branding_settings.favicon

    # Return css variables ready for usage in template.
    # Get:
    # FORMBUILDER_DEFAULT_CSS_VARIABLES = {
    #     "primary_accent_color": value,
    #     "primary_accent_color_darken": value,
    #     "primary_accent_gray": value,
    # }
    # Return:
    # :root {
    #   --primary_accent_color: value;
    #   --primary_accent_color_darken: value;
    #   --primary_accent_color: value;
    # }

    css_variables = []
    for variable, value in branding_settings.branding_css_variables.items():
        css_variables.append(f"--{variable}: {value};")

    css_variables.insert(0, ":root {")
    css_variables.append("}")
    css_variables = ("\n").join(css_variables)

    # Get localized versions of snippet FooterLink - I wonder why I have to
    # manually fetch the active language versions...:
    localized_footer_links = None

    # .first() returns None when no FooterLinks snippet exists for this
    # locale, so the chained .footer_links would trip AttributeError —
    # treat that as "no footer for this locale".
    try:
        localized_footer_links = (
            FooterLinks
            .objects
            .filter(locale_id=current_locale.id)
            .first()
            .footer_links
            .all()
        )
    except AttributeError:
        localized_footer_links = None

    show_admin_link = get_show_admin_link(branding_settings.show_admin_link_for_ips, request)

    return {
        "localized_brand_name": localized_brand_name,
        "brand_logo_en_url": brand_logo_en_url.url if brand_logo_en_url else brand_logo_fallback_url,
        "brand_logo_de_url": brand_logo_de_url.url if brand_logo_de_url else brand_logo_fallback_url,
        "localized_footer_links": localized_footer_links,
        "brand_figurative_mark": brand_figurative_mark if brand_figurative_mark else '',
        "favicon_url": favicon_url if favicon_url else '',
        "css_variables": css_variables,
        "show_admin_link": show_admin_link,
    }

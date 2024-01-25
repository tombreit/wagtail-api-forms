from django.templatetags.static import static
from wagtail.models import Locale

from .models import BrandingSettings, FooterLinks


def branding(request):
    branding_settings = BrandingSettings.load(request_or_site=request)

    # https://docs.wagtail.io/en/stable/reference/pages/model_reference.html?highlight=locale#id3
    current_locale = Locale.get_active()

    # Brand name defaults to english:
    localized_brand_name_attr = "brand_name_en"
    if current_locale.language_code == "de":
        localized_brand_name_attr = f"brand_name_de"

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

    try:
        localized_footer_links = (
            FooterLinks
            .objects
            .filter(locale_id=current_locale.id)
            .first()
            .footer_links
            .all()
        )
    except:
        pass

    return {
        "localized_brand_name": localized_brand_name,
        "brand_logo_en_url": brand_logo_en_url.url if brand_logo_en_url else brand_logo_fallback_url,
        "brand_logo_de_url": brand_logo_de_url.url if brand_logo_de_url else brand_logo_fallback_url,
        "localized_footer_links": localized_footer_links,
        "brand_figurative_mark": brand_figurative_mark if brand_figurative_mark else '',
        "favicon_url": favicon_url if favicon_url else '',
        "css_variables": css_variables,
    }

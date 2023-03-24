from django.contrib.staticfiles.storage import ManifestStaticFilesStorage


class ManifestStaticFilesStorageNotStrict(ManifestStaticFilesStorage):
    """
    A relaxed implementation of django's ManifestStaticFilesStorage.
    https://docs.djangoproject.com/en/4.0/ref/contrib/staticfiles/#django.contrib.staticfiles.storage.ManifestStaticFilesStorage.manifest_strict
    """
    manifest_strict = False

    patterns = (
        (
            "*.css",
            (
                r"""(?P<matched>url\(['"]{0,1}\s*(?P<url>.*?)["']{0,1}\))""",
                (
                    r"""(?P<matched>@import\s*["']\s*(?P<url>.*?)["'])""",
                    """@import url("%(url)s")""",
                ),
                (
                    (
                        r"(?m)(?P<matched>)^(/\*#[ \t]"
                        r"(?-i:sourceMappingURL)=(?P<url>.*)[ \t]*\*/)$"
                    ),
                    "/*# sourceMappingURL=%(url)s */",
                ),
            ),
        ),
        # (
        #     "*.js",
        #     (
        #         (
        #             r"(?m)(?P<matched>)^(//# (?-i:sourceMappingURL)=(?P<url>.*))$",
        #             "//# sourceMappingURL=%(url)s",
        #         ),
        #     ),
        # ),
    )
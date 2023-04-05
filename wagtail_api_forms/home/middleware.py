from django.conf import settings
from whitenoise.middleware import WhiteNoiseMiddleware


class MoreWhiteNoiseMiddleware(WhiteNoiseMiddleware):
    """
    From https://github.com/mblayman/homeschool/blob/5f11ca3208b0d422223ca8da2ddf6a3289a71860/homeschool/middleware.py#L8
    """
    def __init__(self, get_response=None, settings=settings):
        super().__init__(get_response, settings=settings)
        for more_noise in settings.MORE_WHITENOISE:
            self.add_files(more_noise["directory"], prefix=more_noise["prefix"])

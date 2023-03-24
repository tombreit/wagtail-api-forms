from django.db import models


class FileArtChoices(models.TextChoices):
    IMAGE_FILE = 'IMG_FILE'
    DOCUMENT_FILE = 'DOC_FILE'

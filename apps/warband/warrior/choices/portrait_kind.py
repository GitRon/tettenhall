from django.db import models


class PortraitKindChoices(models.TextChoices):
    """
    Which layer of a portrait a piece is. Its own module rather than nested in "PortraitPiece", because
    "Warrior" narrows each of its three portrait keys by it and cannot import the model it points at.
    """

    KIND_FACE = "face", "Face"
    KIND_HAIR = "hair", "Hair"
    KIND_BEARD = "beard", "Beard"

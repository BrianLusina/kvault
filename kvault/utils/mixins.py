from ..logger import logger


class MetaUtils:
    """
    Class with helper properties and utilities
    """

    @property
    def name(self):
        """Returns the class name"""
        return self.__class__.__name__

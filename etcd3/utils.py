import base64
import enum
import six

bytes_types = (bytes, bytearray)


def encode(data):
    """
    Encode the given data using base-64
    :param data:
    :return: base-64 encoded string
    """
    if isinstance(data, enum.Enum):
        data = enum.value
    if not isinstance(data, bytes_types):
        data = six.b(str(data))
    return base64.b64encode(data).decode("utf-8")


def decode(data):
    """
    Decode the base-64 encoded string
    :param data:
    :return: decoded string
    """
    if not isinstance(data, bytes_types):
        data = six.b(str(data))
    return base64.b64decode(data.decode("utf-8"))

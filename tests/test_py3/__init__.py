import pytest
import six

pytestmark = pytest.mark.skipif(six.PY2, reason='tests for python3.5+ only')

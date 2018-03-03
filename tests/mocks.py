import json

import six
from mock import Mock


def fake_post(status_code, content, resp_class):
    mock_response = Mock(spec=resp_class)
    mock_response.status_code = status_code
    mock_response.content = content

    def iter_content(chunk_size):
        p = 0
        while p < len(content):
            yield content[p: p + chunk_size]
            p += chunk_size

    mock_response.iter_content = iter_content
    mock_response.json = lambda: json.loads(six.text_type(content, encoding='utf-8'))

    return Mock(return_value=mock_response)

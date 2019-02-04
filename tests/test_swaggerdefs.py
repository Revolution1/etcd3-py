from etcd3.swaggerdefs import get_spec


def test_swagger_spec():
    assert get_spec()
    assert get_spec('3.0.1')
    assert get_spec('3.1.1')
    assert get_spec('3.2.1')
    assert get_spec('3.3.1')
    assert get_spec('3.4.1')

from os import path
from unittest.mock import call, patch

from configuration import Configuration, load, load_name, loadf, loads, NotConfigured


test_files = path.join(path.dirname(__file__), 'files')

yaml_str = """
    key: value
    some:
        other.key:
            - 1
            - 2
            - 3

    some.thing: false
"""

json_str = """{
    "key": "value",
    "some.other.key": [1, 2, 3],
    "some.thing": false
}"""


def _assert_values(conf):
    assert conf.key == 'value'
    assert isinstance(conf.some, Configuration)
    assert conf.some.thing is False
    assert conf.does_not.exist is NotConfigured


def _assert_has_calls_in_oder(mock, calls):
    # utility as mock.assert_has_calls() requires calls to be sequential within mock_calls,
    # we want to check for ordering among calls only
    idx = -1
    for expected in calls:
        # lookup index for all expected calls
        expected = mock.mock_calls.index(expected)
        # assert index is greater than previous (and thus greater than -1 / not found)
        assert expected > idx
        idx = expected


def test_load_default():
    with open(path.join(test_files, 'config.yaml')) as file:
        _assert_values(load(file))
    # as json is a subset of yaml, this should work just fine
    with open(path.join(test_files, 'config.json')) as file:
        _assert_values(load(file))


def test_load_yaml():
    with open(path.join(test_files, 'config.yaml')) as file:
        _assert_values(load(file))


def test_load_json():
    with open(path.join(test_files, 'config.json')) as file:
        _assert_values(load(file))


def test_load_multiple():
    with open(path.join(test_files, 'config.json')) as file1, open(path.join(test_files, 'config.yaml')) as file2:
        _assert_values(load(file1, file2))


def test_loads_default():
    _assert_values(loads(yaml_str))
    _assert_values(loads(json_str))


def test_loads_yaml():
    _assert_values(loads(yaml_str))


def test_loads_json():
    _assert_values(loads(json_str))


def test_loads_multiple():
    _assert_values(loads(json_str,
                         yaml_str))


def test_loadf_default():
    _assert_values(loadf(path.join(test_files, 'config.yaml')))
    _assert_values(loadf(path.join(test_files, 'config.json')))


def test_loadf_yaml():
    _assert_values(loadf(path.join(test_files, 'config.yaml')))


def test_loadf_json():
    _assert_values(loadf(path.join(test_files, 'config.json')))


def test_loadf_multiple():
    _assert_values(loadf(path.join(test_files, 'config.json'),
                         path.join(test_files, 'config.yaml')))


def test_load_name_single():
    test_path = path.join(test_files, '{name}.{extension}')

    _assert_values(load_name('config', load_order=(test_path,)))
    _assert_values(load_name('config', load_order=(test_path,), extension='json'))


def test_load_name_multiple():
    test_path = path.join(test_files, '{name}.{extension}')

    # bar has precedence over foo
    subject = load_name('foo', 'fake', 'bar', load_order=(test_path,))

    assert len(subject.semi.overlapping) == 2
    assert subject.semi.overlapping.foo is True
    assert subject.semi.overlapping.bar is False
    assert subject.overlapping.fully == 'bar'

    # foo has precedence over bar
    subject = load_name('fake', 'bar', 'foo', load_order=(test_path,))

    assert len(subject.semi.overlapping) == 2
    assert subject.semi.overlapping.foo is True
    assert subject.semi.overlapping.bar is False
    assert subject.overlapping.fully == 'foo'


def test_load_name_order():
    with patch('configuration.path') as mocked:
        mocked.expanduser.return_value = mocked
        # avoid actually opening files that might unexpectedly exist
        mocked.exists.return_value = False

        assert len(load_name('foo', 'bar')) == 0

    _assert_has_calls_in_oder(mocked.expanduser, [
        call('/etc/foo.yaml'),
        call('/etc/bar.yaml'),
        call('~/.foo.yaml'),
        call('~/.bar.yaml'),
        call('./foo.yaml'),
        call('./bar.yaml'),
    ])

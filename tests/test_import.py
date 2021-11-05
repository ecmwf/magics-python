from importlib import util


def test_import():
    assert util.find_spec("Magics").name == "Magics"

from chemspyd.utils import to_zone_string


def test_to_zone_string():
    assert to_zone_string("ISYNTH:1") == "ISYNTH:1"
    assert to_zone_string(["ISYNTH:1"]) == "ISYNTH:1"

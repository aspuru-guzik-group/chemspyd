from chemspyd.routines import get_waste_dst


def test_get_waste_dst():
    assert get_waste_dst("VALVEB:1") == "WASTE1:1"
    assert get_waste_dst("VALVEB:2") == "WASTE1:2"
    assert get_waste_dst("VALVEB:3") == "WASTE1:3"
    assert get_waste_dst("VALVEB:4") == "WASTE2:4"

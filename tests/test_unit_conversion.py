from chemspyd.utils import unit_conversions as units


def test_temp_k_to_c():
    assert units.temp_k_to_c(0) == -273.15
    assert units.temp_k_to_c(298.15) == 25
    assert units.temp_k_to_c(373.15) == 100


def test_pressure_pa_to_mbar():
    assert units.pressure_pa_to_mbar(1) == 0.01
    assert units.pressure_pa_to_mbar(100) == 1
    assert units.pressure_pa_to_mbar(1000000) == 10000


def test_no_change():
    assert units.no_change(-1) == -1
    assert units.no_change(0) == 0
    assert units.no_change(1) == 1

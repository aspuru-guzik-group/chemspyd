def prime_pumps(pump, vol):
    """
    primes chemspeed pumps

    Parameters
    ----------
    pump: pump being primed
    vol: volume

    Returns
    -------
    None

    """


def get_return_dst(dst: str) -> str:
    """
    Converts 'VALVEB' source to correct waste for system liquid dispensing.
    """
    valve2waste = {
        'VALVEB:1': 'WASTE1:1',
        'VALVEB:2': 'WASTE1:2',
        'VALVEB:3': 'WASTE1:3',
        'VALVEB:4': 'WASTE2:4'
    }
    return valve2waste[dst]


def inject_to_hplc():
    """Inject into HPLC"""

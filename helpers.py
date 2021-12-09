"""
High level functions for regular chemspeed use
"""
from pathlib import Path
import ChemspeedController


target = r'\\IPC5\Users\Operator\Desktop\Commands'
mgr = ChemspeedController(target, simulation=False)

dropbox: Path = Path.home() / 'Dropbox (Aspuru-Guzik Lab)'
solvents_path: Path = dropbox / 'chemos_chemspeed_liquid_dispensing' / 'v5' / 'solvents.json'


def prime_pumps(pump: int, vol: float) -> None:
    """
    primes Chemspeed pumps

    Args:
        pump: pump being primed
        vol: volume

    Returns: None

    """
    bottles = ['THF', 'THF', 'Hexanes', 'Water']
    empty = True
    while empty:
        bot = input(f'Is the {bottles[pump - 1]} bottle sufficiently full? (y/n)')
        if bot == 'y':
            empty = False

    src = f'VALVEB:{pump}'
    if pump == 4:
        dst = "WASTE2:4"
    else:
        dst = f"WASTE1:{pump}"

    mgr.transfer_liquid(
        source=src,
        destination=dst,
        volume=vol,
        src_flow=20,
        dst_flow=40,
        rinse_volume=0)
    print('Pumps primed.')
    mgr.unmount_all()


def emergency_unmount() -> None:
    """
    Unmounts any attachment on the Chemspeed arm

    Returns: None

    """
    mgr.unmount_all()


def check_balance() -> None:
    """
    asks the operator to confirm that the balance is level,
    then to confirm that the balance is calibrated

    Returns: None

    """
    level = False
    while not level:
        lev = input(f'Is the balance level? (y/n)')
        if lev == 'y':
            level = True
    calibrated = False
    while not calibrated:
        cal = input(f'Is the balance calibrated? (y/n)')
        if cal == 'y':
            calibrated = True


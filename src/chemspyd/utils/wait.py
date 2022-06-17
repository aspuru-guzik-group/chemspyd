import select
import sys
import time
from threading import Thread


class CountdownThread(Thread):
    def __init__(self, duration: int):
        super().__init__()
        # self.wait_time: int = duration
        self.duration: int = duration
        self.running: bool = True

    def terminate(self) -> None:
        self.running = False

    def run(self) -> None:
        """
        Overwrites Thread.run() method to do the countdown. Called by Thread.start().
        """
        while self.running and self.duration >= 0:
            print(f'Waiting for {self.duration:8.0f} seconds.', end='\r', flush=True)
            self.duration -= 1
            time.sleep(1)


class InputThread(Thread):
    def __init__(self, termination_thread: Thread) -> None:
        super().__init__()
        self.termination_thread: Thread = termination_thread

    def run(self) -> None:
        input('\nPress [Enter] to stop wait.\n')
        self.termination_thread.terminate()
        print('Wait cancelled.')


class Wait:
    """Class wrapper for function to wait for keyboard input or end of timer."""
    @staticmethod
    def _get_input(thread_to_terminate: CountdownThread) -> int:
        """
        Waits for any input from the user, then terminates the `thread_to_terminate` thread.
        Args:
            thread_to_terminate: Instance of CountdownThread that will be terminated.
        """
        input('\nPress [Enter] to stop wait.\n')
        thread_to_terminate.terminate()
        print('Wait cancelled.')

    def _wait_builtins(self, duration: int) -> None:
        """
        Wait using two `threading.Thread` threads.

        Args:
            duration: Time to wait in seconds.
        """
        countdown: CountdownThread = CountdownThread(duration)
        input_thread: Thread = Thread(target=self._get_input, args=(countdown,))

        inpt = input_thread.start()
        countdown.start()
        self._get_input(countdown)
        # TODO: How to retrieve 'waited' value from these threads?

    def wait(self, duration: int) -> int:
        """
        Waits for `duration` seconds, unless interrupted.

        Args:
            duration: Time to wait in seconds.

        Returns:
            Time waited in seconds, rounded to the nearest whole second.
        """
        print(f'Waiting for {duration} seconds.')
        start: float = time.time()
        works = self._wait_builtins(duration)
        stop: float = time.time()
        # TODO: Replace with getting 'waited' from self._wait_builtins if possible.
        waited: int = int(round((stop - start), 0))
        print(f'Waited for {waited} seconds.')
        return waited


def wait(timeout: int) -> int:
    print(f'Waiting for {timeout} seconds.')
    countdown: CountdownThread = CountdownThread(timeout)

    start: float = time.time()
    countdown.start()
    while countdown.running:
        input('\nPress [Enter] to stop wait.\n')
        countdown.terminate()
        print('Wait cancelled.')
    stop: float = time.time()
    waited: int = int(round((stop - start), 0))
    print(f'Waited for {waited} seconds.')
    return waited


def wait_join(timeout: int) -> int:
    print(f'Waiting for {timeout} seconds.')
    countdown: CountdownThread = CountdownThread(timeout)
    input_thread: InputThread = InputThread(countdown)

    start: float = time.time()

    countdown.start()
    input_thread.start()
    input_thread.join(timeout)

    stop: float = time.time()
    waited: int = int(round((stop - start), 0))
    print(f'Waited for {waited} seconds.')
    return waited


def main(timeout) -> int:
    print(f'Waiting for {timeout} seconds.')

    countdown: CountdownThread = CountdownThread(timeout)

    start: float = time.time()
    countdown.start()
    print('\nPress [Enter] to stop wait.\n')
    i, o, e = select.select([sys.stdin], [], [], timeout)
    if i:
        countdown.terminate()
        print('Wait cancelled.')
    else:
        print("Wait complete.")

    stop: float = time.time()
    waited: int = int(round((stop - start), 0))
    print(f'Waited for {waited} seconds.')
    return waited


if __name__ == '__main__':
    # waited = Wait().wait(10)
    # wait(10)
    wait_join(10)

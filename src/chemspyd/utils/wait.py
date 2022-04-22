import time
from threading import Thread


class CountdownThread(Thread):
    def __init__(self, duration: int):
        super().__init__()
        self.wait_time: int = duration
        self.duration: int = duration
        self._running: bool = True

    def terminate(self) -> int:
        self._running = False
        return self.wait_time - self.duration

    def run(self) -> None:
        """
        Overwrites Thread.run() method to do the countdown. Called by Thread.start().
        """
        while self._running and self.duration >= 0:
            print(f'Waiting for {self.duration:8.0f} seconds.', end='\r', flush=True)
            self.duration -= 1
            time.sleep(1)


class Wait:
    """Class wrapper for function to wait for keyboard input or end of timer."""
    @staticmethod
    def _get_input(thread_to_terminate: CountdownThread) -> int:
        """
        Waits for any input from the user, then terminates the `thread_to_terminate` thread.
        Args:
            thread_to_terminate: Instance of CountdownThread that will be terminated.
        """
        dummy: str = input('Press [Enter] to stop wait\n')
        waited: int = thread_to_terminate.terminate()
        print('Wait cancelled.')
        return waited

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


if __name__ == '__main__':
    waited = Wait().wait(30)

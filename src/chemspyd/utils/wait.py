import os
import time

from pynput import keyboard  # type: ignore[import]


class Wait:
    """Class wrapper for function to wait for keyboard input or end of timer."""
    def __init__(self):
        self.terminate: bool = False

    def _on_press(self, key) -> bool:  # type: ignore[return]
        if key == keyboard.Key.space:
            self.terminate = True
            # Stop Listener() context manager by returning False
            return False

    @staticmethod
    def _wait_windows_only(duration):
        """
        Windows-only wait method using only the 'msvcrt' module.
        Args:
            duration: Duration to wait unless interrupted.

        Raises:
            OSError if method is called when not on a Windows machine.
        """
        if os.name == 'nt':
            import msvcrt
        else:
            raise OSError('This method is not available on this operating system.')

        print('press "q" to cancel wait')
        while duration >= 0:
            print(f"", end=f'\rWaiting for {duration} seconds.')
            time.sleep(1)
            duration -= 1
            if msvcrt.kbhit() and msvcrt.getwch() == 'q':  # type: ignore[attr-defined]
                print("\nWait cancelled")
                duration = -1

    def _wait_context_manager(self, duration: int) -> None:
        """
        Waits for a set time, unless interrupted. Uses the pynput context manager.

        Args:
            duration: Duration to wait unless interrupted.

        Returns:
            None

        Raises:
            NotImplementedError
        """
        # with keyboard.Listener(on_press=self._on_press) as listener:
        #     listener.join(duration)
        raise NotImplementedError("Waiting for a fix for the Listener.join() timeout bug in pynput.")

    def _wait_no_block(self, duration: int) -> int:
        """
        Waits for a set time, unless interrupted.
        Instead of the pynput context manager, this method sets the 'terminate' variable.

        Args:
            duration: Duration to wait unless interrupted.

        Returns:
            How long the wait was. Either 'duration' (if completed), or the time after which it was interrupted.
        """
        listener = keyboard.Listener(on_press=self._on_press)
        listener.start()
        wait_time: int = duration
        while duration >= 0:
            if self.terminate:
                listener.stop()
                print('Wait cancelled.')
                return wait_time - duration
            time.sleep(1)
            duration -= 1
        print(f"Finished waiting for {wait_time} seconds.")
        return wait_time

    @staticmethod
    def _wait_events(duration):
        # The event listener will be running in this block
        print(f'Waiting for {duration} seconds.')
        with keyboard.Events() as events:
            event = events.get(duration)
            if event is None:
                print(f'You did not press a key within {duration} seconds.')
            else:
                print('Wait cancelled.')

    def wait(self, duration: int) -> int:
        """
        Waits for 'duration' seconds, unless interrupted.

        Args:
            duration: Time to wait in seconds.

        Returns:
            None
        """
        waited: int = self._wait_no_block(duration)
        return waited

import time
import logging
import curses
import signal
import sys
from abc import ABC, abstractmethod

logging.basicConfig(level = logging.WARN)
logger = logging.getLogger(__name__)

class LeetTimer:

    def __init__(self) -> None:
        self.start_time = time.time()
        self.pause_time = 0
        self.last_pause_start_time = None
        self._state = RunningState()
        self._state.timer = self
    
    def transition_to(self, state):
        logger.info(f"LeetTimer changing state to {type(state).__name__}")
        self._state = state
        self._state.timer = self
    
    def get_elapsed_time_seconds(self) -> int:
        current_pause = 0
        instant = time.time()
        if self.last_pause_start_time is not None:
            current_pause = instant - self.last_pause_start_time

        return round(instant - self.start_time - self.pause_time - current_pause)
    
    def get_elapsed_time_all_fmts(self):
        delta_time = self.get_elapsed_time_seconds()
        sec_elapsed = round(delta_time)
        min_elapsed = round(delta_time/60)
        hr_elapsed = round(delta_time/3600)

        return hr_elapsed, min_elapsed, sec_elapsed
    
    def toggle_pause_resume(self) -> None:
        if type(self._state).__name__ == "RunningState":
            self.pause()
        elif type(self._state).__name__ == "PausedState":
            self.resume()

    def pause(self) -> None:
        self._state.pause()

    def resume(self) -> None:
        self._state.resume()

    def stop(self) -> None:
        self._state.stop()

class TimerState(ABC):
    @property
    def timer(self) -> LeetTimer:
        return self._timer

    @timer.setter
    def timer(self, timer: LeetTimer) -> None:
        self._timer = timer

    @abstractmethod
    def pause(self) -> None:
        pass

    @abstractmethod
    def resume(self) -> None:
        pass

    @abstractmethod
    def stop(self) -> None:
        pass

class RunningState(TimerState):
    def pause(self) -> None:
        logger.info("Running -> Paused")
        self.timer.last_pause_start_time = time.time()
        self.timer.transition_to(PausedState())
    
    def resume(self) -> None:
        pass

    def stop(self) -> None:
        logger.info("Running -> Stopped")
        self.timer.transition_to(StoppedState())

class PausedState(TimerState):
    def pause(self) -> None:
        pass

    def resume(self) -> None:
        logger.info("Paused -> Running")
        if self.timer.last_pause_start_time is None:
            raise RuntimeError("Invalid state transition. Pause start time is None")
        current_pause = round(time.time() - self.timer.last_pause_start_time)
        self.timer.pause_time = self.timer.pause_time + current_pause
        logger.info(f"Current pause : {current_pause}")
        self.timer.last_pause_start_time = None
        self.timer.transition_to(RunningState())

    def stop(self) -> None:
        logger.info("Paused -> Stopped")
        if self.timer.last_pause_start_time is None:
            raise RuntimeError("Invalid state transition. Pause start time is None")
        current_pause = round(time.time() - self.timer.last_pause_start_time)
        self.timer.pause_time = self.timer.pause_time + current_pause
        logger.info(f"Current pause : {current_pause}")
        self.timer.last_pause_start_time = None
        self.timer.transition_to(TerminatedState())

class StoppedState(TimerState):
    def pause(self) -> None:
        pass

    def resume(self) -> None:
        pass

    def stop(self) -> None:
        pass



def screen_handler(stdscr):
    stdscr.nodelay(True)
    timers_list = []
    timer = LeetTimer()
    while True:
        stdscr.clear()
        hr_elapsed, min_elapsed, sec_elapsed = timer.get_elapsed_time_all_fmts()
        stdscr.addstr(0, 1, "############## Time spent ##############")
        stdscr.addstr(1, 1, f"{hr_elapsed:02} : {min_elapsed%60:02} : {sec_elapsed%60:02}")
        stdscr.addstr(2, 1, "########################################")
        stdscr.addstr(3, 1, f"{min_elapsed} minutes elapsed")
        stdscr.addstr(4, 1, f"Options:")
        stdscr.addstr(5, 1, f"Press [q] to quit")
        stdscr.addstr(6, 1, f"Press [N] to start new timer")
        stdscr.addstr(7, 1, f"Press [space] to toggle pause/resume")
        stdscr.addstr(8, 1, f"Input: ")

        stdscr.refresh()
        key_pressed = stdscr.getch()
        if key_pressed == ord('q'):
            timers_list.append(timer.get_elapsed_time_seconds())
            stdscr.nodelay(False)
            break
        elif key_pressed == ord('N'):
            timers_list.append(timer.get_elapsed_time_seconds())
            timer = LeetTimer()
            continue
        elif key_pressed == 32:
            timer.toggle_pause_resume()
        time.sleep(1)
    stdscr.clear()
    i = 0
    total_time_seconds = 0
    while i < len(timers_list):
        stdscr.addstr(i, 1, f"Timer: {i+1} time elapsed: {round(timers_list[i]/60)} minutes")
        total_time_seconds = total_time_seconds + timers_list[i]
        i = i+1
    stdscr.addstr(i, 1, f"Total time spent: {round(total_time_seconds/60)} minutes")
    stdscr.addstr(i+1, 1, f"Press any key to exit")
    stdscr.refresh()
    stdscr.getch()

def signal_handler(sig, frame):
    sys.exit(0)

def main():
    # Attach signal handler for SIGINT
    signal.signal(signal.SIGINT, signal_handler)
    # Start curses screen handler
    curses.wrapper(screen_handler)

if __name__ == '__main__':
    main()
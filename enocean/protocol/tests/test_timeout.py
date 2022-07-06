import threading
import time


class TestThread(threading.Thread):

    def __init__(self, sig_device_found):
        super().__init__()
        self.stopEvent = threading.Event()
        self.device_found = sig_device_found

    def run(self):
        while not self.stopEvent.is_set():
            print("Doing things")
            time.sleep(3)
            self.device_found.set()
            print("found device, aborting thread")
            return  # end the thread

    def get_stop_signal(self):
        return self.stopEvent


class TestTimeoutOfThread:

    def test_thread_timeout(self):
        device_found = threading.Event()
        new_thread = TestThread(device_found)
        stop_signal = new_thread.get_stop_signal()
        new_thread.start()
#        time.sleep(3)
        device_found.wait()
        run_into_timeout = device_found.wait(2)
        #        print("Waited....Now joining with timeout")
#        new_thread.join(timeout=2)


        if new_thread.is_alive():
            stop_signal.set()

        # one could wait for the event that some device has been found to be set, but


if __name__ == '__main__':
    t = TestTimeoutOfThread()
    t.test_thread_timeout()

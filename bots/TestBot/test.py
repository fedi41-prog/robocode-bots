# Source - https://stackoverflow.com/a/76167986
# Posted by jsbueno
# Retrieved 2026-03-08, License - CC BY-SA 4.0


import asyncio, queue

import concurrent.futures
import time

ServerSocketBindingError = Exception

class TestClass:

    def __init__(self):
        self.unfinished_queue = queue.Queue()
        self.finished_queue = queue.Queue()  # an asyncio.Queue here doesn't work properly (get() is not returning)


    async def asyncio_looping_run(self, duration: float):
        i = 0
        while True:
            i += 1
            print(f"taking a nap for {duration} seconds - {i} th time")
            await asyncio.sleep(duration)
            if i % 10 == 0:
                self.unfinished_queue.put(i)
                print("awaiting an entry to finish")

                # can't afford to be blocking here, because we are in this async def, and this would block all
                # other await'ing async defs !!!
                # SO : await'ing an asyncio.Queue should be used here, but this doesn't work !!!
            try:
                entry = self.finished_queue.get(block=False)
            except queue.Empty:
                continue
            else:
                print(f"{entry}")

    def long_lasting_synchronous_loop(self, msg: str):

        print(f"entered long_lasting_synchronous_loop('{msg}')")
        while True:
            print("waiting for something to do")
            input_item = self.unfinished_queue.get()
            print(f"found something to do ! - found {input_item} as input")
            print("mimicking a long synchronous operation by (synchronously) sleeping for 2 seconds")
            time.sleep(2)
            print("long synchronous operation finished ! will put it on the finished queue now")
            self.finished_queue.put_nowait(f"done {input_item} !")
            print(f"the result of {input_item} was put on the finished queue")


async def main():
    print("started for real now !")

    obj = TestClass()

    print("future 1 : outputs every 1/x second, yielding control to the asyncio loop")
    future1 = asyncio.create_task(obj.asyncio_looping_run(0.3))

    print("future 2 : runs the lengthy DB operation, NOT yielding control to the asyncio loop")
    pool = concurrent.futures.ThreadPoolExecutor()
    future2 = asyncio.get_event_loop().run_in_executor(
        pool, obj.long_lasting_synchronous_loop, 'future2')

    print(f"started at {time.strftime('%X')}")

    done, pending = await asyncio.wait([future2, future1],)
    print("async main() loop exited !")


if __name__ == "__main__":

    #constants.init_constants()

    try:
        asyncio.run(
            main()
        )

    except KeyboardInterrupt:
        print(f"Terminated on user request.")
    except asyncio.CancelledError:
        print(f"asyncio.CancelledError: main() terminated by user?")
    except Exception as _e:
        print(f"Terminated due to error: {_e}")
        print(f"main() terminated due to error: {_e}")
    finally:
        print(f"Handling cleanup.")

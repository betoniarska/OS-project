import os
import random
import multiprocessing
import time
from multiprocessing import shared_memory

children = 4
SHMKEY = "shared_memory_example"

def childProcess(pipe_write):
    
    rand = random.randint(0, 19)
    
    os.write(pipe_write, str(rand).encode())

    print("Child process:", os.getpid(), "Random integer:", rand, "generated")

    os._exit(0)

def scheduler(shm_key, ready_event, data_written_event):
    
    shm = shared_memory.SharedMemory(create=True, size=128, name=shm_key)

    print("Shared memory created")

    ready_event.set() 
    
    data_written_event.wait()  
    

    raw_data = bytes(shm.buf[:]).decode().strip('\x00')
    if raw_data:
        numbers = list(map(int, raw_data.split()))
        sorted_numbers = sorted(numbers)
        print("Scheduler: Sorted Numbers: ", sorted_numbers)

    shm.close()
    shm.unlink()

def init():

    ready_event = multiprocessing.Event()
    data_written_event = multiprocessing.Event()

    scheduler_process = multiprocessing.Process(target=scheduler, args=(SHMKEY, ready_event, data_written_event))
    scheduler_process.start()

    pipes = [os.pipe() for _ in range(children)]
    child_pids = []

    for i in range(children):
        pid = os.fork()
        
        if pid == 0:
            os.close(pipes[i][0])
            childProcess(pipes[i][1])
        else:
            child_pids.append(pid)
            print("Forked child process, process pid:", pid)
            
            os.close(pipes[i][1])

    numbers = []
    for i in range(children):
        read_pipe = pipes[i][0]
        number = os.read(read_pipe, 1024).decode()
        numbers.append(int(number))
        print("Init Process (PID:", os.getpid(),"): Received number", number, "from Child Process (PID: ", child_pids[i], ")")

    
    print("Init: Received Numbers: ",numbers )

    ready_event.wait()  

    shm = shared_memory.SharedMemory(name=SHMKEY)
    
    numbers_str = ' '.join(map(str, numbers))
    shm.buf[:len(numbers_str)] = numbers_str.encode()

    data_written_event.set()  

    scheduler_process.join()

    shm.close()

if __name__ == '__main__':
    init()
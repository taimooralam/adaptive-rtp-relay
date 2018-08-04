import time
from multiprocessing import Process, Lock

mutex = Lock()
some_data_global = "This is the data global"

def processData(data):
            with mutex:
                        print(some_data_global)


if __name__ == '__main__':
            jobs = []
            for i in range(5):
                        some_data = "This is the data"
                        p = Process(target = processData, args = (some_data_global,))
                        jobs.append(p)
                        p.start()
                        
            for job in jobs:
                        job.join()
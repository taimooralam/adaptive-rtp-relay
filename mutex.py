from multiprocessing import Process, Lock

mutex = Lock()

def processData(data):
            with mutex:
                        print(data)

if __name__ == '__main__':
            while True:
                        some_data = "This is the data"
                        p = Process(target = processData, args = (some_data,))
                        p.start()
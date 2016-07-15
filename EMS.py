import sys
import threading
import Queue
import time

banks_mail = []
elevators_mail = []
elevators = []
floors_mail = []


class Bank(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.mailbox = Queue.Queue()
        banks_mail.append(self.mailbox)

    def run(self):
        while True:
            data = self.mailbox.get()
            sys.stdout.write(str(self) + ' received: ' + str(data) + '\n')
            if data == 'shutdown':
                sys.stdout.write(str(self) + ' shutting down' + '\n')
                return
            elif data[1] == 'UP':
                for idx, elevator in enumerate(elevators):
                    if elevator.floor <= data[0] and (elevator.direction == 'UP' or elevator.direction == 'IDLE'):
                        sys.stdout.write('Elevator ' + str(idx) + ' available for floor ' + str(data[0]) + '\n')
                        elevators_mail[idx].put(data)
                        break
            elif data[1] == 'DOWN':
                for idx, elevator in enumerate(elevators):
                    if elevator.floor >= data[0] and (elevator.direction == 'DOWN' or elevator.direction == 'IDLE'):
                        sys.stdout.write('Elevator ' + str(idx) + ' available for floor ' + str(data[0]) + '\n')
                        elevators_mail[idx].put(data)
                        break
            else:
                sys.stdout.write('Invalid direction received')

    def stop(self):
        banks_mail.remove(self.mailbox)
        self.mailbox.put('shutdown')
        self.join()


class Elevator(threading.Thread):
    def __init__(self, floor=0, direction='IDLE'):
        threading.Thread.__init__(self)
        self.mailbox = Queue.Queue()
        elevators_mail.append(self.mailbox)
        elevators.append(self)
        self.floor = floor
        self.direction = direction
        self.target = self.floor

    def run(self):
        while True:
            data = self.mailbox.get()
            sys.stdout.write(str(self) + ' received: ' + str(data) + '\n')
            sys.stdout.write(str(data))
            if data == 'shutdown':
                sys.stdout.write(str(self) + ' shutting down' + '\n')
                return
            elif data[0] == self.floor:
                sys.stdout.write(str(self) + ' already at ' + str(data[0]) + '\n')
                break
            elif data[0] >= self.floor:
                self.direction = 'UP'
                for i in xrange(self.floor, data[0]):
                    sys.stdout.write(str(self.floor) + ' from/to ' + str(data[0]) + '\n')
                    self.floor += 1
                    sys.stdout.write(str(self) + ' at ' + str(self.floor) + ' going up\n')
                self.direction = 'IDLE'
            elif data[0] <= self.floor:
                self.direction = 'DOWN'
                for i in xrange(data[0], self.floor):
                    sys.stdout.write(str(self.floor) + ' from/to ' + str(data[0]) + '\n')
                    self.floor -= 1
                    sys.stdout.write(str(self) + ' at ' + str(self.floor) + ' going down' + '\n')
                self.direction = 'IDLE'

    def stop(self):
        elevators_mail.remove(self.mailbox)
        self.mailbox.put('shutdown')
        self.join()


class Floor(threading.Thread):
    def __init__(self, number=0):
        threading.Thread.__init__(self)
        self.mailbox = Queue.Queue()
        floors_mail.append(self.mailbox)
        self.number = number

    def run(self):
        while True:
            data = self.mailbox.get()
            if data == 'shutdown':
                sys.stdout.write(str(self) + ' shutting down' + '\n')
                return
            sys.stdout.write(str(self) + ' received: ' + str(data) + '\n')

    def stop(self):
        floors_mail.remove(self.mailbox)
        self.mailbox.put('shutdown')
        self.join()

    def call(self, data):
        banks_mail[0].put((self.number, data))


def broadcast_event(data):
    for q in elevators_mail:
        q.put(data)

b0 = Bank()
b0.start()

t1 = Elevator()
t2 = Elevator()
t3 = Elevator(8, 'DOWN')
t1.start()
t2.start()
t3.start()

f0 = Floor(0)
f1 = Floor(1)
f2 = Floor(2)
f3 = Floor(3)
f4 = Floor(4)
f5 = Floor(5)
f6 = Floor(6)
f7 = Floor(7)
f8 = Floor(8)

f0.start()
f1.start()
f2.start()
f3.start()
f4.start()
f5.start()
f6.start()
f7.start()
f8.start()

f1.call('UP')
f4.call('UP')
f6.call('DOWN')

time.sleep(0.5) # Make sure all other calls are finished before shutdown

sys.stdout.write('\nRecall all elevators back to Floor 0\n\n')

broadcast_event((0, 'IDLE'))

f0.stop()
f1.stop()
f2.stop()
f3.stop()
f4.stop()
f5.stop()
f6.stop()
f7.stop()
f8.stop()

t1.stop()
t2.stop()
t3.stop()

b0.stop()

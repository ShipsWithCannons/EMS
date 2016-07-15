import sys
import threading
import Queue
import time

banks_mail = []
elevators_mail = []
floors_mail = []


class Bank(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.mailbox = Queue.Queue()
        self.elevators = []
        banks_mail.append(self.mailbox)

    def run(self):
        while True:
            data = self.mailbox.get()
            sys.stdout.write(str(self) + ' received: ' + str(data) + '\n')
            if data == 'shutdown':
                sys.stdout.write(str(self) + ' shutting down' + '\n')
                return
            elif data[1] == 'UP':
                for idx, elevator in enumerate(self.elevators):
                    if elevator.floor <= data[0] and (elevator.direction == 'UP' or elevator.direction == 'IDLE'):
                        sys.stdout.write('Elevator ' + str(idx) + ' available for floor ' + str(data[0]) + '\n')
                        elevators_mail[idx].put(data)
                        break
            elif data[1] == 'DOWN':
                for idx, elevator in enumerate(self.elevators):
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

def main():
    banks = [Bank() for i in range(1)]
    for bank in banks:
        bank.start()

    banks[0].elevators = [Elevator(0) for i in range(5)]
    for elevator in banks[0].elevators:
        elevator.start()

    floors = [Floor(i) for i in range(9)]
    for floor in floors:
        floor.start()

    for floor, direction in ((1, 'UP'), (4, 'UP'), (6, 'DOWN'), (7, 'UP'), (8, 'DOWN')):
        floors[floor].call(direction)

    time.sleep(0.5)

    for floor, direction in ((5, 'UP'), (2, 'UP'), (4, 'DOWN')):
        floors[floor].call(direction)

    time.sleep(0.5)

    for floor, direction in ((2, 'DOWN'), (3, 'UP'), (7, 'DOWN')):
        floors[floor].call(direction)

    time.sleep(0.5)

    for floor, direction in ((6, 'UP'),):
        floors[floor].call(direction)

    time.sleep(0.5) # Make sure all other calls are finished before shutdown

    sys.stdout.write('\nRecall all elevators back to Floor 0\n\n')

    broadcast_event((0, 'IDLE'))

    for floor in floors:
        floor.stop()

    for elevator in banks[0].elevators:
        elevator.stop()

    for bank in banks:
        bank.stop()

if __name__ == "__main__":
    main()

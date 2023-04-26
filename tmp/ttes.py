import threading
import time
import sw



def test_thread1():
    sw.main()
    # for i in range(10):
    #     print("I'm in thread1")
    # time.sleep(60)
    # # print('finshed waiting')
    pass


def test_thread2():
    for i in range(10):
        print("I'm in thread2")
    pass


def main():
    print("hello world")
    t1 = threading.Thread(target=test_thread1)
    t1.name = 'abc'
    # t1.name('meow')
    print(t1.name)
    t2 = threading.Thread(target=test_thread2)
    t1.start()
    print("i m in between")
    t2.start()
    print(t1.is_alive())
    pass


if __name__ == '__main__':
    main()

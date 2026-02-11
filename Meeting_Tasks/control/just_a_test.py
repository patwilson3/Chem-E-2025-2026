import button_on
import threading

x=5

thread_1=threading.Thread(target=button_on.button_on_one(x), args=('One', 1))
thread_2=threading.Thread(target=button_on.button_on_two(x), args=('Two', 1))

thread_1.start()
thread_2.start()
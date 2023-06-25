import time as T
import tkinter as tk
from logs.Logging import log


class Timer:
    def __init__(self, master, time_format):
        self.master = master
        self.time = 0.0
        self.running = False
        self.hours, self.minutes, self.seconds = time_format.split(':')
        self.flag = True

        self.display = tk.Label(master, font=('Arial', 36), text=time_format)
        self.display.pack()

        self.set_time_button = tk.Button(master, text='Set Time', command=self.set_time)
        self.set_time_button.pack(side=tk.LEFT)

        if any([int(self.hours) != 0, int(self.minutes) != 0, int(self.seconds) != 0]):
            self.start_button = tk.Button(master, text='Start', command=lambda: self.set_time_callback(self.flag))
        else:
            self.start_button = tk.Button(master, text='Start', command=self.start)
        self.start_button.pack(side=tk.LEFT)

        self.stop_button = tk.Button(master, text='Stop', command=self.stop, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT)

        self.reset_button = tk.Button(master, text='Reset', command=self.reset, state=tk.DISABLED)
        self.reset_button.pack(side=tk.LEFT)

        self.exit_button = tk.Button(master, text='Exit', command=master.quit)
        self.exit_button.pack(side=tk.LEFT)

        self.set_time_window = tk.Toplevel(self.master)
        self.set_time_window.withdraw()
        self.set_time_window.title('Set Time')

        hours_label = tk.Label(self.set_time_window, text='Hours:')
        hours_label.grid(row=0, column=0)

        minutes_label = tk.Label(self.set_time_window, text='Minutes:')
        minutes_label.grid(row=1, column=0)

        seconds_label = tk.Label(self.set_time_window, text='Seconds:')
        seconds_label.grid(row=2, column=0)

        self.hours_entry = tk.Entry(self.set_time_window)
        self.hours_entry.insert(0, self.hours)
        self.hours_entry.grid(row=0, column=1)

        self.minutes_entry = tk.Entry(self.set_time_window)
        self.minutes_entry.insert(0, self.minutes)
        self.minutes_entry.grid(row=1, column=1)

        self.seconds_entry = tk.Entry(self.set_time_window)
        self.seconds_entry.insert(0, self.seconds)
        self.seconds_entry.grid(row=2, column=1)

        set_time_button = tk.Button(self.set_time_window, text='Set', command=lambda: self.set_time_callback(False))
        set_time_button.grid(row=3, column=1)

    def set_time(self):
        self.running = False
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.DISABLED)
        self.reset_button.config(state=tk.DISABLED)

        self.set_time_window = tk.Toplevel(self.master)
        self.set_time_window.title('Set Time')

        hours_label = tk.Label(self.set_time_window, text='Hours:')
        hours_label.grid(row=0, column=0)

        minutes_label = tk.Label(self.set_time_window, text='Minutes:')
        minutes_label.grid(row=1, column=0)

        seconds_label = tk.Label(self.set_time_window, text='Seconds:')
        seconds_label.grid(row=2, column=0)

        self.hours_entry = tk.Entry(self.set_time_window)
        self.hours_entry.insert(0, self.hours)
        self.hours_entry.grid(row=0, column=1)

        self.minutes_entry = tk.Entry(self.set_time_window)
        self.minutes_entry.insert(0, self.minutes)
        self.minutes_entry.grid(row=1, column=1)

        self.seconds_entry = tk.Entry(self.set_time_window)
        self.seconds_entry.insert(0, self.seconds)
        self.seconds_entry.grid(row=2, column=1)

        set_time_button = tk.Button(self.set_time_window, text='Set', command=lambda: self.set_time_callback(False))
        set_time_button.grid(row=3, column=1)

        self.flag = False
        self.start_button.config(command=self.start)

    def set_time_callback(self, flag):
        hours = int(self.hours_entry.get())
        minutes = int(self.minutes_entry.get())
        seconds = int(self.seconds_entry.get())
        self.time = hours * 3600 + minutes * 60 + seconds
        self.display.config(text=f'{hours:02.0f}:{minutes:02.0f}:{seconds:02.0f}')
        self.set_time_button.config(state=tk.DISABLED)
        self.start_button.config(state=tk.NORMAL)
        if flag:
            self.start()
        else:
            self.set_time_window.destroy()
            self.flag = True

    def start(self):
        self.running = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.reset_button.config(state=tk.DISABLED)
        self.update()

    def stop(self):
        self.running = False
        if self.hours_entry.winfo_exists():
            self.hours_entry.delete(0, tk.END)
            self.hours_entry.insert(0, str(self.hours))
        if self.minutes_entry.winfo_exists():
            self.minutes_entry.delete(0, tk.END)
            self.minutes_entry.insert(0, str(self.minutes))
        if self.minutes_entry.winfo_exists():
            self.seconds_entry.delete(0, tk.END)
            self.seconds_entry.insert(0, str(self.seconds))

        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.reset_button.config(state=tk.NORMAL)
        self.set_time_button.config(state=tk.NORMAL)

    def reset(self):
        self.running = False
        self.time = 0.0
        self.display.config(text='00:00:00.0')
        self.hours = 0
        self.minutes = 0
        self.seconds = 0
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.DISABLED)

    def update(self):
        if self.running and self.time > 0:
            # Subtract one second from the time remaining
            self.time -= 1

            # Convert the time remaining to hours, minutes, and seconds
            self.hours = int(self.time / 3600)
            self.minutes = int((self.time % 3600) / 60)
            self.seconds = int(self.time % 60)

            # Update the display label with the new time
            self.display.config(text=f'{self.hours:02.0f}:{self.minutes:02.0f}:{self.seconds:02.0f}')

            # Call the update method again in one second
            self.master.after(1000, self.update)

        elif self.time <= 0:
            from plyer import notification
            notification.notify(
                title='Timer',
                message='Timer is complete',
                timeout=4  # Display duration in seconds
            )
            T.sleep(2)
            # Notify Mobile
            try:
                from skills.phone import ping_device
                ping_device(message='Your timer is complete!')
            except:
                log.error('Error occurred while sending notification to device')
            self.master.quit()
        else:
            # Stop the timer if the time has run out
            self.stop()


def main(time_format):
    root = tk.Tk()
    root.title('Timer')
    timer = Timer(root, time_format)

    # def on_close():
    #     root.destroy()

    # root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()
    root.destroy()


if __name__ == '__main__':
    time_format = '00:00:00'
    main(time_format)

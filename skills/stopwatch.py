import tkinter as tk


class StopWatch:
    def __init__(self, master):
        self.master = master
        self.time = 0.0
        self.running = False

        self.display = tk.Label(master, font=('Arial', 36), text='00:00:00.0')
        self.display.pack()

        self.start_button = tk.Button(master, text='Start', command=self.start)
        self.start_button.pack(side=tk.LEFT)

        self.stop_button = tk.Button(master, text='Stop', command=self.stop, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT)

        self.reset_button = tk.Button(master, text='Reset', command=self.reset, state=tk.DISABLED)
        self.reset_button.pack(side=tk.LEFT)

        self.exit_button = tk.Button(master, text='Exit', command=master.quit)
        self.exit_button.pack(side=tk.LEFT)

    def start(self):
        self.running = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.reset_button.config(state=tk.DISABLED)
        self.update()

    def stop(self):
        self.running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.reset_button.config(state=tk.NORMAL)

    def reset(self):
        self.running = False
        self.time = 0.0
        self.display.config(text='00:00:00.0')
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.reset_button.config(state=tk.DISABLED)

    def update(self):
        if self.running:
            self.time += 0.1
            minutes, seconds = divmod(self.time, 60)
            hours, minutes = divmod(minutes, 60)
            self.display.config(text=f'{hours:02.0f}:{minutes:02.0f}:{seconds:04.1f}')
            self.master.after(100, self.update)


def main():
    root = tk.Tk()
    root.title('StopWatch')
    StopWatch(root)
    root.mainloop()


if __name__ == '__main__':
    main()

import tkinter as tk


class pop_up:
    '''
    Creates a pop up that asks user for current price and calculates the low and high bracket sell points to be used for semi-automated trading.
    '''

    def __init__(self, sym, low_percentage, high_percentage) -> None:
        '''
        Creates a popup that asks for the user's input on what the current buy price should be for sym,
        and automatically  display the low and high bracket sell points based on low_percentage and high_percentage.
        '''
        self.low_percentage = low_percentage
        self.high_percentage = high_percentage
        self.low = -1
        self.high = -1
        self.price = -1
        self.window = tk.Tk()
        self.label = tk.Label(self.window,
                              text=f"Enter the current buy price for {sym}:")
        self.label.pack()
        self.entry = tk.Entry(self.window)
        self.entry.bind('<Return>', self.get_input)
        self.entry.pack()
        self.label_low = tk.Label(
            self.window,
            text=f"Enter a value to show the low bracket sell point")
        self.label_low.pack()
        self.label_high = tk.Label(
            self.window,
            text=f"Enter a value to show the high bracket sell point")
        self.label_high.pack()
        # self.confirm_button = tk.Button(self.window,
        #                                 text="Confirm",
        #                                 command=self.confirm)
        # self.confirm_button.pack()
        # self.cancel_button = tk.Button(self.window,
        #                                text="Cancel",
        #                                command=self.window.destroy)
        # self.cancel_button.pack()
        self.window.after(100, lambda: self.entry.focus_force())
        self.window.after(300000, lambda: self.window.destroy())
        self.window.mainloop()

    def get_input(self, event=None):
        '''
        Gets the input from the user and calculates the low and high bracket sell points.
        '''
        if self.low != -1 and self.low != 0:
            self.confirm()
            return
        try:
            self.price = float(self.entry.get())
        except Exception as e:
            print(e)
            self.price = 0
        self.low = self.price * self.low_percentage
        self.high = self.price * self.high_percentage
        self.label_low['text'] = f"Low bracket sell point: {self.low}"
        self.label_high['text'] = f"High bracket sell point: {self.high}"

    def confirm(self, event=None):
        '''return the low, high bracket, and price sell points to the main program and close the window'''
        self.window.destroy()
        print(self.low, self.price, self.high)
        return self.low, self.price, self.high


if __name__ == '__main__':
    pop_up('AAPL', 0.95, 1.05)
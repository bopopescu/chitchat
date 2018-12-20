from Controllers import LoginViewController
from Views import LoginView
from tkinter import Tk, messagebox


class App(Tk):
    def __init__(self):
        super().__init__()
        self.title('Welcome to ChitChat')
        self.geometry('400x300')
        self.protocol('WM_DELETE_WINDOW', self.on_close)

    def run(self):
        controller = LoginViewController(self)
        view = LoginView(self, controller)
        controller.view = view
        self.mainloop()

    def on_close(self):
        # Open a pop-up window that asks if the user really wants to close the app
        if messagebox.askquestion('Quit', 'Do you really want to quit?') == 'yes':
            # Close the app
            self.destroy()
            exit(0)


if __name__ == '__main__':
    app = App()
    app.run()



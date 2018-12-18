from src.Models import User
from tkinter import *
from tkinter.font import Font


class LoginView(Frame):
    def __init__(self, app: Tk, controller):
        super().__init__(master=app)
        self.controller = controller
        self.font = Font(family='Segoe UI', size=10)
        self.grid_padding = 5

        self.action = StringVar(self)
        self.action.set('login')

        self.login_radio = Radiobutton(self, variable=self.action,
                                       value='login', text='Login', font=self.font)
        self.login_radio.grid(padx=self.grid_padding, pady=self.grid_padding)

        self.register_radio = Radiobutton(self, variable=self.action,
                                          value='register', text='Registrar', font=self.font)
        self.register_radio.deselect()
        self.register_radio.grid(row=0, column=1)

        self.username_label = Label(master=self, text='Username', font=self.font)
        self.username_label.grid(row=1, column=0, sticky=W, padx=self.grid_padding, pady=self.grid_padding)

        self.pass_label = Label(self, text='Password', font=self.font)
        self.pass_label.grid(row=2, column=0, sticky=W, padx=self.grid_padding, pady=self.grid_padding)

        self.username = StringVar()
        self.username.trace('w', self.controller.username_var_changed)
        self.username_entry = Entry(self, textvariable=self.username, font=self.font)
        self.username_entry.grid(row=1, column=1, padx=self.grid_padding, pady=self.grid_padding)

        self.password = StringVar()
        self.password.trace('w', self.controller.password_var_changed)
        self.pass_entry = Entry(self, textvariable=self.password, show='*', font=self.font)
        self.pass_entry['state'] = 'disabled'
        self.pass_entry.grid(row=2, column=1, padx=self.grid_padding, pady=self.grid_padding)

        self.submit_button = Button(self, text='Enviar',
                                    command=self.controller.submit, font=self.font)
        self.submit_button['state'] = 'disabled'
        self.submit_button.grid(sticky=E, columnspan=2, padx=self.grid_padding, pady=self.grid_padding)

        self.pack(padx=10, pady=10, expand=TRUE)


class MainView(Frame):
    def __init__(self, app: Tk, model: User = None, controller=None):
        super().__init__(master=app)
        self.controller = controller
        self.model = model
        self.font = Font(family='Segoe UI', size=10)
        self.active_chat = Listbox(master=self, font=self.font)
        self.active_chat.pack(fill=BOTH)
        self.pack(padx=4, pady=4, expand=TRUE)


if __name__ == '__main__':
    root = Tk()
    view = MainView(root, None, None)
    root.mainloop()

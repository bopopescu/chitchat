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
        self.pack(padx=2, pady=2, fill=BOTH, expand=TRUE)
        self.controller = controller
        self.model = model
        self.font = Font(family='Segoe UI', size=10)
        self.search_username = StringVar(master=self.master)
        self.search_username.set('username')
        self.search_username.trace('w', self.controller.search_username_changed)
        self.message = StringVar(master=self.master)
        self.message.trace('w', self.controller.message_changed)

        self.inner_frame = Frame(master=self)
        self.inner_frame.pack(padx=20, pady=20)
        self.search_frame = Frame(master=self.inner_frame)
        self.search_frame.pack(padx=5, pady=5, fill=BOTH, expand=1)
        self.search_frame_title = Label(master=self.search_frame,
                                        text='Search for someone to chitchat with',
                                        font=self.font)
        self.search_frame_title.grid(columnspan=2, sticky=NSEW)
        self.username_entry = Entry(master=self.search_frame, textvariable=self.search_username, font=self.font)
        self.username_entry.grid(row=1, column=0, padx=5, sticky=E)
        self.search_button = Button(master=self.search_frame, text='Procurar', font=self.font)
        self.search_button.grid(row=1, column=1, padx=5, sticky=W)

        columns, rows = self.search_frame.grid_size()
        for i in range(columns):
            self.search_frame.columnconfigure(i, weight=1)
        for j in range(rows):
            self.search_frame.rowconfigure(j, weight=1)

        self.chat_frame = Frame(master=self.inner_frame)
        self.chat_frame.pack(padx=5, pady=5, fill=BOTH, expand=1)
        self.chat_scrollbar = Scrollbar(master=self.chat_frame)
        self.active_chat = Listbox(master=self.chat_frame, yscrollcommand=self.chat_scrollbar.set,
                                   width=80, font=self.font, state='disabled')
        self.active_chat.pack(side=LEFT, fill=BOTH)
        self.chat_scrollbar.config(command=self.active_chat.yview)
        self.chat_scrollbar.pack(side=RIGHT, fill=Y)

        self.chat_form_frame = Frame(master=self.inner_frame)
        self.chat_form_frame.pack(padx=5, pady=5, fill=X, expand=1)
        self.message_entry = Entry(master=self.chat_form_frame, textvariable=self.message,
                                   font=self.font, state='disabled')
        self.message_entry.pack(side=LEFT, fill=BOTH, expand=TRUE)
        self.send_message_button = Button(master=self.chat_form_frame, text='send',
                                          font=self.font, state='disabled')
        self.send_message_button.pack(padx=5, side=RIGHT, fill=BOTH)


if __name__ == '__main__':
    root = Tk()
    view = MainView(root, None, None)
    root.mainloop()

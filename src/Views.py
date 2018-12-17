from src.Models import User


class GenericView:
    def __init__(self, controller, model):
        self.controller = controller
        self.model = model


class LoginView(GenericView):
    def __init__(self, controller=None, model=None):
        super().__init__(controller, model)

    @staticmethod
    def show_menu():
        options = [
            'Login',
            'Sign up'
        ]

        print(50*'-')
        for i in range(len(options)):
            print('{}. {}'.format(i+1, options[i]))
        print(50*'-')
        print('Choice: ', end='')

    def show_result(self):
        print(self.controller.result.center(80, '*'))

    def run(self):
        while self.controller.model.logged is False:
            while True:
                self.show_menu()
                self.controller.set_action(int(input()))
                if 1 <= self.controller.action <= 2:
                    break

            while self.controller.result != 'valid username':
                print('Username: ', end='')
                self.controller.set_username(input())

            while self.controller.result != 'valid password':
                print('Password: ', end='')
                self.controller.set_password(input())


class MainView:
    def __init__(self, model: User, controller=None):
        self.model = model
        self.controller = controller

    def run(self):
        print('kkk eae', self.model.username)

    def show_messages(self, messages):
        pass

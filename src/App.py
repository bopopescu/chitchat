from src.Controllers import LoginViewController
from src.Views import LoginView


class App:
    def __init__(self):
        pass

    def run(self):
        controller = LoginViewController()
        view = LoginView(controller)
        controller.view = view
        view.run()


if __name__ == '__main__':
    app = App()
    app.run()


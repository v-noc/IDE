# src/backend/tests/unit/core/parser/sample_project/main.py

from . import utils
from .models.user import User

class MainApp:
    def __init__(self):
        self.user = User(name="Test")

    def run(self):
        utils.helper_function()
        print("App is running")

def start_app():
    app = MainApp()
    app.run()

if __name__ == "__main__":
    start_app()

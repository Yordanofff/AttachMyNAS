from App import Tray

if __name__ == '__main__':
    app = Tray()
    app.run_app()
    # pyinstaller --clean -y --add-data="App.conf;." --add-data="logo.png;." --noconsole main.py
    # pyinstaller --clean -y --add-data="app.conf;." --add-data="logo.png;." --hidden-import main.py --noconsole main.py
    # pyinstaller --clean -y --add-data="app.conf;." --add-data="logo.png;." --hidden-import main.py --noconsole --name AttachMyNAS main.py
import functools
import os
import subprocess
import pystray
import PIL.Image

from SMB import SMB
from Windows import Windows
from Logger import MyLogger
from Config import Config, initial_script_conf_file_name


class Tray:
    def __init__(self):
        # pyinstaller --clean -y --add-data="App.conf;." --add-data="Anycubiclogo.jpg;." --add-data="initial_script.sh;." --noconsole TrayApp.py
        # pyinstaller --clean -y --add-data="App.conf;." --add-data="Anycubiclogo.jpg;." --add-data="initial_script.sh;." --hidden-import App.py --noconsole TrayApp.py

        self.APP_NAME = "AttachMyNAS"

        self.root_folder = os.path.dirname(os.path.abspath(__file__))

        self.RPI_CONFIG_FILENAME = initial_script_conf_file_name
        if "_internal" in self.root_folder:
            self.RPI_CONFIG_FILENAME = os.path.join("_internal", self.RPI_CONFIG_FILENAME)

        self.script_file_path = os.path.abspath(__file__)  # path to TrayApp.py
        self.logo_path = os.path.join(self.root_folder, "nas.png")
        self.logo = PIL.Image.open(self.logo_path)
        self.activate_script_path = os.path.join(self.root_folder, "venv", "Scripts", "activate.bat")

        self.config_file_name = os.path.join(self.root_folder, "App.conf")

        self.logger = MyLogger("Tray")
        self.log_init()

        self.my_config = Config(self.config_file_name)
        self.my_smb = SMB(self.config_file_name)
        self.my_win = Windows(self.config_file_name)

        self.is_config = self.my_config.are_settings_defined()
        self.icon = pystray.Icon(self.APP_NAME, self.logo, menu=self.menu, title=self.APP_NAME)

        # Use another variable to check when config file changes state from filled in to not filled in and vice versa
        self.current_state_of_config_file = self.is_config

    @property
    def menu(self):
        all_section_names = self.my_config.get_all_section_names()

        # TODO: menu won't show if no shares in conf file. Print warning when app starts if none.
        # Create the part of the menu that will have all sections
        sections_menu_items = []
        for section_name in all_section_names:
            num_shares_for_section = len(self.my_config.get_shares_for_section(section_name))

            # Add each share to the list
            inner_menu_for_each_section = [self.create_menu_item(section_name, i) for i in
                                           range(num_shares_for_section)]

            inner_menu_for_each_section.insert(0, pystray.MenuItem("Mount All",
                                                                   lambda Icon, item: Icon.notify(
                                                                       self.my_smb.mount_all_smb(section_name)),
                                                                   enabled=self.is_config))
            inner_menu_for_each_section.insert(1, pystray.Menu.SEPARATOR)

            inner_menu_for_each_section.append(pystray.Menu.SEPARATOR)
            current_section_ip = self.my_config.get_ip_for_section(section_name)
            inner_menu_for_each_section.append(pystray.MenuItem("Unmount All",
                                                                lambda Icon, item: Icon.notify(
                                                                    self.my_smb.unmount_all_smb_for_ip(
                                                                        current_section_ip)),
                                                                enabled=self.is_config))

            section_menu = pystray.Menu(*inner_menu_for_each_section)
            sections_menu_items.append(pystray.MenuItem(section_name, section_menu))

        return pystray.Menu(
            pystray.MenuItem("Unmount All [PC]", lambda Icon, item: Icon.notify(
                self.my_smb.unmount_every_connection_not_only_the_ones_in_conf()),
                             enabled=self.is_config),
            pystray.MenuItem("Unmount All [config]", lambda Icon, item: Icon.notify(self.my_smb.unmount_all_smb()),
                             enabled=self.is_config),
            pystray.Menu.SEPARATOR,
            *sections_menu_items,
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Other", pystray.Menu(
                pystray.MenuItem("Edit config file", self.edit_config_file_and_reload)
            )),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit", self.close_app)
        )

    # Helper function to create menu item
    def create_menu_item(self, section_name, i):
        return pystray.MenuItem(f"Mount {self.my_config.get_shares_for_section(section_name)[i]}",
                                functools.partial(self.notify_mount, section_name, i))

    # Helper function to notify about mount
    def notify_mount(self, section_name, i, Icon, item):
        Icon.notify(self.my_smb.mount_smb_section(section_name, i))


    # Working loop over one section
    # @property
    # def menu(self):
    #     section_name = self.config_checker.get_all_section_names()[0]
    #     shares = self.config_checker.get_shares_for_section(section_name)
    #
    #     # Define a helper function to create menu items
    #     def create_menu_item(i):
    #         return pystray.MenuItem(f"Mount {shares[i]}", functools.partial(self.notify_mount, section_name, i))
    #
    #     menu_items = [create_menu_item(i) for i in range(len(shares))]
    #
    #     return pystray.Menu(
    #         pystray.MenuItem("Unmount All SMB", lambda Icon, item: Icon.notify(self.my_smb.unmount_all_smb()),
    #                          enabled=self.is_config),
    #         pystray.Menu.SEPARATOR,
    #         pystray.MenuItem(section_name, pystray.Menu(*menu_items)),
    #         pystray.Menu.SEPARATOR,
    #         pystray.MenuItem("Other", pystray.Menu(
    #             pystray.MenuItem("Edit config file", self.edit_config_file_and_reload)
    #         )),
    #         pystray.Menu.SEPARATOR,
    #         pystray.MenuItem("Exit", self.close_app)
    #     )
    #
    #
    # def notify_mount(self, section_name, i, Icon, item):
    #     Icon.notify(self.my_smb.mount_smb_section(section_name, i))

    def log_init(self) -> None:
        self.logger.info("*" * 80)
        self.logger.info(f"App [{self.APP_NAME}] starting:")
        self.logger.info(f"root_folder: {self.root_folder}")
        self.logger.info(f"script_file_path: {self.script_file_path}")
        self.logger.info(f"config_file_name: {self.config_file_name}")
        self.logger.info(f"activate_script_path: {self.activate_script_path}")
        self.logger.info(f"logo file: {self.logo_path}")
        self.logger.info("*" * 80)

    def close_app(self) -> None:
        self.logger.info("Closing the app")
        self.icon.stop()

    # def unmount_all(self) -> None:
    #     self.logger.info("Unmounting all SMB locations..")
    #     # self.my_ssh.unmount()
    #     self.my_smb.unmount_smb_letter()

    def edit_config_file_and_reload(self) -> None:
        """
        Will enable or disable most buttons on the interface if config is not filled in.
        """
        app_needs_restart = False
        if self.my_win.edit_config_file():
            # if IP address updated - it needs to re-load the classes
            app_needs_restart = True

        self.is_config = self.my_config.are_settings_defined()
        if not self.is_config:
            # even if changes have been made, but not all data is entered - don't restart the app.
            app_needs_restart = False

        # Close the app and re-open it. Currently - the only way to redraw the app menu. # todo
        if (self.is_config != self.current_state_of_config_file) or app_needs_restart:
            # Only re-open if state has changed - It will restart the app even if just checking the config file.
            self.current_state_of_config_file = self.is_config
            self.close_app()
            if "_internal" in self.root_folder:
                # When compiled - no need to activate venv and will not run .py but exe file.
                app_folder = os.path.dirname(self.root_folder)  # 1 level up from the _internal folder
                executable_file_path = os.path.join(app_folder, "TrayApp.exe")  # todo - name
                self.logger.info(f"Starting {executable_file_path}")
                subprocess.Popen([executable_file_path])
            else:
                self.logger.info(f"Activating venv and starting the py script from {self.script_file_path}")
                subprocess.Popen(["cmd.exe", "/K", self.activate_script_path, "&&", "python", self.script_file_path])

    def run_app(self) -> None:
        self.icon.run()

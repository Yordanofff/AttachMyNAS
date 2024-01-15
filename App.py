import functools
import os
import subprocess
import sys

from pystray import Icon as icon, Menu as menu, MenuItem as item
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
        self.icon = icon(self.APP_NAME, self.logo, menu=self.menu, title=self.APP_NAME)

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
            print(section_name, num_shares_for_section)
            # Add each share to the list
            inner_menu_for_each_section = [self.create_menu_item(section_name, i) for i in
                                           range(num_shares_for_section)]

            # inner_menu_for_each_section.insert(
            #     0, item(f"Mount All - {section_name}",
            #             lambda icon, item: icon.notify(self.my_smb.mount_all_smb(section_name)),
            #             enabled=self.my_config.is_data_entered_for_section(section_name)))
            # inner_menu_for_each_section.insert(1, menu.SEPARATOR)

            inner_menu_for_each_section.insert(
                0, item(f"Mount All - {section_name}", functools.partial(self.get_mount_all_info, section_name),
                        enabled=self.my_config.is_data_entered_for_section(section_name)))

            inner_menu_for_each_section.insert(1, menu.SEPARATOR)
            # inner_menu_for_each_section.insert(0, item("Get info", lambda section_name, icon, item:
            #     icon.notify(self.get_data_for_section(section_name)), enabled=True))

            inner_menu_for_each_section.insert(
                0, item("Get info", functools.partial(self.get_info_action, section_name), enabled=True))

            inner_menu_for_each_section.insert(1, menu.SEPARATOR)

            inner_menu_for_each_section.append(menu.SEPARATOR)

            inner_menu_for_each_section.append(
                item(f"Unmount All - {section_name}", functools.partial(self.get_unmount_all_info, section_name),
                     enabled=self.my_config.is_ip_entered_for_section(section_name)))

            #
            # inner_menu_for_each_section.append(
            #     item(f"Unmount All - {section_name}",
            #          lambda icon, item: icon.notify(self.my_smb.unmount_all_smb_for_ip(current_section_ip)),
            #          enabled=self.my_config.is_ip_entered_for_section(section_name)))

            section_menu = menu(*inner_menu_for_each_section)
            sections_menu_items.append(item(section_name, section_menu))

        return menu(
            item("Unmount All [PC]", lambda icon, item: icon.notify(
                self.my_smb.unmount_every_connection_not_only_the_ones_in_conf()), enabled=True),
            item("Unmount All [config]",
                 lambda icon, item: icon.notify(self.my_smb.unmount_all_smb()), enabled=True),
            menu.SEPARATOR,
            *sections_menu_items,
            menu.SEPARATOR,
            item("Other", menu(
                item("Edit config file", self.edit_config_file_and_reload)
            )),
            menu.SEPARATOR,
            item("Restart", self.restart_app),
            item("Exit", self.close_app)
        )

    def get_unmount_all_info(self, section_name, icon, item):
        current_section_ip = self.my_config.get_ip_for_section(section_name)
        icon.notify(self.my_smb.unmount_all_smb_for_ip(current_section_ip))

    def get_mount_all_info(self, section_name, icon, item):
        icon.notify(self.my_smb.mount_all_smb(section_name))

    def get_info_action(self, section_name, icon, item):
        icon.notify(self.my_config.get_all_data_for_section_for_notification(section_name))

    # def get_info_action(self, section_name, icon, item):
    #     icon.notify(self.get_data_for_section(section_name))

    # def get_data_for_section(self, sectn_name):
    #     #     return self.my_config.get_all_data_for_section_for_notification(section_name)io

    # Helper function to create menu item
    def create_menu_item(self, section_name, i):
        share_name = self.my_config.get_shares_for_section(section_name)[i]
        return item(f"Mount {share_name}",
                    functools.partial(self.notify_mount, section_name, i),
                    enabled=self.my_config.is_data_entered_for_section(section_name))

    # Helper function to notify about mount
    def notify_mount(self, section_name, i, icon, item):
        icon.notify(self.my_smb.mount_smb_section(section_name, i))

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

    def edit_config_file_and_reload(self) -> None:
        """
        Will enable or disable most buttons on the interface depending on the changes made.
        Unmount all for each section will be enabled if there's an IP there.
        Mount options require ip, user, pw and at least 1 share.
        """
        if self.my_win.is_edit_config_file():
            self.restart_app()

    def restart_app(self):
        self.close_app()
        subprocess.Popen([sys.executable] + sys.argv, creationflags=subprocess.CREATE_NO_WINDOW)

    def run_app(self) -> None:
        self.icon.run()

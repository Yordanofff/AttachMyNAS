import os
import configparser
from Logger import MyLogger


class Config:
    def __init__(self, config_file_name):
        self.logger = MyLogger("Config")

        self.config_file = config_file_name
        if not os.path.isfile(self.config_file):
            msg = f"The file '{self.config_file}' does not exist."
            self.logger.critical(msg)

        # Read values from the configuration file and assign them to instance variables
        self.config = configparser.ConfigParser()
        self.config.read(self.config_file)

    def get_all_section_names(self) -> list[str]:
        return [i for i in self.config.sections()]

    def get_all_sections_ip(self) -> list[str]:
        all_ips = [self.get_ip_for_section(i) for i in self.get_all_section_names()]
        return [i for i in all_ips if i != '']

    def _get_is_data_entered_for_section_and_missing_fields(self, section_name: str) -> tuple[bool, list[str]]:
        all_data_entered = True
        error_msgs = []
        if not (self.get_ip_for_section(section_name)):
            all_data_entered = False
            error_msgs.append("ip")
        if not (self.get_username_for_section(section_name)):
            all_data_entered = False
            error_msgs.append("username")
        if not (self.get_password_for_section(section_name)):
            all_data_entered = False
            error_msgs.append("password")
        if len(self.get_shares_for_section(section_name)) == 0:
            all_data_entered = False
            error_msgs.append("shares")
        return all_data_entered, error_msgs

    def is_data_entered_for_section(self, section_name: str) -> bool:
        return self._get_is_data_entered_for_section_and_missing_fields(section_name)[0]

    def get_all_data_for_section(self, section: str) -> dict:
        ip = self.get_ip_for_section(section)
        name = self.get_username_for_section(section)
        shares = self.get_shares_for_section(section)
        preferred_letters = self.get_preferred_letters_for_section(section)
        shares_for_notifications = self.get_formatted_letter_share_for_notification(shares, preferred_letters)
        return {f'IP': f"{ip} - [{section}]", 'Username': name, 'Shares': shares_for_notifications}

    def get_all_data_for_section_for_notification(self, section: str) -> str:
        all_data = self.get_all_data_for_section(section)
        result = ''
        for k, v in all_data.items():
            if isinstance(v, list):
                # Convert the shares list to comma separated values
                v = self.convert_list_to_str(v)
            result += f"{k}: {v}\n"
        return result

    def get_username_for_section(self, section: str) -> str:
        return self.get_value_for_section('username', section)

    def get_password_for_section(self, section: str) -> str:
        return self.get_value_for_section('password', section)

    def get_shares_for_section(self, section: str) -> list[str]:
        shares_str = self.get_value_for_section('shares', section)
        return [i.strip() for i in shares_str.split(",")] if shares_str else []

    def get_preferred_letters_for_section(self, section: str) -> list[str]:
        """ If 'letters' row doesn't exist in the section - it will return [] """
        letters_str = self.get_value_for_section('letters', section)
        return [i.strip() for i in letters_str.split(',')] if letters_str else []

    def get_ip_for_section(self, section: str) -> str:
        return self.get_value_for_section('ip', section)

    def is_ip_entered_for_section(self, section: str) -> bool:
        if self.get_ip_for_section(section):
            return True
        return False

    def get_value_for_section(self, key_to_find: str, section: str) -> str:
        section_items: dict = (dict(self.config.items(section)))
        return section_items[key_to_find].split('#')[0].strip() if key_to_find in section_items else ''

    @staticmethod
    def convert_list_to_str(list_to_convert: list) -> str:
        return f"[{', '.join(list_to_convert)}]"

    @staticmethod
    def get_formatted_letter_share_for_notification(shares: list[str], letters: list[str]):
        result = []
        for i, share in enumerate(shares):
            letter = letters[i] if i < len(letters) else 'None'
            result.append(f"[{letter}]: {share}")
        return ', '.join(result)

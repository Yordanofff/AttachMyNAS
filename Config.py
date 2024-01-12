import os
import configparser
from Logger import MyLogger

rpi_section_name_in_config_file = "rw"
# initial_script_file_name = "initial_script.sh"
# initial_script_conf_file_name = f"{initial_script_file_name.split('.')[0]}.conf"
initial_script_conf_file_name = "app.conf"


class Config:
    def __init__(self, config_file_name):
        self.logger = MyLogger("Config")

        self.config_file = config_file_name
        if not os.path.isfile(self.config_file):
            msg = f"The file '{self.config_file}' does not exist."
            self.logger.critical(msg)
            self.create_config_file_for_rpi()
            # raise FileNotFoundError(msg)

        # Read values from the configuration file and assign them to instance variables
        config = configparser.ConfigParser()
        config.read(self.config_file)

        # self.scripts_folder_location = config.get(rpi_section_name_in_config_file, "SCRIPTS_FOLDER_LOCATION")

        self.root_folder = os.path.dirname(os.path.abspath(__file__))

        self.initial_script_conf_file_name = initial_script_conf_file_name
        # self.initial_script_sh_location = initial_script_file_name
        if "_internal" in self.root_folder:
            # self.initial_script_sh_location = os.path.join("_internal", self.initial_script_sh_location)
            self.initial_script_conf_file_name = os.path.join("_internal", self.initial_script_conf_file_name)

    def create_config_file_for_rpi(self, new_name: str = None) -> None:
        """
        Populates the SMB_USERNAME and SMB_PASSWORD if empty and saves the result in a new file.
        No spaces around the separator
        All values in double quotes.
        Keep comments
        """
        if new_name is None:
            new_name = initial_script_conf_file_name
        self.logger.info(f"Attempting to create a new configuration file for rpi: {new_name}")
        if os.path.isfile(new_name):
            self.logger.info(f"The file '{new_name}' already exists. Will be re-created.")

        conf = configparser.ConfigParser()
        conf.read(self.config_file)

        new_conf = configparser.ConfigParser()
        new_conf.optionxform = str  # Fix upper case
        new_conf.add_section(rpi_section_name_in_config_file)

        for (key, val) in conf[rpi_section_name_in_config_file].items():
            upper_key = key.upper()

            #  Use the SSH user and pass if SMB ones are not filled in.
            if upper_key == "SMB_USERNAME" and val == "":
                val = conf["SSH"].get("user")
            elif upper_key == "SMB_PASSWORD" and val == "":
                val = conf["SSH"].get("pass")

            # Modify the file, so that is readable by the .sh script.
            if len(val.split("#")) > 1:
                first_bit = val.split("#")[0].strip()
                if '\"' not in first_bit:
                    first_bit = f'\"{first_bit}\"'
                val = f'{first_bit}  # {val.split("#")[1].strip()}'
            else:
                if '\"' not in val:
                    val = f'\"{val}\"'

            # Need to set a section name in order to write the data.
            # Will delete that before uploading to the rPI
            new_conf.set(rpi_section_name_in_config_file, upper_key, val)

        # Save the new configuration to the new .conf file
        with open(new_name, 'w') as configfile:
            new_conf.write(configfile, space_around_delimiters=False)

        self.logger.info(f"New configuration file [{new_name}] - created.")
        self._delete_section_name_from_config_file_for_rpi()

    def _delete_section_name_from_config_file_for_rpi(self, txt_in_line_to_del: str = None):
        if txt_in_line_to_del is None:
            txt_in_line_to_del = rpi_section_name_in_config_file

        conf_file_path = self.initial_script_conf_file_name

        self.logger.info(f"Removing the section [{txt_in_line_to_del}] from file [{conf_file_path}]...")

        with open(conf_file_path, 'r') as file:
            lines = file.readlines()

        with open(conf_file_path, 'w') as file:
            for line in lines:
                if txt_in_line_to_del not in line:
                    file.write(line)
        self.logger.info("Row removed.")

    def are_settings_defined(self) -> bool:
        self.logger.info(f"Checking if the required data is entered in the [{self.config_file}] config file.")

        if os.path.isfile(self.config_file):
            conf = configparser.ConfigParser()
            conf.read(self.config_file)
            all_sections_in = True
            for section in ['DEFAULT', 'SSH']:
                if section not in conf:
                    self.logger.error(f"Section {section}, not in the conf file.")
                    all_sections_in = False

            if not all_sections_in:
                return False

            if not (conf['DEFAULT'].get('host_ip')):
                self.logger.error(f"Error: IP address of the host_ip - not in the config file.")
                return False

            all_fields_in = True
            for field in ['user', 'pass']:
                if not (conf['SSH'].get(field)):
                    self.logger.error(f"Error: No details for [SSH] - \"{field}\"")
                    all_fields_in = False

            if not all_fields_in:
                return False

        self.logger.info("All required data is in.")
        return True

    # def replace_source_line_with_path_in_the_initial_script(self):
    #     self.logger.info(f"Attempting to update the source location in {self.initial_script_sh_location}")
    #
    #     full_path = f"{self.scripts_folder_location}/{initial_script_conf_file_name}"
    #     """To be done before uploading to rPI"""
    #     with open(self.initial_script_sh_location, 'r') as file:
    #         lines = file.readlines()
    #
    #     found = False
    #     for index, line in enumerate(lines):
    #         if line.strip().startswith("source"):
    #             lines[index] = f"source {full_path}\n"
    #             found = True
    #             break
    #
    #     if found:
    #         with open(self.initial_script_sh_location, 'w') as file:
    #             file.writelines(lines)
    #         self.logger.info(f"Line starting with 'source' replaced with 'source {full_path}'.")
    #     else:
    #         self.logger.error(f"No line starting with 'source' found in the {self.initial_script_sh_location} file.")

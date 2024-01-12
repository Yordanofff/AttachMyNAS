import configparser
import subprocess

from Config import rpi_section_name_in_config_file
from Logger import MyLogger


class SMB:
    def __init__(self, config_file_name, letter: str = "p"):
        self.logger = MyLogger("SMB")
        self.config_file = config_file_name
        self.letter = letter  # Will be "P" by default - as it will be used on raspberry Pi

        config = configparser.ConfigParser()
        config.read(self.config_file)

        self.MAX_NUMBER_OF_CHARACTERS_IN_TRAY_NOTIFICATION = 256
        self.host = config.get('DEFAULT', 'host_ip')
        self.user = config.get(rpi_section_name_in_config_file, 'SMB_USERNAME')
        self.password = config.get(rpi_section_name_in_config_file, 'SMB_PASSWORD')
        self.share_name = config.get(rpi_section_name_in_config_file, 'SMB_SHARE_NAME')
        # if self.user == "":
            # self.user = config.get('SSH', 'user')
        # if self.password == "":
        #     self.password = config.get('SSH', 'pass')

        # self.log_init()

    # def log_init(self):
    #     self.logger.info("*" * 80)
    #     self.logger.info("INITIALIZING SMB:")
    #     self.logger.info(f"host: {self.host}")
    #     self.logger.info(f"user: {self.user}")
    #     self.logger.info(f"password: {self.password}")
    #     self.logger.info(f"share_name: {self.share_name}")
    #     self.logger.info("*" * 80)

    def mount_smb(self) -> str:
        """
        # This method will unmount a letter if is already mounted and will re-mount it by execute something like:
        # net use p: \\192.168.1.100\downloads /user: my_username my_password
        """
        self.logger.info(f"Attempting to mount the SMB volume to {self.letter.upper()}: drive")

        if self.is_drive_mounted():
            msg = f"Drive letter {self.letter.upper()} - already mounted."
            self.logger.info(msg)
            return msg

        mount_smb_cmd = f'net use {self.letter}: \\\\{self.host}\\{self.share_name} /user:{self.user} {self.password}'
        process = subprocess.Popen(mount_smb_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()

        stdout = stdout.decode('utf-8')
        stderr = stderr.decode('utf-8')

        if stderr:
            msg = f"Error while mounting letter {self.letter.upper()}: \n{stderr}"
            self.logger.error(msg)
        elif stdout:
            msg = f"Success: Drive letter {self.letter.upper()} - mounted: \n{stdout}"
            self.logger.info(msg)
        else:
            # Not sure if this will ever happen
            msg = f"stdout: {stdout} \n stderr: {stderr}"
            self.logger.error(msg)

        return msg[:self.MAX_NUMBER_OF_CHARACTERS_IN_TRAY_NOTIFICATION]

    def unmount_smb_letter(self) -> str:
        self.logger.info(f"Attempting to unmount drive {self.letter.upper()}:")

        if not self.is_drive_mounted():
            msg = f"Drive letter {self.letter.upper()} - not mounted."
            self.logger.warning(msg)
            return msg

        process = subprocess.Popen(f"net use {self.letter}: /del", shell=True, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()

        stdout = stdout.decode('utf-8')
        stderr = stderr.decode('utf-8')

        if stderr:
            msg = f"Error while unmounting letter {self.letter.upper()}: \n{stderr}"
            self.logger.error(msg)
        elif stdout:
            msg = f"Success: Drive letter {self.letter.upper()} - unmounted: \n{stdout}"
            self.logger.info(msg)
        else:
            # Not sure if this will ever happen
            msg = f"stdout: {stdout} \n stderr: {stderr}"
            self.logger.error(msg)
        return msg[:self.MAX_NUMBER_OF_CHARACTERS_IN_TRAY_NOTIFICATION]

    def is_drive_mounted(self) -> bool:
        """
        Run the 'net use' command and capture its output. Then checks if Letter is in it.
        """
        self.logger.info(f"Checking if drive letter {self.letter}: is already mounted.")
        try:
            process = subprocess.Popen(f"net use", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()

            stdout_decoded = stdout.decode('utf-8')
            stderr_decoded = stderr.decode('utf-8')

            if stderr_decoded:
                self.logger.error(stderr)

            result: bool = f"{self.letter.upper()}:" in stdout_decoded.upper()
            if result:
                self.logger.info(f"Drive letter {self.letter}: already mounted.")
            else:
                self.logger.info(f"Drive letter {self.letter}: not mounted.")
            return result
        except subprocess.CalledProcessError as e:
            # An error occurred, and an exception is automatically raised
            self.logger.critical(f"Something went wrong: {e}")
            raise e

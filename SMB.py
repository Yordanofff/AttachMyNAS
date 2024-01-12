import configparser
import string
import subprocess
import ctypes
import psutil

from Logger import MyLogger


class SMB:
    def __init__(self, config_file_name='App.conf'):
        self.logger = MyLogger("SMB")
        self.config_file = config_file_name
        # self.letter = letter  # Will be "P" by default - as it will be used on raspberry Pi

        config = configparser.ConfigParser()
        config.read(self.config_file)

        self.MAX_NUMBER_OF_CHARACTERS_IN_TRAY_NOTIFICATION = 256
        self.host = config.get('DEFAULT', 'host_ip')
        # self.user = config.get(rpi_section_name_in_config_file, 'SMB_USERNAME')
        # self.password = config.get(rpi_section_name_in_config_file, 'SMB_PASSWORD')
        # self.share_name = config.get(rpi_section_name_in_config_file, 'SMB_SHARE_NAME')
        # if self.user == "":
            # self.user = config.get('SSH', 'user')
        # if self.password == "":
        #     self.password = config.get('SSH', 'pass')

        self.log_init()

    def log_init(self):
        self.logger.info("*" * 80)
        self.logger.info("INITIALIZING SMB:")
        self.logger.info(f"host: {self.host}")
        # self.logger.info(f"user: {self.user}")
        # self.logger.info(f"password: {self.password}")
        # self.logger.info(f"share_name: {self.share_name}")
        self.logger.info("*" * 80)

    def mount_smb(self, letter: str, share_name: str, username: str, password: str) -> str:
        """
        # This method will unmount a letter if is already mounted and will re-mount it by execute something like:
        # net use p: \\192.168.1.100\downloads /user: my_username my_password
        """
        self.logger.info(f"Attempting to mount the SMB volume to {letter.upper()}: drive")

        if self.is_drive_mounted(letter):
            msg = f"Drive letter {letter.upper()} - already mounted."
            self.logger.info(msg)
            return msg

        mount_smb_cmd = f'net use {letter}: \\\\{self.host}\\{share_name} /user:{username} {password}'
        process = subprocess.Popen(mount_smb_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()

        stdout = stdout.decode('utf-8')
        stderr = stderr.decode('utf-8')

        if stderr:
            msg = f"Error while mounting letter {letter.upper()}: \n{stderr}"
            self.logger.error(msg)
        elif stdout:
            msg = f"Success: Drive letter {letter.upper()} - mounted: \n{stdout}"
            self.logger.info(msg)
        else:
            # Not sure if this will ever happen
            msg = f"stdout: {stdout} \n stderr: {stderr}"
            self.logger.error(msg)

        return msg[:self.MAX_NUMBER_OF_CHARACTERS_IN_TRAY_NOTIFICATION]

    def unmount_smb_letter(self, letter: str) -> str:
        self.logger.info(f"Attempting to unmount drive {letter.upper()}:")

        if not self.is_drive_mounted(letter):
            msg = f"Drive letter {letter.upper()} - not mounted."
            self.logger.warning(msg)
            return msg

        process = subprocess.Popen(f"net use {letter}: /del", shell=True, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()

        stdout = stdout.decode('utf-8')
        stderr = stderr.decode('utf-8')

        if stderr:
            msg = f"Error while unmounting letter {letter.upper()}: \n{stderr}"
            self.logger.error(msg)
        elif stdout:
            msg = f"Success: Drive letter {letter.upper()} - unmounted: \n{stdout}"
            self.logger.info(msg)
        else:
            # Not sure if this will ever happen
            msg = f"stdout: {stdout} \n stderr: {stderr}"
            self.logger.error(msg)
        return msg[:self.MAX_NUMBER_OF_CHARACTERS_IN_TRAY_NOTIFICATION]

    def is_drive_mounted(self, letter: str) -> bool:
        """
        Run the 'net use' command and capture its output. Then checks if Letter is in it.
        """
        self.logger.info(f"Checking if drive letter {letter}: is already mounted.")
        try:
            process = subprocess.Popen(f"net use", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()

            stdout_decoded = stdout.decode('utf-8')
            stderr_decoded = stderr.decode('utf-8')

            if stderr_decoded:
                self.logger.error(stderr)

            result: bool = f"{letter.upper()}:" in stdout_decoded.upper()
            if result:
                self.logger.info(f"Drive letter {letter}: already mounted.")
            else:
                self.logger.info(f"Drive letter {letter}: not mounted.")
            return result
        except subprocess.CalledProcessError as e:
            # An error occurred, and an exception is automatically raised
            self.logger.critical(f"Something went wrong: {e}")
            raise e

    @staticmethod
    def _get_used_drive_letters():
        drive_bitmask = ctypes.windll.kernel32.GetLogicalDrives()
        drive_letters = [chr(i + ord('A')) for i in range(26) if drive_bitmask & (1 << i)]
        return drive_letters

    def get_free_drive_letters(self):
        used_letters = self._get_used_drive_letters()
        all_letters = list(string.ascii_uppercase)
        diff = set(used_letters).symmetric_difference(set(all_letters))
        diff.remove('A')
        diff.remove('B')
        return list(sorted(diff))

    def get_last_free_letter(self):
        return self.get_free_drive_letters()[-1]

    def unmount_all_smb(self):
        all_mounted_letters_on_server = self.get_all_mounted_letters_for_ip()
        for letter in all_mounted_letters_on_server:
            self.unmount_smb_letter(letter)

    def get_all_mounted_letters_for_ip(self) -> list[str]:
        mount_smb_cmd = f'net use'
        process = subprocess.Popen(mount_smb_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, _ = process.communicate()

        rows = stdout.decode('utf-8').split('\r\n')
        ignored_start_strings = ['New connections', 'Status', '-------', 'The command']
        mounted_letters = []
        for row in rows:
            if row and (not any(row.startswith(prefix) for prefix in ignored_start_strings)):

                # At this point all extra rows have been removed. Should work without removing these too.
                # OK           Z:        \\192.168.1.6\downloads   Microsoft Windows Network
                # OK                     \\192.168.1.6\IPC$        Microsoft Windows Network
                # There might be rows without mounted letter

                letter = row.split(':')[0].split()[1].strip()
                if len(letter) == 1:
                    ip = row.split('\\\\')[1].split('\\')[0]
                    if ip == self.host:
                        mounted_letters.append(letter)

        return mounted_letters

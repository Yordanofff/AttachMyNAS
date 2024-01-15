import configparser
import string
import subprocess
import ctypes
from Config import Config
from Logger import MyLogger


class SMB:
    def __init__(self, config_file_name='App.conf'):
        self.logger = MyLogger("SMB")
        self.config_file = config_file_name
        self.my_conf = Config()
        config = configparser.ConfigParser()
        config.read(self.config_file)

        self.MAX_NUMBER_OF_CHARACTERS_IN_TRAY_NOTIFICATION = 256

    # TODO: Check if share is already mounted

    def mount_smb(self, host_ip: str, username: str, password: str, share_name: str, letter: str = None) -> str:
        """
        # This method will unmount a letter if is already mounted and will re-mount it by execute something like:
        # net use p: \\192.168.1.100\downloads /user: my_username my_password
        """
        if letter is None:
            letter = self.get_last_free_letter()

        self.logger.info(
            f"Attempting to mount {host_ip}\{share_name} using user: {username} to {letter.upper()}: drive")
        if self.is_drive_mounted(letter):
            msg = f"Drive letter {letter.upper()} - already mounted."
            self.logger.info(msg)
            return msg

        mount_smb_cmd = f'net use {letter}: \\\\{host_ip}\\{share_name} /user:{username} {password}'
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

    def mount_smb_section(self, section_name: str, share_name_position: int):
        ip = self.my_conf.get_ip_for_section(section_name)
        username = self.my_conf.get_username_for_section(section_name)
        password = self.my_conf.get_password_for_section(section_name)
        share_name = self.my_conf.get_shares_for_section(section_name)[share_name_position]
        is_mounted = self.is_already_mounted(ip, share_name)
        if is_mounted[0]:
            return f"\\{ip}\\{share_name} - already mounted at {is_mounted[1]}"
        return self.mount_smb(ip, username, password, share_name)
        # TODO - letter

    def is_already_mounted(self, ip, share) -> tuple[bool, str]:
        all_mounts = self.get_all_mounted_letters_for_ip_dict()
        for mount in all_mounts:
            if mount['ip'] == ip and mount['share'] == share:
                return True, mount['letter']
        return False, ''

    def mount_all_smb(self, section_name: str):
        all_shares_names_count = len(self.my_conf.get_shares_for_section(section_name))
        failed_mounts = []
        for i in range(all_shares_names_count):
            result = self.mount_smb_section(section_name, i)
            if not result.startswith('Success'):
                failed_mounts.append(self.my_conf.get_shares_for_section(section_name)[i])
        if len(failed_mounts) == 0:
            return f'All [{all_shares_names_count}] drives mounted successfully.'
        else:
            return f'Not all [{all_shares_names_count}] drives mounted successfully. Failed mounts: {", ".join(failed_mounts)}'

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

    def get_free_drive_letters(self):
        used_letters = self._get_used_drive_letters()
        all_letters = list(string.ascii_uppercase)
        diff = set(used_letters).symmetric_difference(set(all_letters))
        diff.remove('A')
        diff.remove('B')
        return list(sorted(diff))

    def get_last_free_letter(self):
        return self.get_free_drive_letters()[-1]

    def unmount_all_smb_for_ip(self, host_ip: str) -> str:
        all_mounted_letters_on_server = self.get_all_mounted_letters_for_ip(host_ip)
        failed_to_unmount = []
        for letter in all_mounted_letters_on_server:
            result = self.unmount_smb_letter(letter)
            if not result.startswith('Success'):
                failed_to_unmount.append(letter)
        if failed_to_unmount:
            return f"Some drives failed to unmount: {', '.join(failed_to_unmount)}"
        else:
            return f"Success. All {len(all_mounted_letters_on_server)} drives unmounted successfully."

    def unmount_all_smb(self):
        all_ip = self.get_all_ip_from_all_sections()
        failed_to_unmount = []
        for ip in all_ip:
            result = self.unmount_all_smb_for_ip(ip)
            if not result.startswith('Success'):
                failed_to_unmount.append(ip)
        if failed_to_unmount:
            return f"Some drives failed to unmount for IP: {', '.join(failed_to_unmount)}"
        else:
            return f"Success. All connections unmounted successfully."

    def unmount_every_connection_not_only_the_ones_in_conf(self):
        self.logger.info(f"Attempting to unmount all connections")
        cmd = "net use * /delete /yes"
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()

        stdout = stdout.decode('utf-8')
        stderr = stderr.decode('utf-8')

        if stderr:
            msg = f"Error - could not unmount all connections: \n{stderr}"
            self.logger.error(msg)
        elif stdout:
            msg = f"Success: All network drives and connections - unmounted: \n{stdout}"
            self.logger.info(msg)
        else:
            # Not sure if this will ever happen
            msg = f"stdout: {stdout} \n stderr: {stderr}"
            self.logger.error(msg)
        return msg[:self.MAX_NUMBER_OF_CHARACTERS_IN_TRAY_NOTIFICATION]

    def get_all_ip_from_all_sections(self) -> list[str]:
        return list(set(self.my_conf.get_all_section_names()))

    @staticmethod
    def _get_used_drive_letters():
        drive_bitmask = ctypes.windll.kernel32.GetLogicalDrives()
        drive_letters = [chr(i + ord('A')) for i in range(26) if drive_bitmask & (1 << i)]
        return drive_letters

    @staticmethod
    def get_all_mounted_letters_for_ip(host_ip: str) -> list[str]:
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
                    if ip == host_ip:
                        mounted_letters.append(letter)

        return mounted_letters

    @staticmethod
    def get_all_mounted_letters_for_ip_dict() -> list[dict]:
        mount_smb_cmd = f'net use'
        process = subprocess.Popen(mount_smb_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, _ = process.communicate()

        rows = stdout.decode('utf-8').split('\r\n')
        ignored_start_strings = ['New connections', 'Status', '-------', 'The command']
        data = []
        for row in rows:
            if row and (not any(row.startswith(prefix) for prefix in ignored_start_strings)):
                letter = ' '
                path = row.split('\\\\')[1].split()[0].strip()
                ip = path.split('\\')[0]
                share = path.split('\\')[1]
                if ":" in row:
                    letter = row.split(':')[0].split()[1].strip()
                data.append({'letter': letter, 'ip': ip, 'share': share})
        return data

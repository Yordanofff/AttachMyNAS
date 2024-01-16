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

    def mount_smb(self, host_ip: str, username: str, password: str, share_name: str, letter: str) -> str:
        """
        # This method will unmount a letter if is already mounted and will re-mount it by execute something like:
        # net use p: \\192.168.1.100\downloads /user: my_username my_password
        """

        self.logger.info(
            f"Attempting to mount {host_ip}\{share_name} using user: {username} to {letter.upper()}: drive")

        is_mounted = self.is_already_mounted(host_ip, share_name)
        if is_mounted[0]:
            return f"\\{host_ip}\\{share_name} - already mounted at {is_mounted[1]}"

        if not self.is_drive_letter_free(letter):
            # It's possible that the preferred letter is already mounted
            # Will not mount at another letter - because it might be important to be the correct one.
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

    def mount_smb_section(self, section_name: str, share_name_position: int) -> str:
        ip = self.my_conf.get_ip_for_section(section_name)
        username = self.my_conf.get_username_for_section(section_name)
        password = self.my_conf.get_password_for_section(section_name)
        share_name = self.my_conf.get_shares_for_section(section_name)[share_name_position]
        letter = self.get_chosen_letter_for_section(section_name, share_name_position)

        return self.mount_smb(ip, username, password, share_name, letter)

    def is_drive_letter_free(self, letter: str) -> bool:
        if letter in self.get_free_drive_letters():
            return True
        return False

    def get_chosen_letter_for_section(self, section_name: str, position: int) -> str:
        """
        :return: The preferred letter if that letter is available OR a free letter if not
        """
        preferred_letter = self.get_preferred_letter_for_section_if_one(section_name, position)
        if preferred_letter:
            return preferred_letter
        return self.get_last_free_letter()

    def get_preferred_letter_for_section_if_one(self, section_name: str, position: int) -> str | None:
        """
        Use this is the tray drawer - to indicate that there is a preferred letter for that mount.
        :param section_name: section name from the config file
        :param position: The position of the item that is needed: J,K,L - position 0 = J
        :return: the letter or None if there isn't.
        """

        letters_for_section = self.my_conf.get_preferred_letters_for_section(section_name)
        try:
            letter = letters_for_section[position]
            if letter:
                return letter
        except:
            pass
        return None

    def is_already_mounted(self, ip, share) -> tuple[bool, str]:
        """
        Checks if that exact share is already mounted.
        """
        all_mounts = self.get_all_mounted_letters_for_ip_dict()
        for mount in all_mounts:
            if mount['ip'] == ip and mount['share'] == share:
                return True, mount['letter']
        return False, ''

    def mount_all_smb(self, section_name: str) -> str:
        """
        Mounts all shares from the selected section
        :return: Notification msg
        """
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

        if self.is_drive_letter_free(letter):
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

    def get_free_drive_letters(self) -> list[str]:
        used_letters = self._get_used_drive_letters()
        all_letters = list(string.ascii_uppercase)
        diff = set(used_letters).symmetric_difference(set(all_letters))
        diff.remove('A')
        diff.remove('B')
        return list(sorted(diff))

    def get_last_free_letter(self) -> str:
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

    def unmount_all_smb(self) -> str:
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

    def unmount_every_connection_not_only_the_ones_in_conf(self) -> str:
        """
        Removes all SMB network connections on that machine. Nothing to do with this app. ALL.
        :return: Notification msg
        """
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
        return list(set(self.my_conf.get_all_sections_ip()))

    @staticmethod
    def _get_used_drive_letters() -> list[str]:
        """
        :return: list of all used drive letters - local + network drives
        """
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
        ignored_start_strings = ['New connections', 'Status', '-------', 'The command', 'There are no']
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

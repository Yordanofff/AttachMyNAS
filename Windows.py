import subprocess

from Logger import MyLogger


class Windows:
    def __init__(self, config_file_name):
        self.logger = MyLogger("WINDOWS")
        self.config_file = config_file_name

    def edit_config_file(self, log_differences: bool = True) -> bool:
        # Read the file contents before editing
        with open(self.config_file, 'r') as file:
            original_content = file.read()

        self.logger.info(f"Editing the config file: {self.config_file}")
        notepad_process = subprocess.Popen(["notepad.exe", self.config_file])
        notepad_process.wait()

        # Read the file contents after Notepad is closed
        with open(self.config_file, 'r') as file:
            modified_content = file.read()

        if log_differences:
            self.log_differences_between_edits(original_content, modified_content)

        return self.is_difference_between_edits(original_content, modified_content)

    def log_differences_between_edits(self, original_content, modified_content) -> None:
        original_lines = original_content.split('\n')
        modified_lines = modified_content.split('\n')

        if len(original_lines) != len(modified_lines):
            self.logger.warning(f"Rows have been added, or removed from the config file.")
        else:
            for row in range(len(original_lines)):
                if original_lines[row] != modified_lines[row]:
                    self.logger.info(f"Difference in line {row + 1}:")
                    self.logger.info(f"Original: '{original_lines[row]}'")
                    self.logger.info(f"Modified: '{modified_lines[row]}'")
                    self.logger.info("----------------------")

    @staticmethod
    def is_difference_between_edits(original_content, modified_content) -> bool:
        return original_content != modified_content

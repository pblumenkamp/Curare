class InvalidGroupsFileError(Exception):
    """Exception raised for errors in the groups file.

        Attributes:
            path -- path to groups file
            for_pe -- groups file for paired-end data
    """

    def __init__(self, for_pe):
        if for_pe:
            super(InvalidGroupsFileError, self).__init__("Groups file should contain 3 columns in each line")
        else:
            super(InvalidGroupsFileError, self).__init__("Groups file should contain 2 columns in each line")

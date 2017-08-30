from .context import dge

import unittest


class TestGroupsfileParser(unittest.TestCase):
    def test_parser(self):
        groups = dge.parse_groupsfile("tests/ressources/groups.txt")

        self.assertEqual(len(groups), 2)
        self.assertTupleEqual(groups[0],
                              ("input_data/ERR985535_R1.fastq", "input_data/ERR985535_R2.fastq", "extracellular"))
        self.assertTupleEqual(groups[1],
                              ("input_data/ERR985536_R1.fastq", "input_data/ERR985536_R2.fastq", "intracellular"))


if __name__ == '__main__':
    unittest.main()

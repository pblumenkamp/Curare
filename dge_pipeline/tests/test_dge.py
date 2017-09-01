import os
import unittest

from dge_pipeline import dge
from dge_pipeline import customErrors


GROUPS_FILE_SE = os.path.dirname(__file__) + "/ressources/groups_se.txt"
GROUPS_FILE_PE = os.path.dirname(__file__) + "/ressources/groups_pe.txt"
GROUPS_FILE_DEFECT = os.path.dirname(__file__) + "/ressources/groups_defect.txt"
REF_GENOME = os.path.dirname(__file__) + "/ressources/reference/listeria_monocytogenes_egd_e.fasta"
REF_ANNOTATION = os.path.dirname(__file__) + "/ressources/reference/listeria_monocytogenes_egd_e.gff3"


class TestGroupsfileParser(unittest.TestCase):
    def test_parser(self):
        groups = dge.parse_groups_file(GROUPS_FILE_PE)

        self.assertEqual(len(groups), 2)
        self.assertTupleEqual(groups[0],
                              (os.path.join(os.path.dirname(GROUPS_FILE_PE), "input_data/ERR985535_R1.fastq"),
                               os.path.join(os.path.dirname(GROUPS_FILE_PE), "input_data/ERR985535_R2.fastq"),
                               "extracellular"))
        self.assertTupleEqual(groups[1],
                              (os.path.join(os.path.dirname(GROUPS_FILE_PE), "input_data/ERR985536_R1.fastq"),
                               os.path.join(os.path.dirname(GROUPS_FILE_PE), "input_data/ERR985536_R2.fastq"),
                               "intracellular"))


class TestArgsFilesValidation(unittest.TestCase):
    def test_correct_case(self):
        dge.validate_argsfiles(GROUPS_FILE_PE, REF_GENOME, REF_ANNOTATION)
        self.assertTrue(True)

    def test_incorrect_groups_file(self):
        with self.assertRaises(FileNotFoundError):
            dge.validate_argsfiles("wrong_path", REF_GENOME, REF_ANNOTATION)

    def test_incorrect_genome_file(self):
        with self.assertRaises(FileNotFoundError):
            dge.validate_argsfiles(GROUPS_FILE_PE, "wrong_path", REF_ANNOTATION)

    def test_incorrect_annotation_file(self):
        with self.assertRaises(FileNotFoundError):
            dge.validate_argsfiles(GROUPS_FILE_PE, REF_GENOME, "wrong_path")


class TestInputFilesValidation(unittest.TestCase):
    def test_correct_cases(self):
        try:
            groups_se = dge.parse_groups_file(GROUPS_FILE_SE)
            dge.validate_inputfiles(groups_se, False)
        except customErrors.InvalidGroupsFileError as err:
            self.fail(f"InvalidGroupsFileError: {err}")
        except FileNotFoundError as err:
            self.fail(f"FileNotFoundError: {err}")
        except IOError as err:
            self.fail(f"IOError: {err}")
        try:
            groups_pe = dge.parse_groups_file(GROUPS_FILE_PE)
            dge.validate_inputfiles(groups_pe, True)
        except customErrors.InvalidGroupsFileError as err:
            self.fail(f"InvalidGroupsFileError: {err}")
        except FileNotFoundError as err:
            self.fail(f"FileNotFoundError: {err}")
        except IOError as err:
            self.fail(f"IOError: {err}")

    def test_incorrect_groups_files(self):
        groups_se = dge.parse_groups_file(GROUPS_FILE_SE)
        groups_pe = dge.parse_groups_file(GROUPS_FILE_PE)
        groups_defect = dge.parse_groups_file(GROUPS_FILE_DEFECT)
        with self.assertRaises(customErrors.InvalidGroupsFileError):
            dge.validate_inputfiles(groups_se, True)
        with self.assertRaises(customErrors.InvalidGroupsFileError):
            dge.validate_inputfiles(groups_pe, False)
        with self.assertRaises(customErrors.InvalidGroupsFileError):
            dge.validate_inputfiles(groups_defect, True)
        with self.assertRaises(customErrors.InvalidGroupsFileError):
            dge.validate_inputfiles(groups_defect, False)


if __name__ == '__main__':
    unittest.main()

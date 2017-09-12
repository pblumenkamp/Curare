import os
import unittest
import tempfile
import re

from dge_pipeline import dge
from dge_pipeline import customErrors


GROUPS_FILE_SE = os.path.dirname(__file__) + "/ressources/groups_se.txt"
GROUPS_FILE_PE = os.path.dirname(__file__) + "/ressources/groups_pe.txt"
GROUPS_FILE_DEFECT = os.path.dirname(__file__) + "/ressources/groups_defect.txt"
REF_GENOME = os.path.dirname(__file__) + "/ressources/reference/listeria_monocytogenes_egd_e.fasta"
REF_ANNOTATION = os.path.dirname(__file__) + "/ressources/reference/listeria_monocytogenes_egd_e.gff3"


class TestGroupsfileParser(unittest.TestCase):
    def test_parser(self):
        groups = dge.parse_groups_file(GROUPS_FILE_PE, True)

        self.assertEqual(len(groups), 2)
        self.assertTupleEqual(tuple(groups[0]),
                              ("ERR985535",
                               "extracellular",
                               os.path.join(os.path.dirname(GROUPS_FILE_PE), "input_data/ERR985535_R1.fastq"),
                               os.path.join(os.path.dirname(GROUPS_FILE_PE), "input_data/ERR985535_R2.fastq"),
                               ))
        self.assertTupleEqual(tuple(groups[1]),
                              ("ERR985536",
                               "intracellular",
                               os.path.join(os.path.dirname(GROUPS_FILE_PE), "input_data/ERR985536_R1.fastq"),
                               os.path.join(os.path.dirname(GROUPS_FILE_PE), "input_data/ERR985536_R2.fastq"),
                               ))


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
            groups_se = dge.parse_groups_file(GROUPS_FILE_SE, False)
            dge.validate_inputfiles(groups_se, False)
        except customErrors.InvalidGroupsFileError as err:
            self.fail(f"InvalidGroupsFileError: {err}")
        except FileNotFoundError as err:
            self.fail(f"FileNotFoundError: {err}")
        except IOError as err:
            self.fail(f"IOError: {err}")
        try:
            groups_pe = dge.parse_groups_file(GROUPS_FILE_PE, True)
            dge.validate_inputfiles(groups_pe, True)
        except customErrors.InvalidGroupsFileError as err:
            self.fail(f"InvalidGroupsFileError: {err}")
        except FileNotFoundError as err:
            self.fail(f"FileNotFoundError: {err}")
        except IOError as err:
            self.fail(f"IOError: {err}")

    def test_incorrect_groups_files(self):
        groups_se = dge.parse_groups_file(GROUPS_FILE_SE, False)
        groups_pe = dge.parse_groups_file(GROUPS_FILE_PE, True)
        with self.assertRaises(customErrors.InvalidGroupsFileError):
            dge.parse_groups_file(GROUPS_FILE_DEFECT, True)
        with self.assertRaises(customErrors.InvalidGroupsFileError):
            dge.validate_inputfiles(groups_se, True)
        with self.assertRaises(customErrors.InvalidGroupsFileError):
            dge.validate_inputfiles(groups_pe, False)


class TestSnakefile(unittest.TestCase):
    def test_create_snakefile(self):
        tmp = tempfile.TemporaryDirectory()
        dge.create_output_directory(tmp.name)
        groups = dge.parse_groups_file(GROUPS_FILE_PE, True)
        dge.create_snakefile(dge.SNAKEFILES["bowtie2"], tmp.name, REF_GENOME, REF_ANNOTATION, groups, True)
        self.assertTrue(os.path.exists(os.path.join(tmp.name, "snakefile")))
        with open(os.path.join(tmp.name, "snakefile"), 'r') as sf:
            self.assertIsNone(re.search("%%.*%%", sf.read()))
        tmp.cleanup()


if __name__ == '__main__':
    unittest.main()

import os
import sys
import copy
import pytest
import random
import shutil

import virtool.pathoscope
import virtool.orig_pathoscope


SAM_PATH = os.path.join(sys.path[0], "tests", "test_files", "test_al.sam")


@pytest.fixture
def test_sam_path(tmpdir):
    path = os.path.join(str(tmpdir.mkdir("test_sam_file")), "test_al.sam")
    shutil.copy(SAM_PATH, path)
    return path


def get_random_sam_lines(count=50):
    lines = list()

    with open(SAM_PATH, "r") as handle:
        for line in handle:
            if line[0] in ["@", "#"]:
                continue

            if random.randint(1, 5) == 1:
                lines.append(line)
                if len(lines) == count:
                    return lines


@pytest.mark.parametrize("line", get_random_sam_lines())
def test_find_sam_align_score(line):
    split = line.split()

    new_score = virtool.pathoscope.find_sam_align_score(split)
    old_score = virtool.orig_pathoscope.findSamAlignScore(split)

    assert new_score == old_score


@pytest.mark.parametrize("line", get_random_sam_lines())
def test_find_entry_score(line):
    split = line.split()

    new_result = virtool.pathoscope.find_entry_score(split, 0.01)
    old_result = virtool.orig_pathoscope.find_entry_score(line, split, 1, 0.01)

    assert new_result == old_result


def test_create_matrix(test_sam_path):
    old_result = virtool.orig_pathoscope.conv_align2GRmat(test_sam_path, 0.01, 1)
    new_result = virtool.pathoscope.build_matrix(test_sam_path, 0.01)

    assert old_result == new_result


@pytest.mark.parametrize("theta_prior", [0, 1e-5])
@pytest.mark.parametrize("pi_prior", [0, 1e-5])
@pytest.mark.parametrize("epsilon", [1e-6, 1e-7, 1e-8])
@pytest.mark.parametrize("max_iter", [5, 10, 20, 30])
def test_em(theta_prior, pi_prior, epsilon, max_iter, test_sam_path):
    matrix_tuple = virtool.pathoscope.build_matrix(test_sam_path, 0.01)

    u, nu, refs, reads = copy.deepcopy(matrix_tuple)
    new_result = virtool.pathoscope.em(u, nu, refs, max_iter, epsilon, pi_prior, theta_prior)

    u, nu, refs, reads = copy.deepcopy(matrix_tuple)
    old_result = virtool.orig_pathoscope.pathoscope_em(u, nu, refs, max_iter, epsilon, False, pi_prior, theta_prior)

    assert new_result == old_result


@pytest.mark.parametrize("cutoff", [0.01, 0.05, 0.1])
def test_compute_best_hit(cutoff, test_sam_path):
    matrix_tuple = virtool.pathoscope.build_matrix(test_sam_path, cutoff)

    u, nu, refs, reads = copy.deepcopy(matrix_tuple)
    new_result = virtool.pathoscope.compute_best_hit(u, nu, refs, reads)

    u, nu, refs, reads = copy.deepcopy(matrix_tuple)
    old_result = virtool.orig_pathoscope.computeBestHit(u, nu, refs, reads)

    assert new_result == old_result


def test_reassign(tmpdir, test_sam_path, capsys):

    class PathoOptions:

        def __init__(self):
            self.out_matrix_flag = False
            self.verbose = False
            self.score_cutoff = 0.01
            self.exp_tag = "vt"
            self.ali_format = "sam"
            self.ali_file = test_sam_path
            self.outdir = str(tmpdir)
            self.emEpsilon = 1e-7
            self.maxIter = 30
            self.noalign = False
            self.piPrior = 0
            self.thetaPrior = 0
            self.noCutOff = False

    old_result = virtool.orig_pathoscope.pathoscope_reassign(PathoOptions())

    realigned_path = os.path.join(str(tmpdir), "realigned.sam")
    report_path = os.path.join(str(tmpdir), "report.tsv")

    new_result = virtool.pathoscope.reassign(test_sam_path, report_path=report_path, realigned_path=realigned_path)

    assert old_result[1:11] == new_result[1:11]

    with open(os.path.join(str(tmpdir), "updated_test_al.sam"), "r") as old_sam_handle:
        with open(os.path.join(str(tmpdir), "realigned.sam"), "r") as new_sam_handle:
            assert old_sam_handle.read() == new_sam_handle.read()

    with open(os.path.join(str(tmpdir), "vt-sam-report.tsv"), "r") as old_report_handle:
        with open(os.path.join(str(tmpdir), "report.tsv"), "r") as new_report_handle:
            assert old_report_handle.read() == new_report_handle.read()

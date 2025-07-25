# test_annotate.py
# Contact: Jacob Schreiber <jmschreiber91@gmail.com>


import torch
torch.use_deterministic_algorithms(True, warn_only=True)
torch.manual_seed(0)

import numpy
import pytest

from numpy.testing import assert_raises
from numpy.testing import assert_array_almost_equal

from tangermeme.utils import one_hot_encode
from tangermeme.utils import random_one_hot

from tangermeme.seqlet import recursive_seqlets

from tangermeme.annotate import annotate_seqlets
from tangermeme.annotate import count_annotations
from tangermeme.annotate import pairwise_annotations


@pytest.fixture
def annotations():
	r = numpy.random.RandomState(1)
	
	y = torch.zeros(100, 2, dtype=torch.int64)
	y[:, 0] = torch.from_numpy(r.choice(25, size=100))
	y[:, 1] = torch.from_numpy(r.choice(7, size=100))
	return y


@pytest.fixture
def X():
	return torch.load("tests/data/X_gata.torch")


@pytest.fixture
def X_contrib(X):
	X_attr = torch.load("tests/data/X_gata_attr.torch")
	return (X * X_attr).sum(axis=1)


###


def test_annotate_seqlets(X, X_contrib):
	seqlets = recursive_seqlets(X_contrib)
	assert seqlets.shape == (45, 5)

	idxs, pvals = annotate_seqlets(X, seqlets, "tests/data/test.meme")

	assert idxs.shape == (45, 1)
	assert idxs.dtype == torch.int32

	assert pvals.shape == (45, 1)
	assert pvals.dtype == torch.float64

	assert_array_almost_equal(idxs[:, 0], [ 9,  4,  6,  3,  1,  8,  8,  6,  4,  1,
		1,  9,  4,  0,  0,  9,  5,  8,   9,  4,  6,  7,  9,  9,  7,  6,  8,  9,  
		7,  8,  6,  4,  4,  4,  7, 11,   2,  9,  6,  6,  9,  9,  7,  4,  9])

	assert_array_almost_equal(pvals[:, 0], [
		0.1190, 0.0205, 0.1175, 0.1948, 0.0351, 0.0911, 0.0319, 0.1152, 0.1830,
        0.0166, 0.1166, 0.0751, 0.0121, 0.0255, 0.1146, 0.1539, 0.0051, 0.0389,
        0.1410, 0.0190, 0.0227, 0.1354, 0.0210, 0.1313, 0.0493, 0.0124, 0.0389,
        0.0755, 0.0731, 0.0098, 0.0389, 0.0267, 0.0268, 0.0189, 0.1354, 0.0101,
        0.1512, 0.0138, 0.0013, 0.0178, 0.1414, 0.1023, 0.1351, 0.0623, 0.0017
	], 4)


def test_annotate_seqlets_n_nearest(X, X_contrib):
	seqlets = recursive_seqlets(X_contrib)
	assert seqlets.shape == (45, 5)

	idxs, pvals = annotate_seqlets(X, seqlets, "tests/data/test.meme",
		n_nearest=3)
	
	assert idxs.shape == (45, 3)
	assert idxs.dtype == torch.int32

	assert pvals.shape == (45, 3)
	assert pvals.dtype == torch.float64


	idxs, pvals = annotate_seqlets(X, seqlets, "tests/data/test.meme",
		n_nearest=12)
	
	assert idxs.shape == (45, 12)
	assert idxs.dtype == torch.int32

	assert pvals.shape == (45, 12)
	assert pvals.dtype == torch.float64


def test_annotate_seqlets_reverse_complement(X, X_contrib):
	seqlets = recursive_seqlets(X_contrib)
	assert seqlets.shape == (45, 5)

	idxs0, pvals0 = annotate_seqlets(X, seqlets, "tests/data/test.meme",
		reverse_complement=True)
	idxs1, pvals1 = annotate_seqlets(X, seqlets, "tests/data/test.meme",
		reverse_complement=False)
	
	assert_raises(AssertionError, assert_array_almost_equal, idxs0, idxs1)
	assert_raises(AssertionError, assert_array_almost_equal, pvals0, pvals1)


###


def test_count_annotations_small():
	X = torch.Tensor([[0, 0], [0, 0], [0, 1], [1, 0]])
	y = count_annotations(X)

	assert_array_almost_equal(y, [[2, 1], [1, 0]])


def test_count_annotations(annotations):
	X = count_annotations(annotations)

	assert X.shape == (25, 7)
	assert X.sum() == 100

	assert_array_almost_equal(X.sum(dim=0), [16, 15, 14, 10, 18, 15, 12])
	assert_array_almost_equal(X.sum(dim=1), [6, 3, 2, 3, 4, 4, 3, 6, 5, 6, 4, 4, 
		3, 5, 2, 6, 2, 5, 4, 4, 3, 1, 3, 9, 3])


def test_count_annotations_dim0(annotations):
	X0 = count_annotations(annotations)
	X = count_annotations(annotations, dim=0)

	assert X.shape == (7,)
	assert X.sum() == 100
	assert_array_almost_equal(X, X0.sum(dim=0))


def test_count_annotations_dim1(annotations):
	X0 = count_annotations(annotations)
	X = count_annotations(annotations, dim=1)

	assert X.shape == (25,)
	assert X.sum() == 100
	assert_array_almost_equal(X, X0.sum(dim=1))


def test_count_annotations_dtype(annotations):
	X = count_annotations(annotations)
	assert X.dtype == torch.uint8

	X = count_annotations(annotations, dtype=torch.int64)
	assert X.dtype == torch.int64

	X = count_annotations(annotations, dtype=torch.float32)
	assert X.dtype == torch.float32


def test_count_annotations_shape(annotations):
	X = count_annotations(annotations)
	assert X.shape == (25, 7)

	X = count_annotations(annotations, shape=(30, 30))
	assert X.shape == (30, 30)

	assert_raises(RuntimeError, count_annotations, annotations, shape=(3, 3))
	assert_raises(RuntimeError, count_annotations, annotations, shape=(3, 10))
	assert_raises(RuntimeError, count_annotations, annotations, shape=(39, 3))


def test_count_annotations_raises(annotations):
	assert_raises(ValueError, count_annotations, annotations - 10)
	assert_raises(ValueError, count_annotations, annotations.T)
	assert_raises(ValueError, count_annotations, torch.randn(100, 2))
	assert_raises(ValueError, count_annotations, torch.cat([annotations, 
		annotations], dim=1))


###


def test_pairwise_annotations_small():
	X = torch.Tensor([[0, 0], [0, 0], [0, 1], [1, 0], [1, 1]]).type(torch.int8)
	y = pairwise_annotations(X)

	assert_array_almost_equal(y, [[1, 3], [3, 0]])


def test_pairwise_annotations(annotations):
	y = pairwise_annotations(annotations)

	assert y.shape == (7, 7)
	assert y.dtype == torch.int64

	assert_array_almost_equal(y, [[ 4, 12, 10,  5,  8, 12, 12],
		[12,  3,  8,  5,  9, 15,  5],
		[10,  8,  2,  4,  9, 11,  4],
		[ 5,  5,  4,  1, 10,  6,  2],
		[ 8,  9,  9, 10,  4, 11,  3],
		[12, 15, 11,  6, 11, 6,  3],
		[12,  5,  4,  2,  3,  3,  2]])


def test_pairwise_annotations_raises(annotations):
	assert_raises(ValueError, pairwise_annotations, annotations - 10)
	assert_raises(ValueError, pairwise_annotations, annotations.T)
	assert_raises(ValueError, pairwise_annotations, torch.randn(100, 2))
	assert_raises(ValueError, pairwise_annotations, torch.cat([annotations, 
		annotations], dim=1))
	
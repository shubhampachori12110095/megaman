from __future__ import division ## removes integer division

import sys
import warnings
import numpy as np
from scipy import io
from scipy import sparse
from nose.tools import assert_true, assert_equal, assert_raises
from numpy.testing import assert_array_almost_equal, assert_array_equal
from scipy.spatial.distance import pdist, squareform
from Mmani.geometry.geometry import * 
from Mmani.geometry.distance import distance_matrix

random_state = np.random.RandomState(36)
n_sample = 10
d = 2
X = random_state.randn(n_sample, d)
D = squareform(pdist(X)) 
D[D > 1/d] = 0

def _load_test_data():
    """ Loads a .mat file from . that contains the following dense matrices
    test_dist_matrix
    Lsymnorm, Lunnorm, Lgeom, Lreno1_5, Lrw
    rad = scalar, radius used in affinity calculations, Laplacians
        Note: rad is returned as an array of dimension 1. Outside one must
        make it a scalar by rad = rad[0]
    """
#    xdict = io.loadmat('Mmani/geometry/tests/testMmani_laplacian_rad0_2_lam1_5_n200.mat')
    xdict = io.loadmat('testMmani_laplacian_rad0_2_lam1_5_n200.mat')
    rad = xdict[ 'rad' ]
    test_dist_matrix = xdict[ 'S' ] # S contains squared distances
    test_dist_matrix = np.sqrt( test_dist_matrix ) 
    Lsymnorm = xdict[ 'Lsymnorm' ] 
    Lunnorm = xdict[ 'Lunnorm' ] 
    Lgeom = xdict[ 'Lgeom' ] 
    Lrw = xdict[ 'Lrw' ] 
    Lreno1_5 = xdict[ 'Lreno1_5' ] 
    A = xdict[ 'A' ]
    return rad, test_dist_matrix, A, Lsymnorm, Lunnorm, Lgeom, Lreno1_5, Lrw

def test_Geometry_distance(almost_equal_decimals = 5):
    geom = Geometry(X)
    D1 = geom.get_distance_matrix()
    D2 = distance_matrix(X)
    assert_array_almost_equal(D1.todense(), D2.todense(), almost_equal_decimals)

def test_laplacian_unknown_normalization():
    """Test that laplacian fails with an unknown normalization type"""
    A = np.array([[ 5, 2, 1 ], [ 2, 3, 2 ],[1,2,5]]) 
    assert_raises(ValueError, graph_laplacian, A, normed='<unknown>')

def test_laplacian_create_A_sparse():
    """
    Test that A_sparse is the same as A_dense for a small A matrix
    """
    rad = 2.
    n_samples = 6
    X = np.arange(n_samples)
    X = X[ :,np.newaxis]
    X = np.concatenate((X,np.zeros((n_samples,1),dtype=float)),axis=1)
    X = np.asarray( X, order="C" )
    test_dist_matrix = distance_matrix( X, radius = rad )

    A_dense = affinity_matrix( test_dist_matrix.toarray(), rad, symmetrize = False )
    A_sparse = affinity_matrix( sparse.csr_matrix( test_dist_matrix ), rad, symmetrize = False )
    A_spdense = A_sparse.toarray()
    A_spdense[ A_spdense == 0 ] = 1.

    print( 'A_dense')
    print( A_dense )
    print( 'A_sparse',  A_spdense )

    assert_array_equal( A_dense, A_spdense )

def test_equal_original(almost_equal_decimals = 5):
    """ Loads the results from a matlab run and checks that our results
    are the same. The results loaded are A the similarity matrix and 
    all the Laplacians, sparse and dense.
    """
    
    rad, test_dist_matrix, Atest, Lsymnorm, Lunnorm, Lgeom, Lreno1_5, Lrw = _load_test_data()

    rad = rad[0]
    rad = rad[0]
    A_dense = affinity_matrix( test_dist_matrix, rad )
    A_sparse = affinity_matrix( sparse.csr_matrix( test_dist_matrix ), rad )
    B = A_sparse.toarray()
    B[ B == 0. ] = 1.
    assert_array_almost_equal( A_dense, B, almost_equal_decimals )
    assert_array_almost_equal( Atest, A_dense, almost_equal_decimals )

    for (A, issparse) in [(Atest, False), (sparse.coo_matrix(Atest), True)]:
        for (Ltest, normed ) in [(Lsymnorm, 'symmetricnormalized'), (Lunnorm, 'unnormalized'), (Lgeom, 'geometric'), (Lrw, 'randomwalk'), (Lreno1_5, 'renormalized')]:
            L, diag =  graph_laplacian(A, normed=normed, symmetrize=True, scaling_epps=rad, renormalization_exponent=1.5, return_diag=True)
            if issparse:
                print( 'sparse ', normed )
                assert_array_almost_equal( L.toarray(), Ltest, 5 )
                diag_mask = (L.row == L.col )
                assert_array_equal(diag, L.data[diag_mask].squeeze())
            else:
                print( 'dense ', normed )
                assert_array_almost_equal( L, Ltest, 5 )
                di = np.diag_indices( L.shape[0] )
                assert_array_equal(diag, np.array( L[di] )) 
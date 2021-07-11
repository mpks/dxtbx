import itertools

import numpy as np
import pytest

import scitbx.array_family.flex as flex

import dxtbx.flumpy as flumpy

# A mapping of which flex type should map to which numpy dtype - for verification
lookup_flex_type_to_numpy = {
    "uint8": "B",
    "uint16": "H",
    "uint32": "I",
    "size_t": "Q",
    "int8": "b",
    "int16": "h",
    "int": "i",
    "long": "q",
    "int32": "i",
    "int64": "q",
    "float": "f",
    "double": "d",
    "bool": "?",
    "complex_double": "D",
    "vec3_double": "d",
    "vec3_int": "i",
    "vec2_double": "d",
    "tiny_size_t_2": "Q",
}


def test_basics():
    with pytest.raises(ValueError):
        s = flumpy.Scuffer(1)
        memoryview(s)

    i = flex.int(10)
    d = flex.double(10)

    flumpy.Scuffer(d)
    flumpy.Scuffer(i)


@pytest.fixture(
    params=[
        "size_t",
        "uint8",
        "uint16",
        "uint32",
        "int",
        "long",
        "int8",
        "int16",
        "int32",
        "int64",
        "float",
        "double",
    ]
)
def flex_numeric(request):
    flex_typename = request.param
    if not hasattr(flex, flex_typename):
        pytest.skip(f"Type flex.{flex_typename} not available on this flex instance")
    return getattr(flex, flex_typename)


def test_numeric_1d(flex_numeric):
    # 1d basics
    f1d = flex_numeric(range(10))
    as_np = flumpy.to_numpy(f1d)
    assert (f1d == as_np).all()
    # Change and make sure reflected in both
    as_np[2] = 42
    assert (f1d == as_np).all()
    assert as_np.dtype.char != "?"


def test_reverse_numeric_1d(flex_numeric):
    dtype = lookup_flex_type_to_numpy[flex_numeric.__name__]
    npo = np.array([240, 259, 144, 187], dtype=dtype)
    fo = flumpy.from_numpy(npo)
    assert isinstance(fo, flex_numeric)
    assert fo.all() == npo.shape
    assert all(fo[x] == npo[x] for x in range(4))
    npo[0] = 42
    assert all(fo[x] == npo[x] for x in range(4))
    assert fo[0] == 42


def test_numeric_2d(flex_numeric):
    grid = flex.grid(10, 10)
    fo = flex_numeric(grid)
    as_np = flumpy.to_numpy(fo)

    for i in range(10):
        for j in range(10):
            as_np[j, i] = i + j
            assert fo[j, i] == as_np[j, i]
            fo[j, i] = max(i, j) - min(i, j)
            assert fo[j, i] == as_np[j, i]


def test_reverse_numeric_2d(flex_numeric):
    dtype = lookup_flex_type_to_numpy[flex_numeric.__name__]
    npo = np.array(
        [[240, 259, 144, 187], [240, 259, 144, 187], [240, 259, 144, 187]], dtype=dtype
    )
    fo = flumpy.from_numpy(npo)
    assert isinstance(fo, flex_numeric)
    assert fo.all() == npo.shape
    assert all(fo[x] == npo[x] for x in itertools.product(range(3), range(4)))
    npo[0] = 42
    assert all(fo[x] == npo[x] for x in itertools.product(range(3), range(4)))
    assert fo[0] == 42
    fo[0, 1] = 2
    assert npo[0, 1] == 2


def test_numeric_4d(flex_numeric):
    #  Check that we can think fourth-dimnesionally
    grid = flex.grid(1, 9, 8, 5)
    fo = flex_numeric(grid)
    assert fo.nd() == 4
    as_np = flumpy.to_numpy(fo)
    for indices in itertools.product(range(1), range(9), range(8), range(5)):
        fo[indices] = sum(indices)
        assert fo[indices] == as_np[indices]


def test_reverse_numeric_4d(flex_numeric):
    dtype = lookup_flex_type_to_numpy[flex_numeric.__name__]
    npo = np.zeros((1, 9, 8, 5), dtype=dtype)
    fo = flumpy.from_numpy(npo)
    assert isinstance(fo, flex_numeric)
    assert fo.nd() == 4
    for indices in itertools.product(range(1), range(9), range(8), range(5)):
        fo[indices] = sum(indices)
        assert fo[indices] == npo[indices]


def test_bool():
    fo = flex.bool(flex.grid([5, 5, 5, 5, 5]))
    for indices in itertools.product(*([range(5)] * 5)):
        fo[indices] = sum(indices) % 3 == 0 or sum(indices) % 5 == 0
    as_np = flumpy.to_numpy(fo)
    for indices in itertools.product(*([range(5)] * 5)):
        assert fo[indices] == as_np[indices]
    assert fo.count(True) == as_np.sum()


def test_reverse_bool():
    sums = np.sum(np.indices((5, 5, 5, 5, 5)), axis=0)
    npo = np.logical_or(sums % 3 == 3, sums % 5 == 0)
    fo = flumpy.from_numpy(npo)
    for idx in itertools.product(*[range(5)] * 5):
        assert fo[idx] == npo[idx]
    assert fo.count(True) == npo.sum()


@pytest.mark.parametrize("flex_vec", [flex.vec3_double, flex.vec3_int])
def test_vec3(flex_vec):
    basic_vector = [(i, i * 2, i * 3) for i in range(10)]
    fo = flex_vec(basic_vector)
    as_np = flumpy.to_numpy(fo)
    assert (as_np == fo).all()
    as_np[0] = (0, 4, 0)
    as_np[1, 2] = 42
    assert fo[0] == (0, 4, 0)
    assert (as_np == fo).all()


@pytest.mark.parametrize("flex_vec", [flex.vec3_double, flex.vec3_int])
def test_reverse_vec3(flex_vec):
    dtype = lookup_flex_type_to_numpy[flex_vec.__name__]
    no = np.zeros((5, 3), dtype=dtype)
    fo = flumpy.vec_from_numpy(no)
    assert fo.all() == (5,)
    fo[0] = (1, 2, 3)
    assert (no[0] == (1, 2, 3)).all()

    with pytest.raises(ValueError):
        flumpy.vec_from_numpy(no.reshape((1, 15)))


@pytest.mark.parametrize("flex_vec", [flex.vec2_double, flex.tiny_size_t_2])
def test_vec2(flex_vec):
    basic_vector = [(i, i * 2) for i in range(10)]
    fo = flex_vec(basic_vector)
    as_np = flumpy.to_numpy(fo)
    assert (as_np == fo).all()
    as_np[0] = (0, 4)
    as_np[1, 1] = 42
    assert fo[0] == (0, 4)
    assert (as_np == fo).all()


@pytest.mark.parametrize("flex_vec", [flex.vec2_double, flex.tiny_size_t_2])
def test_reverse_vec2(flex_vec):
    dtype = lookup_flex_type_to_numpy[flex_vec.__name__]
    no = np.zeros((5, 2), dtype=dtype)
    fo = flumpy.vec_from_numpy(no)
    assert fo.all() == (5,)
    fo[0] = (1, 2)
    assert (no[0] == (1, 2)).all()


def test_mat3():
    fo = flex.mat3_double(10)
    as_np = flumpy.to_numpy(fo)
    for i in range(10):
        fo[i] = [1, i, 0, 0, 1, 0, i, 0, 1]
    assert (as_np.reshape(10, 9) == fo).all()


def test_reverse_mat3():
    # Want to test both N...x3x3 and N...x9
    no = np.zeros((10, 3, 3))
    for i in range(10):
        no[i] = [[1, i, 0], [0, 1, 0], [i, 0, 1]]
    fo = flumpy.mat3_from_numpy(no)
    assert (no.reshape(10, 9) == fo).all()

    flatter = np.copy(no.reshape(10, 9))
    flatter[0][0] = 14
    assert no[0][0][0] != 14
    fo_2 = flumpy.mat3_from_numpy(flatter)
    assert (flatter == fo_2).all()

    # Check we can't use unsupported dtypes
    with pytest.raises(ValueError):
        flumpy.mat3_from_numpy(np.zeros((10, 3, 3), dtype="i"))


def test_complex():
    fo = flex.complex_double(10)
    as_np = flumpy.to_numpy(fo)
    fo[1] = 3j
    fo[4] = 1.3 + 3j
    assert (as_np == fo).all()


def test_reverse_complex():
    npo = np.array([3j, 4j, 3 + 5j])
    fo = flumpy.from_numpy(npo)
    assert fo[2] == 3 + 5j
    assert (npo == fo).all()
    fo[0] = 1j
    assert npo[0] == 1j


def test_basic_fromnumpy():
    no = np.zeros(10, dtype="B")
    fo = flumpy.from_numpy(no)
    assert len(fo) == 10


def test_already_numpy():
    no = np.zeros(10, dtype="B")
    assert flumpy.to_numpy(no) is no


def test_already_flex():
    fo = flex.int(10)
    assert flumpy.from_numpy(fo) is fo


def test_flex_loop_nesting():
    fo = flex.int(10)
    npo = flumpy.to_numpy(fo)
    assert fo is flumpy.from_numpy(npo)

    # Now try vec
    fo = flex.complex_double(5)
    npo = flumpy.to_numpy(fo)
    assert flumpy.from_numpy(npo) is fo


@pytest.mark.xfail()
def test_flex_looping_vecs():
    # We want to try and avoid recursive nesting, but don't want to
    # return the original object if attempting to miscast vec<->numeric
    # however.... this means lots of conditions to check, so ignore now
    fo = flex.vec3_double(5)
    npo = flumpy.to_numpy(fo)
    assert flumpy.vec_from_numpy(npo) is fo

    # Don't be dumb when casting
    flex_nonvec = flex.double((9, 3))
    assert not flumpy.vec_from_numpy(flumpy.to_numpy(flex_nonvec)) is flex_nonvec

    # mat3
    fo = flex.mat3_double(5)
    npo = flumpy.to_numpy(fo)
    assert flumpy.mat3_from_numpy(npo) is fo


def test_numpy_loop_nesting():
    no = np.array([0, 1, 2])
    fo = flumpy.from_numpy(no)
    no_2 = flumpy.to_numpy(fo)
    assert no_2 is no
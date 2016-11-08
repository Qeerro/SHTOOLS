"""
Class interface for SHTOOLS.

pyshtools defines several classes that facilitate the interactive
examination of geographical gridded data and their associated
spherical harmonic coefficients. Subclasses are used to handle different
internal data types and superclasses are used to implement interface
functions and documentation.

pyshtools class structure:

    SHCoeffs
        SHRealCoeffs
        SHComplexCoeffs

    SHGrid
        DHRealGrid
        DHComplexGrid
        GLQRealGrid
        GLQComplexGrid

    SHWindow
        SHWindowCap
        SHWindowMask

For more information, see the documentation for the top level classes.
"""

from __future__ import absolute_import as _absolute_import
from __future__ import division as _division
from __future__ import print_function as _print_function

import numpy as _np
import matplotlib as _mpl
import matplotlib.pyplot as _plt
import copy as _copy

from . import _SHTOOLS as _shtools


# =============================================================================
# =========    COEFFICIENT CLASSES    =========================================
# =============================================================================

class SHCoeffs(object):
    """
    Spherical Harmonics Coefficient class.

    The coefficients of this class can be initialized using one of the
    four constructor methods:

    >>> x = SHCoeffs.from_array(numpy.zeros((2, lmax+1, lmax+1)))
    >>> x = SHCoeffs.from_random(powerspectrum[0:lmax+1])
    >>> x = SHCoeffs.from_zeros(lmax)
    >>> x = SHCoeffs.from_file('fname.dat')

    The normalization convention of the input coefficents is specified
    by the normalization and csphase parameters, which take the following
    values:

    normalization : '4pi' (default), geodesy 4-pi normalized.
                  : 'ortho', orthonormalized.
                  : 'schmidt', Schmidt semi-normalized.

    csphase       : 1 (default), exlcude the Condon-Shortley phase factor.
                  : -1, include the Condon-Shortley phase factor.

    See the documentation for each constructor method for further options.

    Once initialized, each class instance defines the following class
    attributes:

    lmax          : The maximum spherical harmonic degree of the coefficients.
    coeffs        : The raw coefficients with the specified normalization and
                    csphase conventions.
    normalization : The normalization of the coefficients: '4pi', 'ortho', or
                    'schmidt'.
    csphase       : Defines whether the Condon-Shortley phase is used (1)
                    or not (-1).
    mask          : A boolean mask that is True for the permissible values of
                    degree l and order m.
    kind          : The coefficient data type: either 'complex' or 'real'.

    Each class instance provides the following methods:

    to_array()            : Return an array of spherical harmonic coefficients
                            with a different normalization convention.
    to_file()             : Save raw spherical harmonic coefficients as a file.
    degrees()             : Return an array listing the spherical harmonic
                            degrees from 0 to lmax.
    spectrum()            : Return the spectrum of the function.
    set_coeffs()          : Set coefficients in-place to specified values.
    rotate()              : Rotate the coordinate system used to express the
                            spherical harmonic coefficients and return a new
                            class instance.
    convert()             : Return a new class instance using a different
                            normalization convention.
    expand()              : Evaluate the coefficients on a spherical grid and
                            return a new SHGrid class instance.
    copy()                : Return a copy of the class instance.
    plot_spectrum()       : Plot the  spectrum as a function of spherical
                            harmonic degree.
    plot_spectrum2d()     : Plot the 2D spectrum of all spherical harmonic
                            coefficients.
    info()                : Print a summary of the data stored in the SHCoeffs
                            instance.
    """

    def __init__(self):
        """Unused constructor of the super class."""
        print('Initialize the class using one of the class methods:\n'
              '>>> SHCoeffs.from_array?\n'
              '>>> SHCoeffs.from_random?\n'
              '>>> SHCoeffs.from_zeros?\n'
              '>>> SHCoeffs.from_file?\n')

    # ---- factory methods:
    @classmethod
    def from_zeros(self, lmax, kind='real', normalization='4pi', csphase=1):
        """
        Initialize class with spherical harmonic coefficients set to zero from
        degree 0 to lmax.

        Usage
        -----
        x = SHCoeffs.from_zeros(lmax, [normalization, csphase])

        Returns
        -------
        x : SHCoeffs class instance.

        Parameters
        ----------
        lmax : int
            The highest spherical harmonic degree l of the coefficients.
        normalization : str, optional, default = '4pi'
            '4pi', 'ortho' or 'schmidt' for geodesy 4pi normalized,
            orthonormalized, or Schmidt semi-normalized coefficients,
            respectively.
        csphase : int, optional, default = 1
            Condon-Shortley phase convention: 1 to exclude the phase factor,
            or -1 to include it.
        kind : str, optional, default = 'real'
            'real' or 'complex' spherical harmonic coefficients.
        """
        if kind.lower() not in set(['real', 'complex']):
            raise ValueError(
                "Kind must be 'real' or 'complex'. " +
                "Input value was {:s}."
                .format(repr(kind))
                )

        if normalization.lower() not in set(['4pi', 'ortho', 'schmidt']):
            raise ValueError(
                "The normalization must be '4pi', 'ortho' " +
                "or 'schmidt'. Input value was {:s}."
                .format(repr(normalization))
                )

        if csphase != 1 and csphase != -1:
            raise ValueError(
                "csphase must be either 1 or -1. Input value was {:s}."
                .format(repr(csphase))
                )

        nl = lmax + 1
        if kind.lower() == 'real':
            coeffs = _np.zeros((2, nl, nl))
        else:
            coeffs = _np.zeros((2, nl, nl), dtype=complex)

        for cls in self.__subclasses__():
            if cls.istype(kind):
                return cls(coeffs, normalization=normalization.lower(),
                           csphase=csphase)

    @classmethod
    def from_array(self, coeffs, normalization='4pi', csphase=1, copy=True):
        """
        Initialize the class with spherical harmonic coefficients from an input
        array.

        Usage
        -----
        x = SHCoeffs.from_array(array, [normalization, csphase, copy])

        Returns
        -------
        x : SHCoeffs class instance.

        Parameters
        ----------
        array : ndarray, shape (2, lmax+1, lmax+1).
            The input spherical harmonic coefficients.
        normalization : str, optional, default = '4pi'
            '4pi', 'ortho' or 'schmidt' for geodesy 4pi normalized,
            orthonormalized, or Schmidt semi-normalized coefficients,
            respectively.
        csphase : int, optional, default = 1
            Condon-Shortley phase convention: 1 to exclude the phase factor,
            or -1 to include it.
        copy : bool, optional, default = True
            If True, make a copy of array when initializing the class instance.
            If False, initialize the class instance with a reference to array.
        """
        if _np.iscomplexobj(coeffs):
            kind = 'complex'
        else:
            kind = 'real'

        if type(normalization) != str:
            raise ValueError('normalization must be a string. ' +
                             'Input type was {:s}'
                             .format(str(type(normalization))))

        if normalization.lower() not in set(['4pi', 'ortho', 'schmidt']):
            raise ValueError(
                "The normalization must be '4pi', 'ortho' " +
                "or 'schmidt'. Input value was {:s}."
                .format(repr(normalization))
                )

        if csphase != 1 and csphase != -1:
            raise ValueError(
                "csphase must be either 1 or -1. Input value was {:s}."
                .format(repr(csphase))
                )

        for cls in self.__subclasses__():
            if cls.istype(kind):
                return cls(coeffs, normalization=normalization.lower(),
                           csphase=csphase, copy=copy)

    @classmethod
    def from_random(self, power, kind='real', normalization='4pi', csphase=1,
                    exact_power=False):
        """
        Initialize the class with spherical harmonic coefficients as random
        variables.

        This routine picks random coefficients from a normal distribution.
        The variance of the normal distribution is set to the given input power
        divided by the number of coefficients at degree l. The output
        coefficient power can be fixed exactly using the keyword exact_power.

        Usage
        -----
        x = SHCoeffs.from_random(power, [kind, normalization, csphase,
                                         exact_power])

        Returns
        -------
        x : SHCoeffs class instance.

        Parameters
        ----------
        power : ndarray, shape (lmax+1)
            numpy array of shape (lmax+1) that specifies the expected power per
            degree l of the random coefficients.
        kind : str, optional, default = 'real'
            'real' or 'complex' spherical harmonic coefficients.
        normalization : str, optional, default = '4pi'
            '4pi', 'ortho' or 'schmidt' for geodesy 4pi normalized,
            orthonormalized, or Schmidt semi-normalized coefficients,
            respectively.
        csphase : int, optional, default = 1
            Condon-Shortley phase convention: 1 to exclude the phase factor,
            or -1 to include it.
        exact_power : bool, optional, default = False
            The total variance of the coefficients is set exactly to the input
            power. This means that the distribution of power at degree l
            amongst the angular orders is random, but the total power is fixed.
        """
        # check if all arguments are correct
        if type(normalization) != str:
            raise ValueError('normalization must be a string. ' +
                             'Input type was {:s}'
                             .format(str(type(normalization))))

        if normalization.lower() not in set(['4pi', 'ortho', 'schmidt']):
            raise ValueError(
                "The input normalization must be '4pi', 'ortho' " +
                "or 'schmidt'. Provided value was {:s}"
                .format(repr(normalization))
                )

        if csphase != 1 and csphase != -1:
            raise ValueError(
                "csphase must be 1 or -1. Input value was {:s}"
                .format(repr(csphase))
                )

        if kind.lower() not in set(['real', 'complex']):
            raise ValueError(
                "kind must be 'real' or 'complex'. " +
                "Input value was {:s}.".format(repr(kind)))

        # start initialization
        nl = len(power)
        l = _np.arange(nl)

        if kind.lower() == 'real':
            coeffs = _np.random.normal(size=(2, nl, nl))
            if exact_power:
                power_per_lm = _shtools.SHPowerSpectrumDensity(coeffs)
                with _np.errstate(divide='ignore', invalid='ignore'):
                    power = _np.true_divide(power, power_per_lm)
                    power[~_np.isfinite(power)] = 0  # -inf inf NaN

        elif kind.lower() == 'complex':
            # - need to divide by sqrt 2 as there are two terms for each coeff.
            coeffs = (_np.random.normal(size=(2, nl, nl)) +
                      1j * _np.random.normal(size=(2, nl, nl))) / _np.sqrt(2.)
            if exact_power:
                power_per_lm = _shtools.SHPowerSpectrumC(coeffs)
                with _np.errstate(divide='ignore', invalid='ignore'):
                    power = _np.true_divide(power, power_per_lm)
                    power[~_np.isfinite(power)] = 0  # -inf inf NaN

        if normalization.lower() == '4pi':
            coeffs *= _np.sqrt(
                power / (2.0 * l + 1.0))[_np.newaxis, :, _np.newaxis]
        elif normalization.lower() == 'ortho':
            coeffs *= _np.sqrt(
                4.0 * _np.pi * power / (2.0 * l + 1.0)
                )[_np.newaxis, :, _np.newaxis]
        elif normalization.lower() == 'schmidt':
            coeffs *= _np.sqrt(power)[_np.newaxis, :, _np.newaxis]

        for cls in self.__subclasses__():
            if cls.istype(kind):
                return cls(coeffs, normalization=normalization.lower(),
                           csphase=csphase)

    @classmethod
    def from_file(self, fname, lmax=None, format='shtools', kind='real',
                  normalization='4pi', csphase=1, **kwargs):
        """
        Initialize the class with spherical harmonic coefficients from a file.

        Usage
        -----
        x = SHCoeffs.from_file(filename, lmax, [format='shtools', kind,
                                                normalization, csphase, skip])
        x = SHCoeffs.from_file(filename, [format='npy', kind, normalization,
                                          csphase, **kwargs])

        Returns
        -------
        x : SHCoeffs class instance.

        Parameters
        ----------
        filename : str
            Name of the file, including path.
        lmax : int, required when format = 'shtools'
            Maximum spherical harmonic degree to read from the file when format
            is 'shtools'.
        format : str, optional, default = 'shtools'
            'shtools' format or binary numpy 'npy' format.
        kind : str, optional, default = 'real'
            'real' or 'complex' spherical harmonic coefficients.
        normalization : str, optional, default = '4pi'
            '4pi', 'ortho' or 'schmidt' for geodesy 4pi normalized,
            orthonormalized, or Schmidt semi-normalized coefficients,
            respectively.
        csphase : int, optional, default = 1
            Condon-Shortley phase convention: 1 to exclude the phase factor,
            or -1 to include it.
        skip : int, required when format = 'shtools'
            Number of lines to skip at the beginning of the file when format is
            'shtools'.
        **kwargs : keyword argument list, optional for format = 'npy'
            Keyword arguments of numpy.load() when format is 'npy'.

        Description
        -----------
        If format='shtools', spherical harmonic coefficients will be read from
        an ascii-formatted file. The maximum spherical harmonic degree that is
        read is determined by the input value lmax. If the optional value skip
        is specified, parsing of the file will commence after the first skip
        lines. For this format, each line of the file must contain

        l, m, cilm[0, l, m], cilm[1, l, m]

        For each value of increasing l, increasing from zero, all the angular
        orders are listed in inceasing order, from 0 to l. For more
        information, see SHRead.

        If format='npy', a binary numpy 'npy' file will be read using
        numpy.load().
        """
        if type(normalization) != str:
            raise ValueError('normalization must be a string. ' +
                             'Input type was {:s}'
                             .format(str(type(normalization))))

        if normalization.lower() not in set(['4pi', 'ortho', 'schmidt']):
            raise ValueError(
                "The input normalization must be '4pi', 'ortho' " +
                "or 'schmidt'. Provided value was {:s}"
                .format(repr(normalization))
                )
        if csphase != 1 and csphase != -1:
            raise ValueError(
                "csphase must be 1 or -1. Input value was {:s}"
                .format(repr(csphase))
                )

        if format.lower() == 'shtools' and lmax is None:
            raise ValueError("lmax must be specified when format is 'shtools'")

        if format.lower() == 'shtools':
            if kind.lower() == 'real':
                coeffs, lmax = _shtools.SHRead(fname, lmax, **kwargs)
            else:
                raise NotImplementedError(
                    "Complex coefficients are not yet implemented for "
                    "format='shtools'")
        elif format.lower() == 'npy':
            coeffs = _np.load(fname, **kwargs)
        else:
            raise NotImplementedError(
                'format={:s} not yet implemented'.format(repr(format)))

        for cls in self.__subclasses__():
            if cls.istype(kind):
                return cls(coeffs, normalization=normalization.lower(),
                           csphase=csphase)

    def copy(self):
        """Return a deep copy of the class instance."""
        return _copy.deepcopy(self)

    def to_file(self, filename, format='shtools', **kwargs):
        """
        Save raw spherical harmonic coefficients to a file.

        Usage
        -----
        x.to_file(filename, [format, **kwargs])

        Parameters
        ----------
        filename : str
            Name of the output file.
        format : str, optional, default = 'shtools'
            'shtools' or 'npy'. See method from_file for more information.
        **kwargs : keyword argument list, optional for format = 'npy'
            Keyword arguments of numpy.save().
        """
        if format is 'shtools':
            with open(filename, mode='w') as file:
                for l in range(self.lmax+1):
                    for m in range(l+1):
                        file.write('{:d}, {:d}, {:e}, {:e}\n'
                                   .format(l, m, self.coeffs[0, l, m],
                                           self.coeffs[1, l, m]))
        elif format is 'npy':
            _np.save(filename, self.coeffs, **kwargs)
        else:
            raise NotImplementedError(
                'format={:s} not yet implemented'.format(repr(format)))

    # ---- operators ----
    def __add__(self, other):
        """
        Add two similar sets of coefficients or coefficients and a scalar:
        self + other.
        """
        if isinstance(other, SHCoeffs):
            if (self.normalization == other.normalization and self.csphase ==
                    other.csphase and self.kind == other.kind):
                coeffs = _np.zeros([2, self.lmax+1, self.lmax+1])
                coeffs[self.mask] = (self.coeffs[self.mask] +
                                     other.coeffs[self.mask])
                return SHCoeffs.from_array(coeffs, csphase=self.csphase,
                                           normalization=self.normalization)
            else:
                raise ValueError('The two sets of coefficients must be of ' +
                                 'the same kind and have the same ' +
                                 'normalization and csphase.')
        elif _np.isscalar(other) is True:
            coeffs = _np.zeros([2, self.lmax+1, self.lmax+1])
            coeffs[self.mask] = self.coeffs[self.mask] + other
            return SHCoeffs.from_array(coeffs, csphase=self.csphase,
                                       normalization=self.normalization)
        else:
            raise NotImplementedError('Mathematical operator not implemented' +
                                      'for these operands.')

    def __radd__(self, other):
        """
        Add two similar sets of coefficients or coefficients and a scalar:
        other + self.
        """
        return self.__add__(other)

    def __sub__(self, other):
        """
        Subtract two similar sets of coefficients or coefficients and a scalar:
        self - other.
        """
        if isinstance(other, SHCoeffs):
            if (self.normalization == other.normalization and self.csphase ==
                    other.csphase and self.kind == other.kind):
                coeffs = _np.zeros([2, self.lmax+1, self.lmax+1])
                coeffs[self.mask] = (self.coeffs[self.mask] -
                                     other.coeffs[self.mask])
                return SHCoeffs.from_array(coeffs, csphase=self.csphase,
                                           normalization=self.normalization)
            else:
                raise ValueError('The two sets of coefficients must be of ' +
                                 'the same kind and have the same ' +
                                 'normalization and csphase.')
        elif _np.isscalar(other) is True:
            coeffs = _np.zeros([2, self.lmax+1, self.lmax+1])
            coeffs[self.mask] = self.coeffs[self.mask] - other
            return SHCoeffs.from_array(coeffs, csphase=self.csphase,
                                       normalization=self.normalization)
        else:
            raise NotImplementedError('Mathematical operator not implemented' +
                                      'for these operands.')

    def __rsub__(self, other):
        """
        Subtract two similar sets of coefficients or coefficients and a scalar:
        other - self.
        """
        if isinstance(other, SHCoeffs):
            if (self.normalization == other.normalization and self.csphase ==
                    other.csphase and self.kind == other.kind):
                coeffs = _np.zeros([2, self.lmax+1, self.lmax+1])
                coeffs[self.mask] = (other.coeffs[self.mask] -
                                     self.coeffs[self.mask])
                return SHCoeffs.from_array(coeffs, csphase=self.csphase,
                                           normalization=self.normalization)
            else:
                raise ValueError('The two sets of coefficients must be of ' +
                                 'the same kind and have the same ' +
                                 'normalization and csphase.')
        elif _np.isscalar(other) is True:
            coeffs = _np.zeros([2, self.lmax+1, self.lmax+1])
            coeffs[self.mask] = other - self.coeffs[self.mask]
            return SHCoeffs.from_array(coeffs, csphase=self.csphase,
                                       normalization=self.normalization)
        else:
            raise NotImplementedError('Mathematical operator not implemented' +
                                      'for these operands.')

    def __mul__(self, other):
        """
        Multiply two similar sets of coefficients or coefficients and a scalar:
        self * other.
        """
        if isinstance(other, SHCoeffs):
            if (self.normalization == other.normalization and self.csphase ==
                    other.csphase and self.kind == other.kind):
                coeffs = _np.zeros([2, self.lmax+1, self.lmax+1])
                coeffs[self.mask] = (self.coeffs[self.mask] *
                                     other.coeffs[self.mask])
                return SHCoeffs.from_array(coeffs, csphase=self.csphase,
                                           normalization=self.normalization)
            else:
                raise ValueError('The two sets of coefficients must be of ' +
                                 'the same kind and have the same ' +
                                 'normalization and csphase.')
        elif _np.isscalar(other) is True:
            coeffs = _np.zeros([2, self.lmax+1, self.lmax+1])
            coeffs[self.mask] = self.coeffs[self.mask] * other
            return SHCoeffs.from_array(coeffs, csphase=self.csphase,
                                       normalization=self.normalization)
        else:
            raise NotImplementedError('Mathematical operator not implemented' +
                                      'for these operands.')

    def __rmul__(self, other):
        """
        Multiply two similar sets of coefficients or coefficients and a scalar:
        other * self.
        """
        return self.__mul__(other)

    def __div__(self, other):
        """
        Divide two similar sets of coefficients or coefficients and a scalar
        when __future__.division is not in effect: self / other.
        """
        if isinstance(other, SHCoeffs):
            if (self.normalization == other.normalization and self.csphase ==
                    other.csphase and self.kind == other.kind):
                coeffs = _np.zeros([2, self.lmax+1, self.lmax+1])
                coeffs[self.mask] = (self.coeffs[self.mask] /
                                     other.coeffs[self.mask])
                return SHCoeffs.from_array(coeffs, csphase=self.csphase,
                                           normalization=self.normalization)
            else:
                raise ValueError('The two sets of coefficients must be of ' +
                                 'the same kind and have the same ' +
                                 'normalization and csphase.')
        elif _np.isscalar(other) is True:
            coeffs = _np.zeros([2, self.lmax+1, self.lmax+1])
            coeffs[self.mask] = self.coeffs[self.mask] / other
            return SHCoeffs.from_array(coeffs, csphase=self.csphase,
                                       normalization=self.normalization)
        else:
            raise NotImplementedError('Mathematical operator not implemented' +
                                      'for these operands.')

    def __truediv__(self, other):
        """
        Divide two similar sets of coefficients or coefficients and a scalar
        when __future__.division is in effect: self / other.
        """
        if isinstance(other, SHCoeffs):
            if (self.normalization == other.normalization and self.csphase ==
                    other.csphase and self.kind == other.kind):
                coeffs = _np.zeros([2, self.lmax+1, self.lmax+1])
                coeffs[self.mask] = (self.coeffs[self.mask] /
                                     other.coeffs[self.mask])
                return SHCoeffs.from_array(coeffs, csphase=self.csphase,
                                           normalization=self.normalization)
            else:
                raise ValueError('The two sets of coefficients must be of ' +
                                 'the same kind and have the same ' +
                                 'normalization and csphase.')
        elif _np.isscalar(other) is True:
            coeffs = _np.zeros([2, self.lmax+1, self.lmax+1])
            coeffs[self.mask] = self.coeffs[self.mask] / other
            return SHCoeffs.from_array(coeffs, csphase=self.csphase,
                                       normalization=self.normalization)
        else:
            raise NotImplementedError('Mathematical operator not implemented' +
                                      'for these operands.')

    def __pow__(self, other):
        """
        Raise the spherical harmonic coefficients to a scalar power:
        pow(self, other).
        """
        if _np.isscalar(other) is True:
            return SHCoeffs.from_array(pow(self.coeffs, other),
                                       csphase=self.csphase,
                                       normalization=self.normalization)
        else:
            raise NotImplementedError('Mathematical operator not implemented' +
                                      'for these operands.')

    # ---- Extract data ----
    def degrees(self):
        """
        Return a numpy array with the spherical harmonic degrees from 0 to
        lmax.

        Usage
        -----
        degrees = x.degrees()

        Returns
        -------
        degrees : ndarray, shape (lmax+1)
            1-D numpy ndarray listing the spherical harmonic degrees, where
            lmax is the maximum spherical harmonic degree.
        """
        return _np.arange(self.lmax + 1)

    def spectrum(self, convention='power', unit='per_l', base=10.):
        """
        Return the spectrum as a function of spherical harmonic degree.

        Usage
        -----
        power = x.spectrum([convention, unit, base])

        Returns
        -------
        power : ndarray, shape (lmax+1)
            1-D numpy ndarray of the spectrum, where lmax is the maximum
            spherical harmonic degree.

        Parameters
        ----------
        convention : str, optional, default = 'power'
            The type of spectrum to return: 'power' for power spectrum,
            'energy' for energy spectrum, and 'l2norm' for the l2 norm
            spectrum.
        unit : str, optional, default = 'per_l'
            If 'per_l', return the total contribution to the spectrum for each
            spherical harmonic degree l. If 'per_lm', return the average
            contribution to the spectrum for each coefficient at spherical
            harmonic degree l. If 'per_dlogl', return the spectrum per log
            interval dlog_a(l).
        base : float, optional, default = 10.
            The logarithm base when calculating the 'per_dlogl' power spectrum.

        Description
        -----------
        This function returns either the power spectrum, energy spectrum, or
        l2-norm spectrum. Total power is defined as the integral of the
        function squared over all space, divided by the area the function
        spans. If the mean of the function is zero, this is equivalent to the
        variance of the function. The total energy is the integral of the
        function squared over all space and is 4pi times the total power. The
        l2-norm is the sum of the magnitude of the coefficients squared.

        The output spectrum can be expresed using one of three units. 'per_l'
        returns the contribution to the total spectrum from all angular orders
        at degree l. 'per_lm' returns the average contribution to the total
        spectrum from a single coefficient at degree l. The 'per_lm' spectrum
        is equal to the 'per_l' spectrum divided by (2l+1). 'per_dlogl' returns
        the contribution to the total spectrum from all angular orders over an
        infinitessimal logarithmic degree band. The contrubution in the band
        dlog_a(l) is spectrum(l, 'per_dlogl')*dlog_a(l), where a is the base,
        and where spectrum(l, 'per_dlogl) is equal to
        spectrum(l, 'per_l')*l*log(a).
        """
        return self._spectrum(convention=convention, unit=unit, base=base)

    # ---- Set individual coefficient
    def set_coeffs(self, values, ls, ms):
        """
        Set spherical harmonic coefficients in-place to specified values.

        Usage
        -----
        x.set_coeffs(values, ls, ms)

        Parameters
        ----------
        values : float or complex (list)
            The value(s) of the spherical harmonic coefficient(s).
        ls : int (list)
            The degree(s) of the coefficient(s) that should be set.
        ms : int (list)
            The order(s) of the coefficient(s) that should be set. Positive
            and negative values correspond to the cosine and sine
            components, respectively.

        Examples
        --------
        x.set_coeffs(10.,1,1)               # x.coeffs[0,1,1] = 10.
        x.set_coeffs([1.,2], [1,2], [0,-2]) # x.coeffs[0,1,0] = 1.
                                            # x.coeffs[1,2,2] = 2.
        """
        # make sure that the type is correct
        values = _np.array(values)
        ls = _np.array(ls)
        ms = _np.array(ms)

        mneg_mask = (ms < 0).astype(_np.int)
        self.coeffs[mneg_mask, ls, _np.abs(ms)] = values

    # ---- Return coefficients with a different normalization convention ----
    def to_array(self, normalization=None, csphase=None, lmax=None):
        """
        Return spherical harmonics coefficients as a numpy array.

        Usage
        -----
        coeffs = x.to_array([normalization, csphase, lmax])

        Returns
        -------
        coeffs : ndarry, shape (2, lmax+1, lmax+1)
            numpy ndarray of the spherical harmonic coefficients.

        Parameters
        ----------
        normalization : str, optional, default = x.normalization
            Normalization of the output coefficients. '4pi', 'ortho' or
            'schmidt' for geodesy 4pi normalized, orthonormalized, or Schmidt
            semi-normalized coefficients, respectively.
        csphase : int, optional, default = x.csphase
            Condon-Shortley phase convention: 1 to exclude the phase factor,
            or -1 to include it.
        lmax : int, optional, default = x.lmax
            Maximum spherical harmonic degree to output.
        """
        if normalization is None:
            normalization = self.normalization

        if csphase is None:
            csphase = self.csphase

        if type(normalization) != str:
            raise ValueError('normalization must be a string. ' +
                             'Input type was {:s}'
                             .format(str(type(normalization))))

        if normalization.lower() not in set(['4pi', 'ortho', 'schmidt']):
            raise ValueError(
                "normalization must be '4pi', 'ortho' " +
                "or 'schmidt'. Provided value was {:s}"
                .format(repr(normalization))
                )
        if csphase != 1 and csphase != -1:
            raise ValueError(
                "csphase must be 1 or -1. Input value was {:s}"
                .format(repr(csphase))
                )

        if lmax is not None:
            if lmax > self.lmax:
                raise ValueError('Output lmax is greater than the maximum ' +
                                 'degree of the coefficients. ' +
                                 'Output lmax = {:d}, lmax of coefficients ' +
                                 '= {:d}'.format(lmax, self.lmax))
        if lmax is None:
            lmax = self.lmax

        return self._to_array(
            output_normalization=normalization.lower(),
            output_csphase=csphase, lmax=lmax)

    # ---- Rotate the coordinate system ----
    def rotate(self, alpha, beta, gamma, degrees=True, dj_matrix=None):
        """
        Rotate the coordinate system used to express the spherical harmonic
        coefficients and return a new class instance.

        Usage
        -----
        x_rotated = x.rotate(alpha, beta, gamma, [degrees, dj_matrix])

        Returns
        -------
        x_rotated : SHCoeffs class instance

        Parameters
        ----------
        alpha, beta, gamma : float
            The three Euler rotation angles in degrees.
        degrees : bool, optional, default = True
            True if the Euler angles are in degrees, False if they are in
            radians.
        dj_matrix : ndarray, optional, default = None
            The djpi2 rotation matrix computed by a call to djpi2.

        Description
        -----------
        This method will take the spherical harmonic coefficients of a
        function, rotate the coordinate frame by the three Euler anlges, and
        output the spherical harmonic coefficients of the rotated function.

        The rotation of a coordinate system or body can be viewed in two
        complementary ways involving three successive rotations. Both methods
        have the same initial and final configurations, and the angles listed
        in both schemes are the same.

        Scheme A:

        (I) Rotation about the z axis by alpha.
        (II) Rotation about the new y axis by beta.
        (III) Rotation about the new z axis by gamma.

        Scheme B:

        (I) Rotation about the z axis by gamma.
        (II) Rotation about the initial y axis by beta.
        (III) Rotation about the initial z axis by alpha.

        The rotations can further be viewed either as a rotation of the
        coordinate system or the physical body. For a rotation of the
        coordinate system without rotation of the physical body, use

        (alpha, beta, gamma).

        For a rotation of the physical body without rotation of the coordinate
        system, use

        (-gamma, -beta, -alpha).

        To perform the inverse transform of (alpha, beta, gamma), use

        (-gamma, -beta, -alpha).

        Note that this routine uses the "y convention", where the second
        rotation is with respect to the new y axis. If alpha, beta, and gamma
        were orginally defined in terms of the "x convention", where the second
        rotation was with respect to the new x axis, the Euler angles according
        to the y convention would be

        alpha_y=alpha_x-pi/2, beta_x=beta_y, and gamma_y=gamma_x+pi/2.
        """
        if degrees:
            angles = _np.radians([alpha, beta, gamma])
        else:
            angles = _np.array([alpha, beta, gamma])

        rot = self._rotate(angles, dj_matrix)
        return rot

    # ---- Convert spherical harmonic coefficients to a different normalization
    def convert(self, normalization=None, csphase=None, lmax=None, kind=None,
                check=True):
        """
        Return a SHCoeff class instance with a different normalization
        convention.

        Usage
        -----
        clm = x.convert([normalization, csphase, lmax, kind, check])

        Returns
        -------
        clm : SHCoeffs class instance

        Parameters
        ----------
        normalization : str, optional, default = x.normalization
            Normalization of the output class: '4pi', 'ortho' or 'schmidt'
            for geodesy 4pi normalized, orthonormalized, or Schmidt semi-
            normalized coefficients, respectively.
        csphase : int, optional, default = x.csphase
            Condon-Shortley phase convention for the output class: 1 to exclude
            the phase factor, or -1 to include it.
        lmax : int, optional, default = x.lmax
            Maximum spherical harmonic degree to output.
        kind : str, optional, default = clm.kind
            'real' or 'complex' spherical harmonic coefficients for the output
            class.
        check : bool, optional, default = True
            When converting complex coefficients to real coefficients, if True,
            check if function is entirely real.
        """
        if normalization is None:
            normalization = self.normalization
        if csphase is None:
            csphase = self.csphase
        if lmax is None:
            lmax = self.lmax
        if kind is None:
            kind = self.kind

        # check argument consistency
        if type(normalization) != str:
            raise ValueError('normalization must be a string. ' +
                             'Input type was {:s}'
                             .format(str(type(normalization))))
        if normalization.lower() not in set(['4pi', 'ortho', 'schmidt']):
            raise ValueError(
                "normalization must be '4pi', 'ortho' " +
                "or 'schmidt'. Provided value was {:s}"
                .format(repr(normalization))
                )
        if csphase != 1 and csphase != -1:
            raise ValueError(
                "csphase must be 1 or -1. Input value was {:s}"
                .format(repr(csphase))
                )

        if (kind != self.kind):
            if (kind == 'complex'):
                temp = self._make_complex()
            else:
                temp = self._make_real(check=check)
            coeffs = temp.to_array(normalization=normalization.lower(),
                                   csphase=csphase, lmax=lmax)
        else:
            coeffs = self.to_array(normalization=normalization.lower(),
                                   csphase=csphase, lmax=lmax)

        # because to_array is already a copy, we can pass it as reference
        # to save time
        return SHCoeffs.from_array(coeffs,
                                   normalization=normalization.lower(),
                                   csphase=csphase, copy=False)

    # ---- Expand the coefficients onto a grid ----
    def expand(self, grid='DH', **kwargs):
        """
        Evaluate the spherical harmonic coefficients on a spherical grid.

        Usage
        -----
        f = x.expand([grid, lmax, lmax_calc, zeros])

        Returns
        -------
        f : SHGrid class instance

        Parameters
        ----------
        grid : str, optional, default = 'DH'
            'DH' or 'DH1' for an equisampled lat/lon grid with nlat=nlon,
            'DH2' for an equidistant lat/lon grid with nlon=2*nlat, or 'GLQ'
            for a Gauss-Legendre quadrature grid.
        lmax : int, optional, default = x.lmax
            The maximum spherical harmonic degree, which determines the grid
            spacing of the output grid.
        lmax_calc : int, optional, default = x.lmax
            The maximum spherical harmonic degree to use when evaluating the
            function.
        zeros : ndarray, optional, default = None
            The cos(colatitude) nodes used in the Gauss-Legendre Quadrature
            grids.

        Description
        -----------
        For more information concerning the spherical harmonic expansions, and
        the properties of the output grids, see the documentation for
        SHExpandDH, SHExpandDHC, SHExpandGLQ and SHExpandGLQC.
        """
        if type(grid) != str:
            raise ValueError('grid must be a string. ' +
                             'Input type was {:s}'
                             .format(str(type(grid))))

        if grid.upper() == 'DH' or grid.upper() == 'DH1':
            gridout = self._expandDH(sampling=1, **kwargs)
        elif grid.upper() == 'DH2':
            gridout = self._expandDH(sampling=2, **kwargs)
        elif grid.upper() == 'GLQ':
            gridout = self._expandGLQ(zeros=None, **kwargs)
        else:
            raise ValueError(
                "grid must be 'DH', 'DH1', 'DH2', or 'GLQ'. " +
                "Input value was {:s}".format(repr(grid)))

        return gridout

    # ---- plotting routines ----
    def plot_spectrum(self, convention='power', unit='per_l', base=10.,
                      xscale='lin', yscale='log', show=True, fname=None):
        """
        Plot the spectrum as a function of spherical harmonic degree.

        Usage
        -----
        x.plot_spectrum([convention, unit, base, xscale, yscale, show, fname])

        Parameters
        ----------
        convention : str, optional, default = 'power'
            The type of spectrum to plot: 'power' for power spectrum,
            'energy' for energy spectrum, and 'l2norm' for the l2 norm
            spectrum.
        unit : str, optional, default = 'per_l'
            If 'per_l', plot the total contribution to the spectrum for each
            spherical harmonic degree l. If 'per_lm', plot the average
            contribution to the spectrum for each coefficient at spherical
            harmonic degree l. If 'per_dlogl', plot the spectrum per log
            interval dlog_a(l).
        base : float, optional, default = 10.
            The logarithm base when calculating the 'per_dlogl' power spectrum.
        xscale : str, optional, default = 'lin'
            Scale of the x axis: 'lin' for linear or 'log' for logarithmic.
        yscale : str, optional, default = 'log'
            Scale of the y axis: 'lin' for linear or 'log' for logarithmic.
        show : bool, optional, default = True
            If True, plot to the screen.
        fname : str, optional, default = None
            If present, save the image to the file.
        """
        spectrum = self.spectrum(convention=convention, unit=unit, base=base)
        ls = self.degrees()

        fig, ax = _plt.subplots(1, 1)
        ax.set_xlabel('degree l')
        if convention == 'energy':
            ax.set_ylabel('energy')
            if (unit == 'per_l'):
                legend = 'energy per degree'
            elif (unit == 'per_lm'):
                legend = 'energy per coefficient'
            elif (unit == 'per_dlogl'):
                legend = 'energy per log bandwidth'
        elif convention == 'l2norm':
            ax.set_ylabel('l2 norm')
            if (unit == 'per_l'):
                legend = 'l2 norm per degree'
            elif (unit == 'per_lm'):
                legend = 'l2 norm per coefficient'
            elif (unit == 'per_dlogl'):
                legend = 'l2 norm per log bandwidth'
        else:
            ax.set_ylabel('power')
            if (unit == 'per_l'):
                legend = 'power per degree'
            elif (unit == 'per_lm'):
                legend = 'power per coefficient'
            elif (unit == 'per_dlogl'):
                legend = 'power per log bandwidth'

        ax.grid(True, which='both')

        if xscale == 'log':
            ax.set_xscale('log', basex=base)
        if yscale == 'log':
            ax.set_yscale('log', basey=base)

        if xscale == 'log':
            ax.plot(ls[1:], spectrum[1:], label=legend)
        else:
            ax.plot(ls, spectrum, label=legend)
        ax.legend()

        if show:
            _plt.show()
        if fname is not None:
            fig.savefig(fname)
        return fig, ax

    def plot_spectrum2d(self, convention='power', xscale='lin', yscale='lin',
                        vscale='log', vrange=(1.e-5, 1.0), show=True,
                        fname=None):
        """
        Plot the spectrum of all spherical harmonic coefficients.

        Usage
        -----
        x.plot_spectrum2d([convention, xscale, yscale, vscale, vrange, show,
                           fname])

        Parameters
        ----------
        convention : str, optional, default = 'power'
            The type of spectrum to plot: 'power' for power spectrum,
            'energy' for energy spectrum, and 'l2norm' for the l2 norm
            spectrum.
        xscale : str, optional, default = 'lin'
            Scale of the l axis: 'lin' for linear or 'log' for logarithmic.
        yscale : str, optional, default = 'lin'
            Scale of the m axis: 'lin' for linear or 'log' for logarithmic.
        vscale : str, optional, default = 'log'
            Scale of the color axis: 'lin' for linear or 'log' for logarithmic.
        vrange : (float, float), optional, default = (1.e-5, 1.)
            Colormap range relative to the maximum power.
        show : bool, optional, default = True
            If True, plot to the screen.
        fname : str, optional, default = None
            If present, save the image to the file.
        """
        # Create the matrix of the spectrum for each coefficient
        spectrum = _np.empty((self.lmax + 1, 2 * self.lmax + 1))
        mpositive = _np.abs(self.coeffs[0])**2
        mpositive[~self.mask[0]] = _np.nan
        mnegative = _np.abs(self.coeffs[1])**2
        mnegative[~self.mask[1]] = _np.nan

        spectrum[:, :self.lmax] = _np.fliplr(mnegative)[:, :self.lmax]
        spectrum[:, self.lmax:] = mpositive

        if (convention.lower() == 'l2norm'):
            pass
        elif (convention.lower() == 'power' or convention.lower() == 'energy'):
            if self.normalization == '4pi':
                pass
            elif self.normalization == 'schmidt':
                for l in self.degrees():
                    spectrum[l, :] /= (2.0 * l + 1.0)
            elif self.normalization == 'ortho':
                for l in self.degrees():
                    spectrum[l, :] /= (4.0 * _np.pi)
            else:
                raise ValueError(
                    "normalization must be '4pi', 'ortho', or 'schmidt'. " +
                    "Input value was {:s}".format(repr(self.normalization)))
        else:
            raise ValueError(
                "convention must be 'power', 'energy', or 'l2norm'. " +
                "Input value was {:s}".format(repr(convention)))

        if convention == 'energy':
            spectrum *= 4.0 * _np.pi

        spectrum_masked = _np.ma.masked_invalid(spectrum)

        # need to add one extra value to each in order for pcolormesh
        # to plot the last row and column.
        ls = _np.arange(self.lmax+2).astype(_np.float)
        ms = _np.arange(-self.lmax, self.lmax + 2, dtype=_np.float)
        lgrid, mgrid = _np.meshgrid(ls, ms, indexing='ij')
        lgrid -= 0.5
        mgrid -= 0.5

        fig, ax = _plt.subplots()
        vmin = _np.nanmax(spectrum) * vrange[0]
        vmax = _np.nanmax(spectrum) * vrange[1]

        if vscale.lower() == 'log':
            norm = _mpl.colors.LogNorm(vmin, vmax, clip=True)
            # Clipping is required to avoid an invalid value error
        elif vscale.lower() == 'lin':
            norm = _plt.Normalize(vmin, vmax)
        else:
            raise ValueError(
                "vscale must be 'lin' or 'log'. " +
                "Input value was {:s}".format(repr(vscale)))

        if (xscale == 'lin'):
            cmesh = ax.pcolormesh(lgrid, mgrid, spectrum_masked,
                                  norm=norm, cmap='viridis')
            ax.set(xlim=(-0.5, self.lmax + 0.5))
        elif (xscale == 'log'):
            cmesh = ax.pcolormesh(lgrid[1:], mgrid[1:], spectrum_masked[1:],
                                  norm=norm, cmap='viridis')
            ax.set(xscale='log', xlim=(1., self.lmax + 0.5))
        else:
            raise ValueError(
                "xscale must be 'lin' or 'log'. " +
                "Input value was {:s}".format(repr(xscale)))

        if (yscale == 'lin'):
            ax.set(ylim=(-self.lmax - 0.5, self.lmax + 0.5))
        elif (yscale == 'log'):
            ax.set(yscale='symlog', ylim=(-self.lmax - 0.5, self.lmax + 0.5))
        else:
            raise ValueError(
                "yscale must be 'lin' or 'log'. " +
                "Input value was {:s}".format(repr(yscale)))

        if (convention == 'energy'):
            _plt.colorbar(cmesh, label='energy per coefficient')
        elif (convention == 'power'):
            _plt.colorbar(cmesh, label='power per coefficient')
        else:
            _plt.colorbar(cmesh, label='magnitude-squared coefficient')
        ax.set(xlabel='degree l', ylabel='order m')
        ax.grid(True, which='both')

        if show:
            _plt.show()
        if fname is not None:
            fig.savefig(fname)
        return fig, ax

    def info(self):
        """
        Print a summary of the data stored in the SHCoeffs instance.

        Usage
        -----
        x.info()
        """
        print('kind = {:s}\nnormalization = {:s}\n'
              'csphase = {:d}\nlmax = {:d}'.format(
                  repr(self.kind), repr(self.normalization), self.csphase,
                  self.lmax))


# ================== REAL SPHERICAL HARMONICS ================

class SHRealCoeffs(SHCoeffs):
    """Real Spherical Harmonics Coefficient class."""

    @staticmethod
    def istype(kind):
        """Test if class is Real or Complex."""
        return kind == 'real'

    def __init__(self, coeffs, normalization='4pi', csphase=1, copy=True):
        """Initialize Real SH Coefficients."""
        lmax = coeffs.shape[1] - 1
        # ---- create mask to filter out m<=l ----
        mask = _np.zeros((2, lmax + 1, lmax + 1), dtype=_np.bool)
        mask[0, 0, 0] = True
        for l in _np.arange(lmax + 1):
            mask[:, l, :l + 1] = True
        mask[1, :, 0] = False
        self.mask = mask
        self.lmax = lmax
        self.kind = 'real'
        self.normalization = normalization
        self.csphase = csphase

        if copy:
            self.coeffs = _np.copy(coeffs)
            self.coeffs[~mask] = 0.
        else:
            self.coeffs = coeffs

    def _make_complex(self):
        """Convert the real SHCoeffs class to the complex class."""
        rcomplex_coeffs = _shtools.SHrtoc(self.coeffs,
                                          convention=1, switchcs=0)

        # These coefficients are using real floats, and need to be
        # converted to complex form.
        complex_coeffs = _np.zeros((2, self.lmax+1, self.lmax+1),
                                   dtype='complex')
        complex_coeffs[0, :, :] = (rcomplex_coeffs[0, :, :] + 1j *
                                   rcomplex_coeffs[1, :, :])
        complex_coeffs[1, :, :] = complex_coeffs[0, :, :].conjugate()
        for m in self.degrees():
            if m % 2 == 1:
                complex_coeffs[1, :, m] = - complex_coeffs[1, :, m]

        # complex_coeffs is initialized in this function and can be
        # passed as reference
        return SHCoeffs.from_array(complex_coeffs,
                                   normalization=self.normalization,
                                   csphase=self.csphase, copy=False)

    def _spectrum(self, convention='power', unit='per_l', base=10.):
        """Return the spectrum."""
        if convention.lower() == 'l2norm':
            spectrum = _shtools.SHPowerSpectrum(self.coeffs)
        elif (convention.lower() == 'power' or convention.lower() == 'energy'):
            if self.normalization == '4pi':
                spectrum = _shtools.SHPowerSpectrum(self.coeffs)
            elif self.normalization == 'schmidt':
                spectrum = _shtools.SHPowerSpectrum(self.coeffs)
                l = self.degrees()
                spectrum /= (2.0 * l + 1.0)
            elif self.normalization == 'ortho':
                spectrum = _shtools.SHPowerSpectrum(self.coeffs) / \
                           (4.0 * _np.pi)
            else:
                raise ValueError(
                    "normalization must be '4pi', 'ortho', or 'schmidt'. " +
                    "Input value was {:s}".format(repr(self.normalization)))
        else:
            raise ValueError(
                "convention must be 'power', 'energy', or 'l2norm'. " +
                "Input value was {:s}".format(repr(convention)))

        if convention.lower() == 'energy':
            spectrum *= 4.0 * _np.pi

        if (unit.lower() == 'per_l'):
            pass
        elif (unit.lower() == 'per_lm'):
            l = self.degrees()
            spectrum /= (2.0 * l + 1.0)
        elif (unit.lower() == 'per_dlogl'):
            l = self.degrees()
            spectrum *= l * _np.log(base)
        else:
            raise ValueError(
                "unit must be 'per_l', 'per_lm', or 'per_dlogl'." +
                "Input value was {:s}".format(repr(unit)))
        return spectrum

    def _to_array(self, output_normalization, output_csphase, lmax):
        """Return coefficients with a different normalization convention."""
        coeffs = _np.copy(self.coeffs[:, :lmax+1, :lmax+1])
        degrees = _np.arange(lmax + 1)

        if self.normalization == output_normalization:
            pass
        elif (self.normalization == '4pi' and
              output_normalization == 'schmidt'):
            for l in degrees:
                coeffs[:, l, :l+1] *= _np.sqrt(2.0 * l + 1.0)
        elif self.normalization == '4pi' and output_normalization == 'ortho':
            coeffs *= _np.sqrt(4.0 * _np.pi)
        elif (self.normalization == 'schmidt' and
              output_normalization == '4pi'):
            for l in degrees:
                coeffs[:, l, :l+1] /= _np.sqrt(2.0 * l + 1.0)
        elif (self.normalization == 'schmidt' and
              output_normalization == 'ortho'):
            for l in degrees:
                coeffs[:, l, :l+1] *= _np.sqrt(4.0 * _np.pi / (2.0 * l + 1.0))
        elif self.normalization == 'ortho' and output_normalization == '4pi':
            coeffs /= _np.sqrt(4.0 * _np.pi)
        elif (self.normalization == 'ortho' and
              output_normalization == 'schmidt'):
            for l in degrees:
                coeffs[:, l, :l+1] *= _np.sqrt((2.0 * l + 1.0) /
                                               (4.0 * _np.pi))

        if output_csphase != self.csphase:
            for m in degrees:
                if m % 2 == 1:
                    coeffs[:, :, m] = - coeffs[:, :, m]

        return coeffs

    def _rotate(self, angles, dj_matrix):
        """Rotate the coefficients by the Euler angles alpha, beta, gamma."""
        if dj_matrix is None:
            dj_matrix = _shtools.djpi2(self.lmax + 1)

        # The coefficients need to be 4pi normalized with csphase = 1
        coeffs = _shtools.SHRotateRealCoef(
            self.to_array(normalization='4pi', csphase=1), angles, dj_matrix)

        # Convert 4pi normalized coefficients to the same normalization
        # as the unrotated coefficients. The returned class can take
        # coeffs as reference because it is already copied in the rotation
        # routine.
        if self.normalization != '4pi' or self.csphase != 1:
            temp = SHCoeffs.from_array(coeffs, kind='real')
            tempcoeffs = temp.to_array(
                normalization=self.normalization, csphase=self.csphase)
            return SHCoeffs.from_array(
                tempcoeffs, normalization=self.normalization,
                csphase=self.csphase, copy=False)
        else:
            return SHCoeffs.from_array(coeffs, copy=False)

    def _expandDH(self, sampling, **kwargs):
        """Evaluate the coefficients on a Driscoll and Healy (1994) grid."""
        if self.normalization == '4pi':
            norm = 1
        elif self.normalization == 'schmidt':
            norm = 2
        elif self.normalization == 'ortho':
            norm = 4
        else:
            raise ValueError(
                "Normalization must be '4pi', 'ortho', or 'schmidt'. " +
                "Input value was {:s}".format(repr(self.normalization)))

        data = _shtools.MakeGridDH(self.coeffs, sampling=sampling, norm=norm,
                                   csphase=self.csphase, **kwargs)
        gridout = SHGrid.from_array(data, grid='DH', copy=False)
        return gridout

    def _expandGLQ(self, zeros, **kwargs):
        """Evaluate the coefficients on a Gauss Legendre quadrature grid."""
        if self.normalization == '4pi':
            norm = 1
        elif self.normalization == 'schmidt':
            norm = 2
        elif self.normalization == 'ortho':
            norm = 4
        else:
            raise ValueError(
                "Normalization must be '4pi', 'ortho', or 'schmidt'. " +
                "Input value was {:s}".format(repr(self.normalization)))

        if zeros is None:
            zeros, weights = _shtools.SHGLQ(self.lmax)

        data = _shtools.MakeGridGLQ(self.coeffs, zeros, norm=norm,
                                    csphase=self.csphase, **kwargs)
        gridout = SHGrid.from_array(data, grid='GLQ', copy=False)
        return gridout


# =============== COMPLEX SPHERICAL HARMONICS ================

class SHComplexCoeffs(SHCoeffs):
    """Complex Spherical Harmonics Coefficients class."""

    @staticmethod
    def istype(kind):
        """Check if class has kind 'real' or 'complex'."""
        return kind == 'complex'

    def __init__(self, coeffs, normalization='4pi', csphase=1, copy=True):
        """Initialize Complex coefficients."""
        lmax = coeffs.shape[1] - 1
        # ---- create mask to filter out m<=l ----
        mask = _np.zeros((2, lmax + 1, lmax + 1), dtype=_np.bool)
        mask[0, 0, 0] = True
        for l in _np.arange(lmax + 1):
            mask[:, l, :l + 1] = True
        mask[1, :, 0] = False

        self.mask = mask
        self.lmax = lmax
        self.kind = 'complex'
        self.normalization = normalization
        self.csphase = csphase

        if copy:
            self.coeffs = _np.copy(coeffs)
            self.coeffs[~mask] = 0.
        else:
            self.coeffs = coeffs

    def _make_real(self, check=True):
        """Convert the complex SHCoeffs class to the real class."""
        # Test if the coefficients correspond to a real grid.
        # This is not very elegant, and the equality condition
        # is probably not robust to round off errors.
        if check:
            for l in self.degrees():
                if self.coeffs[0, l, 0] != self.coeffs[0, l, 0].conjugate():
                    raise RuntimeError('Complex coefficients do not ' +
                                       'correspond to a real field. ' +
                                       'l = {:d}, m = 0: {:e}'
                                       .format(l, self.coeffs[0, l, 0]))
                for m in _np.arange(1, l + 1):
                    if m % 2 == 1:
                        if (self.coeffs[0, l, m] != -
                                self.coeffs[1, l, m].conjugate()):
                            raise RuntimeError('Complex coefficients do not ' +
                                               'correspond to a real field. ' +
                                               'l = {:d}, m = {:d}: {:e}, {:e}'
                                               .format(
                                                   l, m, self.coeffs[0, l, 0],
                                                   self.coeffs[1, l, 0]))
                    else:
                        if (self.coeffs[0, l, m] !=
                                self.coeffs[1, l, m].conjugate()):
                            raise RuntimeError('Complex coefficients do not ' +
                                               'correspond to a real field. ' +
                                               'l = {:d}, m = {:d}: {:e}, {:e}'
                                               .format(
                                                   l, m, self.coeffs[0, l, 0],
                                                   self.coeffs[1, l, 0]))

        coeffs_rc = _np.zeros((2, self.lmax + 1, self.lmax + 1))
        coeffs_rc[0, :, :] = self.coeffs[0, :, :].real
        coeffs_rc[1, :, :] = self.coeffs[0, :, :].imag
        real_coeffs = _shtools.SHctor(coeffs_rc, convention=1,
                                      switchcs=0)
        return SHCoeffs.from_array(real_coeffs,
                                   normalization=self.normalization,
                                   csphase=self.csphase)

    def _spectrum(self, convention='power', unit='per_l', base=10.):
        """Return the spectrum."""
        if convention.lower() == 'l2norm':
            spectrum = _shtools.SHPowerSpectrumC(self.coeffs)
        elif (convention.lower() == 'power' or convention.lower() == 'energy'):
            if self.normalization == '4pi':
                spectrum = _shtools.SHPowerSpectrumC(self.coeffs)
            elif self.normalization == 'schmidt':
                spectrum = _shtools.SHPowerSpectrumC(self.coeffs)
                l = self.degrees()
                spectrum /= (2.0 * l + 1.0)
            elif self.normalization == 'ortho':
                spectrum = _shtools.SHPowerSpectrumC(self.coeffs) / \
                           (4.0 * _np.pi)
            else:
                raise ValueError(
                    "normalization must be '4pi', 'ortho', or 'schmidt'. " +
                    "Input value was {:s}".format(repr(self.normalization)))
        else:
            raise ValueError(
                "convention must be 'power', 'energy', or 'l2norm'. " +
                "Input value was {:s}".format(repr(convention)))

        if convention.lower() == 'energy':
            spectrum *= 4.0 * _np.pi

        if (unit.lower() == 'per_l'):
            pass
        elif (unit.lower() == 'per_lm'):
            l = self.degrees()
            spectrum /= (2.0 * l + 1.0)
        elif (unit.lower() == 'per_dlogl'):
            l = self.degrees()
            spectrum *= l * _np.log(base)
        else:
            raise ValueError(
                "unit must be 'per_l', 'per_lm', or 'per_dlogl'." +
                "Input value was {:s}".format(repr(unit)))
        return spectrum

    def _to_array(self, output_normalization, output_csphase, lmax):
        """Return coefficients with a different normalization convention."""
        coeffs = _np.copy(self.coeffs[:, :lmax+1, :lmax+1])
        degrees = _np.arange(lmax + 1)

        if self.normalization == output_normalization:
            pass
        elif (self.normalization == '4pi' and
              output_normalization == 'schmidt'):
            for l in degrees:
                coeffs[:, l, :l+1] *= _np.sqrt(2.0 * l + 1.0)
        elif self.normalization == '4pi' and output_normalization == 'ortho':
            coeffs *= _np.sqrt(4.0 * _np.pi)
        elif (self.normalization == 'schmidt' and
              output_normalization == '4pi'):
            for l in degrees:
                coeffs[:, l, :l+1] /= _np.sqrt(2.0 * l + 1.0)
        elif (self.normalization == 'schmidt' and
              output_normalization == 'ortho'):
            for l in degrees:
                coeffs[:, l, :l+1] *= _np.sqrt(4.0 * _np.pi / (2.0 * l + 1.0))
        elif self.normalization == 'ortho' and output_normalization == '4pi':
            coeffs /= _np.sqrt(4.0 * _np.pi)
        elif (self.normalization == 'ortho' and
              output_normalization == 'schmidt'):
            for l in degrees:
                coeffs[:, l, :l+1] *= _np.sqrt((2.0 * l + 1.0) /
                                               (4.0 * _np.pi))

        if output_csphase != self.csphase:
            for m in degrees:
                if m % 2 == 1:
                    coeffs[:, :, m] = - coeffs[:, :, m]

        return coeffs

    def _rotate(self, angles, dj_matrix):
        """Rotate the coefficients by the Euler angles alpha, beta, gamma."""
        # Note that the current method is EXTREMELY inefficient. The complex
        # coefficients are expanded onto real and imaginary grids, each of
        # the two components are rotated separately as real data, they rotated
        # real data are re-expanded on new real and complex grids, they are
        # combined to make a complex grid, and the resultant is expanded
        # in complex spherical harmonics.
        if dj_matrix is None:
            dj_matrix = _shtools.djpi2(self.lmax + 1)

        cgrid = self.expand(grid='DH')
        rgrid, igrid = cgrid.data.real, cgrid.data.imag
        rgridcoeffs = _shtools.SHExpandDH(rgrid, norm=1, sampling=1, csphase=1)
        igridcoeffs = _shtools.SHExpandDH(igrid, norm=1, sampling=1, csphase=1)

        rgridcoeffs_rot = _shtools.SHRotateRealCoef(
            rgridcoeffs, angles, dj_matrix)
        igridcoeffs_rot = _shtools.SHRotateRealCoef(
            igridcoeffs, angles, dj_matrix)

        rgrid_rot = _shtools.MakeGridDH(rgridcoeffs_rot, norm=1,
                                        sampling=1, csphase=1)
        igrid_rot = _shtools.MakeGridDH(igridcoeffs_rot, norm=1,
                                        sampling=1, csphase=1)
        grid_rot = rgrid_rot + 1j * igrid_rot

        if self.normalization == '4pi':
            norm = 1
        elif self.normalization == 'schmidt':
            norm = 2
        elif self.normalization == 'ortho':
            norm = 4
        else:
            raise ValueError(
                "Normalization must be '4pi', 'ortho', or 'schmidt'")

        coeffs_rot = _shtools.SHExpandDHC(grid_rot, norm=norm,
                                          csphase=self.csphase)

        return SHCoeffs.from_array(coeffs_rot,
                                   normalization=self.normalization,
                                   csphase=self.csphase, copy=False)

    def _expandDH(self, sampling, **kwargs):
        """Evaluate the coefficients on a Driscoll and Healy (1994) grid."""
        if self.normalization == '4pi':
            norm = 1
        elif self.normalization == 'schmidt':
            norm = 2
        elif self.normalization == 'ortho':
            norm = 4
        else:
            raise ValueError(
                "Normalization must be '4pi', 'ortho', or 'schmidt'. " +
                "Input value was {:s}".format(repr(self.normalization)))

        data = _shtools.MakeGridDHC(self.coeffs, sampling=sampling,
                                    norm=norm, csphase=self.csphase, **kwargs)
        gridout = SHGrid.from_array(data, grid='DH', copy=False)
        return gridout

    def _expandGLQ(self, zeros, **kwargs):
        """Evaluate the coefficients on a Gauss-Legendre quadrature grid."""
        if self.normalization == '4pi':
            norm = 1
        elif self.normalization == 'schmidt':
            norm = 2
        elif self.normalization == 'ortho':
            norm = 4
        else:
            raise ValueError(
                "Normalization must be '4pi', 'ortho', or 'schmidt'. " +
                "Input value was {:s}".format(repr(self.normalization)))

        if zeros is None:
            zeros, weights = _shtools.SHGLQ(self.lmax)

        data = _shtools.MakeGridGLQC(self.coeffs, zeros, norm=norm,
                                     csphase=self.csphase, **kwargs)
        gridout = SHGrid.from_array(data, grid='GLQ', copy=False)
        return gridout


# ========================================================================
# ======      GRID CLASSES      ==========================================
# ========================================================================

class SHGrid(object):
    """
    Class for spatial gridded data on the sphere.

    Grids can be initialized from:

    >>> x = SHGrid.from_array(array)
    >>> x = SHGrid.from_file('fname.dat')

    The class instance defines the following class attributes:

    data       : Gridded array of the data.
    nlat, nlon : The number of latitude and longitude bands in the grid.
    lmax       : The maximum spherical harmonic degree that can be resolved
                 by the grid sampling.
    sampling   : For Driscoll and Healy grids, the longitudinal sampling
                 of the grid. Either nlong=nlat or nlong=2*nlat.
    kind       : Either 'complex' or 'real' for the data type.
    grid       : Either 'DH' or 'GLQ' for Driscoll and Healy grids or Gauss-
                 Legendre Quadrature grids.
    zeros      : The cos(colatitude) nodes used with Gauss-Legendre
                 Quadrature grids. Default is None.
    weights    : The latitudinal weights used with Gauss-Legendre
                 Quadrature grids. Default is None.

    Each class instance provides the following methods:

    to_grid()   : Return the raw gridded data as a numpy array.
    to_file()   : Save gridded data to a text or binary file.
    lats()      : Return a vector containing the latitudes of each row
                  of the gridded data.
    lons()      : Return a vector containing the longitudes of each column
                  of the gridded data.
    expand()    : Expand the grid into spherical harmonics.
    copy()      : Return a copy of the class instance.
    plot()      : Plot the raw data using a simple cylindrical projection.
    plot3d      : Plot the raw data on a 3d sphere.
    info()      : Print a summary of the data stored in the SHGrid instance.
    """

    def __init__():
        """Unused constructor of the super class."""
        print('Initialize the class using one of the class methods:\n'
              '>>> SHGrid.from_array?\n'
              '>>> SHGrid.from_file?\n')

    # ---- factory methods
    @classmethod
    def from_array(self, array, grid='DH', copy=True):
        """
        Initialize the class instance from an input array.

        Usage
        -----
        x = SHGrid.from_array(array, [grid, copy])

        Returns
        -------
        x : SHGrid class instance

        Parameters
        ----------
        array : ndarray, shape (nlat, nlon)
            2-D numpy array of the gridded data, where nlat and nlon are the
            number of latitudinal and longitudinal bands, respectively.
        grid : str, optional, default = 'DH'
            'DH' or 'GLQ' for Driscoll and Healy grids or Gauss Legendre
            Quadrature grids, respectively.
        copy : bool, optional, default = True
            If True (default), make a copy of array when initializing the class
            instance. If False, initialize the class instance with a reference
            to array.
        """
        if _np.iscomplexobj(array):
            kind = 'complex'
        else:
            kind = 'real'

        if type(grid) != str:
            raise ValueError('grid must be a string. ' +
                             'Input type was {:s}'
                             .format(str(type(grid))))

        if grid.upper() not in set(['DH', 'GLQ']):
            raise ValueError(
                "grid must be 'DH' or 'GLQ'. Input value was {:s}."
                .format(repr(grid))
                )

        for cls in self.__subclasses__():
            if cls.istype(kind) and cls.isgrid(grid):
                return cls(array, copy=copy)

    @classmethod
    def from_file(self, fname, binary=False, **kwargs):
        """
        Initialize the class instance from gridded data in a file.

        Usage
        -----
        x = SHGrid.from_file(fname, [binary, **kwargs])

        Returns
        -------
        x : SHGrid class instance

        Parameters
        ----------
        fname : str
            The filename containing the gridded data. For text files (default)
            the file is read using the numpy routine loadtxt(), whereas for
            binary files, the file is read using numpy.load(). The dimensions
            of the array must be nlon=nlat or nlon=2*nlat for Driscoll and
            Healy grids, or nlon=2*nlat-1 for Gauss-Legendre Quadrature grids.
        binary : bool, optional, default = False
            If False, read a text file. If True, read a binary 'npy' file.
        **kwargs : keyword arguments, optional
            Keyword arguments of numpy.loadtxt() or numpy.load().
        """
        if binary is False:
            data = _np.loadtxt(fname, **kwargs)
        elif binary is True:
            data = _np.load(fname, **kwargs)
        else:
            raise ValueError('binary must be True or False. '
                             'Input value is {:s}'.format(binary))

        if _np.iscomplexobj(data):
            kind = 'complex'
        else:
            kind = 'real'

        if (data.shape[1] == data.shape[0]) or (data.shape[1] ==
                                                2 * data.shape[0]):
            grid = 'DH'
        elif data.shape[1] == 2 * data.shape[0] - 1:
            grid = 'GLQ'
        else:
            raise ValueError('Input grid must be dimensioned as ' +
                             '(nlat, nlon). For DH grids, nlon = nlat or ' +
                             'nlon = 2 * nlat. For GLQ grids, nlon = ' +
                             '2 * nlat - 1. Input dimensions are nlat = ' +
                             '{:d}, nlon = {:d}'.format(data.shape[0],
                                                        data.shape[1]))

        for cls in self.__subclasses__():
            if cls.istype(kind) and cls.isgrid(grid):
                return cls(data)

    def copy(self):
        """Return a deep copy of the class instance."""
        return _copy.deepcopy(self)

    def to_file(self, filename, binary=False, **kwargs):
        """
        Save gridded data to a file.

        Usage
        -----
        x.to_file(filename, [binary, **kwargs])

        Parameters
        ----------
        filename : str
            Name of output file. For text files (default), the file will be
            saved automatically in gzip compressed format if the filename ends
            in .gz.
        binary : bool, optional, default = False
            If False, save as text using numpy.savetxt(). If True, save as a
            'npy' binary file using numpy.save().
        **kwargs : keyword arguments, optional
            Keyword arguments of numpy.savetxt() and numpy.save().
        """
        if binary is False:
            _np.savetxt(filename, self.data, **kwargs)
        elif binary is True:
            _np.save(filename, self.data, **kwargs)
        else:
            raise ValueError('binary must be True or False. '
                             'Input value is {:s}'.format(binary))

    # ---- operators ----
    def __add__(self, other):
        """Add two similar grids or a grid and a scaler: self + other."""
        if isinstance(other, SHGrid):
            if (self.grid == other.grid and self.data.shape ==
                    other.data.shape and self.kind == other.kind):
                data = self.data + other.data
                return SHGrid.from_array(data, grid=self.grid)
            else:
                raise ValueError('The two grids must be of the ' +
                                 'same kind and have the same shape.')
        elif _np.isscalar(other) is True:
            data = self.data + other
            return SHGrid.from_array(data, grid=self.grid)
        else:
            raise NotImplementedError('Mathematical operator not implemented' +
                                      'for these operands.')

    def __radd__(self, other):
        """Add two similar grids or a grid and a scaler: self + other."""
        return self.__add__(other)

    def __sub__(self, other):
        """Subtract two similar grids or a grid and a scaler: self - other."""
        if isinstance(other, SHGrid):
            if (self.grid == other.grid and self.data.shape ==
                    other.data.shape and self.kind == other.kind):
                data = self.data - other.data
                return SHGrid.from_array(data, grid=self.grid)
            else:
                raise ValueError('The two grids must be of the ' +
                                 'same kind and have the same shape.')
        elif _np.isscalar(other) is True:
            data = self.data - other
            return SHGrid.from_array(data, grid=self.grid)
        else:
            raise NotImplementedError('Mathematical operator not implemented' +
                                      'for these operands.')

    def __rsub__(self, other):
        """Subtract two similar grids or a grid and a scaler: other - self."""
        if isinstance(other, SHGrid):
            if (self.grid == other.grid and self.data.shape ==
                    other.data.shape and self.kind == other.kind):
                data = other.data - self.data
                return SHGrid.from_array(data, grid=self.grid)
            else:
                raise ValueError('The two grids must be of the ' +
                                 'same kind and have the same shape.')
        elif _np.isscalar(other) is True:
            data = other - self.data
            return SHGrid.from_array(data, grid=self.grid)
        else:
            raise NotImplementedError('Mathematical operator not implemented' +
                                      'for these operands.')

    def __mul__(self, other):
        """Multiply two similar grids or a grid and a scaler: self * other."""
        if isinstance(other, SHGrid):
            if (self.grid == other.grid and self.data.shape ==
                    other.data.shape and self.kind == other.kind):
                data = self.data * other.data
                return SHGrid.from_array(data, grid=self.grid)
            else:
                raise ValueError('The two grids must be of the ' +
                                 'same kind and have the same shape.')
        elif _np.isscalar(other) is True:
            data = self.data * other
            return SHGrid.from_array(data, grid=self.grid)
        else:
            raise NotImplementedError('Mathematical operator not implemented' +
                                      'for these operands.')

    def __rmul__(self, other):
        """Multiply two similar grids or a grid and a scaler: other * self."""
        return self.__mul__(other)

    def __div__(self, other):
        """
        Divide two similar grids or a grid and a scalar, when
        __future__.division is not in effect.
        """
        if isinstance(other, SHGrid):
            if (self.grid == other.grid and self.data.shape ==
                    other.data.shape and self.kind == other.kind):
                data = self.data / other.data
                return SHGrid.from_array(data, grid=self.grid)
            else:
                raise ValueError('The two grids must be of the ' +
                                 'same kind and have the same shape.')
        elif _np.isscalar(other) is True:
            data = self.data / other
            return SHGrid.from_array(data, grid=self.grid)
        else:
            raise NotImplementedError('Mathematical operator not implemented' +
                                      'for these operands.')

    def __truediv__(self, other):
        """
        Divide two similar grids or a grid and a scalar, when
        __future__.division is in effect.
        """
        if isinstance(other, SHGrid):
            if (self.grid == other.grid and self.data.shape ==
                    other.data.shape and self.kind == other.kind):
                data = self.data / other.data
                return SHGrid.from_array(data, grid=self.grid)
            else:
                raise ValueError('The two grids must be of the ' +
                                 'same kind and have the same shape.')
        elif _np.isscalar(other) is True:
            data = self.data / other
            return SHGrid.from_array(data, grid=self.grid)
        else:
            raise NotImplementedError('Mathematical operator not implemented' +
                                      'for these operands.')

    def __pow__(self, other):
        """Raise a grid to a scalar power: pow(self, other)."""
        if _np.isscalar(other) is True:
            data = pow(self.data, other)
            return SHGrid.from_array(data, grid=self.grid)
        else:
            raise NotImplementedError('Mathematical operator not implemented' +
                                      'for these operands.')

    # ---- Extract grid properties ----
    def lats(self, degrees=True):
        """
        Return the latitudes of each row of the gridded data.

        Usage
        -----
        lats = x.lats([degrees])

        Returns
        -------
        lats : ndarray, shape (nlat)
            1-D numpy array of size nlat containing the latitude of each row
            of the gridded data.

        Parameters
        -------
        degrees : bool, optional, default = True
            If True, the output will be in degrees. If False, the output will
            be in radians.
        """
        if degrees is False:
            return _np.radians(self._lats())
        else:
            return self._lats()

    def lons(self, degrees=True):
        """
        Return the longitudes of each column of the gridded data.

        Usage
        -----
        lons = x.get_lon([degrees])

        Returns
        -------
        lons : ndarray, shape (nlon)
            1-D numpy array of size nlon containing the longitude of each row
            of the gridded data.

        Parameters
        -------
        degrees : bool, optional, default = True
            If True, the output will be in degrees. If False, the output will
            be in radians.
        """
        if degrees is False:
            return _np.radians(self._lons())
        else:
            return self._lons()

    def to_grid(self):
        """
        Return the raw gridded data as a numpy array.

        Usage
        -----
        grid = x.to_grid()

        Returns
        -------
        grid : ndarray, shape (nlat, nlon)
            2-D numpy array of the gridded data.
        """
        return self.data

    def plot3d(self, show=True, fname=None, elevation=0, azimuth=0):
        """
        Plot the raw data on a 3d sphere.

        This routines becomes slow for large grids because it is based on
        matplotlib3d.

        Usage
        -----
        x.plot3d([show, fname])

        Parameters
        ----------
        show : bool, optional, default = True
            If True, plot the image to the screen.
        fname : str, optional, default = None
            If present, save the image to the file.
        """
        from mpl_toolkits.mplot3d import Axes3D  # NOQA

        nlat, nlon = self.nlat, self.nlon
        cmap = _plt.get_cmap('RdBu_r')

        if self.kind == 'real':
            data = self.data
        elif self.kind == 'complex':
            data = _np.abs(self.data)
        else:
            raise ValueError('Grid has to be either real or complex, not {}'
                             .format(self.kind))

        lats = self.lats()
        lons = self.lons()

        if self.grid == 'DH':
            # add south pole
            lats_circular = _np.append(lats, [-90.])
        elif self.grid == 'GLQ':
            # add north and south pole
            lats_circular = _np.hstack(([90.], lats, [-90.]))
        lons_circular = _np.append(lons, [lons[0]])

        nlats_circular = len(lats_circular)
        nlons_circular = len(lons_circular)

        sshape = nlats_circular, nlons_circular

        # make uv sphere and store all points
        u = _np.radians(lons_circular)
        v = _np.radians(90. - lats_circular)

        x = _np.sin(v)[:, None] * _np.cos(u)[None, :]
        y = _np.sin(v)[:, None] * _np.sin(u)[None, :]
        z = _np.cos(v)[:, None] * _np.ones_like(lons_circular)[None, :]

        points = _np.vstack((x.flatten(), y.flatten(), z.flatten()))

        # fill data for all points. 0 lon has to be repeated (circular mesh)
        # and the south pole has to be added in the DH grid
        if self.grid == 'DH':
            magn_point = _np.zeros((nlat + 1, nlon + 1))
            magn_point[:-1, :-1] = data
            magn_point[-1, :] = _np.mean(data[-1])  # not exact !
            magn_point[:-1, -1] = data[:, 0]
        if self.grid == 'GLQ':
            magn_point = _np.zeros((nlat + 2, nlon + 1))
            magn_point[1:-1, :-1] = data
            magn_point[0, :] = _np.mean(data[0])  # not exact !
            magn_point[-1, :] = _np.mean(data[-1])  # not exact !
            magn_point[1:-1, -1] = data[:, 0]

        # compute face color, which is the average of all neighbour points
        magn_face = 1./4. * (magn_point[1:, 1:] + magn_point[:-1, 1:] +
                             magn_point[1:, :-1] + magn_point[:-1, :-1])

        magnmax_face = _np.max(_np.abs(magn_face))
        magnmax_point = _np.max(_np.abs(magn_point))

        # compute colours and displace the points
        norm = _plt.Normalize(-magnmax_face / 2., magnmax_face / 2., clip=True)
        colors = cmap(norm(magn_face.flatten()))
        colors = colors.reshape(nlats_circular - 1, nlons_circular - 1, 4)
        points *= (1. + magn_point.flatten() / magnmax_point / 2.)
        x = points[0].reshape(sshape)
        y = points[1].reshape(sshape)
        z = points[2].reshape(sshape)

        # plot 3d radiation pattern
        fig = _plt.figure(figsize=(10, 10))
        ax3d = fig.add_subplot(1, 1, 1, projection='3d')
        ax3d.plot_surface(x, y, z, rstride=1, cstride=1, facecolors=colors)
        ax3d.set(xlim=(-1.5, 1.5), ylim=(-1.5, 1.5), zlim=(-1.5, 1.5),
                 xticks=[-1, 1], yticks=[-1, 1], zticks=[-1, 1])
        ax3d.set_axis_off()
        ax3d.view_init(elev=elevation, azim=azimuth)

        # show or save output
        if show:
            _plt.show()
        if fname is not None:
            fig.savefig(fname)

        return fig, ax3d

    # ---- Plotting routines ----
    def plot(self, show=True, fname=None):
        """
        Plot the raw data using a simple cylindrical projection.

        Usage
        -----
        x.plot([show, fname])

        Parameters
        ----------
        show : bool, optional, default = True
            If True, plot the image to the screen.
        fname : str, optional, default = None
            If present, save the image to the file.
        """
        fig, ax = self._plot()
        if show:
            _plt.show()
        if fname is not None:
            fig.savefig(fname)
        return fig, ax

    def expand(self, normalization='4pi', csphase=1, **kwargs):
        """
        Expand the grid into spherical harmonics.

        Usage
        -----
        clm = x.expand([normalization, csphase, lmax_calc])

        Returns
        -------
        clm : SHCoeffs class instance

        Parameters
        ----------
        normalization : str, optional, default = '4pi'
            Normalization of the spherical harmonic coefficients: '4pi' for
            geodesy 4-pi normalized, 'ortho' for orthonormalized, or 'schmidt'
            for Schmidt semi-normalized.
        csphase : int, optional, default = 1
            Condon-Shortley phase convention: 1 to exclude the phase factor,
            or -1 to include it.
        lmax_calc : int, optional, default = x.lmax
            Maximum spherical harmonic degree to return.
        """
        if type(normalization) != str:
            raise ValueError('normalization must be a string. ' +
                             'Input type was {:s}'
                             .format(str(type(normalization))))

        if normalization.lower() not in set(['4pi', 'ortho', 'schmidt']):
            raise ValueError(
                "The normalization must be '4pi', 'ortho' " +
                "or 'schmidt'. Input value was {:s}."
                .format(repr(normalization))
                )

        if csphase != 1 and csphase != -1:
            raise ValueError(
                "csphase must be either 1 or -1. Input value was {:s}."
                .format(repr(csphase))
                )

        return self._expand(normalization=normalization, csphase=csphase,
                            **kwargs)

    def info(self):
        """
        Print a summary of the data stored in the SHGrid instance.

        Usage
        -----
        x.info()
        """
        print('kind = {:s}\ngrid = {:s}\n'.format(repr(self.kind),
                                                  repr(self.grid)), end='')
        if self.grid == 'DH':
            print('sampling = {:d}\n'.format(self.sampling), end='')
        print('nlat = {:d}\nnlon = {:d}\nlmax = {:d}'.format(self.nlat,
                                                             self.nlon,
                                                             self.lmax))


# ---- Real Driscoll and Healy grid class ----

class DHRealGrid(SHGrid):
    """Class for real Driscoll and Healy (1994) grids."""

    @staticmethod
    def istype(kind):
        return kind == 'real'

    @staticmethod
    def isgrid(grid):
        return grid == 'DH'

    def __init__(self, array, copy=True):
        self.nlat, self.nlon = array.shape

        if self.nlat % 2 != 0:
            raise ValueError('Input arrays for DH grids must have an even ' +
                             'number of latitudes: nlat = {:d}'
                             .format(self.nlat)
                             )
        if self.nlon == 2 * self.nlat:
            self.sampling = 2
        elif self.nlat == self.nlon:
            self.sampling = 1
        else:
            raise ValueError('Input array has shape (nlat={:d},nlon={:d})\n'
                             .format(self.nlat, self.nlon) +
                             'but needs nlat=nlon or nlat=2*nlon'
                             )

        self.lmax = int(self.nlat / 2 - 1)
        self.grid = 'DH'
        self.kind = 'real'

        if copy:
            self.data = _np.copy(array)
        else:
            self.data = array

    def _lats(self):
        """Return the latitudes (in degrees) of the gridded data."""
        lats = _np.linspace(90.0, -90.0 + 180.0 / self.nlat, num=self.nlat)
        return lats

    def _lons(self):
        """Return the longitudes (in degrees) of the gridded data."""
        lons = _np.linspace(0.0, 360.0 - 360.0 / self.nlon, num=self.nlon)
        return lons

    def _expand(self, normalization, csphase, **kwargs):
        """Expand the grid into real spherical harmonics."""
        if normalization.lower() == '4pi':
            norm = 1
        elif normalization.lower() == 'schmidt':
            norm = 2
        elif normalization.lower() == 'ortho':
            norm = 4
        else:
            raise ValueError(
                "The normalization must be '4pi', 'ortho' " +
                "or 'schmidt'. Input value was {:s}."
                .format(repr(normalization))
                )

        cilm = _shtools.SHExpandDH(self.data, norm=norm, csphase=csphase,
                                   sampling=self.sampling,
                                   **kwargs)
        coeffs = SHCoeffs.from_array(cilm,
                                     normalization=normalization.lower(),
                                     csphase=csphase, copy=False)
        return coeffs

    def _plot(self):
        """Plot the raw data using a simply cylindrical projection."""
        fig, ax = _plt.subplots(1, 1)
        ax.imshow(self.data, origin='upper', extent=(0., 360., -90., 90.))
        ax.set_xlabel('longitude')
        ax.set_ylabel('latitude')
        fig.tight_layout(pad=0.5)
        return fig, ax


# ---- Complex Driscoll and Healy grid class ----
class DHComplexGrid(SHGrid):
    """
    Class for complex Driscoll and Healy (1994) grids.
    """
    @staticmethod
    def istype(kind):
        return kind == 'complex'

    @staticmethod
    def isgrid(grid):
        return grid == 'DH'

    def __init__(self, array, copy=True):
        self.nlat, self.nlon = array.shape

        if self.nlat % 2 != 0:
            raise ValueError('Input arrays for DH grids must have an even ' +
                             'number of latitudes: nlat = {:d}'
                             .format(self.nlat)
                             )
        if self.nlon == 2 * self.nlat:
            self.sampling = 2
        elif self.nlat == self.nlon:
            self.sampling = 1
        else:
            raise ValueError('Input array has shape (nlat={:d},nlon={:d})\n' +
                             'but needs nlat=nlon or nlat=2*nlon'
                             .format(self.nlat, self.nlon)
                             )

        self.lmax = int(self.nlat / 2 - 1)
        self.grid = 'DH'
        self.kind = 'complex'

        if copy:
            self.data = _np.copy(array)
        else:
            self.data = array

    def _lats(self):
        """
        Return a vector containing the latitudes (in degrees) of each row
        of the gridded data.
        """
        lats = _np.linspace(90.0, -90.0 + 180.0 / self.nlat, num=self.nlat)
        return lats

    def _lons(self):
        """
        Return a vector containing the longitudes (in degrees) of each row
        of the gridded data.
        """
        lons = _np.linspace(0., 360.0 - 360.0 / self.nlon, num=self.nlon)
        return lons

    def _expand(self, normalization, csphase, **kwargs):
        """Expand the grid into real spherical harmonics."""
        if normalization.lower() == '4pi':
            norm = 1
        elif normalization.lower() == 'schmidt':
            norm = 2
        elif normalization.lower() == 'ortho':
            norm = 4
        else:
            raise ValueError(
                "The normalization must be '4pi', 'ortho' " +
                "or 'schmidt'. Input value was {:s}."
                .format(repr(normalization))
                )

        cilm = _shtools.SHExpandDHC(self.data, norm=norm, csphase=csphase,
                                    **kwargs)
        coeffs = SHCoeffs.from_array(cilm,
                                     normalization=normalization.lower(),
                                     csphase=csphase, copy=False)
        return coeffs

    def _plot(self):
        """Plot the raw data using a simply cylindrical projection."""
        fig, ax = _plt.subplots(2, 1)
        ax.flat[0].imshow(self.data.real, origin='upper',
                          extent=(0., 360., -90., 90.))
        ax.flat[0].set_title('Real component')
        ax.flat[0].set_xlabel('longitude')
        ax.flat[0].set_ylabel('latitude')
        ax.flat[1].imshow(self.data.imag, origin='upper',
                          extent=(0., 360., -90., 90.))
        ax.flat[1].set_title('Imaginary component')
        ax.flat[1].set_xlabel('longitude')
        ax.flat[1].set_ylabel('latitude')
        fig.tight_layout(pad=0.5)
        return fig, ax


# ---- Real Gaus Legendre Quadrature grid class ----

class GLQRealGrid(SHGrid):
    """
    Class for real Gauss-Legendre Quadrature grids.
    """
    @staticmethod
    def istype(kind):
        return kind == 'real'

    @staticmethod
    def isgrid(grid):
        return grid == 'GLQ'

    def __init__(self, array, zeros=None, weights=None, copy=True):
        self.nlat, self.nlon = array.shape
        self.lmax = self.nlat - 1

        if self.nlat != self.lmax + 1 or self.nlon != 2 * self.lmax + 1:
            raise ValueError('Input array has shape (nlat={:d}, nlon={:d})\n' +
                             'but needs (nlat={:d}, {:d})'
                             .format(self.nlat, self.nlon, self.lmax+1,
                                     2*self.lmax+1)
                             )

        if zeros is None or weights is None:
            self.zeros, self.weights = _shtools.SHGLQ(self.lmax)
        else:
            self.zeros = zeros
            self.weights = weights

        self.grid = 'GLQ'
        self.kind = 'real'
        if copy:
            self.data = _np.copy(array)
        else:
            self.data = array

    def _lats(self):
        """
        Return a vector containing the latitudes (in degrees) of each row
        of the gridded data.
        """
        lats = 90. - _np.arccos(self.zeros) * 180. / _np.pi
        return lats

    def _lons(self):
        """
        Return a vector containing the longitudes (in degrees) of each column
        of the gridded data.
        """
        lons = _np.linspace(0.0, 360.0 - 360.0 / self.nlon, num=self.nlon)
        return lons

    def _expand(self, normalization, csphase, **kwargs):
        """Expand the grid into real spherical harmonics."""
        if normalization.lower() == '4pi':
            norm = 1
        elif normalization.lower() == 'schmidt':
            norm = 2
        elif normalization.lower() == 'ortho':
            norm = 4
        else:
            raise ValueError(
                "The normalization must be '4pi', 'ortho' " +
                "or 'schmidt'. Input value was {:s}."
                .format(repr(normalization))
                )

        cilm = _shtools.SHExpandGLQ(self.data, self.weights, self.zeros,
                                    norm=norm, csphase=csphase, **kwargs)
        coeffs = SHCoeffs.from_array(cilm,
                                     normalization=normalization.lower(),
                                     csphase=csphase,
                                     copy=False)
        return coeffs

    def _plot(self):
        """Plot the raw data using a simply cylindrical projection."""

        fig, ax = _plt.subplots(1, 1)
        ax.imshow(self.data, origin='upper')
        ax.set_xlabel('GLQ longitude index')
        ax.set_ylabel('GLQ latitude index')
        fig.tight_layout(pad=0.5)
        return fig, ax


# ---- Complex Gaus Legendre Quadrature grid class ----

class GLQComplexGrid(SHGrid):
    """
    Class for complex Gauss Legendre Quadrature grids.
    """
    @staticmethod
    def istype(kind):
        return kind == 'complex'

    @staticmethod
    def isgrid(grid):
        return grid == 'GLQ'

    def __init__(self, array, zeros=None, weights=None, copy=True):
        self.nlat, self.nlon = array.shape
        self.lmax = self.nlat - 1

        if self.nlat != self.lmax + 1 or self.nlon != 2 * self.lmax + 1:
            raise ValueError('Input array has shape (nlat={:d}, nlon={:d})\n' +
                             'but needs (nlat={:d}, {:d})'
                             .format(self.nlat, self.nlon, self.lmax+1,
                                     2*self.lmax+1)
                             )

        if zeros is None or weights is None:
            self.zeros, self.weights = _shtools.SHGLQ(self.lmax)
        else:
            self.zeros = zeros
            self.weights = weights

        self.grid = 'GLQ'
        self.kind = 'complex'

        if copy:
            self.data = _np.copy(array)
        else:
            self.data = array

    def _lats(self):
        """Return the latitudes (in degrees) of the gridded data rows."""
        lats = 90. - _np.arccos(self.zeros) * 180. / _np.pi
        return lats

    def _lons(self):
        """Return the longitudes (in degrees) of the gridded data columns."""
        lons = _np.linspace(0., 360. - 360. / self.nlon, num=self.nlon)
        return lons

    def _expand(self, normalization, csphase, **kwargs):
        """Expand the grid into real spherical harmonics."""
        if normalization.lower() == '4pi':
            norm = 1
        elif normalization.lower() == 'schmidt':
            norm = 2
        elif normalization.lower() == 'ortho':
            norm = 4
        else:
            raise ValueError(
                "The normalization must be '4pi', 'ortho' " +
                "or 'schmidt'. Input value was {:s}."
                .format(repr(normalization))
                )

        cilm = _shtools.SHExpandGLQC(self.data, self.weights, self.zeros,
                                     norm=norm, csphase=csphase, **kwargs)
        coeffs = SHCoeffs.from_array(cilm,
                                     normalization=normalization.lower(),
                                     csphase=csphase, copy=False)
        return coeffs

    def _plot(self):
        """Plot the raw data using a simply cylindrical projection."""
        fig, ax = _plt.subplots(2, 1)
        ax.flat[0].imshow(self.data.real, origin='upper')
        ax.flat[0].set_title('Real component')
        ax.flat[0].set_xlabel('longitude index')
        ax.flat[0].set_ylabel('latitude index')
        ax.flat[1].imshow(self.data.imag, origin='upper')
        ax.flat[1].set_title('Imaginary component')
        ax.flat[1].set_xlabel('GLQ longitude index')
        ax.flat[1].set_ylabel('GLQ latitude index')
        fig.tight_layout(pad=0.5)
        return fig, ax


# ========================================================================
# ======      SPHERICAL HARMONICS WINDOW FUNCTION CLASS      =============
# ========================================================================

class SHWindow(object):
    """
    Class for spatio-spectral localization windows on the sphere.

    The windows can be initialized from:

    >>>  x = SHWindow.from_cap(theta, lwin, [clat, clon, nwin])
    >>>  x = SHWindow.from_mask(SHGrid)

    Each class instance defines the following class attributes:

    kind            : Either 'cap' or 'mask'.
    tapers          : Matrix containing the spherical harmonic coefficients
                      (in packed form) of either the unrotated spherical cap
                      localization windows or the localization windows
                      corresponding to the input mask.
    coeffs          : Array of spherical harmonic coefficients of the
                      rotated spherical cap localization windows. These are
                      '4pi' normalized and do not use the Condon-Shortley phase
                      factor.
    eigenvalues     : Concentration factors of the localization windows.
    orders          : The angular orders for each of the spherical cap
                      localization windows.
    weights         : Taper weights used with the multitaper spectral analyses.
                      Defaut is None.
    lwin            : Spherical harmonic bandwidth of the localization windows.
    theta           : Angular radius of the spherical cap localization domain
                      (default in degrees).
    theta_degrees   : True (default) if theta is in degrees.
    nwin            : Number of localization windows. Default is (lwin+1)**2.
    nwinrot         : The number of best concentrated windows that were rotated
                      and whose coefficients are stored in coeffs.
    clat, clon      : Latitude and longitude of the center of the rotated
                      spherical cap localization windows (default in degrees).
    coord_degrees   : True (default) if clat and clon are in degrees.

    Each class instance provides the following methods:

    to_array()            : Return an array of the spherical harmonic
                            coefficients for taper i, where i=0 is the best
                            concentrated, optionally using a different
                            normalization convention.
    to_grid()             : Return as an array a grid of taper i, where i=0
                            is the best concentrated window.
    return_coeffs()       : Return the spherical harmonic coefficients of taper
                            i, where i=0 is the best concentrated, as a new
                            SHCoeffs class instance, optionally using a
                            different normalization convention.
    return_grid()         : Return as a new SHGrid instance a grid of taper i,
                            where i=0 is the best concentrated window.
    number()              : Return the number of windows that have
                            concentration factors greater or equal to a
                            specified value.
    degrees()             : Return an array containing the spherical harmonic
                            degrees of the localization windows, from 0 to
                            lwin.
    powerspectra()        : Return the power spectra of one or more
                            localization windows.
    rotate()              : Rotate the spherical cap tapers, originally located
                            at the north pole, to clat and clon and save the
                            spherical harmonic coefficients in the attribute
                            coeffs.
    couplingmatrix()      : Return the coupling matrix of the first nwin
                            localization windows.
    biasedpowerspectrum() : Calculate the multitaper (cross-)power spectrum
                            expectation of a localized function.
    multitaperpowerspectrum()      : Return the multitaper power spectrum
                                     estimate and uncertainty for the input
                                     SHCoeffs class instance.
    multitapercrosspowerspectrum() : Return the multitaper cross-power
                                     spectrum estimate and uncertainty for
                                     two input SHCoeffs class instances.
    copy()                : Return a copy of the class instance.
    plot_windows()        : Plot the best concentrated localization windows
                            using a simple cylindrical projection.
    plot_powerspectra()   : Plot the power spectra of the best concentrated
                            localization windows.
    plot_couplingmatrix() : Plot the multitaper coupling matrix.
    info()                : Print a summary of the data stored in the SHWindow
                            instance.
"""

    def __init__(self):
        """Initialize with a factory method."""
        pass

    # ---- factory methods:
    @classmethod
    def from_cap(self, theta, lwin, clat=None, clon=None, nwin=None,
                 theta_degrees=True, coord_degrees=True, dj_matrix=None,
                 weights=None):
        """
        Construct spherical cap localization windows.

        Usage
        -----
        x = SHWindow.from_cap(theta, lwin, [clat, clon, nwin, theta_degrees,
                                            coord_degrees, dj_matrix, weights])

        Returns
        -------
        x : SHWindow class instance

        Parameters
        ----------
        theta : float
            Angular radius of the spherical cap localization domain (default
            in degrees).
        lwin : int
            Spherical harmonic bandwidth of the localization windows.
        clat, clon : float, optional, default = None
            Latitude and longitude of the center of the rotated spherical cap
            localization windows (default in degrees).
        nwin : int, optional, default (lwin+1)**2
            Number of localization windows.
        theta_degrees : bool, optional, default = True
            True if theta is in degrees.
        coord_degrees : bool, optional, default = True
            True if clat and clon are in degrees.
        dj_matrix : ndarray, optional, default = None
            The djpi2 rotation matrix computed by a call to djpi2.
        weights : ndarray, optional, default = None
            Taper weights used with the multitaper spectral analyses.
        """
        if theta_degrees:
            tapers, eigenvalues, taper_order = _shtools.SHReturnTapers(
                _np.radians(theta), lwin)
        else:
            tapers, eigenvalues, taper_order = _shtools.SHReturnTapers(
                theta, lwin)

        return SHWindowCap(theta, tapers, eigenvalues, taper_order,
                           clat, clon, nwin, theta_degrees, coord_degrees,
                           dj_matrix, weights, copy=False)

    @classmethod
    def from_mask(self, dh_mask, lwin, nwin=None, weights=None):
        """
        Construct localization windows that are optimally concentrated within
        the region specified by a mask.

        Usage
        -----
        x = SHWindow.from_mask(dh_mask, lwin, [nwin, weights])

        Returns
        -------
        x : SHWindow class instance

        Parameters
        ----------
        dh_mask :ndarray, shape (nlat, nlon)
            A Driscoll and Healy (1994) sampled grid describing the
            concentration region R. All elements should either be 1 (for inside
            the concentration region) or 0 (for outside the concentration
            region). The grid must have dimensions nlon=nlat or nlon=2*nlat,
            where nlat is even.
        lwin : int
            The spherical harmonic bandwidth of the localization windows.
        nwin : int, optional, default = (lwin+1)**2
            The number of best concentrated eigenvalues and eigenfunctions to
            return.
        weights ndarray, optional, default = None
            Taper weights used with the multitaper spectral analyses.
        """
        if nwin is None:
            nwin = (lwin + 1)**2
        else:
            if nwin > (lwin + 1)**2:
                raise ValueError('nwin must be less than or equal to ' +
                                 '(lwin + 1)**2. lwin = {:d} and nwin = {:d}'
                                 .format(lwin, nwin))

        if dh_mask.shape[0] % 2 != 0:
            raise ValueError('The number of latitude bands in dh_mask ' +
                             'must be even. nlat = {:d}'
                             .format(dh_mask.shape[0]))
        if (dh_mask.shape[1] != dh_mask.shape[0] and
                dh_mask.shape[1] != 2 * dh_mask.shape[0]):
            raise ValueError('dh_mask must be dimensioned as (n, n) or ' +
                             '(n, 2 * n). Input shape is ({:d}, {:d})'
                             .format(dh_mask.shape[0], dh_mask.shape[1]))

        tapers, eigenvalues = _shtools.SHReturnTapersMap(dh_mask, lwin,
                                                         ntapers=nwin)
        return SHWindowMask(tapers, eigenvalues, weights, copy=False)

    def copy(self):
        """Return a deep copy of the class instance."""
        return _copy.deepcopy(self)

    def degrees(self):
        """
        Return a numpy array listing the spherical harmonic degrees of the
        localization windows from 0 to lwin.

        Usage
        -----
        degrees = x.degrees()

        Returns
        -------
        degrees : ndarray, shape (lwin+1)
            numpy ndarray containing a list of the spherical harmonic degrees.
        """
        return _np.arange(self.lwin + 1)

    def number(self, alpha):
        """
        Return the number of localization windows that have concentration
        factors greater or equal to alpha.

        Usage
        -----
        k = x.number(alpha)

        Returns
        -------
        k : int
            The number of windows with concentration factors greater or equal
            to alpha.

        Parameters
        ----------
        alpha : float
            The concentration factor, which is the power of the window within
            the concentration region divided by the total power.
        """
        return len(self.eigenvalues[self.eigenvalues >= alpha])

    def to_array(self, itaper, normalization='4pi', csphase=1):
        """
        Return the spherical harmonic coefficients of taper i as a numpy
        array.

        Usage
        -----
        coeffs = x.to_array(itaper, [normalization, csphase])

        Returns
        -------
        coeffs : ndarray, shape (2, lwin+1, lwin+11)
            3-D numpy ndarray of size of the spherical harmonic coefficients
            of the window.

        Parameters
        ----------
        itaper : int
            Taper number, where itaper=0 is the best concentrated.
        normalization : str, optional, default = '4pi'
            Normalization of the output coefficients: '4pi', 'ortho' or
            'schmidt' for geodesy 4pi normalized, orthonormalized, or Schmidt
            semi-normalized coefficients, respectively.
        csphase : int, optional, default = 1
            Condon-Shortley phase convention: 1 to exclude the phase factor,
            or -1 to include it.
        """
        if type(normalization) != str:
            raise ValueError('normalization must be a string. ' +
                             'Input type was {:s}'
                             .format(str(type(normalization))))

        if normalization.lower() not in set(['4pi', 'ortho', 'schmidt']):
            raise ValueError(
                "normalization must be '4pi', 'ortho' " +
                "or 'schmidt'. Provided value was {:s}"
                .format(repr(output_normalization))
                )
        if csphase != 1 and csphase != -1:
            raise ValueError(
                "csphase must be 1 or -1. Input value was {:s}"
                .format(repr(csphase))
                )

        return self._to_array(
            itaper, normalization=normalization.lower(), csphase=csphase)

    def to_grid(self, itaper, grid='DH2', zeros=None):
        """
        Evaluate the coefficients of taper i on a spherical grid and return a
        numpy array.

        Usage
        -----
        gridout = x.to_grid(itaper, [grid, zeros])

        Returns
        -------
        gridout : ndarray, shape (nlat, nlon)
            2-D numpy array of localization window.

        Parameters
        ----------
        itaper : int
            Taper number, where itaper=0 is the best concentrated.
        grid : str, optional, default = 'DH'
            'DH' or 'DH1' for an equisampled lat/lon grid with nlat=nlon,
            'DH2' for an equidistant lat/lon grid with nlon=2*nlat, or 'GLQ'
            for a Gauss-Legendre quadrature grid.
        zeros : ndarray, optional, default = None
            The cos(colatitude) nodes used in the Gauss-Legendre Quadrature
            grids.

        Description
        -----------
        For more information concerning the spherical harmonic expansions and
        the properties of the output grids, see the documentation for
        SHExpandDH and SHExpandGLQ.
        """
        if type(grid) != str:
            raise ValueError('grid must be a string. ' +
                             'Input type was {:s}'
                             .format(str(type(grid))))

        if grid.upper() == 'DH' or grid.upper() == 'DH1':
            gridout = _shtools.MakeGridDH(self.to_array(itaper), sampling=1,
                                          norm=1, csphase=1)
        elif grid.upper() == 'DH2':
            gridout = _shtools.MakeGridDH(self.to_array(itaper), sampling=2,
                                          norm=1, csphase=1)
        elif grid.upper() == 'GLQ':
            if zeros is None:
                zeros, weights = _shtools.SHGLQ(self.lwin)

            gridout = _shtools.MakeGridGLQ(self.to_array(itaper), zeros,
                                           norm=1, csphase=1)
        else:
            raise ValueError(
                "grid must be 'DH', 'DH1', 'DH2', or 'GLQ'. " +
                "Input value was {:s}".format(repr(grid)))

        return gridout

    def return_coeffs(self, itaper, normalization='4pi', csphase=1):
        """
        Return the spherical harmonic coefficients of taper i as a SHCoeffs
        class instance.

        Usage
        -----
        clm = x.return_coeffs(itaper, [normalization, csphase])

        Returns
        -------
        clm : SHCoeffs class instance

        Parameters
        ----------
        itaper : int
            Taper number, where itaper=0 is the best concentrated.
        normalization : str, optional, default = '4pi'
            Normalization of the output class: '4pi', 'ortho' or 'schmidt' for
            geodesy 4pi-normalized, orthonormalized, or Schmidt semi-normalized
            coefficients, respectively.
        csphase : int, optional, default = 1
            Condon-Shortley phase convention: 1 to exclude the phase factor,
            or -1 to include it.
        """
        if type(normalization) != str:
            raise ValueError('normalization must be a string. ' +
                             'Input type was {:s}'
                             .format(str(type(normalization))))

        if normalization.lower() not in set(['4pi', 'ortho', 'schmidt']):
            raise ValueError(
                "normalization must be '4pi', 'ortho' " +
                "or 'schmidt'. Provided value was {:s}"
                .format(repr(normalization))
                )
        if csphase != 1 and csphase != -1:
            raise ValueError(
                "csphase must be 1 or -1. Input value was {:s}"
                .format(repr(csphase))
                )

        coeffs = self.to_array(itaper, normalization=normalization.lower(),
                               csphase=csphase)
        return SHCoeffs.from_array(coeffs,
                                   normalization=normalization.lower(),
                                   csphase=csphase, copy=False)

    def return_grid(self, itaper, grid='DH2', zeros=None):
        """
        Evaluate the coefficients of taper i on a spherical grid and return
        a SHGrid class instance.

        Usage
        -----
        f = x.return_grid(itaper, [grid, zeros])

        Returns
        -------
        f : SHGrid class instance

        Parameters
        ----------
        itaper : int
            Taper number, where itaper=0 is the best concentrated.
        grid : str, optional, default = 'DH2'
            'DH' or 'DH1' for an equisampled lat/lon grid with nlat=nlon, 'DH2'
            for an equidistant lat/lon grid with nlon=2*nlat, or 'GLQ' for a
            Gauss-Legendre quadrature grid.
        zeros : ndarray, optional, default = None
            The cos(colatitude) nodes used in the Gauss-Legendre Quadrature
            grids.

        Description
        -----------
        For more information concerning the spherical harmonic expansions and
        the properties of the output grids, see the documentation for
        SHExpandDH and SHExpandGLQ.
        """
        if type(grid) != str:
            raise ValueError('grid must be a string. ' +
                             'Input type was {:s}'
                             .format(str(type(grid))))

        if (grid.upper() == 'DH' or grid.upper() == 'DH1' or
                grid.upper() == 'DH2'):
            return SHGrid.from_array(self.to_grid(itaper, grid=grid.upper()),
                                     grid='DH', copy=False)
        elif grid.upper() == 'GLQ':
            if zeros is None:
                zeros, weights = _shtools.SHGLQ(self.lwin)

            return SHGrid.from_array(self.to_grid(itaper, grid=grid.upper(),
                                                  zeros=zeros),
                                     grid='GLQ', copy=False)
        else:
            raise ValueError(
                "grid must be 'DH', 'DH1', 'DH2', or 'GLQ'. " +
                "Input value was {:s}".format(repr(grid)))

    def multitaperpowerspectrum(self, clm, k, **kwargs):
        """
        Return the multitaper power spectrum estimate and uncertainty.

        Usage
        -----
        mtse, sd = x.multitaperpowerspectrum(clm, k, [lmax, taper_wt, clat,
                                                      clon, coord_degrees])

        Returns
        -------
        mtse : ndarray, shape (lmax-lwin+1)
            The localized multitaper power spectrum estimate, where lwin is the
            spherical harmonic bandwidth of the localization windows.
        sd : ndarray, shape (lmax-lwin+1)
            The standard error of the localized multitaper power spectral
            estimates.

        Parameters
        ----------
        clm : SHCoeffs class instance
            SHCoeffs class instance containing the spherical harmonic
            coefficients of the global field to analyze.
        k : int
            The number of tapers to be utilized in performing the multitaper
            spectral analysis.
        lmax : int, optional, default = clm.lmax
            The maximum spherical harmonic degree of clm to use.
        taper_wt : ndarray, optional, default = None
            1-D numpy arrar of the weights used in calculating the multitaper
            spectral estimates and standard error.
        clat, clon : float, optional, default = 90., 0.
            Latitude and longitude of the center of the spherical-cap
            localization windows.
        coord_degrees : bool, optional, default = True
            True if clat and clon are in degrees.
        """
        return self._multitaperpowerspectrum(clm, k, **kwargs)

    def multitapercrosspowerspectrum(self, clm, slm, k, **kwargs):
        """
        Return the multitaper cross power spectrum estimate and uncertainty.

        Usage
        -----
        mtse, sd = x.multitapercrosspowerspectrum(
                      clm, slm, k, [lmax, taper_wt, clat, clon, coord_degrees])

        Returns
        -------
        mtse : ndarray, shape (lmax-lwin+1)
            The localized multitaper cross-power spectrum estimate, where lwin
            is the spherical harmonic bandwidth of the localization windows.
        sd : ndarray, shape (lmax-lwin+1)
            The standard error of the localized multitaper cross-power spectral
            estimates.

        Parameters
        ----------
        clm : SHCoeffs class instance
            SHCoeffs class instance containing the spherical harmonic
            coefficients of the first global field to analyze.
        slm : SHCoeffs class instance
            SHCoeffs class instance containing the spherical harmonic
            coefficients of the second global field to analyze.
        k : int
            The number of tapers to be utilized in performing the multitaper
            spectral analysis.
        lmax : int, optional, default = min(clm.lmax, slm.lmax)
            The maximum spherical harmonic degree of the input coefficients
            to use.
        taper_wt : ndarray, optional, default = None
            The weights used in calculating the multitaper spectral estimates
            and standard error.
        clat, clon : float, optional, default = 90., 0.
            Latitude and longitude of the center of the spherical-cap
            localization windows.
        coord_degrees : bool, optional, default = True
            True if clat and clon are in degrees.
        """
        return self._multitapercrosspowerspectrum(clm, slm, k, **kwargs)

    def biasedpowerspectrum(self, power, k, **kwargs):
        """
        Calculate the multitaper (cross-)power spectrum expectation of a
        localized function.

        Usage
        -----
        outspectrum = x.biasedpowerspectrum(power, k, [taper_wt, save_cg,
                                            ldata])

        Returns
        -------
        outspectrum : ndarray, shape (ldata+lwin+1)
            The expectation of the windowed power spectrum, where lwin is the
            spherical harmonic bandwidth of the localization windows.

        Parameters
        ----------
        power : ndarray, shape (ldata+1)
            The global power spectrum.
        k : int
            The number of best concentrated localization windows to use in
            constructing the windowed power spectrum.
        taper_wt : ndarray, optional, default = None
            The weights used in calculating the multitaper spectral estimates
            and standard error.
        save_cg : int, optional, default = 0
            If 1, the Clebsch-Gordon coefficients will be precomputed and saved
            for future use. If 0, the Clebsch-Gordon coefficients will be
            recomputed for each call.
        ldata : int, optional, default = len(power)-1
            The maximum degree of the global unwindowed power spectrum.
        """
        outspectrum = self._biasedpowerspectrum(power, k, **kwargs)
        return outspectrum

    def powerspectra(self, itaper=None, nwin=None, unit='per_l', base=10.,
                     energy=False):
        """
        Return the power spectra of one or more localization windows.

        Usage
        -----
        power = x.powerperdegree([itaper, nwin, unit, base, energy])

        Returns
        -------
        power : ndarray, shape (lwin+1, nwin)
             A matrix with each column containing the power spectrum of a
             localization window, and where the windows are arranged with
             increasing concentration factors. If itaper is set, only a single
             vector is returned, whereas if nwin is set, the first nwin spectra
             are returned.

        Parameters
        ----------
        itaper : int, optional, default = None
            The taper number of the output power spectrum, where itaper=0
            corresponds to the best concentrated taper.
        nwin : int, optional, default = 1
            The number of best concentrated localization window power spectra
            to return.
        unit : str, optional, default = 'per_l'
            If 'per_l', return the total power for each spherical harmonic
            degree l. If 'per_lm', return the average contribution to the power
            for each coefficient at spherical harmonic degree l. If
            'per_dlogl', return the power per log interval dlog_a(l).
        base : float, optional, default = 10.
            The logarithm base when calculating the 'per_dlogl' power spectrum.
        energy : bool, optional, default = False
            Return the energy spectrum instead of the power spectrum.

        Description
        -----------
        Total power is defined as the integral of the function squared over all
        space, divided by the area the function spans. If the mean of the
        function is zero, this is equivalent to the variance of the function.
        The total energy is the integral of the function squared over all space
        and is 4pi times the total power.

        The output power spectra can be one of three types. 'per_l' returns
        the contribution to the total power from all angular orders at degree
        l. 'per_lm' returns the average contribution from a single coefficient
        at degree l to the total power. The power 'per_lm' is equal to the
        power 'per_l' divided by (2l+1). 'per_dlogl' returns the contribution
        to the total power from all angular orders over an infinitessimal
        logarithmic degree band. The power in the band dlog_a(l) is
        power(l, 'per_dlogl')*dlog_a(l), where a is the base, and where
        power(l, 'per_dlogl) is equal to power(l, 'per_l')*l*log(a).
         """
        if itaper is None:
            if nwin is None:
                nwin = self.nwin
            power = _np.zeros((self.lwin+1, nwin))

            for iwin in range(nwin):
                coeffs = self.to_array(iwin)
                power[:, iwin] = _shtools.SHPowerSpectrum(coeffs)
                if (unit.lower() == 'per_l'):
                    pass
                elif (unit.lower() == 'per_lm'):
                    l = self.degrees()
                    power[:, iwin] /= (2.0 * l + 1.0)
                elif (unit.lower() == 'per_dlogl'):
                    l = self.degrees()
                    power[:, iwin] *= l * _np.log(base)
                else:
                    raise ValueError(
                        "unit must be 'per_l', 'per_lm', or 'per_dlogl'." +
                        "Input value was {:s}".format(repr(unit)))
        else:
            coeffs = self.to_array(itaper)
            power = _shtools.SHPowerSpectrum(coeffs)
            if (unit.lower() == 'per_l'):
                pass
            elif (unit.lower() == 'per_lm'):
                l = self.degrees()
                power /= (2.0 * l + 1.0)
            elif (unit.lower() == 'per_dlogl'):
                l = self.degrees()
                power *= l * _np.log(base)
            else:
                raise ValueError(
                    "unit must be 'per_l', 'per_lm', or 'per_dlogl'." +
                    "Input value was {:s}".format(repr(unit)))

        if energy:
            power *= 4.0 * _np.pi
        return power

    def couplingmatrix(self, lmax, nwin=None, weights=None, mode='full'):
        """
        Return the coupling matrix of the first nwin tapers. This matrix
        relates the global power spectrum to the expectation of the localized
        multitaper spectrum.

        Usage
        -----
        Mmt = x.couplingmatrix(lmax, [nwin, weights, mode])

        Returns
        -------
        Mmt : ndarray, shape (lmax+lwin+1, lmax+1) or (lmax+1, lmax+1) or
              (lmax-lwin+1, lmax+1)

        Parameters
        ----------
        lmax : int
            Spherical harmonic bandwidth of the global power spectrum.
        nwin : int, optional, default = x.nwin
            Number of tapers used in the mutlitaper spectral analysis.
        weights : ndarray, optional, default = x.weights
            Taper weights used with the multitaper spectral analyses.
        mode : str, opitonal, default = 'full'
            'full' returns a biased output spectrum of size lmax+lwin+1. The
            input spectrum is assumed to be zero for degrees l>lmax.
            'same' returns a biased output spectrum with the same size
            (lmax+1) as the input spectrum. The input spectrum is assumed to be
            zero for degrees l>lmax.
            'valid' returns a biased spectrum with size lmax-lwin+1. This
            returns only that part of the biased spectrum that is not
            influenced by the input spectrum beyond degree lmax.
        """
        if weights is not None:
            if nwin is not None:
                if len(weights) != nwin:
                    raise ValueError(
                        'Length of weights must be equal to nwin. ' +
                        'len(weights) = {:d}, nwin = {:d}'.format(len(weights),
                                                                  nwin))
            else:
                if len(weights) != self.nwin:
                    raise ValueError(
                        'Length of weights must be equal to nwin. ' +
                        'len(weights) = {:d}, nwin = {:d}'.format(len(weights),
                                                                  self.nwin))

        if mode == 'full':
            return self._couplingmatrix(lmax, nwin=nwin, weights=weights)
        elif mode == 'same':
            cmatrix = self._couplingmatrix(lmax, nwin=nwin,
                                           weights=weights)
            return cmatrix[:lmax+1, :]
        elif mode == 'valid':
            cmatrix = self._couplingmatrix(lmax, nwin=nwin,
                                           weights=weights)
            return cmatrix[:lmax - self.lwin+1, :]
        else:
            raise ValueError("mode has to be 'full', 'same' or 'valid', not "
                             "{}".format(mode))

    def plot_windows(self, nwin, show=True, fname=None):
        """
        Plot the best-concentrated localization windows.

        Usage
        -----
        x.plot_windows(nwin, [show, fname])

        Parameters
        ----------
        nwin : int
            The number of localization windows to plot.
        show : bool, optional, default = True
            If True, plot the image to the screen.
        fname : str, optional, default = None
            If present, save the image to the file.
        """
        if self.kind == 'cap':
            if self.nwinrot is not None and self.nwinrot <= nwin:
                nwin = self.nwinrot

        maxcolumns = 5
        ncolumns = min(maxcolumns, nwin)
        nrows = _np.ceil(nwin / ncolumns).astype(int)
        figsize = ncolumns * 2.4, nrows * 1.2 + 0.5
        fig, axes = _plt.subplots(nrows, ncolumns, figsize=figsize)

        for ax in axes[:-1, :].flatten():
            for xlabel_i in ax.get_xticklabels():
                xlabel_i.set_visible(False)
        for ax in axes[:, 1:].flatten():
            for ylabel_i in ax.get_yticklabels():
                ylabel_i.set_visible(False)

        for itaper in range(min(self.nwin, nwin)):
            evalue = self.eigenvalues[itaper]
            ax = axes.flatten()[itaper]
            ax.imshow(self.to_grid(itaper), origin='upper',
                      extent=(0., 360., -90., 90.))
            ax.set_title('concentration: {:2.2f}'.format(evalue))

        fig.tight_layout(pad=0.5)

        if show:
            _plt.show()
        if fname is not None:
            fig.savefig(fname)
        return fig, axes

    def plot_powerspectra(self, nwin, unit='per_l', base=10., energy=False,
                          loglog=False, show=True, fname=None):
        """
        Plot the power spectra of the best-concentrated localization windows.

        Usage
        -----
        x.plot_powerspectra(nwin, [unit, base, energy, loglog, show, fname])

        Parameters
        ----------
        nwin : int
            The number of localization windows to plot.
        unit : str, optional, default = 'per_l'
            If 'per_l', return the total power for each spherical harmonic
            degree l. If 'per_lm', return the average contribution to the power
            for each coefficient at spherical harmonic degree l. If
            'per_dlogl', return the power per log interval dlog_a(l).
        base : float, optional, default = 10.
            The logarithm base when calculating the 'per_dlogl' power spectrum.
        energy : bool, optional, default = False
            Return the energy spectrum instead of the power spectrum.
        loglog : bool, optional, default = False
            If True, use log-log axis.
        show : bool, optional, default = True
            If True, plot the image to the screen.
        fname : str, optional, default = None
            If present, save the image to the file.
        """
        degrees = self.degrees()
        power = self.powerspectra(nwin=nwin, unit=unit, base=base,
                                  energy=energy)

        maxcolumns = 5
        ncolumns = min(maxcolumns, nwin)
        nrows = _np.ceil(nwin / ncolumns).astype(int)
        figsize = ncolumns * 2.4, nrows * 1.2 + 0.5

        fig, axes = _plt.subplots(nrows, ncolumns, figsize=figsize)

        for ax in axes[:-1, :].flatten():
            for xlabel_i in ax.get_xticklabels():
                xlabel_i.set_visible(False)
        for ax in axes[:, 1:].flatten():
            for ylabel_i in ax.get_yticklabels():
                ylabel_i.set_visible(False)

        for itaper in range(min(self.nwin, nwin)):
            evalue = self.eigenvalues[itaper]
            ax = axes.flatten()[itaper]
            ax.set_xlabel('degree l')
            ax.set_ylabel('power')
            ax.set_yscale('log', basey=base)
            if loglog:
                ax.set_xscale('log', basex=base)
            ax.grid(True, which='both')
            ax.plot(degrees[0:], power[0:, itaper])
            ax.set_title('concentration: {:2.2f}'.format(evalue))

        fig.tight_layout(pad=0.5)

        if show:
            _plt.show()
        if fname is not None:
            fig.savefig(fname)
        return fig, axes

    def plot_couplingmatrix(self, lmax, nwin=None, weights=None, mode='full',
                            show=True, fname=None):
        """
        Plot the multitaper coupling matrix.

        This matrix relates the global power spectrum to the expectation of
        the localized multitaper spectrum.

        Usage
        -----
        x.plot_couplingmatrix(lmax, [nwin, weights, mode, show, fname])

        Parameters
        ----------
        lmax : int
            Spherical harmonic bandwidth of the global power spectrum.
        nwin : int, optional, default = x.nwin
            Number of tapers used in the mutlitaper spectral analysis.
        weights : ndarray, optional, default = x.weights
            Taper weights used with the multitaper spectral analyses.
        mode : str, opitonal, default = 'full'
            'full' returns a biased output spectrum of size lmax+lwin+1. The
            input spectrum is assumed to be zero for degrees l>lmax.
            'same' returns a biased output spectrum with the same size
            (lmax+1) as the input spectrum. The input spectrum is assumed to be
            zero for degrees l>lmax.
            'valid' returns a biased spectrum with size lmax-lwin+1. This
            returns only that part of the biased spectrum that is not
            influenced by the input spectrum beyond degree lmax.
        show : bool, optional, default = True
            If True, plot the image to the screen.
        fname : str, optional, default = None
            If present, save the image to the file.
        """
        figsize = _mpl.rcParams['figure.figsize']
        figsize[0] = figsize[1]
        fig = _plt.figure(figsize=figsize)
        ax = fig.add_subplot(111)
        ax.imshow(self.couplingmatrix(lmax, nwin=nwin, weights=weights,
                                      mode=mode), aspect='auto')
        ax.set_xlabel('input power')  # matrix index 1 (columns)
        ax.set_ylabel('output power')  # matrix index 0 (rows)
        fig.tight_layout(pad=0.1)

        if show:
            _plt.show()
        if fname is not None:
            fig.savefig(fname)
        return fig, ax

    def info(self):
        """
        Print a summary of the data stored in the SHWindow instance.

        Usage
        -----
        x.info()
        """
        self._info()


class SHWindowCap(SHWindow):
    """Class for localization windows concentrated within a spherical cap."""

    @staticmethod
    def istype(kind):
        return kind == 'cap'

    def __init__(self, theta, tapers, eigenvalues, taper_order,
                 clat, clon, nwin, theta_degrees, coord_degrees, dj_matrix,
                 weights, copy=True):
        self.kind = 'cap'
        self.theta = theta
        self.clat = clat
        self.clon = clon
        self.lwin = tapers.shape[0] - 1
        self.theta_degrees = theta_degrees
        self.coord_degrees = coord_degrees
        self.dj_matrix = dj_matrix
        self.weights = weights
        self.nwinrot = None

        if nwin is not None:
            self.nwin = nwin
        else:
            self.nwin = tapers.shape[1]

        if self.nwin > (self.lwin + 1)**2:
            raise ValueError('nwin must be less than or equal to ' +
                             '(lwin+1)**2. nwin = {:s} and lwin = {:s}.'
                             .format(repr(self.nwin), repr(self.lwin)))

        if copy:
            self.tapers = _np.copy(tapers[:, :self.nwin])
            self.eigenvalues = _np.copy(eigenvalues[:self.nwin])
            self.orders = _np.copy(taper_order[:self.nwin])
        else:
            self.tapers = tapers[:, :self.nwin]
            self.eigenvalues = eigenvalues[:self.nwin]
            self.orders = taper_order[:self.nwin]

        # If the windows aren't rotated, don't store them.
        if self.clat is None and self.clon is None:
            self.coeffs = None
        else:
            self.rotate(clat=self.clat, clon=self.clon,
                        coord_degrees=self.coord_degrees,
                        dj_matrix=self.dj_matrix)

    def _taper2coeffs(self, itaper):
        """
        Return the spherical harmonic coefficients of the unrotated taper i
        as an array, where i = 0 is the best concentrated.
        """
        taperm = self.orders[itaper]
        coeffs = _np.zeros((2, self.lwin + 1, self.lwin + 1))
        if taperm < 0:
            coeffs[1, :, abs(taperm)] = self.tapers[:, itaper]
        else:
            coeffs[0, :, abs(taperm)] = self.tapers[:, itaper]

        return coeffs

    def _to_array(self, itaper, normalization='4pi', csphase=1):
        """
        Return the spherical harmonic coefficients of taper i as an
        array, where i = 0 is the best concentrated.
        """
        if self.coeffs is None:
            coeffs = _np.copy(self._taper2coeffs(itaper))
        else:
            if itaper > self.nwinrot - 1:
                raise ValueError('itaper must be less than or equal to ' +
                                 'nwinrot - 1. itaper = {:d}, nwinrot = {:d}'
                                 .format(itaper, self.nwinrot))
            coeffs = _shtools.SHVectorToCilm(self.coeffs[:, itaper])

        if normalization == 'schmidt':
            for l in range(self.lwin + 1):
                coeffs[:, l, :l+1] *= _np.sqrt(2.0 * l + 1.0)
        elif normalization == 'ortho':
            coeffs *= _np.sqrt(4.0 * _np.pi)

        if csphase == -1:
            for m in range(self.lwin + 1):
                if m % 2 == 1:
                    coeffs[:, :, m] = - coeffs[:, :, m]

        return coeffs

    def rotate(self, clat, clon, coord_degrees=True, dj_matrix=None,
               nwinrot=None):
        """"
        Rotate the spherical-cap windows centered on the north pole to clat
        and clon, and save the spherical harmonic coefficients in the
        attribute coeffs.

        Usage
        -----
        x.rotate(clat, clon [coord_degrees, dj_matrix, nwinrot])

        Parameters
        ----------
        clat, clon : float
            Latitude and longitude of the center of the rotated spherical-cap
            localization windows (default in degrees).
        coord_degrees : bool, optional, default = True
            True if clat and clon are in degrees.
        dj_matrix : ndarray, optional, default = None
            The djpi2 rotation matrix computed by a call to djpi2.
        nwinrot : int, optional, default = (lwin+1)**2
            The number of best concentrated windows to rotate, where lwin is
            the spherical harmonic bandwidth of the localization windows.

        Description
        -----------
        This function will take the spherical-cap localization windows
        centered at the north pole (and saved in the attributes tapers and
        orders), rotate each function to the coordinate (clat, clon), and save
        the spherical harmonic coefficients in the attribute coeffs. Each
        column of coeffs contains a single window, and is ordered according to
        the convention in SHCilmToVector.
        """
        self.coeffs = _np.zeros(((self.lwin + 1)**2, self.nwin))
        self.clat = clat
        self.clon = clon
        self.coord_degrees = coord_degrees

        if nwinrot is not None:
            self.nwinrot = nwinrot
        else:
            self.nwinrot = self.nwin

        if self.coord_degrees:
            angles = _np.radians(_np.array([0., -(90. - clat), -clon]))
        else:
            angles = _np.array([0., -(_np.pi/2. - clat), -clon])

        if dj_matrix is None:
            if self.dj_matrix is None:
                self.dj_matrix = _shtools.djpi2(self.lwin + 1)
                dj_matrix = self.dj_matrix
            else:
                dj_matrix = self.dj_matrix

        for i in range(self.nwinrot):
            if ((coord_degrees is True and clat == 90. and clon == 0.) or
                    (coord_degrees is False and clat == _np.pi/2. and
                     clon == 0.)):
                coeffs = self._taper2coeffs(i)
                self.coeffs[:, i] = _shtools.SHCilmToVector(coeffs)

            else:
                coeffs = _shtools.SHRotateRealCoef(self._taper2coeffs(i),
                                                   angles, dj_matrix)
                self.coeffs[:, i] = _shtools.SHCilmToVector(coeffs)

    def _couplingmatrix(self, lmax, nwin=None, weights=None):
        """Return the coupling matrix of the first nwin tapers."""
        if nwin is None:
            nwin = self.nwin

        if weights is None:
            weights = self.weights

        if weights is None:
            return _shtools.SHMTCouplingMatrix(lmax, self.tapers**2, k=nwin)
        else:
            return _shtools.SHMTCouplingMatrix(lmax, self.tapers**2, k=nwin,
                                               taper_wt=self.weights)

    def _multitaperpowerspectrum(self, clm, k, clat=None, clon=None,
                                 coord_degrees=True, lmax=None, taper_wt=None):
        """
        Return the multitaper power spectrum estimate and uncertainty for an
        input SHCoeffs class instance.
        """
        if lmax is None:
            lmax = clm.lmax

        if (clat is not None and clon is not None and clat == self.clat and
                clon == self.clon and coord_degrees is self.coord_degrees and
                k <= self.nwinrot):
            # use the already stored coeffs
            pass
        elif (clat is None and clon is None) and \
                (self.clat is not None and self.clon is not None and
                 k <= self.nwinrot):
            # use the already stored coeffs
            pass
        else:
            if clat is None:
                clat = self.clat
            if clon is None:
                clon = self.clon
            if (clat is None and clon is not None) or \
                    (clat is not None and clon is None):
                raise ValueError('clat and clon must both be input. ' +
                                 'clat = {:s}, clon = {:s}'
                                 .format(repr(clat), repr(clon)))
            if clat is None and clon is None:
                self.rotate(clat=90., clon=0., coord_degrees=True, nwinrot=k)
            else:
                self.rotate(clat=clat, clon=clon, coord_degrees=coord_degrees,
                            nwinrot=k)

        sh = clm.to_array(normalization='4pi', csphase=1, lmax=lmax)

        if taper_wt is None:
            return _shtools.SHMultiTaperMaskSE(sh, self.coeffs, lmax=lmax, k=k)
        else:
            return _shtools.SHMultiTaperMaskSE(sh, self.coeffs, lmax=lmax, k=k,
                                               taper_wt=taper_wt)

    def _multitapercrosspowerspectrum(self, clm, slm, k, clat=None,
                                      clon=None, coord_degrees=True,
                                      lmax=None, taper_wt=None):
        """
        Return the multitaper cross-power spectrum estimate and uncertainty for
        two input SHCoeffs class instances.
        """
        if lmax is None:
            lmax = min(clm.lmax, slm.lmax)

        if (clat is not None and clon is not None and clat == self.clat and
                clon == self.clon and coord_degrees is self.coord_degrees and
                k <= self.nwinrot):
            # use the already stored coeffs
            pass
        elif (clat is None and clon is None) and \
                (self.clat is not None and self.clon is not None and
                 k <= self.nwinrot):
            # use the already stored coeffs
            pass
        else:
            if clat is None:
                clat = self.clat
            if clon is None:
                clon = self.clon
            if (clat is None and clon is not None) or \
                    (clat is not None and clon is None):
                raise ValueError('clat and clon must both be input. ' +
                                 'clat = {:s}, clon = {:s}'
                                 .format(repr(clat), repr(clon)))
            if clat is None and clon is None:
                self.rotate(clat=90., clon=0., coord_degrees=True, nwinrot=k)
            else:
                self.rotate(clat=clat, clon=clon, coord_degrees=coord_degrees,
                            nwinrot=k)

        sh1 = clm.to_array(normalization='4pi', csphase=1, lmax=lmax)
        sh2 = slm.to_array(normalization='4pi', csphase=1, lmax=lmax)

        if taper_wt is None:
            return _shtools.SHMultiTaperMaskCSE(sh1, sh2, self.coeffs,
                                                lmax1=lmax, lmax2=lmax, k=k)
        else:
            return _shtools.SHMultiTaperMaskCSE(sh1, sh2, self.coeffs,
                                                lmax1=lmax, lmax2=lmax, k=k,
                                                taper_wt=taper_wt)

    def _biasedpowerspectrum(self, power, k, **kwargs):
        """
        Calculate the multitaper (cross-)power spectrum expectation of function
        localized by spherical cap windows.
        """
        outspectrum = _shtools.SHBiasK(self.tapers, power, k=k, **kwargs)
        return outspectrum

    def _info(self):
        """Print a summary of the data in the SHWindow instance."""
        print('kind = {:s}\n'.format(repr(self.kind)), end='')

        if self.theta_degrees:
            print('theta = {:f} degrees\n'.format(self.theta), end='')
        else:
            print('theta = {:f} radians'.format(self.theta), end='')

        print('lwin = {:d}\n'.format(self.lwin), end='')
        print('nwin = {:d}\n'.format(self.nwin), end='')

        if self.clat is not None:
            if self.coord_degrees:
                print('clat = {:f} degrees\n'.format(self.clat), end='')
            else:
                print('clat = {:f} radians\n'.format(self.clat), end='')
        else:
            print('clat is not specified')

        if self.clon is not None:
            if self.coord_degrees:
                print('clon = {:f} degrees\n'.format(self.clon), end='')
            else:
                print('clon = {:f} radians\n'.format(self.clon), end='')
        else:
            print('clon is not specified')

        print('nwinrot = {:s}'.format(repr(self.nwinrot)))

        if self.dj_matrix is not None:
            print('dj_matrix is stored')
        else:
            print('dj_matrix is not stored')

        if self.weights is None:
            print('Taper weights are not set.')
        else:
            print('Taper weights are set.')


class SHWindowMask(SHWindow):
    """
    Class for localization windows concentrated within a specified mask and
    for a given spherical harmonic bandwidth.
    """

    @staticmethod
    def istype(kind):
        return kind == 'mask'

    def __init__(self, tapers, eigenvalues, weights, copy=True):
        self.kind = 'mask'
        self.lwin = _np.sqrt(tapers.shape[0]).astype(int) - 1
        self.nwin = tapers.shape[1]
        if copy:
            self.weights = weights
            self.tapers = _np.copy(tapers)
            self.eigenvalues = _np.copy(eigenvalues)
        else:
            self.weights = weights
            self.tapers = tapers
            self.eigenvalues = eigenvalues

    def _to_array(self, itaper, normalization='4pi', csphase=1):
        """
        Return the spherical harmonic coefficients of taper i as an
        array, where i=0 is the best concentrated.
        """
        coeffs = _shtools.SHVectorToCilm(self.tapers[:, itaper])

        if normalization == 'schmidt':
            for l in range(self.lwin + 1):
                coeffs[:, l, :l+1] *= _np.sqrt(2.0 * l + 1.0)
        elif normalization == 'ortho':
            coeffs *= _np.sqrt(4.0 * _np.pi)

        if csphase == -1:
            for m in range(self.lwin + 1):
                if m % 2 == 1:
                    coeffs[:, :, m] = - coeffs[:, :, m]

        return coeffs

    def _couplingmatrix(self, lmax, nwin=None, weights=None):
        """Return the coupling matrix of the first nwin tapers."""
        if nwin is None:
            nwin = self.nwin

        if weights is None:
            weights = self.weights

        tapers_power = _np.zeros((self.lwin+1, nwin))
        for i in range(nwin):
            tapers_power[:, i] = _shtools.SHPowerSpectrum(self.to_array(i))

        if weights is None:
            return _shtools.SHMTCouplingMatrix(lmax, tapers_power, k=nwin)
        else:
            return _shtools.SHMTCouplingMatrix(lmax, tapers_power, k=nwin,
                                               taper_wt=self.weights)

    def _multitaperpowerspectrum(self, clm, k, lmax=None, taper_wt=None):
        """
        Return the multitaper power spectrum estimate and uncertainty for an
        input SHCoeffs class instance.
        """
        if lmax is None:
            lmax = clm.lmax

        sh = clm.to_array(normalization='4pi', csphase=1, lmax=lmax)

        if taper_wt is None:
            return _shtools.SHMultiTaperMaskSE(sh, self.tapers, lmax=lmax, k=k)
        else:
            return _shtools.SHMultiTaperMaskSE(sh, self.tapers, lmax=lmax,
                                               k=k, taper_wt=taper_wt)

    def _multitapercrosspowerspectrum(self, clm, slm, k, lmax=None,
                                      taper_wt=None):
        """
        Return the multitaper cross-power spectrum estimate and uncertainty for
        two input SHCoeffs class instances.
        """
        if lmax is None:
            lmax = min(clm.lmax, slm.lmax)

        sh1 = clm.to_array(normalization='4pi', csphase=1, lmax=lmax)
        sh2 = slm.to_array(normalization='4pi', csphase=1, lmax=lmax)

        if taper_wt is None:
            return _shtools.SHMultiTaperMaskCSE(sh1, sh2, self.tapers,
                                                lmax=lmax, k=k)
        else:
            return _shtools.SHMultiTaperMaskCSE(sh1, sh2, self.tapers,
                                                lmax=lmax, k=k,
                                                taper_wt=taper_wt)

    def _biasedpowerspectrum(self, power, k, **kwargs):
        """
        Calculate the multitaper (cross-)power spectrum expectation of function
        localized by arbitary windows.
        """
        outspectrum = _shtools.SHBiasKMask(self.tapers, power, k=k, **kwargs)
        return outspectrum

    def _info(self):
        """Print a summary of the data in the SHWindow instance."""
        print('kind = {:s}\n'.format(repr(self.kind)), end='')

        print('lwin = {:d}\n'.format(self.lwin), end='')
        print('nwin = {:d}\n'.format(self.nwin), end='')

        if self.weights is None:
            print('Taper weights are not set.')
        else:
            print('Taper weights are set.')

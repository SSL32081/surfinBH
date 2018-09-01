import numpy as np
from surfinBH import surfinBH
import warnings

#=============================================================================
class Fit3dq8(surfinBH.SurFinBH):
    """ A class for the surfinBH3dq8 model presented in Varma et al., 2018,
    in prep. This model predicts the final mass mC, final spin chiC and final
    kick velocity velC, for the remnants of nonprecessing binary black hole
    systems. The fits are done using Gaussian Process Regression (GPR) and
    also provide an error estimate along with the fit value.

    This model has been trained in the parameter space:
        q <= 8, |chiAz| <= 0.8, |chiBz| <= 0.8

    However, it extrapolates reasonably to:
        q <= 10, |chiAz| <= 1, |chiBz| <= 1

    =========================================================================
    Usage:

    import surfinBH

    # Load the fit
    fit = surfinBH.LoadFits('surfinBH3dq8')

    # Define params
    q = 4.3             # Mass ratio q>=1
    chiA = [0,0,0.6]    # Spin of larger BH (z-direction only)
    chiB = [0,0,-0.7]   # Spin of smaller BH (z-direction only)

    ## Evaluate fits

    # remnant mass and 1-sigma error estimate
    mC, mC_err = fit.mC(q, chiA, chiB)

    # remnant spin and 1-sigma error estimate
    chiC, chiC_err = fit.chiC(q, chiA, chiB)

    # remnant recoil kick and 1-sigma error estimate
    velC, velC_err = fit.velC(q, chiA, chiB)

    # All of these together
    mC, chiC, velC, mC_err, chiC_err, velC_err = fit.all(q, chiA, chiB)

    The spin and kick vectors are defined in the coorbital frame at t=-100 M
    from the peak of the waveform. This frame is defined as:
    The z-axis is along the orbital angular momentum direction of the binary.
    The x-axis is along the line of separation from the smaller BH to
        the larger BH at this time.
    The y-axis completes the triad.
    We obtain this frame from the waveform as defined in arxiv:1705.07089.
    """

    #-------------------------------------------------------------------------
    def __init__(self, name):
        super(Fit3dq8, self).__init__(name)


    #-------------------------------------------------------------------------
    def _load_fits(self, h5file):
        """ Loads fits from h5file and returns a dictionary of fits. """
        fits = {}
        for key in ['mC', 'chiCz', 'velCx', 'velCy']:
            fits[key] = self._load_scalar_fit(fit_key=key, h5file=h5file)
        return fits

    #-------------------------------------------------------------------------
    def _get_fit_params(self, x, fit_key):
        """ Transforms the input parameter to fit parameters for the 3dq8 model.
    That is, maps from [q, chiAz, chiBz] to [np.log(q), chiHat, chi_a]
    chiHat is defined in Eq.(3) of 1508.07253.
    chi_a = (chiAz - chiBz)/2.
        """
        q, chiAz, chiBz = x
        eta = q/(1.+q)**2
        chi_wtAvg = (q*chiAz+chiBz)/(1.+q)
        chiHat = (chi_wtAvg - 38.*eta/113.*(chiAz + chiBz))/(1. - 76.*eta/113.)
        chi_a = (chiAz - chiBz)/2.
        fit_params = [np.log(q), chiHat, chi_a]
        return fit_params

    #-------------------------------------------------------------------------
    def _check_param_limits(self, q, chiA, chiB, **kwargs):
        """ Checks that x is within allowed range of paramters.
        Raises a warning if outside training limits and
        raises an error if outside allowed limits.
        Training limits: q <= 8.01, |chiAz| <= 0.81, |chiBz| <= 0.81.
        Allowed limits: q <= 10.01, |chiAz| <= 1, |chiBz| <= 1.
        """
        if np.sqrt(np.sum(chiA[:2]**2)) > 1e-10:
            raise ValueError('The x and y components of chiA should be zero.')

        if np.sqrt(np.sum(chiB[:2]**2)) > 1e-10:
            raise ValueError('The x and y components of chiB should be zero.')

        if q < 1:
            raise ValueError('Mass ratio should be >= 1.')
        elif q > 10.01:
            raise Exception('Mass ratio outside allowed range.')
        elif q > 8.01:
            warnings.warn('Mass ratio outside training range.')

        if abs(chiA[2]) > 1.:
            raise Exception('Spin magnitude of BhA outside allowed range.')
        elif abs(chiA[2]) > 0.81:
            warnings.warn('Spin magnitude of BhA outside training range.')

        if abs(chiB[2]) > 1.:
            raise Exception('Spin magnitude of BhB outside allowed range.')
        elif abs(chiB[2]) > 0.81:
            warnings.warn('Spin magnitude of BhB outside training range.')

    #-------------------------------------------------------------------------
    def _eval_wrapper(self, fit_key, q, chiA, chiB, **kwargs):
        """ Evaluates the surfinBH3dq8 model.
        """
        chiA = np.array(chiA)
        chiB = np.array(chiB)

        # Warn/Exit if extrapolating
        self._check_param_limits(q, chiA, chiB, **kwargs)

        self._check_unused_kwargs(kwargs)

        x = [q, chiA[2], chiB[2]]
        if fit_key == 'mC' or fit_key == 'all':
            mC, mC_err = self._evaluate_fits(x, 'mC')
            if fit_key == 'mC':
                return mC, mC_err
        if fit_key == 'chiC' or fit_key == 'all':
            chiCz, chiCz_err = self._evaluate_fits(x, 'chiCz')
            chiC = np.array([0,0,chiCz])
            chiC_err = np.array([0,0,chiCz_err])
            if fit_key == 'chiC':
                return chiC, chiC_err
        if fit_key == 'velC' or fit_key == 'all':
            velCx, velCx_err = self._evaluate_fits(x, 'velCx')
            velCy, velCy_err = self._evaluate_fits(x, 'velCy')
            velC = np.array([velCx, velCy, 0])
            velC_err = np.array([velCx_err, velCy_err, 0])
            if fit_key == 'velC':
                return velC, velC_err
        if fit_key == 'all':
            return mC, chiC, velC, mC_err, chiC_err, velC_err

"""
Wrappers around ElectronOZM and ProtonOZM to be used as sherpa models
"""

import numpy as np
from .onezone import ElectronOZM, ProtonOZM

from sherpa.models.parameter import Parameter, tinyval
from sherpa.models.model import ArithmeticModel, modelCacher1d


def _mergex(xlo,xhi,midpoints=False):
    """
    We are assuming that points are consecutive, so that xlo[n]=xhi[n-1]
    This is usually valid for fits from a single spectrum, but breaks for
    simultaneous multiwavelength fitting
    """
    N=xlo.size
    x=np.zeros(N+1)
    x[:N]=xlo.copy()
    x[-1]=xhi[-1]

    if midpoints:
        mid=(xlo+xhi)/2.
        x=np.concatenate((x,mid))
        x.sort()

    return x

class InverseCompton(ArithmeticModel):
    def __init__(self,name='IC'):
        self.index   = Parameter(name, 'index', 2.0, min=-10, max=10)
        self.ref     = Parameter(name, 'ref', 20, min=0, frozen=True)
        self.ampl    = Parameter(name, 'ampl', 1, min=0)
        self.cutoff  = Parameter(name, 'cutoff', 1e15, min=0,frozen=True)
        self.beta    = Parameter(name, 'beta', 1, min=0, max=10, frozen=True)
        ArithmeticModel.__init__(self,name,(self.index,self.ref,self.ampl,self.cutoff,self.beta))
        self._use_caching = True
        self.cache = 10

    def guess(self,dep,*args,**kwargs):
        # guess normalization from total flux
        xlo,xhi=args
        model=self.calc([p.val for p in self.pars],xlo,xhi)
        modflux=np.trapz(model,xlo)
        obsflux=np.trapz(dep*(xhi-xlo),xlo)
        self.ampl.set(self.ampl.val*obsflux/modflux)

    @modelCacher1d
    def calc(self,p,xlo,xhi):

        index,ref,ampl,cutoff,beta = p

        # Sherpa provides xlo, xhi in KeV, we convert to eV and merge into a
        # single array
        outspec=_mergex(xlo,xhi)*1e3

        ozm=ElectronOZM(outspec,
                ampl,
                index=index,
                norm_energy=ref*1e12,
                cutoff=cutoff*1e12,
                beta=beta,
                seedspec=['CMB',],
                nolog=True,
                gmin=1e5,
                gmax=1e10,
                ngamd=30,
                )

        ozm.calc_ic()
        model=ozm.specic
        del ozm # avoid memory leaks

        # Do a trapz integration to obtain the photons per bin
        photons=(outspec[1:]-outspec[:-1])*((model[1:]+model[:-1])/2.)

        print outspec.min(), outspec.max(),len(outspec), p, np.trapz((outspec*1.60217656e-12)*model,outspec)

        return photons

class Synchrotron(ArithmeticModel):
    def __init__(self,name='IC'):
        self.index   = Parameter(name, 'index', 2.0, min=-10, max=10)
        self.ref     = Parameter(name, 'ref', 20, min=0, frozen=True)
        self.ampl    = Parameter(name, 'ampl', 1, min=0)
        self.cutoff  = Parameter(name, 'cutoff', 1e15, min=0,frozen=True)
        self.beta    = Parameter(name, 'beta', 1, min=0, max=10, frozen=True)
        self.B       = Parameter(name, 'B', 1, min=0, max=10, frozen=True)
        ArithmeticModel.__init__(self,name,(self.index,self.ref,self.ampl,self.cutoff,self.beta,self.B))
        self._use_caching = True
        self.cache = 10

    def guess(self,dep,*args,**kwargs):
        # guess normalization from total flux
        xlo,xhi=args
        model=self.calc([p.val for p in self.pars],xlo,xhi)
        modflux=np.trapz(model,xlo)
        obsflux=np.trapz(dep*(xhi-xlo),xlo)
        self.ampl.set(self.ampl.val*obsflux/modflux)

    @modelCacher1d
    def calc(self,p,xlo,xhi):

        index,ref,ampl,cutoff,beta,B = p

        # Sherpa provides xlo, xhi in KeV, we convert to eV and merge into a
        # single array
        outspec=_mergex(xlo,xhi)*1e3

        ozm=ElectronOZM(outspec,
                ampl,
                index=index,
                norm_energy=ref*1e12,
                cutoff=cutoff*1e12,
                beta=beta,
                B=B,
                seedspec=['CMB',],
                nolog=True,
                gmin=1e5,
                gmax=1e10,
                ngamd=30,
                )

        ozm.calc_sy()
        model=ozm.specsy
        del ozm # avoid memory leaks

        # Do a trapz integration to obtain the photons per bin
        photons=(outspec[1:]-outspec[:-1])*((model[1:]+model[:-1])/2.)

        print outspec.min(), outspec.max(),len(outspec), p, np.trapz((outspec*1.60217656e-12)*model,outspec)

        return photons

class PionDecay(ArithmeticModel):
    def __init__(self,name='pp'):
        self.index   = Parameter(name,  'index',   2.1,  min=-10,  max=10)
        self.ref     = Parameter(name,  'ref',     60,   min=0,    frozen=True)
        self.ampl    = Parameter(name,  'ampl',    100,    min=0)
        self.cutoff  = Parameter(name,  'cutoff',  0,    min=0,    frozen=True)
        self.beta    = Parameter(name,  'beta',    1,    min=0,    max=10,       frozen=True)
        ArithmeticModel.__init__(self,name,(self.index,self.ref,self.ampl,self.cutoff,self.beta))
        self._use_caching = True
        self.cache = 10

    def guess(self,dep,*args,**kwargs):
        # guess normalization from total flux
        xlo,xhi=args
        model=self.calc([p.val for p in self.pars],xlo,xhi)
        modflux=np.trapz(model,xlo)
        obsflux=np.trapz(dep*(xhi-xlo),xlo) 
        self.ampl.set(self.ampl.val*obsflux/modflux)

    @modelCacher1d
    def calc(self,p,xlo,xhi):

        index,ref,ampl,cutoff,beta = p

        if cutoff == 0:
            cutoff=None
        else:
            cutoff*=1e12

        # Sherpa provides xlo, xhi in KeV, we convert to eV and merge into a
        # single array
        outspec=_mergex(xlo,xhi)*1e3

        ozm=ProtonOZM(outspec,
                ampl,
                index=index,
                norm_energy=ref*1e12,
                cutoff=cutoff,
                beta=beta,
                seedspec=['CMB',],
                nolog=True,
                Etrans=1e10,
                )

        ozm.calc_outspec()
        model=ozm.specpp
        del ozm # avoid memory leaks

        # Do a trapz integration to obtain the photons per bin
        photons=(outspec[1:]-outspec[:-1])*((model[1:]+model[:-1])/2.)

        print outspec.min(), outspec.max(),len(outspec), p, np.trapz((outspec*1.60217656e-12)*model,outspec)

        return photons

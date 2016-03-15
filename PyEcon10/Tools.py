# -*- coding: utf-8 -*-
# Tools.py
from scipy import *
from scipy import signal
from scipy import fftpack
import pandas as pd


def FFT(TD,T=None):
    """
    Single time domain array (TD) to FFT series and powerspectrum
    """
    TD = array(TD).flatten()    
    Tfull = TD.shape[0]

    if T==None:
        nn = argmin(abs(Tfull-array([2**n for n in range(14)])))
        T = 2**nn

    # cencering    
    TD=TD[-T:]
        
    
    # Detrend
    TD=signal.detrend(TD)
    
    # Windowing
    TD=TD*signal.hamming(T)
    
    # Tsukiyama [2013]
    a=10.0
    b=10.0
    
    def TK(t):
        if t>T/2.:
            return 1.0/(1.0+b*exp((t-T)/a))
        else:
            return 1.0/(1.0+b*exp(-t/a))
    
    TD=TD*map(TK,arange(T))
    
    
    # Do FFT
    FD = fftpack.fft(TD)
    fX = fftpack.fftfreq(T) # freq list
    PS = array([sqrt(c.real ** 2 + c.imag ** 2) for c in FD])/T
    fXr=fX[fX>=0]
    PSr=PS[fX>=0]

    return {'fXr':fXr,'PSr':PSr,"FD":FD}
    
    

# Agent list operation support -----------------------------

def ID_pick(agents,ID):
    return agents[[agents[i].ID for i in range(len(agents))].index(ID)]
    
    
def ID_ind(agents,ID):
    return [agents[i].ID for i in range(len(agents))].index(ID)


# DataFrame ala Distibution as a cell ----------------------

def Data_agr(Data, varlst, how='mean'):
    if how=='mean':
        return pd.DataFrame([[nanmean(Data[varlst][v].iloc[i]) for v in varlst] for i in range(Data.shape[0])],index=Data.index,columns=varlst)
        
    if how=='sum':
        return pd.DataFrame([[nansum(Data[varlst][v].iloc[i]) for v in varlst] for i in range(Data.shape[0])],index=Data.index,columns=varlst)






# Dictionary List manuplation ------------------------------------------------------

def dict_dst(lst_of_dict,com_keys=None):
    """
    return value distributions of common keys in multiple dictionaries
    """
    if com_keys==None:
        com_keys=lst_of_dict[0].keys()
    
    newdict={}
    for key in com_keys:
        dst=[]
        for Dict in lst_of_dict:
            dst.append(Dict[key])
        newdict[key]= dst
        
    return newdict






def dict_sum(lst_of_dict,com_keys=None):
    """
    return a summed dict of common keys in multiple dictionaries
    Each element of key must be able to numerically sum up
    """
    if com_keys==None:
        com_keys=lst_of_dict[0].keys()
            
    newdict={}
    for key in com_keys:
        val=0
        for Dict in lst_of_dict:
            val=val+Dict[key]
        newdict[key]=val
        
    return newdict



def dict_sumprod(lst_of_dict,weight,com_keys=None):
    """
    return a sumproduct dict of common keys in multiple dictionaries
    Each element of key must be able to numerically sum and prod
    """
    if com_keys==None:
        com_keys=lst_of_dict[0].keys()
        
    newdict={}
    Nlst = len(lst_of_dict)
    for key in com_keys:
        val=0
        for i in range(Nlst):
            Dict=lst_of_dict[i]
            val=val+weight[i]*Dict[key]
        newdict[key]=val
        
    return newdict



def dict_mean(lst_of_dict,com_keys=None):
    """
    return a mean dict of common keys in multiple dictionaries
    Each element of key must be able to numerically mean
    """
    if com_keys==None:
        com_keys=lst_of_dict[0].keys()
    
    newdict={}
    Nlst = len(lst_of_dict)
    for key in com_keys:
        val=0
        for Dict in lst_of_dict:
            val=val+(1.0/Nlst)*Dict[key]
        newdict[key]=val
        
    return newdict


    
    

def dict_std(lst_of_dict,com_keys=None):
    """
    return a mean dict of common keys in multiple dictionaries
    Each element of key must be able to numerically mean
    """
    if com_keys==None:
        com_keys=lst_of_dict[0].keys()
    
    newdict={}
    Nlst = len(lst_of_dict)
    for key in com_keys:
        temp=[]
        for Dict in lst_of_dict:
            temp.append(Dict[key])
        newdict[key]=std(array(temp),axis=0)
    
    return newdict




def dict_median(lst_of_dict,com_keys=None):
    """
    return a mean dict of common keys in multiple dictionaries
    Each element of key must be able to numerically mean
    """
    if com_keys==None:
        com_keys=lst_of_dict[0].keys()
    
    newdict={}
    Nlst = len(lst_of_dict)
    for key in com_keys:
        temp=[]
        for Dict in lst_of_dict:
            temp.append(Dict[key])
        newdict[key]=median(array(temp),axis=0)
    
    return newdict
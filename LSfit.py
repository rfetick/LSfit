# -*- coding: utf-8 -*-
"""
Created on Tue Jan 02 17:57:41 2018

Least-square minimization algorithm
Xhi = sum(weights*(f(X,param) - data)^2)

WEIGHTS = 1/sigma^2 for a homogeneous gaussian noise
WEIGHTS = 1/data for a Poisson-like noise

TO-DO
- Create a LSfit2D(.)
- Define more precisely stopping criteria for algorithm
- Include Levenberg-Marquardt regularization to help convergence
- String formatting for "eval(.)" is ugly, improve that
- Check the WEIGHTED least-square convergence

EXAMPLE
# DEFINE NOISY GAUSS
from numpy import linspace, array
from numpy.random import rand
from pylab import plot, legend
X = linspace(0,10,num=100)
paramTrue = array([1.,5.,1.,5.])
Ytrue = gauss(X,paramTrue)
Ynoisy = Ytrue + 2*(rand(100)-.5)
# MINIMIZATION
param0 = array([1.5,4.,2.,5.5])
Ystart = gauss(X,param0)
param = LSfit('gauss',Ynoisy,X,param0)
Yfit = gauss(X,param)
# SHOW RESULTS
print "Param      : [bck,amp,sig,mid]"
print "Param true : "+str(paramTrue)
print "Param start: "+str(param0)
print "Param fit  : "+str(param)
plot(X,Ytrue,'b',linewidth=3)
plot(X,Ynoisy,'orange',linewidth=2)
plot(X,Ystart,'g',linewidth=2)
plot(X,Yfit,'r',linewidth=2)
legend(("True","Noisy","Start","Fit"))

@author: rfetick
"""

# arange might be used as a string in eval('arange(.)')
# so I let it, whatever the warning says
from numpy import size, zeros, arange, array, dot, eye, diag
from scipy.linalg import inv

def LSfit(funct_str,data,X,param0, weights=-1, quiet=False, LM=False):
    """
    ### USAGE ###
     Parametric least-square fitting.
     Minimises Xhi2 = sum(weights*(f(X,param) - data)^2)
     where the sum(.) is on the coordinates X
     "data" is the noisy observation
     "f(X,param)" is your model, with the vector of parameters "param" and evaluated on coordinates X
    ### INPUTS ###
     funct_str - [String] Name of the function to call
     data      - [Vector] Noisy data
     X         - [Vector] Coordinates where to evaluate the function
     param0    - [Vector] First estimation of parameters
    ### OPTIONAL INPUTS ###
     weights   - [Vector] Weights (1/noise^2) on each coordinate X
     quiet     - [Boolean] Print status of algorithm
     LM        - [Boolean] Levenberg-Marquardt algorithm
    ### OUTPUT ###
     param     - [Vector] Best parameters for least-square fitting
    """
    # INITIALIZATION
    sX = size(X)
    sP = size(param0)
    J = zeros((sX,sP)) # Jacobian
    h = 1e-10 #step to compute Jacobian
    param = param0.copy()
    
    # STOPPING CONDITIONS
    J_min = 1e-5*sP*sP # stopping criteria based on small Jacobian
    dp_min = 1e-7 # stopping criteria based on small variation of parameters
    max_iter = 3000 # stopping criteria based on max number of iteration
    stop_loop = False # boolean for stopping the loop
    stop_trace = "Maximum iteration reached (iter="+str(max_iter)+")"
    
    # WEIGHTS
    if size(weights)==1 and weights<=0:
        weights = zeros(sX)+1
    elif size(weights)>1 and size(weights)!=sX:
        raise ValueError("WEIGHTS should be a scalar or same size as X")
    
    # LEVENBERG-MARQUARDT
    # Not used yet, "mu" should be modified in the loop, but how?
    mu = 0
    if LM:
        mu = 1
    
    # FORMAT Xstr for eval(.)
    # Ugly method :(
    Xstr = array2str(X)
    
    # LOOP
    i = 0
    while (i < max_iter) and not stop_loop:
        
        # FORMAT Pstr for eval(.)
        # Ugly method :(
        Pstr = array2str(param)
        
        f_str = funct_str+'('+Xstr+','+Pstr+')'
        f = eval(f_str)
        
        ## Iterate over each parameter to compute derivative
        for ip in arange(sP):
            dparam = zeros(sP)
            dparam[ip] = h
            
            # FORMAT dPstr for eval(.)
            # Ugly method :(
            dPstr = array2str(dparam)
            
            df_str = funct_str+'('+Xstr+','+Pstr+'+'+dPstr+')'
            J[:,ip] = weights*(eval(df_str)-f)/h
        
        ## Compute dparam = -{(transpose(J)*J)^(-1)}*transpose(J)*(func-data)
        # It is possible to implement Levenberg-Marquardt if you know in which
        # way to modify "mu" in the loop
        JTJ = dot(J.T,J)
        dparam = - dot(dot(inv(JTJ+mu*diag(JTJ.diagonal())),J.T),weights*(f-data))
        param = param + dparam
        
        ## Xhi square
        Xhi2 = sum(weights*(f-data)**2)
        if not quiet:
            if not LM:
                print "Xhi2 = "+str(Xhi2)
            else:
                print "Xhi2 = "+str(Xhi2)+" [mu="+str(mu)+"]"
        if LM:
            Pstr = array2str(param)
            f_str = funct_str+'('+Xstr+','+Pstr+')'
            f = eval(f_str)
            Xhi2_new = sum(weights*(f-data)**2)
            if Xhi2_new > Xhi2:
                mu = 10*mu
            else:
                mu = 0.1*mu
        
        ##Stop loop based on small variation of parameter
        if sum(abs(dparam)) < dp_min*sum(abs(param)):
            stop_loop = True
            stop_trace = "Parameter not evolving enough at iter="+str(i)
        
        ## Stop loop based on small Jacobian
        if abs(J).sum() < J_min:
            stop_loop = True
            stop_trace = "Jacobian small enough at iter="+str(i)
        
        ## Increment
        i = i+1  
    
    if not quiet:
        print " "
        print "Stopping condition: "+stop_trace
        print " "
    
    return param
    



###############################################################################
#    Function to transform array to a string that can be used in eval(.)      #
###############################################################################

def array2str(arr):
    arrStr = str(arr)
    arrStr = arrStr.replace('\n','')
    arrStr = arrStr.replace(' ',',')
    for i in arange(10):
        arrStr = arrStr.replace(',,',',')
    arrStr = arrStr.replace('[,','[')
    arrStr = arrStr.replace(',]',']')
    arrStr = 'array('+arrStr+')'
    return arrStr
    


###############################################################################
#    I provide here the function "gauss(X,A) to run the example in LSfit      #
###############################################################################

from numpy import exp

def gauss(X,A):
    return A[1]*exp(-((X-A[3])**2)/(2*A[2]**2))+A[0]


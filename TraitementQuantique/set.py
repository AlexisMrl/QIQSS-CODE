#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
    Python module for the simulation of single-electron devices.
    Master equation approach.

    Mathieu Pierre - november 2008
"""

try:
    import scipy
    import scipy.linalg
except ImportError:
    raise ImportError, 'Please install Python-Scipy. http://www.scipy.org/'

# Constants
from scipy.constants import Boltzmann as kB
from scipy.constants import e
h = 6.62607015e-34

# Function definitions
def convol_fermi(x):
    """autoconvolution of fermi-dirac function"""
    temp = x/(scipy.exp(x)-1)
    # Undertermined values NaN (not a number) due to null values are replaced by 1.
    temp[scipy.nonzero(scipy.isnan(temp))]=1
    return temp             
    
def fermi(x):
    """fermi-dirac function"""
    return 1/(scipy.exp(x)+1)

def delta(x):
    return x

#TODO  delta function : to be implemented for tunnel rate between two levels
#def delta(x,L):
#    """delta function"""
#    if abs(x)<L :
#        return 1
#    else :
#        return 0


#--------------------------------------------------------------------------------
class SET:
    """Class representing a coupled-dot circuit"""

    # Initialization
    #----------------------------------------------------------------------------
    def __init__(self,T=0):
        """Initialization : create a new SET class.
        optional parameter : temperature system in Kelvin
        """
        self.set_temperature(T)
        self.refgates =[]
        self.refleads = []
        self.refdots = []
        self.dots = []
        self.links_dd = []
        self.links_dg = []
        self.links_dl = []

    # Interface
    #---------------------------------------------------------------------------
    def set_temperature(self,T):
        """Define system temperature (leads and metallic dots)
        T has to be given in K
        """        
        self.T = 1000*kB*T/e   # T in meV

    def add_metallic_dot(self, name, N, first=0, offset_energy=0):
        """add a new metallic dot to the system
        arguments :
                name : a string to identify the dot
                N    : maximum number of electrons
        optional :
                first : minimum number of electrons to consider
                offset_energy : offset level in meV
        """
        self.refdots.append(name)
        self.dots.append({'name':name,'nature':'o','first':first, 'last':N, 'level':offset_energy})

    def add_quantum_dot(self, name, levels, degeneracy=0):
        """add a new quantum dot to the system
        arguments :
                name : a string to identify the dot
                levels : a list of energy levels in meV
        optional :
                degeneracy : corresponding levels degeneracy (list of integers)
        """
        if degeneracy==0 :
            degeneracy = scipy.ones(scipy.shape(levels),dtype=int).tolist()
        self.refdots.append(name)
        self.dots.append({'name':name,'nature':'q','level':levels, 'degeneracy':degeneracy})
        
    def add_lead(self, name):
        """add a new lead"""
        self.refleads.append(name)

    def add_gate(self, name):
        """add a new gate"""
        self.refgates.append(name)

    def add_link(self, nature, name1, name2, C, G=0):
        """add a new link between dots, leads and gates
        first argument : the nature of the link
            'dd' : between two dots
            'dl' : between a dot and a lead
            'dg' : between a dot and a gate
        second and third arguments : the names of the elements
        fourth argument : the capacitance in F
        last argument : 
            - a conductance in e^2/h unit for metallic dots
            - or a current in A if one of the elements is a quantum dot
        """
        if nature == 'dd':
            self.links_dd.append((name1,name2,C,G))
        if nature == 'dg':
            self.links_dg.append((name1,name2,C))        
        if nature == 'dl':
            self.links_dl.append((name1,name2,C,G))             


    # Preprocessing : needed before any calculation
    #---------------------------------------------------------------------------
    def pre_processing(self):
        """Initialize all matrices needed for the calculations"""

        # Number of dots, leads and gates
        self.nd = len(self.refdots)	   # number of dots
        self.nl = len(self.refleads)   # number of leads       
        self.ng = len(self.refgates)   # number of gates 
        self.refdotsleads = self.refdots + self.refleads

        # Capacitance matrices (unit : e/mV)
        #  A between dots
        #  B between dots and leads, and dots and gates
        #  C deduced from A and B to calculate the energy
        A = scipy.zeros((self.nd,self.nd),dtype=float)
        B = scipy.zeros((self.nd,self.nl+self.ng),dtype=float)
        for (dot1,dot2,C,G) in self.links_dd:
            i=self.refdots.index(dot1)
            j=self.refdots.index(dot2)
            A[i,j]=C
            A[j,i]=C
        for (dot,lead,C,G) in self.links_dl:
            i=self.refdots.index(dot)
            j=self.refleads.index(lead)
            B[i,j]=C
        for (dot,gate,C) in self.links_dg:
            i=self.refdots.index(dot)
            j=self.refgates.index(gate)+self.nl
            B[i,j]=C
        self.B= B/1000.0/e
        A = A/1000.0/e
        self.C = -A + scipy.diag(scipy.sum(self.B,1)+scipy.sum(A,1)) # sum along the lines
        self.invC = scipy.linalg.inv(self.C)

        # States and levels
        #-----------------------------------------------------------------------        
        # Each state is a column in both arrays self.states ans self.states2 :
        #    - self.states contains the number of electrons in each level
        #    - self.states2 contains the number of electrons in each dot
        #    The difference comes from quantum dots with several levels.
        # We also creates two vectors whose length is the state vector length:
        #    - which_dot : indicates which dot the level belongs to
        #    - which_level : indicates which level of its dot the level is.
        #    Example : 1 dot with 1 level - 1 dot with 3 levels
        #    which_dot = [0, 1, 1, 1]
        #    which_level = [0, 0, 1, 2]
        # energy_levels contains the offset energy of each level
        #-----------------------------------------------------------------------
        self.states=[[]] # list of states
        self.energy_levels=[]
        self.which_dot=[]
        self.which_level=[]
        
        # We first create the first (developped) form of state vectors.
        for dot in self.dots:
            if dot['nature'] == 'o':
                first = dot['first']
                last = dot['last']
                self.states = [ state+[n] for state in self.states for n in xrange(first,last+1)]
                self.energy_levels.append(dot['level'])
                self.which_dot.append(self.refdots.index(dot['name'])) # dot number        
                self.which_level.append(0) # only level 0 for a metallic dot
            else:
                self.energy_levels += dot['level']
                self.which_dot += [ self.refdots.index(dot['name']) for i in dot['level']]
                self.which_level += [ i for i in range(0,len(dot['level']))] # [0, 1, 2,...]
                dot_states = [[]] # list of dot states
                for i in xrange(0,len(dot['level'])):
                    dot_states = [ state+[n] for state in dot_states for n in xrange(0,dot['degeneracy'][i]+1)]
                self.states = [ state+dot_state for state in self.states for dot_state in dot_states ]

        # convert from lists into scipy.arrays for calculations
        self.states = scipy.array(self.states).transpose()
        self.energy_levels = scipy.array(self.energy_levels)

        # To obtain the second form of state vectors, we will use a transformation matrix
        matrix = scipy.zeros((len(self.refdots),len(self.which_dot)),dtype=int)
        for i in range(0,len(self.which_dot)):
           matrix[self.which_dot[i],i]=1
        self.states2 = scipy.dot(matrix,self.states)

        
        # Now we prepare the calculations. For each transition between one state and one other,
        # we store in several arrays the parameters to use to compute the transition rate.
        self.s = self.states.shape[1] # number of states
        self.k = len(self.refdotsleads)  # number of dots+leads        
        s = self.s        
        k = self.k

        self.m2m = scipy.zeros((4,0),dtype=int)
        self.d2m = scipy.zeros((4,0),dtype=int)
        self.d2d = scipy.zeros((4,0),dtype=int)

        self.bias = scipy.zeros((4,0),dtype=int)
        self.index_bias = []
        self.sgn_bias = []
        self.prefactor = scipy.zeros((s,s,k,k),dtype=float)

        for n in range(0,s):
            final = self.states[:,n]
            for m in range(0,s):
                initial = self.states[:,m]           
                # given an initial and a final state, we have to determine
                # if they correspond to a transition involving a single electron tunneling
                transition = final - initial # difference between initial and final occupation
                # list of levels which received an electron
                gain = scipy.nonzero(transition > 0)[0]
                # list of levels which lost an electron
                loss = scipy.nonzero(transition < 0)[0]

                # first case : a level received an electron
                # It comes from the leads connected to this dot
                if len(gain)==1 and len(loss)==0 and transition[gain[0]]==1:
                    dotnum = self.which_dot[gain[0]] # number of the dot
                    dot = self.dots[dotnum] # properties of the dot
                    for (d,lead,C,G) in self.links_dl:
                        # We study all links between a dot and a contact
                        if d==dot['name']:
                            j=self.refleads.index(lead) # number of the lead                            
                            if dot['nature']=='o':
                                self.m2m  = scipy.concatenate((self.m2m,scipy.array([n,m,dotnum,self.nd+j]).reshape((4,1))),1)         
                                self.bias = scipy.concatenate((self.bias,scipy.array([n,m,dotnum,self.nd+j]).reshape((4,1))),1)
                                self.index_bias.append(j)
                                self.sgn_bias.append(1)
                                self.prefactor[n,m,dotnum,self.nd+j] = G*self.T/1000.0/h*e                                
                            else :
                                levelnum = self.which_level[gain[0]]
                                self.d2m  = scipy.concatenate((self.d2m,scipy.array([n,m,dotnum,self.nd+j]).reshape((4,1))),1)
                                self.bias = scipy.concatenate((self.bias,scipy.array([n,m,dotnum,self.nd+j]).reshape((4,1))),1)
                                self.index_bias.append(j)
                                self.sgn_bias.append(1)
                                self.prefactor[n,m,dotnum,self.nd+j] = G/e * (dot['degeneracy'][levelnum] - initial[gain[0]])

                # second case : a level lost an electron
                # It goes to the leads connected to this dot
                if len(gain)==0 and len(loss)==1 and transition[loss[0]]==-1:
                    dotnum = self.which_dot[loss[0]] # number of the dot
                    dot = self.dots[dotnum] # properties of the dot
                    for (d,lead,C,G) in self.links_dl:
                        # We study all links between a dot and a contact
                        if d==dot['name']:
                            j=self.refleads.index(lead) # number of the lead
                            if dot['nature']=='o':
                                self.m2m  = scipy.concatenate((self.m2m,scipy.array([n,m,self.nd+j,dotnum]).reshape((4,1))),1)
                                self.bias = scipy.concatenate((self.bias,scipy.array([n,m,self.nd+j,dotnum]).reshape((4,1))),1)
                                self.index_bias.append(j)
                                self.sgn_bias.append(-1)
                                self.prefactor[n,m,self.nd+j,dotnum] = G*self.T/1000.0/h*e                                
                            else :
                                levelnum = self.which_level[loss[0]]
                                self.d2m  = scipy.concatenate((self.d2m,scipy.array([n,m,self.nd+j,dotnum]).reshape((4,1))),1)
                                self.bias = scipy.concatenate((self.bias,scipy.array([n,m,self.nd+j,dotnum]).reshape((4,1))),1)
                                self.index_bias.append(j)
                                self.sgn_bias.append(-1)
                                self.prefactor[n,m,self.nd+j,dotnum] = G/e * (initial[loss[0]])

                # third case : exchange between two dots
                if len(gain)==1 and len(loss)==1 and transition[gain[0]]==1 and transition[loss[0]]==-1 :
                    dotnum1 = self.which_dot[gain[0]] # number of the dot
                    dotnum2 = self.which_dot[loss[0]] # number of the dot
                    # we check that the two dots are not the same - no relaxation between levels of a dot                
                    if dotnum1 != dotnum2 :
                        dot1 = self.dots[dotnum1] # properties of the dot
                        dot2 = self.dots[dotnum2] # properties of the dot
                        for (d1,d2,C,G) in self.links_dd:
                            # We study all links between two dots
                            if (d1==dot1['name'] and d2==dot2['name']) or (d1==dot2['name'] and d2==dot1['name']):                        
                                if dot1['nature']=='o' and dot2['nature']=='o':
                                    self.m2m  = scipy.concatenate((self.m2m,scipy.array([n,m,dotnum1,dotnum2]).reshape((4,1))),1)
                                    self.prefactor[n,m,dotnum1,dotnum2] = G*self.T/1000.0/h*e
                                if dot1['nature']=='q' and dot2['nature']=='o':
                                    levelnum = self.which_level[gain[0]]
                                    self.d2m  = scipy.concatenate((self.d2m,scipy.array([n,m,dotnum1,dotnum2]).reshape((4,1))),1)
                                    self.prefactor[n,m,dotnum1,dotnum2]= G/e * (dot['degeneracy'][levelnum] - initial[gain[0]])
                                if dot1['nature']=='o' and dot2['nature']=='q':
                                    levelnum = self.which_level[loss[0]]
                                    self.d2m  = scipy.concatenate((self.d2m,scipy.array([n,m,dotnum1,dotnum2]).reshape((4,1))),1)
                                    self.prefactor[n,m,dotnum1,dotnum2] = G/e * (initial[loss[0]])
                                if dot1['nature']=='q' and dot2['nature']=='q':
                                    levelnum1 = self.which_level[gain[0]]        
                                    levelnum2 = self.which_level[loss[0]]
                                    self.d2d  = scipy.concatenate((self.d2d,scipy.array([n,m,dotnum1,dotnum2]).reshape((4,1))),1)
                                    self.prefactor[n,m,dotnum1,dotnum2] = G/e * (initial[loss[0]]) * (dot['degeneracy'][levelnum1] - initial[gain[0]])

        self.m2m = tuple(self.m2m)
        self.d2m = tuple(self.d2m)
        self.d2d = tuple(self.d2d)
        self.bias = tuple(self.bias)


    def getW(self,V):
        """compute the electrostatic energy of each state (meV)
        for a comparison between states at same bias		
        V : bias vector [Vleads	| Vgates] (mV)
        """	
        V=scipy.array(V)
        self.V=V
        V=V[:,scipy.newaxis]
        X = self.states2 - scipy.dot(self.B,V)

        self.W = 0.5 * scipy.sum(X * scipy.dot(self.invC, X),0) + scipy.dot(self.energy_levels , self.states)


    def tunnel_rate(self,V):
        """compute the transition rate between states
        V : bias vector [Vleads	| Vgates] (mV)
        """
        # First we compute the energy of each state
        self.getW(V)
        # Then we compute the energy difference between each couple of state        
        self.diffW = self.W[:,scipy.newaxis]-self.W[scipy.newaxis,:]        

        # We add the energy given by the lead
        self.diffE = scipy.zeros((self.s,self.s,self.k,self.k),dtype=float)
        self.diffE[self.bias] = self.sgn_bias * scipy.take(V,self.index_bias)
        self.diffE += self.diffW[:,:,scipy.newaxis,scipy.newaxis]

        # normalization
        self.diffE = self.diffE / self.T

        # Finally we compute the transition rate
        self.gamma = scipy.zeros(self.diffE.shape,dtype=float)
        i = self.m2m
        #print(self.diffE[i])
        self.gamma[i] = convol_fermi(self.diffE[i])
        i = self.d2m
        self.gamma[i] = fermi(self.diffE[i])
        i = self.d2d
        self.gamma[i] = delta(self.diffE[i])

        self.gamma = self.prefactor * self.gamma


    def solver(self):
        """solve the problem"""
        s = self.s
        # We sum over axes 2 and 3 : all the tunneling events contributing to a transition
        gamma = scipy.sum(self.gamma,3)
        gamma = scipy.sum(gamma,2)       
        # The master equation is written under a matricial form
        # M*P=Z    -  M is deduced from Gamma
        M = gamma - scipy.diag(scipy.sum(gamma,0))
        Z=scipy.zeros((s,1))
        # The last line is replaced by a normalization equation sum(Pi)=1
        M[s-1,:]=scipy.ones((s),dtype=float)        
        Z[s-1,0]=1

        try :
            self.P = scipy.linalg.solve(M,Z)
        except scipy.linalg.basic.LinAlgError:
            print "matrice non inversible"""
            self.P = scipy.zeros((s,1))


    def current(self,i,j):
        """Current from i to j
        i,j : name of a dot or a lead
        """
        # We sum over the final state of transitions
        gamma_current = scipy.sum(self.gamma,0)
        ni = self.refdotsleads.index(i)
        nj = self.refdotsleads.index(j)
        I = -e * scipy.dot( (gamma_current[:,nj,ni] - gamma_current[:,ni,nj]) , self.P[:,0])
        return I

    def proba(self,i,level=-1):
        """Mean occupation of a dot or a level
        i : name of a dot
        optional :
            level : index of the level in the dot 
        """
        ni = self.refdots.index(i)
        if level == -1:
            P = scipy.dot(self.states2[ni,:] , self.P[:,0])
        else :
            n = self.which_dot.index(ni)
            P = scipy.dot(self.states[n+level,:] , self.P[:,0])
        return P

    def voltage(self,i):
        """Mean voltage of a dot (mV)
        i : name of a dot
        """
        ni = self.refdots.index(i)
        V = scipy.dot(self.invC, (self.states2 - scipy.dot(self.B, self.V)))
        return -scipy.dot(self.P[:,0], V[0,:])

# END of class
#-------------------------------------------------------------------------------

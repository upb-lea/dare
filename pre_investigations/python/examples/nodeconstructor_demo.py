import numpy as np
from pre_investigations.python.dare.utils.nodeconstructor import NodeConstructor
import control
import matplotlib.pyplot as plt

"""This file is intended to show the functionality of the NodeConstructor class. 
The class is used to generate the ODE system of a grid. 
The grid can ether be externally specified or randomly generated by the class itself. 
The goal is then to create the grid given the parameters of the objects within and generate the ODEs, 
which will then be output in the state space representation and 
can be solved via control.ss() (Source) or scipy.signal (Source).

For more documentation check out the nodeconstructor_demo.ipynb
"""

# define parameters
R = 0.4
L = 2.3e-3
C = 10e-6
LT = 2.3e-3
R_load = 14

parameter = dict()
parameter['R_source'] = R
parameter['L_source'] = L
parameter['C_source'] = C
parameter['L_cable'] = LT
parameter['R_cable'] = R
parameter['R_load'] = R_load

# set up CM
#An entry in the CM reads as follows: Object x (row) is connected to object y (column) via connection line z:
# x ---z---> y
CM = np.array([[0, 0, 1],
               [0, 0, 2],
               [-1, -2, 0]])

# grid with 2 sources, 1 load and a total of 2 connections
Grid_S2_L1_2C = NodeConstructor(2, 1, parameter, CM = CM)
Grid_S2_L1_2C.draw_graph()

# generate 5 sources + 5 loads grid with 10 % probability of a random connection source to source
# and 80 % source to load
Grid_S5_L5 = NodeConstructor(5, 5, parameter, S2S_p=0.1, S2L_p=0.8)

# corresponding graph
Grid_S5_L5.draw_graph()

A, B, C, D = Grid_S5_L5.get_sys()

sys = control.ss(A, B, C, D)

# define time vector
ts = 1e-4
t_end = 0.005
steps = int(1/ts)
t = np.arange(0, t_end+ts, ts)
num_samples = len(t)

# generate init state
x0 = np.zeros((A.shape[0],1))

# simple input signal of constant 230V from all sources
u = np.array([230]).repeat(Grid_S5_L5.num_source)[:,None] * np.ones((Grid_S5_L5.num_source,len(t)))

T, yout, xout = control.forced_response(sys, T=t, U=u, X0=x0, return_x=True, squeeze=True)

plt.plot(t, xout[1], label='$v_1$')
plt.xlabel(r'$t\,/\,\mathrm{s}$')
plt.ylabel('$v_{\mathrm{1}}\,/\,\mathrm{V}$')
plt.title('Plot current $v_1$')
plt.legend()
plt.grid()
plt.show()

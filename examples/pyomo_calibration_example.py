import wntr
import matplotlib.pyplot as plt 
from wntr.sim.solvers import PyomoSolver
import pyomo.environ as pyo
from pyomo.opt import SolverFactory
import numpy as np
import pandas as pd

################## Inputs ################## 
# Create a solver
opt = pyo.SolverFactory('ipopt')

inp_file = 'networks/Net1.inp'
mode = 'DD' # DD or PDD
HW_approx = 'piecewise' 
estimate_err = [0,20]	#mean, std for noise used to create initial estimate of pipe roughness
meas_error = [0,0]  #mean, std for noise used to create synthetic pressure observations, in meters of head
observed_nodes = ['11','32','21']		#nodes with (synthetic) measurements
param_to_var={'11':'hw_resistance[11]', '12':'hw_resistance[12]'}		#dict of parameters that will become decision variables, with pipe name as key and parameter name as value
tol= 0.5		#convergence tolerance for absolute difference between measured and computed pressures, in meters of head
np.random.seed(7)
delta_e=0.05		#+/- delta_e*e_star used in calculating sensitivity matrix
max_iter=100		#maximum number of iterations for convergence

################## Extract original model data and configuration ################## 
#Original Model that we are trying to uncover
wn = wntr.network.WaterNetworkModel(inp_file)

# Change from DD (default) to PDD
wn.options.hydraulic.demand_model=mode
wn.options.hydraulic.minimum_pressure=3.516		# 5 psi
wn.options.hydraulic.required_pressure=21.097	#30 psi

# Pipe roughness: decision variable
e_true={}
for pipe_name, pipe in wn.pipes():
	if pipe_name in param_to_var.keys():
		e_true.update({pipe_name : pipe.roughness})		#true values

# Simulate Hydraulics
sim = wntr.sim.WNTRSimulator(wn)
results = sim.run_sim(HW_approx=HW_approx, solver=PyomoSolver, solver_options={'tee': False})

################## Generate Synthetic Data ################## 
#Add noise to true head readings to generate synthetic head measurements
head = results.node['head']
head_meas = head[observed_nodes]
noise = np.random.normal(meas_error[0],meas_error[1],[len(head.index),len(observed_nodes)])
head_meas=head_meas+noise

################## Calibrate Hydraulic Model ################## 
# Solve using Pyomo and ipopt (PyomoSolver)
wn = wntr.network.WaterNetworkModel(inp_file)
wn.options.time.duration = 24*3600
sim = wntr.sim.WNTRSimulator(wn)

options={'tee': False, 'calibrate': True, 'meas': head_meas, 'param_to_var': param_to_var}
results2 = sim.run_sim(HW_approx=HW_approx, solver=PyomoSolver, solver_options=options)


################## Output ################## 
# Compare results
fig, (ax0, ax1) = plt.subplots(1,2, figsize=(10,5))
head_sim = results.node['head'].loc[6*3600, wn.junction_name_list]
flow_sim = results.link['flowrate'].loc[6*3600,:]
wntr.graphics.plot_network(wn, head_sim, flow_sim, title='True Configuration', ax=ax0)

head_opt = results2.node['head'].loc[6*3600, wn.junction_name_list]
flow_opt = results2.link['flowrate'].loc[6*3600,:]
wntr.graphics.plot_network(wn, head_opt, flow_opt, title='Pyomo Solver with Calibration', ax=ax1)
fig.suptitle('Network Operations at Hour 6', fontsize=16)

fig, (ax2, ax3) = plt.subplots(1,2, figsize=(10,5))
results.node['head'].plot(title='True Configuration', ax=ax2)
results2.node['head'].plot(title='Pyomo Solver with Calibration', ax=ax3)
fig.suptitle('Head', fontsize=16)

fig, (ax4, ax5) = plt.subplots(1,2, figsize=(10,5))
results.link['flowrate'].plot(title='True Configuration', ax=ax4)
results2.link['flowrate'].plot(title='Pyomo Solver with Calibration', ax=ax5)
fig.suptitle('Flowrate', fontsize=16)

for pipe_name in param_to_var.keys():
	res1=[wn.get_link(pipe_name).roughness]*len(results2.calibration.keys())
	res2=list()
	for t in results2.calibration.keys():
		res2.append(results2.calibration[t][pipe_name])
	plt.figure(pipe_name)
	plt.plot(list(results2.calibration.keys()),res2)
	plt.plot(list(results2.calibration.keys()),res1)
	plt.legend(['Calibration Results', 'Original Value'])
	plt.suptitle('Roughness on pipe '+pipe_name, fontsize=16)
plt.show()

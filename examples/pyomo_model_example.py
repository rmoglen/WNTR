import wntr

inp_file = 'networks/Net1.inp'

### Simulate with WNTRSimulator
wn = wntr.network.WaterNetworkModel(inp_file)
wn.options.time.duration = 24*3600

sim = wntr.sim.WNTRSimulator(wn)
sim_results = sim.run_sim(HW_approx='piecewise')

### Solve optimization with Pyomo
wn = wntr.network.WaterNetworkModel(inp_file)
wn.options.time.duration = 24*3600

pm = wntr.sim.PyomoModel(wn)
aml_model = pm.create_hydraulic_model()
pyomo_model, pyomo_map = pm.create_pyomo_model(aml_model)
opt_results = pm.solve()

### Plot results
head_sim = sim_results.node['head'].loc[12*3600, wn.junction_name_list]
flow_sim = sim_results.link['flowrate'].loc[12*3600,:]
wntr.graphics.plot_network(wn, head_sim, flow_sim, title='Simulation')

head_opt = opt_results.node['head'].loc[12*3600, wn.junction_name_list]
flow_opt = opt_results.link['flowrate'].loc[12*3600,:]
wntr.graphics.plot_network(wn, head_opt, flow_opt, title='Optimization')

sim_results.node['head'].plot(title='Simulation')
opt_results.node['head'].plot(title='Optimization')

sim_results.link['flowrate'].plot(title='Simulation')
opt_results.link['flowrate'].plot(title='Optimization')
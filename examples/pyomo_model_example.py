import wntr

inp_file = 'networks/Net1.inp'

### Simulate with WNTRSimulator
wn = wntr.network.WaterNetworkModel(inp_file)

sim = wntr.sim.WNTRSimulator(wn)
sim_results = sim.run_sim(HW_approx='piecewise')

head_sim = sim_results.node['head'].loc[3600, wn.junction_name_list]
flow_sim = sim_results.link['flowrate'].loc[3600,:]
wntr.graphics.plot_network(wn, head_sim, flow_sim, title='Simulation')

### Solve optimization with Pyomo
wn = wntr.network.WaterNetworkModel(inp_file)

pm = wntr.sim.PyomoModel(wn)
aml_model = pm.create_hydraulic_model()
pyomo_model, pyomo_map = pm.create_pyomo_model(aml_model)
opt_results = pm.solve()

head_opt = opt_results.node['head'].loc[3600, wn.junction_name_list]
flow_opt = opt_results.link['flowrate'].loc[3600,:]
wntr.graphics.plot_network(wn, head_opt, flow_opt, title='Optimization')

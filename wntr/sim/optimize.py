import wntr.sim as sim
try:
    import pyomo.environ as pe
    import pyomo.core.expr.current as EXPR
except:
    pe = None

class PyomoModel(object):
    
    def __init__(self, wn, mode='DD', HW_approx='piecewise'):
        
        if pe is None:
            raise ImportError('pyomo is required')
        
        self._wn = wn
        self._mode = mode
        self._HW_approx = HW_approx
        #self.aml_model, updater = self.create_hydraulic_model()
        #self.pyomo_model, self.pyomo_map = self.create_pyomo_model(self.aml_model)
        
    
    def create_hydraulic_model(self):
        aml_model, updater = sim.hydraulics.create_hydraulic_model(self._wn, mode=self._mode, 
                                           HW_approx=self._HW_approx)
        return aml_model
    
    def create_pyomo_model(self, aml_model):
        
        # Pyomo model
        pyomo_m = pe.Block(concrete=True)
        
        # Map of pyomo index to aml objects
        pyomo_map = {'params': {}, 
                     'vars': {},
                     'cons': {}} 
        
        # Maps aml parameters and variables to pyomo param and var
        # used to evaluate pyomo expressions
        aml_to_pyomo = {}
        
        ### Parameters
        n_params = len(list(aml_model.params()))
        pyomo_m.params = pe.Param(range(n_params), mutable=True)
        for i, p in enumerate(aml_model.params()):
            pyomo_m.params[i] = p._value
            pyomo_map['params'][i] = p
            aml_to_pyomo[p] = p._value
        
        ### Variables
        n_vars = len(list(aml_model.vars()))
        pyomo_m.vars = pe.Var(range(n_vars))
        for i, v in enumerate(aml_model.vars()):
            pyomo_m.vars[i].set_value(v._value) # intialize
            pyomo_map['vars'][i] = v
            aml_to_pyomo[v] = pyomo_m.vars[i]
            
        ### Constraint
        n_cons = len(list(aml_model.cons()))
        pyomo_m.cons = pe.Constraint(range(n_cons))
        for i, c in enumerate(aml_model.cons()):
            expr = c.expr
            pyomo_expr = expr.evaluate_pyomo(aml_to_pyomo)
            try:
                pyomo_m.cons[i] = pyomo_expr == 0
                pyomo_map['cons'][i] = c
            except: # infeasible constraint, occurs when pipes are closed?
                pass

        ### Objective
        pyomo_m.obj = pe.Objective(expr=1, sense=pe.minimize)
        
        return pyomo_m, pyomo_map
    
    def solve(self, tee=False):
    
        node_res, link_res = sim.hydraulics.initialize_results_dict(self._wn)
        results = sim.results.SimulationResults()
        results.error_code = None
        results.time = []
        results.network_name = self._wn.name
    
        while True:
            # Create an AML model
            aml_m = self.create_hydraulic_model()
            
            # Create a Pyomo model
            pyomo_m, pyomo_map = self.create_pyomo_model(aml_m)
            
            # Solve the Pyomo model
            opt = pe.SolverFactory('ipopt')
            opt.solve(pyomo_m, tee=tee)
    
            # Extract variable values and update the aml
            var_values = {}
            for i in pyomo_m.vars:
                val = pyomo_m.vars[i].value
                var_values[pyomo_m.vars[i].index()] = val
                pyomo_map['vars'][i].value = val # update the aml var 
            
            # Update wn
            sim.hydraulics.store_results_in_network(self._wn, aml_m)
            
            # Update the results object
            sim.hydraulics.save_results(self._wn, node_res, link_res)
            results.time.append(int(self._wn.sim_time))
            
            # Update sim time
            self._wn.sim_time += self._wn.options.time.hydraulic_timestep
            overstep = float(self._wn.sim_time) % self._wn.options.time.hydraulic_timestep
            self._wn.sim_time -= overstep
            
            if self._wn.sim_time > self._wn.options.time.duration:
                break
            
        sim.hydraulics.get_results(self._wn, results, node_res, link_res)
        
        return results

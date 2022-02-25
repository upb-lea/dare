import json
from os import makedirs
import pandas as pd

from pre_investigations.python.solver_investigations.timing_evaluation import plot_result, timing_experiment_simulation

parameter_used = dict()
parameter_used['R_source'] = 0.4
parameter_used['L_source'] = 2.3e-3
parameter_used['C_source'] = 10e-6
parameter_used['L_cabel'] = 2.3e-3
parameter_used['R_cabel'] = 0.4
parameter_used['R_load'] = 14
parameter_used['V_dc'] = 300

# hyperparameters:
repeat_used = 1
loops_used = 1
num_cm = 3
t_s_used = 1e-4
t_end_used = [0.03]  # , 0.1]
num_nodes_used = [6, 8, 10]
#used_methode = ['control.py', 'env_standalone', 'scipy_ode', 'scipy_odeint', 'scipy_solve_ivp']
#used_methode_args = ['discrete', '', {'integrator': 'lsoda', 'methode': 'bdf'}, 'LSODA', 'LSODA']
used_methode = [ 'env_standalone'] #, 'scipy_ode', 'scipy_odeint', 'scipy_solve_ivp']
used_methode_args = [ ''] #, {'integrator': 'lsoda', 'methode': 'bdf'}, 'LSODA', 'LSODA']
# store HPs to json
python_simulation_HPs = {
    't_s_used': t_s_used,
    't_end_used': t_end_used,
    'num_nodes_used': num_nodes_used,
    'used_methode': used_methode,
    'used_methode_args': used_methode_args,
    'parameter_used': parameter_used,
    'repeat': repeat_used,
    'loops': loops_used
}
makedirs('saves', exist_ok=True)
file_name = 'saves/sim_setting_python_time_experiment'
with open(file_name + '.json', 'w') as outfile: json.dump(python_simulation_HPs, outfile)

time_result = timing_experiment_simulation(repeat=repeat_used, loops=loops_used, num_nodes=num_nodes_used,
                                           t_end=t_end_used, num_cm= num_cm, ts=t_s_used,
                                           methode=used_methode,
                                           methode_args=used_methode_args,
                                           parameter=parameter_used,
                                           save_data=False, save_folder_name='saves_python',
                                           debug=True)


with open('saves/time_result_all_python.json', 'w') as outfile: json.dump(time_result, outfile)

#time_result_df = pd.DataFrame(time_result.items())
#time_result_df.to_pickle('saves_python/time_result_all.pkl.bz2')

plot_result(time_result, num_nodes_used, t_end_used)
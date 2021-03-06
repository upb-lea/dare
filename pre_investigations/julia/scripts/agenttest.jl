using DrWatson
@quickactivate "MicroGridSimWithRL"

using PProf, Profile
# using DifferentialEquations
# using Sundials
using Plots
# using LinearAlgebra
# using ControlSystems
using BenchmarkTools
using ReinforcementLearning
using Flux
using StableRNGs
using IntervalSets
using TimerOutputs
using JSON

include(srcdir("nodeconstructor.jl"))
include(srcdir("env.jl"))
include(srcdir("agent.jl"))
include(srcdir("run_timed.jl"))

global timer = TimerOutput()

env_cuda = false
agent_cuda = true

num_nodes = 20

CM = [ 0.  1.
        -1.  0.]

CM_list = JSON.parsefile(srcdir("CM_matrices", "CM_nodes" * string(num_nodes) * ".json"))

CM = reduce(hcat, CM_list[1])'
CM = convert(Matrix{Int}, CM)

parameters = Dict()
# LC filter
parameters["source"] = [Dict("fltr" => "LC", "R" => 0.4, "L1" => 2.3e-3, "C" => 10e-6)]
parameters["cable"] = [Dict("R" => 0.722, "L" => 0.955e-3, "C" => 8e-09)]
parameters["load"] = [Dict("impedance" => "R", "R" => 14)]

#nc = NodeConstructor(num_sources=1, num_loads=1, CM=CM, parameters=parameters)
nc = NodeConstructor(num_sources=num_nodes, num_loads=num_nodes, CM=CM)

#draw_graph(Grid_FC)   ---   not yet implemented

A, B, C, D = get_sys(nc)

limits = Dict("i_lim" => 20, "v_lim" => 600)

norm_array = vcat([limits[i] for j = 1:nc.num_sources for i in ["i_lim", "v_lim"]], [limits["i_lim"] for i = 1:nc.num_connections] )
norm_array = vcat( norm_array, [limits["v_lim"] for i = 1:nc.num_loads] )

states = get_states(nc)
norm_array = []
for state_name in states
    if startswith(state_name, "i")
        push!(norm_array, limits["i_lim"])
    elseif startswith(state_name, "u")
        push!(norm_array, limits["v_lim"])
    end
end

ns = length(A[1,:])
na = length(B[1,:])

# time step
ts = 1e-5

V_source = 300

x0 = [ 0.0 for i = 1:length(A[1,:]) ]
Ad = exp(A*ts)
Bd = A \ (Ad - C) * B

if env_cuda
    A = CuArray(A)
    B = CuArray(B)
    C = CuArray(C)
    Ad = CuArray(Ad)
    Bd = CuArray(Bd)
    x0 = CuArray(x0)
end

env = SimEnv(A=A, B=B, C=C, Ad=Ad, Bd=Bd, norm_array=norm_array, x0=x0, v_dc=V_source, ts=rationalize(ts), convert_state_to_cpu=true)
agent = create_agent(na, ns, agent_cuda)

# ----------------------------------------------------------------------------------------
function execute_env(env::SimEnv, agent::Agent, t_len::Int, debug::Bool)
    if debug
        output = zeros(length(env.Ad[1,:]), t_len+1)
    else
        output = 0.0
    end

    RLBase.reset!(env)

    for i = 1:t_len
        action = agent(env)
        env(action)
        println(reward(env))
        if debug output[:,i+1] = env.state.*env.norm_array end
    end

    return output
end

P_required = 466 # W
V_required = 230 # V
PLoad = []
Pdiff = []

function reward_func(method::String, env::SimEnv)

    i_1, u_1, i_c1, u_l1 = Array(env.state)

    P_load = (env.norm_array[end] * u_l1)^2 / 14
    
    if method == "Power_exp"
        # push!(PLoad, P_load)
        P_diff = -abs(P_required - P_load) 
        # push!(Pdiff, P_diff)
        reward = exp(P_diff/130) - 1
    
    elseif method == "Power"
        reward = -abs(P_required - P_load) / (600 * 20)

    elseif method == "Voltage"
        reward = -((V_required - u_l1)/ 600) ^2
    end
    return reward
end

hook = TotalRewardPerEpisode()

No_Episodes = 5

run(agent, env, StopAfterEpisode(1), hook)

@timeit timer "Overall run" begin
run(
    agent,
    env,
    timer,
    StopAfterEpisode(No_Episodes),
    hook
)
end

show(timer)


# @benchmark run(
#     agent,
#     env,
#     StopAfterEpisode(No_Episodes),
#     hook
# ) seconds = 120 evals = 2

# pprof(;webport=58699)

# plot(hook.rewards, 
#     title = "Total reward per episode",
#     xlabel = "Episodes",
#     ylabel = "Rewards",
#     legend = false)

# plot(PLoad,
#     title = "Power @ Load",
#     ylabel = "Power in Watts",
#     xlabel = "Time steps for 150 episodes [150 x 300]",
#     legend = false)

# plot(PLoad[end-300 : end],
#     title = "Power @ Load for the last episode",
#     ylabel = "Power in Watts",
#     xlabel = "Time steps",
#     legend = false
#     )

# Plots.savefig(p, plotsdir())
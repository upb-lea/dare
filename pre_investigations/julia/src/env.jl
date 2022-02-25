using ReinforcementLearning
using IntervalSets
using LinearAlgebra
using ControlSystems

# --- RL ENV ---

Base.@kwdef mutable struct SimEnv <: AbstractEnv
    A = [1.0 0.0; 0.0 1.0]
    B = [1.0 0.0; 0.0 1.0]
    C = 0
    D = 0
    action_space::Space{Vector{ClosedInterval{Float64}}} = Space([ -1.0..1.0 for i = 1:length(B[1,:]) ], )
    observation_space::Space{Vector{ClosedInterval{Float64}}} = Space([ -1.0..1.0 for i = 1:length(A[1,:]) ], )
    done::Bool = false
    x0::Vector{Float64} = [ 0.0 for i = 1:length(A[1,:]) ]
    x::Vector{Float64} = x0
    state::Vector{Float64} = x0
    maxsteps::Int = 1000
    steps::Int = 0
    t::Rational = 0
    ts::Rational = 1//10_000
    Ad::AbstractMatrix = exp(A*ts)
    Bd::AbstractMatrix = A \ (Ad - C) * B
    sys_d::StateSpace = ss(Ad, Bd, C, D, Float64(ts))
    norm_array::Vector{Float64} = [ 600.0 for i = 1:length(A[1,:]) ]
    v_dc::Float64 = 300
end


RLBase.action_space(env::SimEnv) = env.action_space
RLBase.state_space(env::SimEnv) = env.observation_space
RLBase.reward(env::SimEnv) = 1.0 #max(0, ((-1) * abs(env.state[2] - 150.0)) + 30 )
RLBase.is_terminated(env::SimEnv) = env.done
RLBase.state(env::SimEnv) = env.state

function RLBase.reset!(env::SimEnv)
    env.state = env.x0
    env.x = env.x0
    env.t = 0
    env.steps = 0
    env.done = false
    nothing
end

function (env::SimEnv)(action)
    env.steps += 1

    tt = [env.t, env.t + env.ts]

    env.t = tt[2]

    action *= env.v_dc
    u = [action action]

    yout_d, tout_d, xout_d, uout_d = lsim(env.sys_d, u, tt, x0=env.x)

    env.x = xout_d'[2,:]
    env.state = yout_d'[2,:] ./ env.norm_array

    env.done = env.steps >= env.maxsteps
end
#!/usr/bin/env julia
"""
Dense, finite-dimensional quantum-jump teaching code. Run from any directory:
  julia --project=. --startup-file=no scripts/trajectories.jl
Uses only Julia standard libraries; never approximates jumps by Bernoulli steps.
Output is deterministic for a fixed Julia release and seed (seed = 20261020).
"""
module TrajectoryLab
using LinearAlgebra, Random
export JumpModel, jump_trajectory, ensemble, master, lindblad, fluorescence,
       dephasing_dimer, loss_dimer, survival, generate_data

struct JumpModel
    H::Matrix{ComplexF64}
    jumps::Vector{Matrix{ComplexF64}}
    A::Matrix{ComplexF64}
end
function JumpModel(H::AbstractMatrix, jumps::AbstractVector)
    h = Matrix{ComplexF64}(H)
    ishermitian(h) || error("Hamiltonian must be Hermitian")
    ls = Matrix{ComplexF64}.(jumps)
    all(size(L) == size(h) for L in ls) || error("Operator dimensions differ")
    A = -im * h
    for L in ls
        A -= L' * L / 2
    end
    JumpModel(h, ls, A)
end

# The dense matrix exponential is used deliberately: these are benchmark systems,
# including potentially defective effective Hamiltonians; no eigenbasis is assumed.
no_jump(model, psi, dt) = exp(model.A * dt) * psi
survival(model, psi, dt) = sum(abs2, no_jump(model, psi, dt))

"""
One exact-waiting-time quantum-jump trajectory on increasing output times.
Returns normalized conditional observables plus event times/channels.
The unnormalized phi and ONE fixed threshold r are retained between jumps.
The output grid does not define a Bernoulli approximation or reset the clock.
Event times are located by bisection with absolute tolerance event_tol.
"""
function jump_trajectory(model::JumpModel, psi0, times, observables;
                         rng=Random.default_rng(), event_tol=1e-11)
    length(times) >= 1 && times[1] == 0 || error("times must start at zero")
    all(diff(times) .> 0) || error("times must strictly increase")
    event_tol > 0 || error("event_tol must be positive")
    phi = ComplexF64.(psi0)
    norm(phi) > 0 || error("initial state has zero norm")
    phi /= norm(phi)
    r = max(rand(rng), eps(Float64))
    nobs = length(observables)
    out = zeros(length(times), nobs)
    event_times, channels = Float64[], Int[]
    t = 0.0
    # Cache the propagator for the common output spacing; residuals are exact exp.
    step = length(times) > 1 ? times[2] - times[1] : 0.0
    Ustep = exp(model.A * step)
    function record!(row)
        p = sum(abs2, phi)
        for (k, O) in enumerate(observables)
            out[row, k] = real(dot(phi, O * phi)) / p
        end
    end
    record!(1)
    for row in 2:length(times)
        target = Float64(times[row])
        while t < target
            remaining = target - t
            trial = isapprox(remaining, step; atol=1e-13, rtol=1e-12) ?
                    Ustep * phi : no_jump(model, phi, remaining)
            if sum(abs2, trial) > r
                phi = trial
                t = target
            else
                lo, hi = 0.0, remaining
                while hi - lo > event_tol
                    mid = (lo + hi) / 2
                    if survival(model, phi, mid) > r
                        lo = mid
                    else
                        hi = mid
                    end
                end
                # phi is the UNNORMALIZED pre-jump state; its common norm cancels
                # in channel probabilities, but the post-jump state is normalized.
                phi = no_jump(model, phi, (lo + hi) / 2)
                t += (lo + hi) / 2
                weights = [sum(abs2, L * phi) for L in model.jumps]
                total = sum(weights)
                total > 0 || error("Threshold crossed with zero jump intensity")
                draw = rand(rng) * total
                channel = something(findfirst(cumsum(weights) .>= draw), length(weights))
                phi = model.jumps[channel] * phi
                phi /= norm(phi)
                push!(event_times, t)
                push!(channels, channel)
                r = max(rand(rng), eps(Float64))
            end
        end
        record!(row)
    end
    (values=out, event_times=event_times, channels=channels)
end

"""Independent seeded trajectories. Store observables, not state histories."""
function ensemble(model, psi0, times, observables; trajectories=1024, seed=20261020)
    trajectories >= 2 || error("At least two trajectories are needed for a sample SEM")
    samples = zeros(length(times), length(observables), trajectories)
    for m in 1:trajectories
        # Per-trajectory RNG makes results independent of trajectory scheduling.
        rng = Xoshiro(seed + m)
        samples[:, :, m] = jump_trajectory(model, psi0, times, observables; rng).values
    end
    avg = dropdims(sum(samples; dims=3); dims=3) / trajectories
    centered = samples .- reshape(avg, size(avg,1), size(avg,2), 1)
    sem = sqrt.(dropdims(sum(abs2, centered; dims=3); dims=3) / (trajectories-1) / trajectories)
    (mean=avg, sem=sem, samples=samples)
end

function lindblad(model::JumpModel, rho)
    result = -im * (model.H * rho - rho * model.H)
    for L in model.jumps
        Q = L' * L
        result += L * rho * L' - (Q * rho + rho * Q) / 2
    end
    result
end

"""
Independent deterministic RK4 reference with substeps <= max_dt.
No post-hoc trace/positivity correction: errors must remain visible to tests.
Returns actual matrices for trace, Hermiticity and positivity diagnostics.
"""
function master(model, rho0, times; max_dt=0.002)
    times[1] == 0 || error("times must start at zero")
    all(diff(times) .> 0) || error("times must strictly increase")
    max_dt > 0 || error("max_dt must be positive")
    rho = Matrix{ComplexF64}(rho0)
    result = Matrix{ComplexF64}[copy(rho)]
    for k in 2:length(times)
        n = ceil(Int, (times[k] - times[k-1]) / max_dt)
        h = (times[k] - times[k-1]) / n
        for _ in 1:n
            k1 = lindblad(model, rho)
            k2 = lindblad(model, rho + h * k1 / 2)
            k3 = lindblad(model, rho + h * k2 / 2)
            k4 = lindblad(model, rho + h * k3)
            rho += h * (k1 + 2k2 + 2k3 + k4) / 6
        end
        push!(result, copy(rho))
    end
    result
end

function fluorescence(; omega=2.0, gamma=1.0, detuning=0.0)
    # Basis |g>, |e>; rate lives inside the jump operator.
    lowering = ComplexF64[0 1; 0 0]
    ne = lowering' * lowering
    H = omega / 2 * (lowering + lowering') - detuning * ne
    (model=JumpModel(H, [sqrt(gamma) * lowering]),
     psi0=ComplexF64[1, 0], observables=[ne])
end

function dephasing_dimer(; J=1.0, gamma=1.0)
    # One hard-core particle, basis |10>, |01>.
    H = ComplexF64[0 -J; -J 0]
    n1, n2 = ComplexF64[1 0; 0 0], ComplexF64[0 0; 0 1]
    coherence = ComplexF64[0 0.5; 0.5 0]
    (model=JumpModel(H, [sqrt(gamma)*n1, sqrt(gamma)*n2]),
     psi0=ComplexF64[1, 1]/sqrt(2), observables=[coherence, n1])
end

function loss_dimer(; J=1.0, gamma=1.0)
    # |00>, |10>, |01>. Loss changes number, so the vacuum must be present.
    H = ComplexF64[0 0 0; 0 0 -J; 0 -J 0]
    L1, L2 = zeros(ComplexF64,3,3), zeros(ComplexF64,3,3)
    L1[1,2] = sqrt(gamma); L2[1,3] = sqrt(gamma)
    N = Diagonal(ComplexF64[0,1,1])
    (model=JumpModel(H,[L1,L2]), psi0=ComplexF64[0,1,0], observables=[N])
end

function writecsv(path, header, matrix)
    open(path, "w") do io
        println(io, join(header, ","))
        for row in eachrow(matrix)
            println(io, join(row, ","))
        end
    end
end

"""Generate all committed numerical figure data; no plotting dependency."""
function generate_data(outdir=joinpath(@__DIR__, "..", "data"))
    mkpath(outdir)
    BLAS.set_num_threads(1)
    seed = 20261020
    ts = collect(range(0, 8; length=161))
    f = fluorescence()
    e = ensemble(f.model, f.psi0, ts, f.observables; trajectories=4096, seed)
    rho = master(f.model, f.psi0*f.psi0', ts)
    exact = [real(tr(r*f.observables[1])) for r in rho]
    writecsv(joinpath(outdir,"fluorescence.csv"),
             ["t","master","mean","sem","trajectory_1","trajectory_2","trajectory_3"],
             hcat(ts,exact,e.mean[:,1],e.sem[:,1],e.samples[:,1,1:3]))

    # Disjoint groups from the same independent pool. RMSE over groups at fixed t.
    groupsizes = [16,32,64,128,256,512]
    fixed = 81 # t=4, chosen in advance
    scaling = zeros(length(groupsizes),4)
    for (k,M) in enumerate(groupsizes)
        B = size(e.samples,3) ÷ M
        estimates = [sum(e.samples[fixed,1,(b-1)*M+1:b*M])/M for b in 1:B]
        rmse = sqrt(sum((estimates .- exact[fixed]).^2)/B)
        # Population SD estimated once from all single-trajectory samples.
        prediction = sqrt(sum(abs2, e.samples[fixed,1,:] .- e.mean[fixed,1]) / (size(e.samples,3)-1)) / sqrt(M)
        scaling[k,:] = [M,B,rmse,prediction]
    end
    writecsv(joinpath(outdir,"sampling-scaling.csv"),["M","groups","rmse","predicted_sem"],scaling)

    d = dephasing_dimer()
    ed = ensemble(d.model,d.psi0,ts,d.observables; trajectories=4096, seed=seed+10000)
    rd = master(d.model,d.psi0*d.psi0',ts)
    exactd = [real(tr(r*d.observables[1])) for r in rd]
    writecsv(joinpath(outdir,"dephasing.csv"),["t","analytic","master","mean","sem"],
             hcat(ts,0.5exp.(-ts),exactd,ed.mean[:,1],ed.sem[:,1]))

    # Deterministic Zeno diagnostic: loss from a coupled lossy level.
    # |a>, |b>, |vac>; L=sqrt(Gamma)|vac><b|, starting in |a>.
    zts = collect(range(0,20;length=201))
    gammas = [0.5,4.0,20.0,80.0]
    zs = zeros(length(zts),length(gammas))
    for (k,G) in enumerate(gammas)
        H = ComplexF64[0 -1 0; -1 0 0; 0 0 0]
        loss = zeros(ComplexF64,3,3); loss[3,2] = sqrt(G)
        model = JumpModel(H,[loss])
        initial = ComplexF64[1,0,0]
        rs = master(model,initial*initial',zts;max_dt=min(0.002,0.1/G))
        zs[:,k] = [real(r[1,1]+r[2,2]) for r in rs]
    end
    writecsv(joinpath(outdir,"zeno.csv"),["t"; ["gamma_$(g)" for g in gammas]],hcat(zts,zs))
    open(joinpath(outdir,"numerics-metadata.txt"),"w") do io
        println(io,"Julia version: ",VERSION)
        println(io,"Seed: ",seed,"; trajectories/model: 4096; BLAS threads: 1")
        println(io,"Fluorescence: Omega=2, gamma=1, Delta=0, t=0:0.05:8")
        println(io,"Dimer: J=1, gamma=1, initial (|10>+|01>)/sqrt(2)")
        println(io,"Method: norm-threshold event bisection, tolerance 1e-11")
        println(io,"Reference: RK4, maximum step 0.002; Zeno max step min(0.002,0.1/Gamma)")
    end
    println("Wrote numerical data to ",abspath(outdir))
end
end

if abspath(PROGRAM_FILE) == @__FILE__
    TrajectoryLab.generate_data()
end

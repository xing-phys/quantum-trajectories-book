using Test, LinearAlgebra, Random
include(joinpath(@__DIR__,"..","scripts","trajectories.jl"))
using .TrajectoryLab
BLAS.set_num_threads(1)

@testset "Lindblad structure and deterministic reference" begin
    f = fluorescence()
    psi = ComplexF64[1,im]/sqrt(2)
    rho = psi*psi'
    @test abs(tr(lindblad(f.model,rho))) < 1e-14
    @test lindblad(f.model,rho) ≈ lindblad(f.model,rho)'
    times = collect(0:0.05:2)
    states = master(f.model,rho,times)
    @test maximum(abs(tr(r)-1) for r in states) < 1e-12
    @test maximum(norm(r-r') for r in states) < 1e-12
    @test minimum(minimum(eigvals(Hermitian(r))) for r in states) > -1e-10
    # RK4 convergence against a more accurate result, not a corrected matrix.
    coarse = master(f.model,rho,[0.,2.];max_dt=0.05)[end]
    fine = master(f.model,rho,[0.,2.];max_dt=0.025)[end]
    ref = master(f.model,rho,[0.,2.];max_dt=0.002)[end]
    @test norm(coarse-ref) / norm(fine-ref) > 14
end

@testset "Waiting-time law, probabilities, output-grid invariance" begin
    gamma = 1.7
    lowering = ComplexF64[0 1;0 0]
    model = JumpModel(zeros(2,2),[sqrt(gamma)*lowering])
    excited = ComplexF64[0,1]
    @test survival(model,excited,0.8) ≈ exp(-gamma*0.8)
    @test all(0 <= survival(model,excited,t) <= 1 for t in 0:0.1:5)
    @test issorted([survival(model,excited,t) for t in 0:0.1:5];rev=true)
    a = jump_trajectory(model,excited,collect(0:0.1:8),[lowering'*lowering];rng=Xoshiro(40))
    b = jump_trajectory(model,excited,[0.,8.],[lowering'*lowering];rng=Xoshiro(40))
    @test length(a.event_times) == 1
    @test a.event_times ≈ b.event_times atol=2e-10
    @test all(0 .<= a.values .<= 1)
    # Exact waiting time from the first RNG draw; channel draw occurs afterwards.
    @test a.event_times[1] ≈ -log(rand(Xoshiro(40)))/gamma atol=2e-10
    # Two marked channels with identical final state: frequency equals rate ratio.
    two = JumpModel(zeros(2,2),[sqrt(1.0)*lowering,sqrt(3.0)*lowering])
    labels = [only(jump_trajectory(two,excited,[0.,10.],[];rng=Xoshiro(500+m)).channels) for m in 1:2000]
    @test abs(sum(labels .== 2)/length(labels)-0.75) < 0.04
end

@testset "Unbiased ensembles, dark states, particle-number changes" begin
    f = fluorescence()
    times = [0.,1.,2.,4.]
    e = ensemble(f.model,f.psi0,times,f.observables;trajectories=4096,seed=932)
    ref = master(f.model,f.psi0*f.psi0',times)
    expected = [real(tr(r*f.observables[1])) for r in ref]
    @test all(abs.(e.mean[:,1]-expected) .<= 6e.sem[:,1] .+ 1e-8)
    @test all(-1e-12 .<= e.samples .<= 1+1e-12)
    # No-jump dark state must evolve without attempting to choose a zero channel.
    zero = JumpModel(zeros(2,2),[zeros(2,2)])
    dark = jump_trajectory(zero,f.psi0,[0.,100.],f.observables;rng=Xoshiro(1))
    @test isempty(dark.event_times)
    @test dark.values == zeros(2,1)
    # Fixed-N implementation would fail this test because the vacuum is needed.
    l = loss_dimer(;gamma=1.0)
    el = ensemble(l.model,l.psi0,times,l.observables;trajectories=2048,seed=200)
    @test all(abs.(el.mean[:,1]-exp.(-times)) .<= 6el.sem[:,1] .+ 1e-8)
    d = dephasing_dimer()
    states = master(d.model,d.psi0*d.psi0',times)
    @test [real(tr(r*d.observables[1])) for r in states] ≈ 0.5exp.(-times) atol=1e-10
end

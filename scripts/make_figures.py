#!/usr/bin/env python3
"""Plot original figures from Julia-generated CSV data; no independent simulation.
Run .venv/bin/python scripts/make_figures.py from the repository root.
"""
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import NullLocator, ScalarFormatter

ROOT = Path(__file__).resolve().parents[1]
DATA, FIGS = ROOT / "data", ROOT / "figs"
FIGS.mkdir(exist_ok=True)
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 11,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.labelsize": 11, "axes.titlesize": 12,
    "savefig.dpi": 190, "pdf.fonttype": 42,
    "figure.constrained_layout.use": True,
})
BLUE, ORANGE, TEAL = "#245d87", "#d97136", "#25877c"

def load(name):
    return np.genfromtxt(DATA / (name + ".csv"), delimiter=",", names=True)

def save(fig, name):
    fig.savefig(FIGS / (name + ".png"), facecolor="white")
    fig.savefig(FIGS / (name + ".pdf"), facecolor="white")
    plt.close(fig)

f = load("fluorescence")
fig, axes = plt.subplots(2, 1, figsize=(7.2, 6.0), sharex=True)
for k, color in enumerate([TEAL, ORANGE, "#886ba0"], 1):
    axes[0].plot(f["t"], f[f"trajectory_{k}"], lw=1.1, color=color, alpha=.85,
                 label=f"Conditional path {k}")
axes[0].set(ylabel=r"$\langle n_e\rangle_\psi$", ylim=(-.025, 1.025),
            title="Resonance fluorescence: individual records and their ensemble")
axes[0].legend(ncol=3, fontsize=8, loc="upper right")
axes[1].plot(f["t"], f["master"], color="#222222", lw=1.8, label="Master equation (RK4)")
axes[1].plot(f["t"], f["mean"], color=BLUE, lw=1.3, label="4,096 trajectories")
axes[1].fill_between(f["t"], f["mean"]-1.96*f["sem"], f["mean"]+1.96*f["sem"],
                     color=BLUE, alpha=.22, label=r"Pointwise $\pm 1.96$ SEM")
axes[1].set(xlabel=r"Time $t\gamma$", ylabel=r"$\langle n_e\rangle$", ylim=(-.02,.72))
axes[1].legend(fontsize=9, loc="upper right")
save(fig, "fluorescence")

s = load("sampling-scaling")
fig, ax = plt.subplots(figsize=(6.4,4.2))
ax.loglog(s["M"],s["rmse"],"o-",color=BLUE,label="RMSE across disjoint groups")
ax.loglog(s["M"],s["predicted_sem"],"--",color=ORANGE,label=r"$s_\mathrm{single}/\sqrt{M}$")
for M, B, err in zip(s["M"], s["groups"], s["rmse"]):
    ax.annotate(f"{int(B)} groups",(M,err),xytext=(4,7),textcoords="offset points",fontsize=8)
ax.set(xlabel="Trajectories per group, M",ylabel=r"Population error at $t\gamma=4$",
       title="Monte Carlo uncertainty falls as the square root of sample size")
ax.set_xticks(s["M"])
ax.xaxis.set_major_formatter(ScalarFormatter())
ax.xaxis.set_minor_locator(NullLocator())
ax.legend(fontsize=9)
save(fig,"sampling-scaling")

d = load("dephasing")
fig, ax = plt.subplots(figsize=(6.4,4.2))
ax.plot(d["t"],d["analytic"],color="#222222",lw=2,label=r"Exact $e^{-\gamma t}/2$")
ax.plot(d["t"],d["master"],"--",color=ORANGE,lw=1.2,label="Master equation")
ax.plot(d["t"],d["mean"],color=BLUE,lw=1.3,label="4,096 trajectories")
ax.fill_between(d["t"],d["mean"]-1.96*d["sem"],d["mean"]+1.96*d["sem"],color=BLUE,alpha=.22)
ax.set(xlabel=r"Time $t\gamma$",ylabel=r"$\mathrm{Re}\langle b_1^\dagger b_2\rangle$",
       title="A single hard-core particle loses intersite coherence",ylim=(-.02,.53))
ax.legend(fontsize=9)
save(fig,"dephasing")

z = load("zeno")
fig, ax = plt.subplots(figsize=(6.4,4.3))
for field, gamma, color in zip(z.dtype.names[1:],[.5,4,20,80],
                             ["#886ba0",ORANGE,BLUE,TEAL]):
    ax.plot(z["t"],z[field],color=color,lw=1.7,label=rf"$\Gamma/J={gamma:g}$")
ax.plot(z["t"],np.exp(-4*z["t"]/80),"--",color="#222222",lw=1.1,
        label=r"$e^{-4J^2t/\Gamma}$ for $\Gamma/J=80$")
ax.set(xlabel=r"Time $tJ$",ylabel="Survival outside the vacuum",
       title="Continuous Zeno effect: stronger loss protects survival",
       ylim=(-.02,1.03))
ax.legend(fontsize=9)
save(fig,"zeno")
print("Wrote four original figures as PNG and PDF to", FIGS)

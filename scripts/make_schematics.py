"""Draw original conceptual figures; no source-paper images are reused."""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

ROOT = Path(__file__).resolve().parents[1]
plt.rcParams.update({"font.size": 12, "font.family": "DejaVu Sans", "pdf.fonttype": 42})

def box(ax, xy, w, h, text, face, edge="#214c60", fs=12):
    ax.add_patch(FancyBboxPatch(xy, w, h, boxstyle="round,pad=0.02,rounding_size=.08", facecolor=face, edgecolor=edge, lw=1.5))
    ax.text(xy[0]+w/2, xy[1]+h/2, text, ha="center", va="center", fontsize=fs, color="#163e50")

def arrow(ax, p, q, label=None, yoff=.2, color="#286f85"):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=16, color=color, lw=1.6))
    if label:
        ax.text((p[0]+q[0])/2, (p[1]+q[1])/2+yoff, label, ha="center", va="bottom", color="#163e50", fontsize=10)

def save(fig, name):
    for ext in ("png", "pdf"):
        fig.savefig(ROOT/"figs"/f"{name}.{ext}", dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)

fig, ax = plt.subplots(figsize=(10,4.8))
ax.set(xlim=(0,10), ylim=(0,4.8)); ax.axis("off")
box(ax,(.2,1.8),2.1,1.3,"Quantum system\n$H,\\;L_\\mu$", "#dceff0", fs=12)
box(ax,(3.4,1.8),2.1,1.3,"Fresh bath bin\n$|0\\rangle_k$", "#e5ecfa", fs=13)
box(ax,(6.7,1.8),2.7,1.3,"Choose a measurement\ncounting / homodyne", "#fff0d4", fs=12)
arrow(ax,(2.35,2.45),(3.35,2.45),"interact")
arrow(ax,(5.55,2.45),(6.65,2.45),"output field")
box(ax,(6.7,.25),2.7,.8,"Conditioned state $\\rho_c$", "#e6f2e5")
arrow(ax,(8.05,1.75),(8.05,1.1))
ax.text(3.7,.72,"Average over records",ha="center",color="#163e50",fontsize=12)
arrow(ax,(6.65,.65),(1.25,.65))
ax.text(1.25,.14,"Master equation $\\dot\\rho=\\mathcal{L}\\rho$",ha="center",fontsize=11,color="#163e50")
ax.text(5,4.25,"A different fresh bin meets the system at each step",ha="center",fontsize=14,fontweight="bold",color="#163e50")
ax.text(5,3.65,"Memory is neglected; measurement determines the unraveling",ha="center",fontsize=11,color="#4b606a")
save(fig,"measurement-chain")

fig, ax = plt.subplots(figsize=(9.4,4.5))
ax.set(xlim=(0,10),ylim=(0,4.5)); ax.axis("off")
box(ax,(.35,1.45),2.6,1.3,"Slow subspace $P$\nallowed occupations", "#dceff0",fs=13)
box(ax,(4.1,1.45),2.6,1.3,"Lossy subspace $Q$\ncomplex energy\n$\\Delta-i\\Gamma/2$", "#ffead6",fs=12)
box(ax,(7.8,1.45),1.8,1.3,"Loss products\nreservoir", "#edf0f2",fs=12)
arrow(ax,(3,2.35),(4.05,2.35),"$g$")
arrow(ax,(4.05,1.8),(3,1.8))
arrow(ax,(6.75,2.1),(7.75,2.1),"$\\Gamma$")
ax.text(5,3.65,"Strong loss suppresses entry into the lossy sector",ha="center",fontsize=14,fontweight="bold",color="#163e50")
ax.text(5,.65,"Effective leakage:  $\\Gamma_{\\mathrm{eff}}=|g|^2\\Gamma/[\\Delta^2+(\\Gamma/2)^2]$",ha="center",fontsize=13,color="#163e50")
ax.text(5,.15,"For $\\Gamma\\gg |g|,|\\Delta|$: leakage decreases as $4|g|^2/\\Gamma$",ha="center",fontsize=11,color="#4b606a")
save(fig,"zeno-subspaces")
print("Created original measurement and Zeno schematics (PNG + PDF)")

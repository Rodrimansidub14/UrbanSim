import os
import time
import psutil
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime


# Genera tablas y gráficas a partir del DataFrame de resultados


def create_outputs_dir(base_dir: str):
    # Crea carpeta con timestamp para mantener salidas ordenadas
    # Evita anteponer "sim/" para que no se cree sim/sim/outputs si ejecutas dentro de sim/
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    path = os.path.join(base_dir, f"run-{ts}")
    os.makedirs(path, exist_ok=True)
    return path


def summarize(df: pd.DataFrame):
    last = df.iloc[-1]
    summary = {
        "avg_rent_final": round(last["avg_rent"], 2),
        "avg_travel_final": round(last["avg_travel"], 2),
        "share_low_income_final": round(last["share_low_income"], 3),
        "gentr_dispersion_final": round(last["gentr_dispersion"], 3),
        "vacancy_rate_final": round(last["vacancy_rate"], 3),
        "aff_units_final": int(last["aff_units"]),
        "mkt_units_final": int(last["mkt_units"]),
        "total_units_final": int(last["total_units"]),
        "cum_displacements": int(df["displacements"].sum()),
    }
    return pd.Series(summary)


def plot_time_series(df: pd.DataFrame, show=True, savepath=None):
    fig1, axs1 = plt.subplots(3, 2, figsize=(12, 9))
    ax = axs1[0, 0]
    df.plot(x="step", y="avg_rent", ax=ax, legend=False)
    ax.set_title("Renta promedio")
    ax.set_xlabel("Paso (mes)")
    ax.set_ylabel("Moneda")
    ax = axs1[0, 1]
    df.plot(x="step", y="avg_travel", ax=ax, legend=False)
    ax.set_title("Tiempo de viaje promedio")
    ax.set_xlabel("Paso (mes)")
    ax.set_ylabel("Minutos")
    ax = axs1[1, 0]
    df.plot(x="step", y="share_low_income", ax=ax, legend=False)
    ax.set_title("% población de bajos ingresos")
    ax.set_xlabel("Paso (mes)")
    ax.set_ylabel("Proporción")
    ax = axs1[1, 1]
    df.plot(x="step", y="gentr_dispersion", ax=ax, legend=False)
    ax.set_title("Dispersión del índice de gentrificación")
    ax.set_xlabel("Paso (mes)")
    ax.set_ylabel("Índice")
    ax = axs1[2, 0]
    df.plot(x="step", y="displacements", ax=ax, legend=False)
    ax.set_title("Desplazamientos por paso")
    ax.set_xlabel("Paso (mes)")
    ax.set_ylabel("Hogares")
    ax = axs1[2, 1]
    df.plot(x="step", y="vacancy_rate", ax=ax, legend=False)
    ax.set_title("Tasa de vacancia")
    ax.set_xlabel("Paso (mes)")
    ax.set_ylabel("Proporción")
    fig1.tight_layout()

    fig2, axs2 = plt.subplots(1, 3, figsize=(12, 3.5))
    df.plot(x="step", y="aff_units", ax=axs2[0], legend=False)
    axs2[0].set_title("Unidades asequibles")
    axs2[0].set_xlabel("Paso (mes)")
    axs2[0].set_ylabel("Unidades")
    df.plot(x="step", y="mkt_units", ax=axs2[1], legend=False)
    axs2[1].set_title("Unidades de mercado")
    axs2[1].set_xlabel("Paso (mes)")
    axs2[1].set_ylabel("Unidades")
    df.plot(x="step", y="total_units", ax=axs2[2], legend=False)
    axs2[2].set_title("Unidades totales")
    axs2[2].set_xlabel("Paso (mes)")
    axs2[2].set_ylabel("Unidades")
    fig2.tight_layout()

    if savepath:
        fig1.savefig(savepath, dpi=150)
        fig2.savefig(savepath.replace(".png", "_housing.png"), dpi=150)

    if show:
        plt.show()


class PerfMeter:
    # Mide rendimiento para streaming o logging
    def __init__(self):
        self.proc = psutil.Process()
        self.tprev = time.perf_counter()

    def sample(self):
        now = time.perf_counter()
        dt = (now - self.tprev) * 1000.0
        self.tprev = now
        return {
            "ms_per_tick": dt,
            "cpu_percent": psutil.cpu_percent(interval=None),
            "mem_mb": self.proc.memory_info().rss / 1e6,
        }


def save_spatial_maps(model, outdir, step):
    grids = model.spatial_grids()
    for key, arr in grids.items():
        plt.figure(figsize=(4.5, 4))
        im = plt.imshow(arr.T, origin="lower", aspect="equal")
        plt.title(f"Mapa {key} - paso {step}")
        plt.xlabel("i")
        plt.ylabel("j")
        plt.colorbar(im, fraction=0.046)
        fname = f"map_{key}_step{step:03d}.png"
        plt.tight_layout()
        plt.savefig(os.path.join(outdir, fname), dpi=150)
        plt.close()


def hold_plots():
    # Mantiene las ventanas abiertas hasta que el usuario las cierre
    import matplotlib.pyplot as plt

    plt.ioff()
    plt.show(block=True)

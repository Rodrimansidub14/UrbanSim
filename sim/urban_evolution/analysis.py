import time
import psutil
import matplotlib.pyplot as plt
import pandas as pd

# Genera tablas y gráficas a partir del DataFrame de resultados

def summarize(df: pd.DataFrame):
    # Tabla resumen simple
    last = df.iloc[-1]
    summary = {
        "avg_rent_final": round(last["avg_rent"], 2),
        "avg_travel_final": round(last["avg_travel"], 2),
        "share_low_income_final": round(last["share_low_income"], 3),
        "gentr_dispersion_final": round(last["gentr_dispersion"], 3),
        "cum_displacements": int(df["displacements"].sum())
    }
    return pd.Series(summary)

def plot_time_series(df: pd.DataFrame, show=True, savepath=None):
    fig, axs = plt.subplots(3, 2, figsize=(11, 9))
    ax = axs[0,0]; df.plot(x="step", y="avg_rent", ax=ax, legend=False); ax.set_title("Renta promedio")
    ax = axs[0,1]; df.plot(x="step", y="avg_travel", ax=ax, legend=False); ax.set_title("Tiempo de viaje promedio")
    ax = axs[1,0]; df.plot(x="step", y="share_low_income", ax=ax, legend=False); ax.set_title("% población de bajos ingresos")
    ax = axs[1,1]; df.plot(x="step", y="gentr_dispersion", ax=ax, legend=False); ax.set_title("Dispersión del índice de gentrificación")
    ax = axs[2,0]; df.plot(x="step", y="displacements", ax=ax, legend=False); ax.set_title("Desplazamientos por tick")
    axs[2,1].axis("off")
    fig.tight_layout()
    if savepath:
        fig.savefig(savepath, dpi=150)
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
            "mem_mb": self.proc.memory_info().rss / 1e6
        }

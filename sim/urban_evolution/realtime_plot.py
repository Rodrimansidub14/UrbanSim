import matplotlib.pyplot as plt


# Gráficas “en vivo” en una sola ventana persistente
class LivePlotter:
    def __init__(self):
        plt.ion()
        self.fig, self.axs = plt.subplots(2, 3, figsize=(14, 7))
        self.fig.suptitle("Evolución urbana (stream en vivo)", fontsize=13)

        # Configura títulos y ejes
        titles = [
            ("Renta promedio", "Paso (mes)", "Moneda"),
            ("Tiempo de viaje promedio", "Paso (mes)", "Minutos"),
            ("Desplazamientos por paso", "Paso (mes)", "Hogares"),
            ("% población de bajos ingresos", "Paso (mes)", "Proporción"),
            ("Dispersión del índice de gentrificación", "Paso (mes)", "Índice"),
            ("Tasa de vacancia", "Paso (mes)", "Proporción"),
        ]
        self.lines = [None] * 6
        self.cols = [
            "avg_rent",
            "avg_travel",
            "displacements",
            "share_low_income",
            "gentr_dispersion",
            "vacancy_rate",
        ]

        for k, ax in enumerate(self.axs.flatten()):
            t, xl, yl = titles[k]
            ax.set_title(t)
            ax.set_xlabel(xl)
            ax.set_ylabel(yl)

        self.fig.tight_layout(rect=[0, 0, 1, 0.97])

    def update(self, df):
        x = df["step"].values
        for i, col in enumerate(self.cols):
            y = df[col].values
            ax = self.axs.flatten()[i]
            if self.lines[i] is None:
                (self.lines[i],) = ax.plot(x, y, label=col)
                ax.legend()
            else:
                self.lines[i].set_xdata(x)
                self.lines[i].set_ydata(y)
                ax.relim()
                ax.autoscale_view()

        self.fig.canvas.draw_idle()
        plt.pause(0.001)

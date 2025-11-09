import matplotlib.pyplot as plt


# Gráficas simples en vivo desde el DataFrame de resultados en crecimiento
class LivePlotter:
    def __init__(self):
        plt.ion()
        # Ventana 1
        self.fig1, self.axs1 = plt.subplots(1, 3, figsize=(13, 3.8))
        self.axs1[0].set_title("Renta promedio")
        self.axs1[0].set_xlabel("Paso (mes)")
        self.axs1[0].set_ylabel("Moneda")
        self.axs1[1].set_title("Tiempo de viaje promedio")
        self.axs1[1].set_xlabel("Paso (mes)")
        self.axs1[1].set_ylabel("Minutos")
        self.axs1[2].set_title("Desplazamientos por paso")
        self.axs1[2].set_xlabel("Paso (mes)")
        self.axs1[2].set_ylabel("Hogares")
        self.lines1 = [None, None, None]
        # Ventana 2
        self.fig2, self.axs2 = plt.subplots(1, 3, figsize=(13, 3.8))
        self.axs2[0].set_title("% población de bajos ingresos")
        self.axs2[0].set_xlabel("Paso (mes)")
        self.axs2[0].set_ylabel("Proporción")
        self.axs2[1].set_title("Dispersión gentrificación")
        self.axs2[1].set_xlabel("Paso (mes)")
        self.axs2[1].set_ylabel("Índice")
        self.axs2[2].set_title("Tasa de vacancia")
        self.axs2[2].set_xlabel("Paso (mes)")
        self.axs2[2].set_ylabel("Proporción")
        self.lines2 = [None, None, None]

    def update(self, df):
        x = df["step"].values

        # Ventana 1
        series1 = [
            df["avg_rent"].values,
            df["avg_travel"].values,
            df["displacements"].values,
        ]
        labels1 = ["Renta", "Tiempo viaje", "Desplazamientos"]
        for i, y in enumerate(series1):
            if self.lines1[i] is None:
                (self.lines1[i],) = self.axs1[i].plot(x, y, label=labels1[i])
                self.axs1[i].legend()
            else:
                self.lines1[i].set_xdata(x)
                self.lines1[i].set_ydata(y)
                self.axs1[i].relim()
                self.axs1[i].autoscale_view()

        # Ventana 2
        series2 = [
            df["share_low_income"].values,
            df["gentr_dispersion"].values,
            df["vacancy_rate"].values,
        ]
        labels2 = ["% bajos ingresos", "Disp. gentrificación", "Vacancia"]
        for i, y in enumerate(series2):
            if self.lines2[i] is None:
                (self.lines2[i],) = self.axs2[i].plot(x, y, label=labels2[i])
                self.axs2[i].legend()
            else:
                self.lines2[i].set_xdata(x)
                self.lines2[i].set_ydata(y)
                self.axs2[i].relim()
                self.axs2[i].autoscale_view()

        plt.pause(0.001)

import matplotlib.pyplot as plt

# Gráficas simples en vivo desde el DataFrame de resultados en crecimiento
class LivePlotter:
    def __init__(self):
        plt.ion()
        self.fig, self.axs = plt.subplots(1, 3, figsize=(12, 3.8))
        self.axs[0].set_title("Renta promedio")
        self.axs[1].set_title("Tiempo de viaje promedio")
        self.axs[2].set_title("Desplazamientos/tick")
        self.lines = [None, None, None]

    def update(self, df):
        x = df["step"].values
        series = [
            df["avg_rent"].values,
            df["avg_travel"].values,
            df["displacements"].values
        ]
        for i, y in enumerate(series):
            if self.lines[i] is None:
                self.lines[i], = self.axs[i].plot(x, y)
            else:
                self.lines[i].set_xdata(x)
                self.lines[i].set_ydata(y)
                self.axs[i].relim()
                self.axs[i].autoscale_view()
        plt.pause(0.001)

import asyncio
from urban_evolution.model import CityModel
from urban_evolution.realtime_plot import LivePlotter
from urban_evolution.analysis import plot_time_series, summarize
from urban_evolution.streaming import StreamServer

# Ejecuta la simulación, dibuja gráficas en vivo y emite stream WebSocket

async def main():
    model = CityModel()
    plotter = LivePlotter()
    streamer = StreamServer(model)
    await streamer.start()

    async def tick_loop():
        for _ in range(model.N * 12):  # ejemplo: N*12 meses; cambia a STEPS si prefieres
            model.step_once()
            plotter.update(model.results_df())
            await streamer.broadcast_tick()
        # Gráfica final y resumen
        df = model.results_df()
        print(summarize(df))
        plot_time_series(df, show=True, savepath="results.png")
        df.to_csv("results.csv", index=False)

    await tick_loop()

if __name__ == "__main__":
    asyncio.run(main())

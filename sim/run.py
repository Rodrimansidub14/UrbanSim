import asyncio
import os
from urban_evolution.model import CityModel
from urban_evolution.realtime_plot import LivePlotter
from urban_evolution.analysis import (
    plot_time_series,
    summarize,
    save_spatial_maps,
    create_outputs_dir,
    hold_plots,
)
from urban_evolution.streaming import StreamServer  # se asume ya existe en tu repo
from urban_evolution.config import (
    STEPS,
    OUTPUTS_DIR,
    HOLD_PLOTS_OPEN,
)

# Ejecuta la simulación, dibuja gráficas en vivo y emite stream WebSocket


async def main():
    model = CityModel()
    plotter = LivePlotter()
    streamer = StreamServer(model)
    await streamer.start()

    outdir = create_outputs_dir(OUTPUTS_DIR)

    # Mapas de calor solo del inicio y del final
    save_spatial_maps(model, outdir, model.step)  # paso 0

    async def tick_loop():
        for _ in range(STEPS):
            model.step_once()
            plotter.update(model.results_df())
            await streamer.broadcast_tick()

        # Guardar mapas del final
        save_spatial_maps(model, outdir, model.step)

        # Guardar CSV y gráficas finales; además mostrarlas en pantalla
        df = model.results_df()
        print(summarize(df))
        df.to_csv(os.path.join(outdir, "results.csv"), index=False)
        plot_time_series(
            df, show=True, savepath=os.path.join(outdir, "time_series.png")
        )

        if HOLD_PLOTS_OPEN:
            hold_plots()

    await tick_loop()


if __name__ == "__main__":
    asyncio.run(main())

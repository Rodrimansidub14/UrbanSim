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
from urban_evolution.streaming import StreamServer
from urban_evolution.config import (
    STEPS,
    OUTPUTS_DIR,
    SAVE_SNAPSHOTS_EVERY,
    HOLD_PLOTS_OPEN,
)

# Ejecuta la simulación, dibuja gráficas en vivo y emite stream WebSocket


async def main():
    model = CityModel()
    plotter = LivePlotter()
    streamer = StreamServer(model)
    await streamer.start()

    outdir = create_outputs_dir(OUTPUTS_DIR)

    async def tick_loop():
        for _ in range(STEPS):
            model.step_once()
            plotter.update(model.results_df())
            await streamer.broadcast_tick()
            if (
                SAVE_SNAPSHOTS_EVERY is not None
                and model.step % SAVE_SNAPSHOTS_EVERY == 0
            ):
                save_spatial_maps(model, outdir, model.step)

        df = model.results_df()
        print(summarize(df))
        # Guardar resultados y gráficas finales
        df.to_csv(os.path.join(outdir, "results.csv"), index=False)
        plot_time_series(
            df, show=False, savepath=os.path.join(outdir, "time_series.png")
        )

        if HOLD_PLOTS_OPEN:
            hold_plots()

    await tick_loop()


if __name__ == "__main__":
    asyncio.run(main())

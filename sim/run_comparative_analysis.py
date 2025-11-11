"""
Script para ejecutar análisis comparativo rápido
Uso: python run_comparative_analysis.py
"""
from comparative_analysis import ScenarioAnalyzer
from pathlib import Path


def run_analysis():
    """Ejecutar análisis comparativo de escenarios disponibles"""
    
    print("\n🔬 ANÁLISIS COMPARATIVO DE ESCENARIOS URBANSIM")
    print("=" * 70)
    
    # Crear analizador
    analyzer = ScenarioAnalyzer(output_dir="outputs/comparative_analysis")
    
    # Definir rutas de escenarios
    scenarios_config = [
        ("outputs/rt_results.csv", "B0", "Baseline"),
        ("run_sim/S1RUN/results1.csv", "S1", "Escenario 1"),
        ("run_sim/S2RUN/results2.csv", "S2", "Escenario 2"),
        # Agregar más escenarios aquí según sea necesario
        # ("run_sim/S3RUN/results3.csv", "S3", "Escenario 3"),
    ]
    
    # Cargar escenarios disponibles
    print("\n📂 Buscando y cargando escenarios...\n")
    loaded_scenarios = []
    
    for csv_path, name, description in scenarios_config:
        path = Path(csv_path)
        if path.exists():
            try:
                analyzer.load_scenario(str(path), name)
                loaded_scenarios.append((name, description))
            except Exception as e:
                print(f"⚠️  Error cargando {name}: {e}")
        else:
            print(f"⚠️  Archivo no encontrado: {csv_path}")
    
    if len(loaded_scenarios) < 2:
        print("\n❌ Error: Se necesitan al menos 2 escenarios para comparar")
        return
    
    print(f"\n✅ {len(loaded_scenarios)} escenarios cargados:")
    for name, desc in loaded_scenarios:
        print(f"   • {name}: {desc}")
    
    # Generar análisis
    print("\n🔍 Generando análisis comparativo...\n")
    df_summary, df_targets = analyzer.generate_all_analyses()
    
    # Mostrar resumen ejecutivo
    print("\n" + "=" * 70)
    print("📊 RESUMEN EJECUTIVO")
    print("=" * 70 + "\n")
    
    print("TABLA 1: Indicadores Finales por Escenario")
    print("-" * 70)
    print(df_summary.to_string(index=False))
    
    print("\n\nTABLA 2: Comparación con Metas Deseables")
    print("-" * 70)
    print(df_targets.to_string(index=False))
    
    # Análisis de mejor escenario
    print("\n\n" + "=" * 70)
    print("🏆 ANÁLISIS DE MEJORES RESULTADOS")
    print("=" * 70 + "\n")
    
    # Evaluar cada métrica
    metrics_eval = {
        'Menores desplazamientos': df_summary.loc[df_summary['Desplazamientos acumulados'].idxmin(), 'Escenario'],
        'Mayor diversidad (bajos ingresos)': df_summary.loc[df_summary['Proporción bajos ingresos'].idxmax(), 'Escenario'],
        'Menor segregación': df_summary.loc[df_summary['Dispersión gentrificación'].idxmin(), 'Escenario'],
        'Mejor tasa de vacancia': df_summary.loc[(df_summary['Tasa de vacancia'] - 0.10).abs().idxmin(), 'Escenario'],
        'Menor tiempo de viaje': df_summary.loc[df_summary['Tiempo de viaje promedio'].idxmin(), 'Escenario']
    }
    
    for metric, best_scenario in metrics_eval.items():
        print(f"✓ {metric}: {best_scenario}")
    
    print("\n" + "=" * 70)
    print("✅ ANÁLISIS COMPLETADO CON ÉXITO")
    print("=" * 70)
    print(f"\n📁 Resultados guardados en: outputs/comparative_analysis/")
    print("\n💡 Abre los archivos .html en tu navegador para ver las gráficas interactivas")
    print("\n")


if __name__ == "__main__":
    try:
        run_analysis()
    except Exception as e:
        print(f"\n❌ Error durante el análisis: {e}")
        import traceback
        traceback.print_exc()

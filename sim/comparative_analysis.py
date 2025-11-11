"""
Módulo de Análisis Comparativo de Escenarios
Genera tablas resumen y gráficas profesionales para presentaciones
"""
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from pathlib import Path
import json
from datetime import datetime
import warnings


class ScenarioAnalyzer:
    """Analiza y compara múltiples escenarios de simulación"""
    
    def __init__(self, output_dir="outputs/comparative_analysis"):
        """
        Inicializar el analizador
        
        Args:
            output_dir: Directorio donde se guardarán los resultados
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.scenarios = {}
        self.summary_stats = {}
        
        # Check if kaleido is available for static image export
        self.can_export_images = self._check_kaleido()
        
        # Definir metas deseables
        self.targets = {
            'avg_rent': {'label': 'Renta promedio', 'goal': 'Estabilidad sin caídas abruptas', 'format': '{:.2f}'},
            'vacancy_rate': {'label': 'Tasa de vacancia', 'goal': '5–15% (equilibrio)', 'format': '{:.1%}', 'min': 0.05, 'max': 0.15},
            'displacements': {'label': 'Desplazamientos acumulados', 'goal': '<30,000', 'format': '{:,.0f}', 'max': 30000},
            'share_low_income': {'label': 'Proporción bajos ingresos', 'goal': '≥0.40 (diversidad)', 'format': '{:.3f}', 'min': 0.40},
            'gentr_dispersion': {'label': 'Dispersión gentrificación', 'goal': '≤0.35 (menor segregación)', 'format': '{:.3f}', 'max': 0.35},
            'avg_travel': {'label': 'Tiempo de viaje promedio', 'goal': '<16 min (compacta)', 'format': '{:.1f}', 'max': 16.0}
        }
        
    def load_scenario(self, csv_path, scenario_name):
        """
        Cargar datos de un escenario
        
        Args:
            csv_path: Ruta al archivo CSV con resultados
            scenario_name: Nombre del escenario (ej: 'B0', 'S1', 'S2')
        """
        df = pd.read_csv(csv_path)
        self.scenarios[scenario_name] = df
        
        # Calcular estadísticas finales
        final_row = df.iloc[-1]
        
        self.summary_stats[scenario_name] = {
            'avg_rent': final_row['avg_rent'],
            'avg_travel': final_row['avg_travel'],
            'share_low_income': final_row['share_low_income'],
            'gentr_dispersion': final_row['gentr_dispersion'],
            'vacancy_rate': final_row['vacancy_rate'],
            'aff_units': final_row['aff_units'],
            'mkt_units': final_row['mkt_units'],
            'total_units': final_row['total_units'],
            'displacements_cum': df['displacements'].sum()
        }
        
        print(f"✅ Escenario '{scenario_name}' cargado: {len(df)} pasos")
    
    def _check_kaleido(self):
        """Check if kaleido is installed for image export"""
        try:
            import kaleido
            return True
        except ImportError:
            warnings.warn(
                "⚠️ Kaleido no está instalado. Las imágenes PNG/JPEG no se generarán.\n"
                "Para instalar: pip install kaleido",
                UserWarning
            )
            return False
    
    def _save_figure(self, fig, base_name, save_png=True, save_jpeg=False):
        """
        Guardar figura en múltiples formatos
        
        Args:
            fig: Figura de Plotly
            base_name: Nombre base del archivo (sin extensión)
            save_png: Guardar como PNG
            save_jpeg: Guardar como JPEG
        """
        # Siempre guardar HTML
        html_path = self.output_dir / f'{base_name}.html'
        fig.write_html(html_path)
        print(f"  📄 HTML: {html_path}")
        
        # Guardar imágenes si kaleido está disponible
        if self.can_export_images:
            if save_png:
                png_path = self.output_dir / f'{base_name}.png'
                try:
                    # Adjust dimensions for subplots
                    height = getattr(fig.layout, 'height', 1080) or 1080
                    fig.write_image(png_path, width=1920, height=height, scale=2)
                    print(f"  🖼️  PNG: {png_path}")
                except Exception as e:
                    print(f"  ⚠️  Error guardando PNG ({base_name}): {e}")
            
            if save_jpeg:
                jpg_path = self.output_dir / f'{base_name}.jpg'
                try:
                    height = getattr(fig.layout, 'height', 1080) or 1080
                    fig.write_image(jpg_path, width=1920, height=height, scale=2, format='jpeg')
                    print(f"  🖼️  JPEG: {jpg_path}")
                except Exception as e:
                    print(f"  ⚠️  Error guardando JPEG ({base_name}): {e}")
        else:
            print(f"  ℹ️  Kaleido no disponible - solo HTML generado")
        
        return html_path
        
    def generate_summary_table(self):
        """Generar tabla resumen de indicadores finales"""
        
        # Crear DataFrame con todos los escenarios
        data = []
        for scenario, stats in self.summary_stats.items():
            row = {
                'Escenario': scenario,
                'Renta promedio': stats['avg_rent'],
                'Tiempo de viaje promedio': stats['avg_travel'],
                'Proporción bajos ingresos': stats['share_low_income'],
                'Dispersión gentrificación': stats['gentr_dispersion'],
                'Tasa de vacancia': stats['vacancy_rate'],
                'Unidades asequibles': stats['aff_units'],
                'Unidades de mercado': stats['mkt_units'],
                'Unidades totales': stats['total_units'],
                'Desplazamientos acumulados': stats['displacements_cum']
            }
            data.append(row)
        
        df_summary = pd.DataFrame(data)
        
        # Guardar CSV
        csv_path = self.output_dir / 'summary_table.csv'
        df_summary.to_csv(csv_path, index=False)
        print(f"📊 Tabla resumen guardada: {csv_path}")
        
        return df_summary
    
    def generate_targets_table(self):
        """Generar tabla de metas vs resultados"""
        
        data = []
        for metric, info in self.targets.items():
            row = {
                'Métrica': info['label'],
                'Meta deseable': info['goal']
            }
            
            # Agregar valores de cada escenario
            for scenario in sorted(self.summary_stats.keys()):
                if metric == 'displacements':
                    value = self.summary_stats[scenario]['displacements_cum']
                else:
                    value = self.summary_stats[scenario][metric]
                
                row[scenario] = info['format'].format(value)
            
            data.append(row)
        
        df_targets = pd.DataFrame(data)
        
        # Guardar CSV
        csv_path = self.output_dir / 'targets_comparison.csv'
        df_targets.to_csv(csv_path, index=False)
        print(f"🎯 Tabla de metas guardada: {csv_path}")
        
        return df_targets
    
    def plot_time_series_comparison(self):
        """Gráfica de series temporales comparando todos los escenarios"""
        
        # Métricas clave para comparar
        metrics = [
            ('avg_rent', 'Renta Promedio'),
            ('vacancy_rate', 'Tasa de Vacancia'),
            ('share_low_income', 'Proporción Bajos Ingresos'),
            ('displacements', 'Desplazamientos por Paso')
        ]
        
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=[title for _, title in metrics],
            vertical_spacing=0.12,
            horizontal_spacing=0.10
        )
        
        colors = px.colors.qualitative.Set2
        
        for idx, (metric, title) in enumerate(metrics):
            row = (idx // 2) + 1
            col = (idx % 2) + 1
            
            for i, (scenario, df) in enumerate(sorted(self.scenarios.items())):
                fig.add_trace(
                    go.Scatter(
                        x=df['step'],
                        y=df[metric],
                        name=scenario,
                        mode='lines',
                        line=dict(width=2, color=colors[i % len(colors)]),
                        showlegend=(idx == 0)  # Solo mostrar leyenda en primer gráfico
                    ),
                    row=row, col=col
                )
                
                # Agregar línea de meta si existe
                if metric in self.targets:
                    target_info = self.targets[metric]
                    if 'min' in target_info:
                        fig.add_hline(
                            y=target_info['min'],
                            line_dash="dash",
                            line_color="green",
                            opacity=0.5,
                            row=row, col=col
                        )
                    if 'max' in target_info:
                        fig.add_hline(
                            y=target_info['max'],
                            line_dash="dash",
                            line_color="red",
                            opacity=0.5,
                            row=row, col=col
                        )
        
        fig.update_layout(
            height=700,
            title_text="<b>Comparación Temporal de Indicadores Clave</b>",
            title_font_size=20,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5
            ),
            hovermode='x unified'
        )
        
        # Guardar
        print(f"📈 Gráfica de series temporales:")
        self._save_figure(fig, 'time_series_comparison', save_png=True)
        
        return fig
    
    def plot_final_comparison_radar(self):
        """Gráfica de radar comparando estado final de escenarios"""
        
        fig = go.Figure()
        
        # Métricas a incluir (normalizadas)
        metrics = ['avg_rent', 'vacancy_rate', 'share_low_income', 
                   'gentr_dispersion', 'avg_travel']
        labels = ['Renta', 'Vacancia', 'Bajos Ingresos', 
                  'Dispersión', 'Tiempo Viaje']
        
        colors = px.colors.qualitative.Set2
        
        for i, (scenario, stats) in enumerate(sorted(self.summary_stats.items())):
            # Normalizar valores (0-100)
            values = []
            for metric in metrics:
                val = stats[metric]
                # Normalización simple para visualización
                if metric == 'avg_rent':
                    norm_val = (val / 500) * 100  # Escala respecto a 500
                elif metric == 'vacancy_rate':
                    norm_val = (1 - abs(val - 0.10) / 0.35) * 100  # Óptimo cerca de 10%
                elif metric == 'share_low_income':
                    norm_val = val * 250  # Escala 0-1 a 0-100
                elif metric == 'gentr_dispersion':
                    norm_val = (1 - val / 0.5) * 100  # Menos es mejor
                elif metric == 'avg_travel':
                    norm_val = (1 - val / 20) * 100  # Menos es mejor
                else:
                    norm_val = val
                    
                values.append(max(0, min(100, norm_val)))
            
            values.append(values[0])  # Cerrar el polígono
            
            fig.add_trace(go.Scatterpolar(
                r=values,
                theta=labels + [labels[0]],
                name=scenario,
                fill='toself',
                line=dict(color=colors[i % len(colors)], width=2)
            ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )
            ),
            title="<b>Comparación Multidimensional de Escenarios</b><br>(Estado Final Normalizado)",
            title_font_size=18,
            showlegend=True,
            height=600
        )
        
        print(f"🎯 Gráfica radar:")
        self._save_figure(fig, 'radar_comparison', save_png=True)
        
        return fig
    
    def plot_displacement_story(self):
        """Gráfica que cuenta la historia de los desplazamientos"""
        
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=('Desplazamientos Acumulados', 'Desplazamientos por Paso'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        colors = px.colors.qualitative.Set2
        
        for i, (scenario, df) in enumerate(sorted(self.scenarios.items())):
            # Desplazamientos acumulados
            cumulative = df['displacements'].cumsum()
            
            fig.add_trace(
                go.Scatter(
                    x=df['step'],
                    y=cumulative,
                    name=scenario,
                    mode='lines',
                    line=dict(width=3, color=colors[i % len(colors)]),
                    showlegend=True
                ),
                row=1, col=1
            )
            
            # Desplazamientos por paso
            fig.add_trace(
                go.Scatter(
                    x=df['step'],
                    y=df['displacements'],
                    name=scenario,
                    mode='lines',
                    line=dict(width=2, color=colors[i % len(colors)]),
                    showlegend=False
                ),
                row=1, col=2
            )
        
        # Línea de meta
        if 'displacements' in self.targets and 'max' in self.targets['displacements']:
            fig.add_hline(
                y=self.targets['displacements']['max'],
                line_dash="dash",
                line_color="red",
                annotation_text="Meta (<30k)",
                row=1, col=1
            )
        
        fig.update_xaxes(title_text="Paso (mes)", row=1, col=1)
        fig.update_xaxes(title_text="Paso (mes)", row=1, col=2)
        fig.update_yaxes(title_text="Desplazamientos Acumulados", row=1, col=1)
        fig.update_yaxes(title_text="Desplazamientos", row=1, col=2)
        
        fig.update_layout(
            height=500,
            title_text="<b>Historia de Desplazamientos: Impacto de Políticas</b>",
            title_font_size=18,
            hovermode='x unified',
            showlegend=True
        )
        
        print(f"🏠 Gráfica de desplazamientos:")
        self._save_figure(fig, 'displacement_story', save_png=True)
        
        return fig
    
    def plot_housing_evolution(self):
        """Gráfica de evolución de unidades de vivienda"""
        
        fig = go.Figure()
        
        colors = px.colors.qualitative.Set2
        
        for i, (scenario, df) in enumerate(sorted(self.scenarios.items())):
            color = colors[i % len(colors)]
            
            # Unidades asequibles
            fig.add_trace(go.Scatter(
                x=df['step'],
                y=df['aff_units'],
                name=f'{scenario} - Asequibles',
                mode='lines',
                line=dict(width=2, color=color, dash='solid'),
                stackgroup=f'one{i}'
            ))
            
            # Unidades de mercado
            fig.add_trace(go.Scatter(
                x=df['step'],
                y=df['mkt_units'],
                name=f'{scenario} - Mercado',
                mode='lines',
                line=dict(width=2, color=color, dash='dash'),
                stackgroup=f'one{i}'
            ))
        
        fig.update_layout(
            title="<b>Evolución del Stock de Vivienda por Escenario</b>",
            title_font_size=18,
            xaxis_title="Paso (mes)",
            yaxis_title="Unidades de Vivienda",
            hovermode='x unified',
            height=600,
            showlegend=True
        )
        
        print(f"🏘️  Gráfica de vivienda:")
        self._save_figure(fig, 'housing_evolution', save_png=True)
        
        return fig
    
    def plot_equity_story(self):
        """Gráfica que cuenta la historia de equidad y gentrificación"""
        
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=(
                'Diversidad: Proporción de Hogares de Bajos Ingresos',
                'Segregación: Dispersión del Índice de Gentrificación'
            ),
            vertical_spacing=0.15
        )
        
        colors = px.colors.qualitative.Set2
        
        for i, (scenario, df) in enumerate(sorted(self.scenarios.items())):
            color = colors[i % len(colors)]
            
            # Proporción de bajos ingresos
            fig.add_trace(
                go.Scatter(
                    x=df['step'],
                    y=df['share_low_income'],
                    name=scenario,
                    mode='lines',
                    line=dict(width=2, color=color),
                    showlegend=True
                ),
                row=1, col=1
            )
            
            # Dispersión de gentrificación
            fig.add_trace(
                go.Scatter(
                    x=df['step'],
                    y=df['gentr_dispersion'],
                    name=scenario,
                    mode='lines',
                    line=dict(width=2, color=color),
                    showlegend=False
                ),
                row=2, col=1
            )
        
        # Líneas de meta
        if 'share_low_income' in self.targets and 'min' in self.targets['share_low_income']:
            fig.add_hline(
                y=self.targets['share_low_income']['min'],
                line_dash="dash",
                line_color="green",
                annotation_text="Meta (≥0.40)",
                row=1, col=1
            )
        
        if 'gentr_dispersion' in self.targets and 'max' in self.targets['gentr_dispersion']:
            fig.add_hline(
                y=self.targets['gentr_dispersion']['max'],
                line_dash="dash",
                line_color="red",
                annotation_text="Meta (≤0.35)",
                row=2, col=1
            )
        
        fig.update_xaxes(title_text="Paso (mes)", row=2, col=1)
        fig.update_yaxes(title_text="Proporción", row=1, col=1)
        fig.update_yaxes(title_text="Índice", row=2, col=1)
        
        fig.update_layout(
            height=700,
            title_text="<b>Equidad y Gentrificación: Impacto de Políticas</b>",
            title_font_size=18,
            hovermode='x unified'
        )
        
        print(f"⚖️  Gráfica de equidad:")
        self._save_figure(fig, 'equity_story', save_png=True)
        
        return fig
    
    def plot_dashboard(self):
        """Crear un dashboard completo con las métricas clave"""
        
        fig = make_subplots(
            rows=3, cols=2,
            subplot_titles=(
                'Renta Promedio',
                'Tasa de Vacancia',
                'Tiempo de Viaje',
                'Diversidad (Bajos Ingresos)',
                'Desplazamientos Acumulados',
                'Segregación (Dispersión)'
            ),
            vertical_spacing=0.10,
            horizontal_spacing=0.12
        )
        
        colors = px.colors.qualitative.Set2
        metrics_layout = [
            (1, 1, 'avg_rent'),
            (1, 2, 'vacancy_rate'),
            (2, 1, 'avg_travel'),
            (2, 2, 'share_low_income'),
            (3, 1, 'displacements_cum'),
            (3, 2, 'gentr_dispersion')
        ]
        
        for i, (scenario, df) in enumerate(sorted(self.scenarios.items())):
            color = colors[i % len(colors)]
            
            for row, col, metric in metrics_layout:
                if metric == 'displacements_cum':
                    y_data = df['displacements'].cumsum()
                else:
                    y_data = df[metric]
                
                fig.add_trace(
                    go.Scatter(
                        x=df['step'],
                        y=y_data,
                        name=scenario,
                        mode='lines',
                        line=dict(width=2, color=color),
                        showlegend=(row == 1 and col == 1)
                    ),
                    row=row, col=col
                )
        
        fig.update_layout(
            height=900,
            title_text="<b>Dashboard Comparativo de Escenarios</b>",
            title_font_size=20,
            hovermode='x unified',
            showlegend=True
        )
        
        print(f"📊 Dashboard completo guardado:")
        self._save_figure(fig, 'dashboard_complete', save_png=True)
        
        return fig
    
    def generate_all_analyses(self):
        """Generar todos los análisis y gráficas"""
        
        print("\n" + "="*70)
        print("🔍 INICIANDO ANÁLISIS COMPARATIVO DE ESCENARIOS")
        print("="*70 + "\n")
        
        # Tablas
        print("📋 Generando tablas resumen...")
        df_summary = self.generate_summary_table()
        df_targets = self.generate_targets_table()
        
        # Gráficas
        print("\n📈 Generando gráficas...")
        self.plot_time_series_comparison()
        self.plot_final_comparison_radar()
        self.plot_displacement_story()
        self.plot_housing_evolution()
        self.plot_equity_story()
        self.plot_dashboard()
        
        # Resumen final
        print("\n" + "="*70)
        print("✅ ANÁLISIS COMPLETADO")
        print("="*70)
        print(f"\n📁 Todos los archivos guardados en: {self.output_dir}")
        print("\nArchivos generados:")
        print("  📄 summary_table.csv - Tabla resumen de indicadores")
        print("  📄 targets_comparison.csv - Comparación con metas")
        print("  📊 time_series_comparison.html - Series temporales")
        print("  🎯 radar_comparison.html - Comparación multidimensional")
        print("  🏠 displacement_story.html - Historia de desplazamientos")
        print("  🏘️  housing_evolution.html - Evolución de vivienda")
        print("  ⚖️  equity_story.html - Equidad y gentrificación")
        print("  📊 dashboard_complete.html - Dashboard completo")
        print("\n" + "="*70 + "\n")
        
        return df_summary, df_targets


def main():
    """Función principal para ejecutar el análisis"""
    
    # Crear analizador
    analyzer = ScenarioAnalyzer(output_dir="outputs/comparative_analysis")
    
    # Cargar escenarios (ajustar rutas según tu estructura)
    print("📂 Cargando escenarios...")
    
    # Ejemplo: cargar baseline y escenarios
    analyzer.load_scenario("outputs/rt_results.csv", "B0")
    analyzer.load_scenario("run_sim/S1RUN/results1.csv", "S1")
    analyzer.load_scenario("run_sim/S2RUN/results2.csv", "S2")
    analyzer.load_scenario("run_sim/S3RUN/results3.csv", "S3")
    
    # Generar todos los análisis
    df_summary, df_targets = analyzer.generate_all_analyses()
    
    # Mostrar resumen
    print("\n📊 RESUMEN DE INDICADORES FINALES:")
    print(df_summary.to_string(index=False))
    
    print("\n🎯 COMPARACIÓN CON METAS:")
    print(df_targets.to_string(index=False))


if __name__ == "__main__":
    main()

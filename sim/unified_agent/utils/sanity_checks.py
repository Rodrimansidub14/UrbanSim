"""
Sanity Checks - Validadores de integridad y coherencia del modelo
Verifica conservación de stock, dimensiones, rangos válidos y alertas de rendimiento
"""
import numpy as np
from typing import Dict, Any, List, Tuple


class SanityChecker:
    """
    Ejecuta validaciones automáticas de coherencia del modelo
    Retorna resultados tipo semáforo (green/yellow/red)
    """
    
    def __init__(self):
        self.checks_history = []
        self.alert_threshold = 3  # Número de fallos consecutivos para alerta crítica
        
    def run_all_checks(self, state: Dict[str, Any]) -> Dict[str, Dict]:
        """
        Ejecuta todas las validaciones sobre el estado actual
        
        Args:
            state: Diccionario con el estado de la simulación
            
        Returns:
            Diccionario con resultados de cada check
        """
        kpis = state.get('kpis', {})
        spatial = state.get('spatial', {})
        performance = state.get('performance', {})
        
        results = {
            'stock_balance': self.check_stock_balance(kpis),
            'vacancy_range': self.check_vacancy_range(kpis),
            'capacity_balance': self.check_capacity_balance(spatial, kpis),
            'dimensions_valid': self.check_dimensions(kpis),
            'coherence_vacancy': self.check_coherence_vacancy_rent(kpis),
            'coherence_policy': self.check_coherence_policy_effects(kpis),
            'performance': self.check_performance(performance),
        }
        
        # Guardar en historial
        self.checks_history.append(results)
        if len(self.checks_history) > 100:
            self.checks_history.pop(0)
            
        return results
        
    def check_stock_balance(self, kpis: Dict) -> Dict:
        """Verifica que total_units = aff_units + mkt_units"""
        try:
            total = kpis.get('total_units', 0)
            aff = kpis.get('aff_units', 0)
            mkt = kpis.get('mkt_units', 0)
            
            balance = abs(total - (aff + mkt))
            
            if balance == 0:
                return {'status': 'green', 'message': 'Stock balanced', 'value': balance}
            elif balance < 5:
                return {'status': 'yellow', 'message': f'Minor imbalance: {balance} units', 'value': balance}
            else:
                return {'status': 'red', 'message': f'Stock imbalance: {balance} units!', 'value': balance}
                
        except Exception as e:
            return {'status': 'red', 'message': f'Error: {str(e)}', 'value': None}
            
    def check_vacancy_range(self, kpis: Dict) -> Dict:
        """Verifica que 0 <= vacancy_rate <= 1"""
        try:
            vacancy = kpis.get('vacancy_rate', 0)
            
            if 0 <= vacancy <= 1:
                if 0.05 <= vacancy <= 0.25:
                    return {'status': 'green', 'message': f'Vacancy OK: {vacancy:.1%}', 'value': vacancy}
                elif vacancy < 0.05:
                    return {'status': 'yellow', 'message': f'Very low vacancy: {vacancy:.1%}', 'value': vacancy}
                else:
                    return {'status': 'yellow', 'message': f'High vacancy: {vacancy:.1%}', 'value': vacancy}
            else:
                return {'status': 'red', 'message': f'Invalid vacancy: {vacancy:.1%}!', 'value': vacancy}
                
        except Exception as e:
            return {'status': 'red', 'message': f'Error: {str(e)}', 'value': None}
            
    def check_capacity_balance(self, spatial: Dict, kpis: Dict) -> Dict:
        """Verifica que población <= capacidad ocupada"""
        try:
            if 'population' not in spatial:
                return {'status': 'yellow', 'message': 'No spatial data', 'value': None}
                
            pop_grid = np.array(spatial['population'])
            total_pop = pop_grid.sum()
            
            # Estimar capacidad (unidades ocupadas * k personas/unidad)
            total_units = kpis.get('total_units', 0)
            vacancy = kpis.get('vacancy_rate', 0)
            occupied = total_units * (1 - vacancy)
            capacity = occupied * 3  # Asumiendo k=3 personas/unidad promedio
            
            if total_pop <= capacity:
                ratio = total_pop / capacity if capacity > 0 else 0
                return {'status': 'green', 'message': f'Capacity OK: {ratio:.1%}', 'value': ratio}
            else:
                return {'status': 'red', 'message': f'Overpopulation!', 'value': total_pop / capacity}
                
        except Exception as e:
            return {'status': 'yellow', 'message': f'Cannot verify: {str(e)}', 'value': None}
            
    def check_dimensions(self, kpis: Dict) -> Dict:
        """Verifica que todas las magnitudes sean no-negativas"""
        try:
            checks = {
                'avg_rent': kpis.get('avg_rent', 0),
                'avg_travel': kpis.get('avg_travel', 0),
                'vacancy_rate': kpis.get('vacancy_rate', 0),
                'share_low_income': kpis.get('share_low_income', 0),
            }
            
            invalid = [k for k, v in checks.items() if v < 0]
            
            if not invalid:
                return {'status': 'green', 'message': 'All dimensions valid', 'value': checks}
            else:
                return {'status': 'red', 'message': f'Invalid: {invalid}', 'value': checks}
                
        except Exception as e:
            return {'status': 'red', 'message': f'Error: {str(e)}', 'value': None}
            
    def check_coherence_vacancy_rent(self, kpis: Dict) -> Dict:
        """Verifica coherencia: vacancia alta → renta baja (tendencia esperada)"""
        try:
            if len(self.checks_history) < 5:
                return {'status': 'yellow', 'message': 'Not enough data', 'value': None}
                
            # Obtener últimas 5 observaciones
            recent = self.checks_history[-5:]
            
            # Extraer series de vacancia y renta
            vacancy_series = [r.get('vacancy_range', {}).get('value', 0) for r in recent]
            rent_series = [kpis.get('avg_rent', 0) for _ in recent]  # Simplificado
            
            # Correlación esperada: negativa (↑ vacancy → ↓ rent)
            # En simulación real deberíamos ver esta tendencia
            
            current_vacancy = kpis.get('vacancy_rate', 0)
            current_rent = kpis.get('avg_rent', 0)
            
            # Lógica simplificada: si vacancy > 0.3 pero rent sigue alto, warning
            if current_vacancy > 0.3 and current_rent > 400:
                return {'status': 'yellow', 'message': 'High vacancy but high rent', 'value': (current_vacancy, current_rent)}
            else:
                return {'status': 'green', 'message': 'Vacancy-rent coherent', 'value': (current_vacancy, current_rent)}
                
        except Exception as e:
            return {'status': 'yellow', 'message': f'Cannot verify: {str(e)}', 'value': None}
            
    def check_coherence_policy_effects(self, kpis: Dict) -> Dict:
        """Verifica coherencia de efectos de políticas"""
        try:
            params = kpis.get('params', {})
            
            # Si hay voucher o affordable share alta, low_income_share debería ser mayor
            aff_share = params.get('aff_share', 0)
            voucher = params.get('voucher_discount', 0)
            low_income_share = kpis.get('share_low_income', 0)
            
            # Expectativa: si aff_share > 0.4 o voucher > 0.15, entonces low_income > 0.35
            if (aff_share > 0.4 or voucher > 0.15) and low_income_share < 0.25:
                return {'status': 'yellow', 'message': 'Policy not effective?', 'value': low_income_share}
            else:
                return {'status': 'green', 'message': 'Policy effects coherent', 'value': low_income_share}
                
        except Exception as e:
            return {'status': 'yellow', 'message': f'Cannot verify: {str(e)}', 'value': None}
            
    def check_performance(self, performance: Dict) -> Dict:
        """Verifica rendimiento del sistema (ms/tick, memory, etc.)"""
        try:
            ms_per_tick = performance.get('ms_per_tick', 0)
            ws_queue = performance.get('ws_queue_size', 0)
            
            status = 'green'
            messages = []
            
            if ms_per_tick > 150:
                status = 'red'
                messages.append(f'Slow: {ms_per_tick:.0f}ms/tick')
            elif ms_per_tick > 100:
                status = 'yellow'
                messages.append(f'Degraded: {ms_per_tick:.0f}ms/tick')
            else:
                messages.append(f'Performance OK: {ms_per_tick:.0f}ms/tick')
                
            if ws_queue > 10:
                status = 'red' if status != 'red' else status
                messages.append(f'WS backlog: {ws_queue}')
                
            return {
                'status': status,
                'message': ', '.join(messages),
                'value': {'ms_per_tick': ms_per_tick, 'ws_queue': ws_queue}
            }
            
        except Exception as e:
            return {'status': 'yellow', 'message': f'Cannot measure: {str(e)}', 'value': None}
            
    def get_overall_status(self, results: Dict[str, Dict]) -> str:
        """
        Calcula estado general basado en todos los checks
        
        Returns:
            'green', 'yellow', o 'red'
        """
        statuses = [r['status'] for r in results.values()]
        
        if 'red' in statuses:
            return 'red'
        elif 'yellow' in statuses:
            return 'yellow'
        else:
            return 'green'
            
    def get_alerts(self, results: Dict[str, Dict]) -> List[str]:
        """
        Retorna lista de mensajes de alerta (solo yellow y red)
        
        Returns:
            Lista de strings con alertas
        """
        alerts = []
        for check_name, result in results.items():
            if result['status'] in ['yellow', 'red']:
                icon = '⚠️' if result['status'] == 'yellow' else '🚨'
                alerts.append(f"{icon} {check_name}: {result['message']}")
        return alerts

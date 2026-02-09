import numpy as np
from scipy.optimize import minimize
from cvar_portfolio_sampler import CVaRPortfolioSampler


def linear_path_projection(
    w_previous,
    cvar_limit,
    returns,
    confidence_level,
    w_safe=None,
    max_bisection_iters=20
):
    """
    Proyecta w_previous al espacio factible usando bisección en línea recta.
    
    Encuentra el punto más cercano a w_previous en la línea [w_safe, w_previous]
    que cumple CVaR < cvar_limit.
    
    Parameters:
    -----------
    w_previous : array
        Portafolio anterior que no cumple la restricción
    cvar_limit : float
        Límite de CVaR que debe cumplirse
    returns : array
        Matriz de retornos para calcular CVaR
    confidence_level : float
        Nivel de confianza para CVaR (ej: 0.05)
    w_safe : array, optional
        Portafolio de referencia que cumple CVaR. Si None, usa pesos iguales.
    max_bisection_iters : int
        Número de iteraciones para bisección
    
    Returns:
    --------
    w_projected : array
        Portafolio proyectado que cumple CVaR < cvar_limit
    """
    n_assets = len(w_previous)
    
    # Si no se proporciona w_safe, usar pesos iguales
    if w_safe is None:
        w_safe = np.ones(n_assets) / n_assets
    
    # Crear sampler para calcular CVaR
    sampler = CVaRPortfolioSampler(returns, confidence_level)
    
    # Verificar que w_safe cumple la restricción
    cvar_safe = sampler.calculate_cvar(w_safe)
    if cvar_safe >= cvar_limit:
        # w_safe no cumple, intentar encontrar otro punto
        # Buscar portafolio de mínimo CVaR
        try:
            w_safe = find_minimum_cvar_portfolio(returns, confidence_level)
            cvar_safe = sampler.calculate_cvar(w_safe)
            
            if cvar_safe >= cvar_limit:
                raise ValueError(
                    f"No se pudo encontrar un punto factible. "
                    f"CVaR mínimo posible ({cvar_safe:.6f}) >= límite ({cvar_limit:.6f})"
                )
        except Exception as e:
            raise ValueError(f"Error al buscar punto factible: {str(e)}")
    
    # Bisección en la línea [w_safe, w_previous]
    # Buscamos: w = (1-λ)*w_safe + λ*w_previous
    # donde λ es máximo tal que CVaR(w) < cvar_limit
    
    lambda_low = 0.0   # w_safe (cumple CVaR)
    lambda_high = 1.0  # w_previous (no cumple CVaR)
    
    for _ in range(max_bisection_iters):
        lambda_mid = (lambda_low + lambda_high) / 2
        w_mid = (1 - lambda_mid) * w_safe + lambda_mid * w_previous
        w_mid = w_mid / np.sum(w_mid)  # Renormalizar
        
        cvar_mid = sampler.calculate_cvar(w_mid)
        
        if cvar_mid < cvar_limit:
            lambda_low = lambda_mid  # w_mid cumple, podemos ir más cerca de w_previous
        else:
            lambda_high = lambda_mid  # w_mid no cumple, debemos acercarnos a w_safe
    
    # Retornar el punto más cercano a w_previous que cumple
    w_projected = (1 - lambda_low) * w_safe + lambda_low * w_previous
    w_projected = w_projected / np.sum(w_projected)
    
    return w_projected


def find_minimum_cvar_portfolio(returns, confidence_level):
    """
    Encuentra el portafolio con el CVaR más bajo posible.
    
    Parameters:
    -----------
    returns : array
        Matriz de retornos
    confidence_level : float
        Nivel de confianza para CVaR
    
    Returns:
    --------
    w_min : array
        Portafolio de mínimo CVaR
    """
    n_assets = returns.shape[1]
    
    sampler = CVaRPortfolioSampler(returns, confidence_level)
    
    def objective(w):
        return sampler.calculate_cvar(w)
    
    constraints = {'type': 'eq', 'fun': lambda w: np.sum(w) - 1}
    bounds = [(0, 1) for _ in range(n_assets)]
    x0 = np.ones(n_assets) / n_assets
    
    result = minimize(
        objective,
        x0,
        method='SLSQP',
        bounds=bounds,
        constraints=constraints,
        options={'maxiter': 200, 'ftol': 1e-8}
    )
    
    if result.success:
        return result.x
    else:
        # Si falla, retornar pesos iguales
        return x0


def calculate_adaptive_burn_in(expansion_ratio, base_burn_in=5, max_burn_in=20):
    """
    Calcula burn-in cuando el espacio factible se expande.
    
    SIMPLIFIED VERSION: Returns fixed burn-in value (base_burn_in).
    The max_burn_in parameter is kept for backward compatibility but not used.
    
    Parameters:
    -----------
    expansion_ratio : float
        Ratio cvar_limit_current / cvar_limit_prev
    base_burn_in : int
        Fixed burn-in value to return when space expands
    max_burn_in : int
        Not used (kept for compatibility)
    
    Returns:
    --------
    burn_in : int
        Número de iteraciones de burn-in
        
    Examples:
    ---------
    expansion_ratio = 1.0 (sin cambio) → burn_in = 0
    expansion_ratio > 1.01 (expansión) → burn_in = base_burn_in (default: 5)
    """
    if expansion_ratio <= 1.01:  # Cambio insignificante
        return 0
    
    # Retornar valor fijo cuando hay expansión
    return base_burn_in


def determine_burn_in_and_initial_point(
    w_prev,
    cvar_limit_current,
    cvar_limit_prev,
    returns_current_month,
    confidence_level,
    w_safe=None,
    tolerance=1e-6,
    adaptive_base_burn_in=5,
    adaptive_max_burn_in=20,
    projection_burn_in=10
):
    """
    Determina burn-in e initial_point según factibilidad y cambio de restricción.
    
    Parameters:
    -----------
    w_prev : array
        Portafolio del mes anterior (posterior en tiempo, ya que vamos backward)
    cvar_limit_current : float
        Límite CVaR del mes actual
    cvar_limit_prev : float
        Límite CVaR del mes anterior (posterior)
    returns_current_month : array
        Retornos simulados del mes actual
    confidence_level : float
        Nivel de confianza para CVaR
    w_safe : array, optional
        Portafolio de referencia factible
    tolerance : float
        Tolerancia numérica para comparaciones
    adaptive_base_burn_in : int
        Burn-in base para expansión adaptativa
    adaptive_max_burn_in : int
        Burn-in máximo para expansión adaptativa
    projection_burn_in : int
        Burn-in cuando se requiere proyección
    
    Returns:
    --------
    initial_point : array
        Punto inicial para Hit-and-Run
    burn_in : int
        Número de iteraciones de burn-in
    feasibility_status : str
        Estado de factibilidad ('feasible', 'projected', 'same_limit')
    """
    # Crear sampler para calcular CVaR
    sampler = CVaRPortfolioSampler(returns_current_month, confidence_level)
    
    # Calcular CVaR del portafolio anterior con returns del mes actual
    cvar_prev = sampler.calculate_cvar(w_prev)
    
    # Verificar factibilidad con tolerancia numérica
    is_feasible = (cvar_prev < cvar_limit_current - tolerance)
    
    # CASO 1: Portafolio previo es factible
    if is_feasible:
        initial_point = w_prev
        
        # Sub-caso 1a: Misma restricción → Sin burn-in
        if abs(cvar_limit_current - cvar_limit_prev) < tolerance:
            burn_in = 0
            feasibility_status = 'same_limit'
        
        # Sub-caso 1b: Restricción más relajada → Burn-in adaptativo
        else:
            expansion_ratio = cvar_limit_current / cvar_limit_prev
            burn_in = calculate_adaptive_burn_in(
                expansion_ratio,
                base_burn_in=adaptive_base_burn_in,
                max_burn_in=adaptive_max_burn_in
            )
            feasibility_status = 'feasible'
    
    # CASO 2: Portafolio previo NO es factible
    else:
        # Proyectar al espacio factible
        initial_point = linear_path_projection(
            w_previous=w_prev,
            cvar_limit=cvar_limit_current,
            returns=returns_current_month,
            confidence_level=confidence_level,
            w_safe=w_safe
        )
        
        # Burn-in moderado para explorar desde el punto proyectado
        burn_in = projection_burn_in
        feasibility_status = 'projected'
    
    return initial_point, burn_in, feasibility_status


def generate_single_trajectory_backward(
    cvar_limits,
    returns_matrix,
    confidence_level,
    initial_burn_in=25,
    adaptive_base_burn_in=5,
    adaptive_max_burn_in=20,
    projection_burn_in=10,
    verbose=False
):
    """
    Genera UNA trayectoria completa de atrás hacia adelante.
    
    Parameters:
    -----------
    cvar_limits : array, shape (n_months,)
        Límites de CVaR para cada mes
    returns_matrix : array, shape (n_months, n_scenarios, n_assets)
        Retornos simulados por mes
    confidence_level : float
        Nivel de confianza para CVaR (ej: 0.05 para 95% CVaR)
    initial_burn_in : int
        Burn-in para el último mes (más restrictivo)
    adaptive_base_burn_in : int
        Burn-in base para expansión adaptativa
    adaptive_max_burn_in : int
        Burn-in máximo para expansión adaptativa
    projection_burn_in : int
        Burn-in cuando se requiere proyección
    verbose : bool
        Si True, imprime información de debug
    
    Returns:
    --------
    trajectory : array, shape (n_months, n_assets)
        Trayectoria de portafolios en orden cronológico [mes 0, mes 1, ..., mes T-1]
    stats : dict
        Estadísticas de la generación (para debugging)
    """
    n_months = len(cvar_limits)
    n_assets = returns_matrix.shape[2]
    trajectory_backward = []
    
    # Estadísticas para debugging
    stats = {
        'feasible_count': 0,
        'projected_count': 0,
        'same_limit_count': 0,
        'total_burn_in': 0,
        'projection_events': []
    }
    
    # Calcular w_safe una sola vez (para usar en proyecciones)
    # Usamos los retornos del último mes (más restrictivo)
    returns_last_month = returns_matrix[-1]
    w_safe = find_minimum_cvar_portfolio(returns_last_month, confidence_level)
    
    w_current = None
    cvar_limit_prev = None
    
    # Iterar de atrás hacia adelante: mes T-1, T-2, ..., 1, 0
    for t in range(n_months - 1, -1, -1):
        cvar_limit = cvar_limits[t]
        returns_t = returns_matrix[t]  # Retornos del mes t
        
        # Crear sampler para este mes específico
        sampler = CVaRPortfolioSampler(returns_t, confidence_level)
        
        # MES FINAL (t = n_months - 1)
        if t == n_months - 1:
            initial_point = None  # Buscar desde cero
            burn_in = initial_burn_in
            feasibility_status = 'initial'
            
            if verbose:
                print(f"Mes {t}: INICIAL - Burn-in = {burn_in}")
        
        # MESES ANTERIORES
        else:
            initial_point, burn_in, feasibility_status = determine_burn_in_and_initial_point(
                w_prev=w_current,
                cvar_limit_current=cvar_limit,
                cvar_limit_prev=cvar_limit_prev,
                returns_current_month=returns_t,
                confidence_level=confidence_level,
                w_safe=w_safe,
                adaptive_base_burn_in=adaptive_base_burn_in,
                adaptive_max_burn_in=adaptive_max_burn_in,
                projection_burn_in=projection_burn_in
            )
            
            # Actualizar estadísticas
            if feasibility_status == 'feasible':
                stats['feasible_count'] += 1
            elif feasibility_status == 'projected':
                stats['projected_count'] += 1
                stats['projection_events'].append({
                    'month': t,
                    'cvar_limit': cvar_limit,
                    'cvar_prev': sampler.calculate_cvar(w_current)
                })
            elif feasibility_status == 'same_limit':
                stats['same_limit_count'] += 1
            
            if verbose and feasibility_status == 'projected':
                cvar_prev = sampler.calculate_cvar(w_current)
                print(f"Mes {t}: PROYECCIÓN - CVaR_prev={cvar_prev:.6f} > límite={cvar_limit:.6f}, Burn-in={burn_in}")
            elif verbose and burn_in > 0:
                print(f"Mes {t}: {feasibility_status.upper()} - Burn-in = {burn_in}")
        
        stats['total_burn_in'] += burn_in
        
        # Generar portafolio con Hit-and-Run
        portfolios = sampler.generate_portfolios(
            target_cvar=cvar_limit,
            n_samples=1,
            burn_in=burn_in,
            initial_point=initial_point
        )
        
        w_current = portfolios[0]
        cvar_limit_prev = cvar_limit
        trajectory_backward.append(w_current)
    
    # Invertir para orden cronológico [mes 0, mes 1, ..., mes T-1]
    trajectory_forward = np.array(list(reversed(trajectory_backward)))
    
    return trajectory_forward, stats


def validate_trajectory(trajectory, cvar_limits, returns_matrix, confidence_level, tolerance=1e-6):
    """
    Valida que toda la trayectoria cumpla las restricciones.
    
    Parameters:
    -----------
    trajectory : array, shape (n_months, n_assets)
        Trayectoria de portafolios
    cvar_limits : array, shape (n_months,)
        Límites de CVaR
    returns_matrix : array, shape (n_months, n_scenarios, n_assets)
        Retornos simulados
    confidence_level : float
        Nivel de confianza para CVaR
    tolerance : float
        Tolerancia para violaciones
    
    Returns:
    --------
    violations : list
        Lista de violaciones (vacía si todo está bien)
    """
    violations = []
    
    for t in range(len(trajectory)):
        w_t = trajectory[t]
        returns_t = returns_matrix[t]
        cvar_limit_t = cvar_limits[t]
        
        # Verificar sum(w) = 1
        weight_sum = np.sum(w_t)
        if not np.isclose(weight_sum, 1.0, atol=tolerance):
            violations.append({
                'month': t,
                'type': 'weight_sum',
                'value': weight_sum,
                'message': f'Sum of weights = {weight_sum:.6f} ≠ 1.0'
            })
        
        # Verificar w >= 0
        min_weight = np.min(w_t)
        if min_weight < -tolerance:
            violations.append({
                'month': t,
                'type': 'negative_weight',
                'value': min_weight,
                'message': f'Negative weight = {min_weight:.6f} < 0'
            })
        
        # Verificar CVaR < límite
        sampler = CVaRPortfolioSampler(returns_t, confidence_level)
        cvar_t = sampler.calculate_cvar(w_t)
        
        if cvar_t >= cvar_limit_t + tolerance:
            violations.append({
                'month': t,
                'type': 'cvar_violation',
                'cvar': cvar_t,
                'limit': cvar_limit_t,
                'excess': cvar_t - cvar_limit_t,
                'message': f'CVaR = {cvar_t:.6f} >= limit = {cvar_limit_t:.6f}'
            })
    
    return violations

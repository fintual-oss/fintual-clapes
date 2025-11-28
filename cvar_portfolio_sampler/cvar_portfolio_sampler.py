import numpy as np
from scipy.optimize import minimize


class CVaRPortfolioSampler:
    """
    Portfolio sampler using Hit-and-Run algorithm for CVaR-constrained portfolios.

    Generates random portfolios that satisfy:
    - sum(w) = 1 (weights sum to 1)
    - w >= 0 (no short selling)
    - CVaR(w) < target_cvar (CVaR constraint)
    """

    def __init__(self, returns, confidence_level=0.05):
        """
        Initialize the portfolio sampler.

        Parameters:
        -----------
        returns : array-like, shape (n_periods, n_assets)
            Historical returns matrix
        confidence_level : float, default=0.05
            CVaR confidence level (e.g., 0.05 for 5% tail)
        """
        self.returns = np.asarray(returns)
        self.confidence_level = confidence_level
        self.n_periods, self.n_assets = self.returns.shape

    def calculate_cvar(self, weights):
        """
        Calculate Conditional Value at Risk (CVaR) for given weights.

        Parameters:
        -----------
        weights : array-like, shape (n_assets,)
            Portfolio weights

        Returns:
        --------
        cvar : float
            Conditional Value at Risk
        """
        portfolio_returns = self.returns.dot(weights)
        var = -np.percentile(portfolio_returns, self.confidence_level * 100)
        losses = -portfolio_returns
        cvar = np.mean(losses[losses >= var])
        return cvar

    def _find_initial_feasible_point(self, target_cvar, max_iter=100):
        """
        Find an initial portfolio that satisfies all constraints.

        Parameters:
        -----------
        target_cvar : float
            Maximum allowed CVaR
        max_iter : int
            Maximum iterations for random search

        Returns:
        --------
        weights : array
            Initial feasible portfolio weights
        """
        n_assets = self.n_assets

        # Try equal weights first
        w = np.ones(n_assets) / n_assets
        if self.calculate_cvar(w) < target_cvar:
            return w

        # Try random portfolios
        for _ in range(max_iter):
            w = np.random.dirichlet(np.ones(n_assets))
            if self.calculate_cvar(w) < target_cvar:
                return w

        # If no random portfolio works, try optimization to minimize CVaR
        def objective(w):
            return self.calculate_cvar(w)

        constraints = {"type": "eq", "fun": lambda w: np.sum(w) - 1}
        bounds = [(0, 1) for _ in range(n_assets)]
        x0 = np.ones(n_assets) / n_assets

        result = minimize(
            objective,
            x0,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
            options={"maxiter": 100},
        )

        if result.success and self.calculate_cvar(result.x) < target_cvar:
            return result.x

        raise ValueError(
            "Could not find initial feasible point. Try increasing target_cvar."
        )

    @staticmethod
    def _project_direction_onto_simplex(direction):
        """
        Project a direction vector onto the hyperplane sum(w) = 0.
        This ensures that moving in this direction preserves sum(w) = 1.
        """
        return direction - np.mean(direction)

    def _find_feasible_line_segment(
        self, current_point, direction, target_cvar, tol=1e-8
    ):
        """
        Find the line segment [t_min, t_max] such that:
        - current_point + t * direction is in the feasible region
        - Feasible region: sum(w)=1, w>=0, CVaR < target_cvar

        Returns:
        --------
        t_min, t_max : float
            Bounds of feasible line segment
        """
        n_assets = len(current_point)

        # Find bounds from non-negativity constraints: w_i >= 0
        t_bounds = []
        for i in range(n_assets):
            if abs(direction[i]) > tol:
                t_bound = -current_point[i] / direction[i]
                if direction[i] > 0:
                    t_bounds.append((t_bound, np.inf))  # Lower bound
                else:
                    t_bounds.append((-np.inf, t_bound))  # Upper bound

        t_min_linear = max([b[0] for b in t_bounds if b[0] != -np.inf], default=-np.inf)
        t_max_linear = min([b[1] for b in t_bounds if b[1] != np.inf], default=np.inf)

        # Binary search for CVaR constraint boundaries
        t_min_cvar = t_min_linear
        t_max_cvar = t_max_linear

        # Find lower bound (going negative)
        if t_min_linear > -np.inf:
            t_test = t_min_linear - 0.1
            step = 0.1
            while t_test >= t_min_linear - 10:  # Limit search range
                w_test = current_point + t_test * direction
                w_test = np.clip(w_test, 0, 1)
                if np.sum(w_test) > tol:
                    w_test = w_test / np.sum(w_test)
                    if self.calculate_cvar(w_test) < target_cvar:
                        t_min_cvar = t_test
                        t_test -= step
                    else:
                        break
                else:
                    break

        # Find upper bound (going positive)
        if t_max_linear < np.inf:
            t_test = t_max_linear + 0.1
            step = 0.1
            while t_test <= t_max_linear + 10:  # Limit search range
                w_test = current_point + t_test * direction
                w_test = np.clip(w_test, 0, 1)
                if np.sum(w_test) > tol:
                    w_test = w_test / np.sum(w_test)
                    if self.calculate_cvar(w_test) < target_cvar:
                        t_max_cvar = t_test
                        t_test += step
                    else:
                        break
                else:
                    break

        # Refine boundaries with binary search
        def refine_boundary(t_low, t_high, is_lower=True):
            for _ in range(20):  # Max iterations
                t_mid = (t_low + t_high) / 2
                w_test = current_point + t_mid * direction
                w_test = np.clip(w_test, 0, 1)
                if np.sum(w_test) > tol:
                    w_test = w_test / np.sum(w_test)
                    cvar_val = self.calculate_cvar(w_test)
                    if cvar_val < target_cvar:
                        if is_lower:
                            t_high = t_mid
                        else:
                            t_low = t_mid
                    else:
                        if is_lower:
                            t_low = t_mid
                        else:
                            t_high = t_mid
                else:
                    if is_lower:
                        t_low = t_mid
                    else:
                        t_high = t_mid
            return t_high if is_lower else t_low

        if t_min_cvar > t_min_linear:
            t_min_cvar = refine_boundary(t_min_linear, t_min_cvar, is_lower=True)
        if t_max_cvar < t_max_linear:
            t_max_cvar = refine_boundary(t_max_cvar, t_max_linear, is_lower=False)

        return max(t_min_cvar, t_min_linear), min(t_max_cvar, t_max_linear)

    def generate_portfolios(
        self,
        target_cvar,
        n_samples=1000,
        burn_in=100,
        initial_point=None,
    ):
        """
        Generate random portfolios using Hit-and-Run algorithm.

        Parameters:
        -----------
        target_cvar : float
            Maximum allowed CVaR
        n_samples : int, default=1000
            Number of portfolios to generate
        burn_in : int, default=100
            Number of burn-in iterations
        initial_point : array-like, optional
            Starting portfolio (must be feasible). If None, will find one.

        Returns:
        --------
        samples : array, shape (n_samples, n_assets)
            Generated portfolio weights
        """
        n_assets = self.n_assets

        # Find or use initial feasible point
        if initial_point is None:
            current_point = self._find_initial_feasible_point(target_cvar)
        else:
            current_point = np.asarray(initial_point)
            if not np.allclose(np.sum(current_point), 1.0):
                raise ValueError("Initial point must sum to 1")
            if np.any(current_point < 0):
                raise ValueError("Initial point must have non-negative weights")
            if self.calculate_cvar(current_point) >= target_cvar:
                raise ValueError("Initial point must satisfy CVaR < target_cvar")

        samples = []
        n_total = burn_in + n_samples

        for i in range(n_total):
            # Generate random direction on unit sphere
            direction = np.random.randn(n_assets)
            direction = direction / np.linalg.norm(direction)

            # Project onto hyperplane sum(w) = 0
            direction = self._project_direction_onto_simplex(direction)
            if np.linalg.norm(direction) < 1e-10:
                continue  # Skip if direction is too small
            direction = direction / np.linalg.norm(direction)

            # Find feasible line segment
            t_min, t_max = self._find_feasible_line_segment(
                current_point, direction, target_cvar
            )

            if t_max <= t_min:
                continue  # No feasible segment

            # Sample uniformly along the line segment
            t = np.random.uniform(t_min, t_max)
            new_point = current_point + t * direction
            new_point = np.clip(new_point, 0, 1)
            new_point = new_point / np.sum(new_point)  # Renormalize

            # Verify feasibility (should always be true, but check for numerical issues)
            if (
                np.all(new_point >= 0)
                and np.allclose(np.sum(new_point), 1.0)
                and self.calculate_cvar(new_point) < target_cvar
            ):
                current_point = new_point

            # Collect sample after burn-in
            if i >= burn_in:
                samples.append(current_point.copy())

        return np.array(samples)

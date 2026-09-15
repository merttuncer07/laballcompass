"""LabCompass product prototypes v0.

Two minimal, executable transfer products:
1) ClosureFinderV0: searches observable lifts that make target dynamics more closed.
2) CycleFlowAnalyzerV0: separates cut/potential flow from divergence-free cycle flow.

Research prototype, not production hardened.
"""
import numpy as np

class ClosureFinderV0:
    def __init__(self, min_relative_gain=0.02, max_features=6, ridge=1e-10, seed=20260825):
        self.min_relative_gain=min_relative_gain
        self.max_features=max_features
        self.ridge=ridge
        self.seed=seed

    @staticmethod
    def _fit_affine(Z, Zn, ridge):
        A=np.c_[np.ones(len(Z)),Z]
        G=A.T@A + ridge*np.eye(A.shape[1])
        G[0,0]-=ridge
        return np.linalg.solve(G,A.T@Zn)

    @staticmethod
    def _rmse(a,b): return float(np.sqrt(np.mean((a-b)**2)))

    def fit(self, X, X_next, target_fn, candidate_observables):
        X=np.asarray(X,float); X_next=np.asarray(X_next,float)
        n=len(X); rng=np.random.default_rng(self.seed)
        idx=rng.permutation(n); cut=int(.75*n); tr,va=idx[:cut],idx[cut:]
        self.target_fn=target_fn; self.candidate_observables=candidate_observables
        selected=[]

        def build(Xv,names):
            cols=[np.asarray(target_fn(Xv),float).reshape(-1)]
            cols += [np.asarray(candidate_observables[k](Xv),float).reshape(-1) for k in names]
            return np.column_stack(cols)

        def score(names):
            Z=build(X,names); Zn=build(X_next,names)
            B=self._fit_affine(Z[tr],Zn[tr],self.ridge)
            pred=np.c_[np.ones(len(va)),Z[va]]@B
            return self._rmse(pred[:,0],Zn[va,0]), B

        current,_=score(selected)
        history=[('BASE',current,0.0)]
        remaining=list(candidate_observables)
        while remaining and len(selected)<self.max_features:
            trials=[]
            for k in remaining:
                rm,_=score(selected+[k]); trials.append((rm,k))
            rm,k=min(trials)
            gain=(current-rm)/max(current,1e-15)
            if gain < self.min_relative_gain: break
            selected.append(k); remaining.remove(k); current=rm
            history.append((k,current,gain))
        self.selected_=selected
        self.selection_history_=history
        Z=build(X,selected); Zn=build(X_next,selected)
        self.B_=self._fit_affine(Z,Zn,self.ridge)
        self.validation_target_rmse_=current
        return self

    def lift(self,X):
        cols=[np.asarray(self.target_fn(X),float).reshape(-1)]
        cols += [np.asarray(self.candidate_observables[k](X),float).reshape(-1) for k in self.selected_]
        return np.column_stack(cols)

    def predict_horizon(self,X0,horizon):
        Z=self.lift(np.asarray(X0,float))
        for _ in range(horizon):
            Z=np.c_[np.ones(len(Z)),Z]@self.B_
        return Z[:,0]

class CycleFlowAnalyzerV0:
    def __init__(self,n_nodes,edges,tol=1e-10):
        self.n_nodes=n_nodes; self.edges=list(edges)
        m=len(self.edges)
        B=np.zeros((n_nodes,m))
        for k,(u,v) in enumerate(self.edges): B[u,k]-=1; B[v,k]+=1
        self.B=B
        _,s,Vt=np.linalg.svd(B,full_matrices=True)
        rank=int((s>tol).sum())
        N=Vt[rank:].T
        self.cycle_basis=N
        self.cycle_projector=N@N.T
        self.cut_projector=np.eye(m)-self.cycle_projector

    def decompose(self,flows):
        F=np.asarray(flows,float)
        cycle=F@self.cycle_projector.T
        cut=F@self.cut_projector.T
        return cut,cycle

    def cycle_score(self,flows):
        _,c=self.decompose(flows)
        return np.linalg.norm(c,axis=-1)

    def node_net_flow(self,flows):
        return np.asarray(flows,float)@self.B.T

if __name__=='__main__':
    rng=np.random.default_rng(7)
    # ClosureFinder demo: y'=.75y+.4x^2, x'=.92x.
    n=20000
    x=rng.uniform(-2,2,n); y=rng.normal(size=n)
    X=np.c_[x,y]; Xn=np.c_[.92*x,.75*y+.4*x*x]
    cf=ClosureFinderV0(min_relative_gain=.01).fit(
        X,Xn,target_fn=lambda z:z[:,1],
        candidate_observables={'x':lambda z:z[:,0], 'x2':lambda z:z[:,0]**2}
    )
    print('ClosureFinder selected:',cf.selected_,'validation RMSE',cf.validation_target_rmse_)

    # Cycle-flow demo.
    edges=[(0,1),(1,2),(2,0),(2,3)]
    ca=CycleFlowAnalyzerV0(4,edges)
    f=np.array([[1,1,1,0]],float)
    print('node net:',ca.node_net_flow(f)[0])
    print('cycle score:',ca.cycle_score(f)[0])

# ---- Added by V5 continuation: IM-058 x IM-069 ----
class SharedCapacityAllocatorV0:
    """Linear-value optimizer over a polymatroid given a monotone rank oracle f(S).

    For nonnegative item values, Edmonds' greedy construction returns an exact
    optimizer: sort by value, then allocate each item's marginal rank increment.
    This is useful when capacity belongs to subsets/pools rather than independent items.
    """
    def __init__(self, rank_oracle):
        self.rank_oracle=rank_oracle

    def allocate(self, values):
        values=np.asarray(values,float)
        order=np.argsort(-values)
        chosen=[]; prev=0.0; x=np.zeros(len(values))
        for i in order:
            chosen.append(int(i))
            cur=float(self.rank_oracle(chosen))
            if cur + 1e-12 < prev:
                raise ValueError('rank oracle must be monotone')
            x[i]=cur-prev; prev=cur
        return x

class TruncatedPoolRankV0:
    """Example monotone-submodular rank oracle: sum_r min(C_r, sum_{i in S} a_{ri})."""
    def __init__(self, contributions, pool_capacities):
        self.A=np.asarray(contributions,float)
        self.C=np.asarray(pool_capacities,float)
        if self.A.ndim!=2 or self.A.shape[0]!=len(self.C):
            raise ValueError('contributions must be pools x items')
    def __call__(self, subset):
        if len(subset)==0: return 0.0
        return float(np.minimum(self.C,self.A[:,list(subset)].sum(axis=1)).sum())

# ---- Added by V6 continuation: IM-074 x IM-435 ----
class DiscrepancyRandomizerV0:
    """Randomize inside a low-discrepancy set of balanced assignments.

    The objective is max absolute standardized mean difference across columns.
    This is designed for many-guardrail balance. It is not universally superior
    to L2/Mahalanobis balance, and causal analysis must use the actual design law.
    """
    def __init__(self, n_candidates=200, top_fraction=0.05, seed=20260825):
        self.n_candidates=int(n_candidates)
        self.top_fraction=float(top_fraction)
        self.rng=np.random.default_rng(seed)

    @staticmethod
    def _standardize(X):
        X=np.asarray(X,float)
        return (X-X.mean(axis=0))/(X.std(axis=0,ddof=1)+1e-12)

    @staticmethod
    def _balanced_signs(n,rng):
        if n % 2: raise ValueError('V0 requires an even number of units')
        s=-np.ones(n,dtype=int)
        s[rng.choice(n,n//2,replace=False)]=1
        return s

    @staticmethod
    def score(Xz, signs):
        n=len(signs)
        smd=(2.0/n)*(signs[:,None]*Xz).sum(axis=0)
        return float(np.max(np.abs(smd)))

    def assign(self, X):
        Xz=self._standardize(X); n=len(Xz)
        candidates=[]
        for _ in range(self.n_candidates):
            s=self._balanced_signs(n,self.rng)
            candidates.append((self.score(Xz,s),s))
        candidates.sort(key=lambda q:q[0])
        k=max(1,int(np.ceil(self.top_fraction*len(candidates))))
        score,s=candidates[self.rng.integers(k)]
        self.last_score_=score
        self.last_admissible_scores_=np.array([q[0] for q in candidates[:k]])
        return s.copy()

class DeepTailScannerV0:
    """Multiscale joint-tail diagnostic for hidden dependence.

    It estimates how the observed joint-exceedance rate deviates from the
    product-of-marginals benchmark as the tail threshold deepens. This is a
    diagnostic/forecasting component, not a proof of regular variation.
    """
    def __init__(self, tail_probs=(0.05, 0.03, 0.02, 0.01)):
        import numpy as np
        self.np = np
        self.tail_probs = np.asarray(tail_probs, dtype=float)
        if np.any((self.tail_probs <= 0) | (self.tail_probs >= 0.5)):
            raise ValueError("tail probabilities must be in (0, 0.5)")

    def _ratio(self, x, y, p):
        np = self.np
        x=np.asarray(x,float); y=np.asarray(y,float)
        if len(x)!=len(y): raise ValueError("x and y must have equal length")
        tx=np.quantile(x,1-p); ty=np.quantile(y,1-p)
        j=np.mean((x>tx)&(y>ty))
        n=len(x)
        # Half-count stabilization for sparse deep tails.
        return float((j+0.5/n)/(p*p+0.5/n))

    def fit(self, x, y):
        np = self.np
        self.ratios_=np.array([self._ratio(x,y,p) for p in self.tail_probs])
        z=np.log(1.0/self.tail_probs)
        self.slope_, self.intercept_=np.polyfit(z,np.log(self.ratios_),1)
        self.log_pearson_corr_=float(np.corrcoef(np.log(np.asarray(x,float)),np.log(np.asarray(y,float)))[0,1])
        return self

    def predict_excess_ratio(self, tail_probability):
        np=self.np
        p=float(tail_probability)
        if not (0<p<0.5): raise ValueError("tail_probability must be in (0,0.5)")
        return float(np.exp(self.intercept_ + self.slope_*np.log(1.0/p)))

    def report(self, target_tail_probability=0.005):
        return {
            'tail_probs': self.tail_probs.tolist(),
            'observed_excess_ratios': self.ratios_.tolist(),
            'deepening_slope': float(self.slope_),
            'log_pearson_corr': float(self.log_pearson_corr_),
            'predicted_target_excess_ratio': self.predict_excess_ratio(target_tail_probability),
            'target_tail_probability': float(target_tail_probability),
        }


class ObservationTimingSensorV0:
    """Bayesian event-time evidence layer for two latent states with exponential interarrival models."""
    def __init__(self, prior_state1=0.3, rate0=1.0, rate1=1.0):
        import math
        self.prior_state1=float(prior_state1); self.rate0=float(rate0); self.rate1=float(rate1)
        self._logit_prior=math.log(self.prior_state1/(1-self.prior_state1))
    def timing_log_likelihood_ratio(self, dt):
        import math
        if self.rate0<=0 or self.rate1<=0: raise ValueError("rates must be positive")
        return math.log(self.rate1/self.rate0) - (self.rate1-self.rate0)*float(dt)
    def posterior_from_log_mark_lr(self, dt, log_mark_lr=0.0, gate=True, min_rate_ratio=1.05):
        import math
        use_timing=(max(self.rate0,self.rate1)/min(self.rate0,self.rate1) >= min_rate_ratio) if gate else True
        ll=self._logit_prior+float(log_mark_lr)+(self.timing_log_likelihood_ratio(dt) if use_timing else 0.0)
        return 1.0/(1.0+math.exp(-ll))


# ---- Added by V10 continuation: IM-204 x IM-127 ----
class DecisionFluctuationGuardV0:
    """Decision-risk guard based on aggregate fluctuation scale relative to action gap.

    Under a Gaussian aggregate-error shell, P(flip)=Phi(-gap/aggregate_sd).
    For non-Gaussian/dependent systems, pass an empirically/certifiably estimated aggregate_sd
    or replace the Gaussian probability with a validated quantile model. Do not infer aggregate_sd
    from raw N when common-mode dependence is present.
    """
    def __init__(self, alpha=0.05):
        from statistics import NormalDist
        self.alpha=float(alpha)
        if not (0.0 < self.alpha < 0.5):
            raise ValueError('alpha must lie in (0, 0.5)')
        self._nd=NormalDist()
        self._z=float(self._nd.inv_cdf(1.0-self.alpha))

    def evaluate(self, gap, aggregate_sd):
        gap=float(gap); aggregate_sd=float(aggregate_sd)
        if gap <= 0: raise ValueError('gap must be positive')
        if aggregate_sd < 0: raise ValueError('aggregate_sd must be nonnegative')
        if aggregate_sd == 0:
            return {'flip_probability_gaussian':0.0,'fluctuation_gap_ratio':0.0,
                    'alpha':self.alpha,'safe_at_alpha':True,'required_gap':0.0}
        ratio=aggregate_sd/gap
        p=float(self._nd.cdf(-gap/aggregate_sd))
        required=self._z*aggregate_sd
        return {'flip_probability_gaussian':p,'fluctuation_gap_ratio':ratio,
                'alpha':self.alpha,'safe_at_alpha':bool(gap>=required),
                'required_gap':float(required)}

# ---- LCB-7F3A91 continuation: IM-223 x IM-227 ----
class ConstraintPressureMonitorV0:
    """Feature kernel for hard-cap systems whose reported state saturates.

    Feed the *minimum correction* needed to enforce the cap at each step.
    The monitor returns current regulator pressure plus local-time-like recent
    accumulation. It is a telemetry/state-augmentation primitive, not by itself
    a probabilistic risk model.
    """
    def __init__(self, window=8):
        from collections import deque
        if int(window) < 1:
            raise ValueError('window must be >= 1')
        self.window=int(window)
        self._corr=deque(maxlen=self.window)

    @staticmethod
    def upper_cap_correction(unconstrained_value, cap):
        """Minimum nonnegative correction needed to enforce x <= cap."""
        return max(0.0, float(unconstrained_value)-float(cap))

    def update(self, correction):
        c=max(0.0,float(correction))
        self._corr.append(c)
        vals=list(self._corr)
        return {
            'regulator_now': c,
            'pressure_window': float(sum(vals)),
            'boundary_hits': int(sum(v>0.0 for v in vals)),
            'window_fill': len(vals),
        }

    def reset(self):
        self._corr.clear()

# ---- LCB-7F3A91 continuation: IM-280 -> IM-453 ----
class CoverageFeedbackControllerV0:
    """Online interval-width controller for a target miss rate.

    Update law: q <- max(min_width, q + eta * (miss - alpha)).
    It is intentionally simple: callers must separately validate the exchangeability/
    drift shell and the meaning of the residual score being covered.
    """
    def __init__(self, initial_halfwidth, alpha=0.10, eta=0.08, min_width=1e-9):
        self.q=float(initial_halfwidth)
        self.alpha=float(alpha)
        self.eta=float(eta)
        self.min_width=float(min_width)
        if self.q <= 0: raise ValueError('initial_halfwidth must be positive')
        if not 0 < self.alpha < 1: raise ValueError('alpha must be in (0,1)')
        if self.eta <= 0: raise ValueError('eta must be positive')

    def interval(self, center):
        c=float(center)
        return (c-self.q, c+self.q)

    def update_from_residual(self, absolute_residual):
        r=abs(float(absolute_residual))
        miss=1.0 if r > self.q else 0.0
        old=self.q
        self.q=max(self.min_width, self.q + self.eta*(miss-self.alpha))
        return {'old_halfwidth':old,'miss':bool(miss),'new_halfwidth':self.q,'target_coverage':1-self.alpha}

# ---- LCB-7F3A91 continuation: IM-292 -> IM-050 ----
class MemoryKernelClosureV0:
    """Linear finite-memory closure diagnostic for a scalar observed process.

    Fits AR(p) candidates and only promotes memory beyond AR(1) when held-out
    one-step RMSE improves by a minimum relative amount. This is a small
    operational kernel, not a general Mori-Zwanzig solver.
    """
    def __init__(self, max_lag=8, min_relative_gain=0.02, train_fraction=0.7, simplicity_tolerance=0.002):
        self.max_lag=int(max_lag)
        self.min_relative_gain=float(min_relative_gain)
        self.train_fraction=float(train_fraction)
        self.simplicity_tolerance=float(simplicity_tolerance)
        if self.max_lag < 1: raise ValueError('max_lag must be >=1')
        if not 0.2 < self.train_fraction < 0.95: raise ValueError('train_fraction must be in (0.2,0.95)')

    @staticmethod
    def _design(x,p,start,stop):
        import numpy as np
        y=x[start:stop]
        X=np.column_stack([np.ones(len(y))]+[x[start-k-1:stop-k-1] for k in range(p)])
        return X,y

    @staticmethod
    def _fit(X,y):
        import numpy as np
        return np.linalg.lstsq(X,y,rcond=None)[0]

    @staticmethod
    def _acf1(r):
        import numpy as np
        if len(r)<3: return float('nan')
        return float(np.corrcoef(r[:-1],r[1:])[0,1])

    def fit(self, series):
        import numpy as np
        x=np.asarray(series,float).reshape(-1)
        if len(x) < max(100, 20*self.max_lag):
            raise ValueError('series too short for requested max_lag')
        split=int(len(x)*self.train_fraction)
        records=[]
        for p in range(1,self.max_lag+1):
            Xtr,ytr=self._design(x,p,p,split)
            beta=self._fit(Xtr,ytr)
            Xv,yv=self._design(x,p,split,len(x))
            pred=Xv@beta
            rmse=float(np.sqrt(np.mean((yv-pred)**2)))
            resid=ytr-Xtr@beta
            records.append((p,rmse,beta,self._acf1(resid)))
        base=records[0]
        raw_best=min(records,key=lambda z:z[1])
        cutoff=raw_best[1]*(1.0+self.simplicity_tolerance)
        best=min((r for r in records if r[1] <= cutoff), key=lambda z:z[0])
        gain=(base[1]-best[1])/max(base[1],1e-15)
        if best[0] == 1 or gain < self.min_relative_gain:
            chosen=base; promoted=False
        else:
            chosen=best; promoted=True
        self.selected_lag_=chosen[0]
        self.validation_rmse_=chosen[1]
        self.baseline_rmse_=base[1]
        self.relative_gain_=float((base[1]-chosen[1])/max(base[1],1e-15))
        self.promoted_memory_=promoted
        self.baseline_residual_acf1_=base[3]
        p=self.selected_lag_
        Xall,yall=self._design(x,p,p,len(x))
        self.coef_=self._fit(Xall,yall)
        self.selection_table_=[{'lag':r[0],'validation_rmse':r[1],'residual_acf1':r[3]} for r in records]
        return self

    def forecast(self, history, horizon=1):
        vals=[float(v) for v in history]
        p=self.selected_lag_
        if len(vals)<p: raise ValueError('history shorter than selected lag')
        for _ in range(int(horizon)):
            lags=[vals[-k-1] for k in range(p)]
            nxt=float(self.coef_[0] + sum(self.coef_[k+1]*lags[k] for k in range(p)))
            vals.append(nxt)
        return vals[-1]

# ---- LCB-7F3A91 continuation: IM-190 -> IM-040 ----
class PolicyAwareTimingSensorV0:
    """Policy-conditioned event-time likelihood layer for binary hidden state.

    Learns exponential event rates separately by hidden state and observed
    measurement-policy regime. Use when policy can alter event/visit intensity.
    """
    def __init__(self):
        self.fitted_=False

    def fit(self, state, policy, interarrival):
        import numpy as np
        y=np.asarray(state,int).reshape(-1)
        p=np.asarray(policy,int).reshape(-1)
        dt=np.asarray(interarrival,float).reshape(-1)
        if not (len(y)==len(p)==len(dt)): raise ValueError('inputs must have equal length')
        if np.any(dt<=0): raise ValueError('interarrival times must be positive')
        self.prior_state1_=float(y.mean())
        self.rates_={}
        for s in (0,1):
            for pol in np.unique(p):
                m=(y==s)&(p==pol)
                if m.sum()<10: raise ValueError('need at least 10 observations per state-policy cell')
                self.rates_[(s,int(pol))]=float(1.0/dt[m].mean())
        self.policies_=sorted(int(v) for v in np.unique(p))
        self.fitted_=True
        return self

    def timing_log_likelihood_ratio(self, interarrival, policy):
        import numpy as np
        if not self.fitted_: raise RuntimeError('fit first')
        dt=np.asarray(interarrival,float)
        pol=np.asarray(policy,int)
        out=np.empty(np.broadcast(dt,pol).shape,float)
        dtb,polb=np.broadcast_arrays(dt,pol)
        for pv in self.policies_:
            m=(polb==pv)
            if np.any(m):
                r0=self.rates_[(0,pv)]; r1=self.rates_[(1,pv)]
                out[m]=np.log(r1/r0)-(r1-r0)*dtb[m]
        return out

    def posterior(self, interarrival, policy, log_mark_lr=0.0):
        import numpy as np
        if not self.fitted_: raise RuntimeError('fit first')
        lp=np.log(self.prior_state1_/(1.0-self.prior_state1_))
        z=lp+self.timing_log_likelihood_ratio(interarrival,policy)+np.asarray(log_mark_lr,float)
        z=np.clip(z,-40,40)
        return 1.0/(1.0+np.exp(-z))


# ---- LCB-7F3A91 continuation: RX-076 ----
class RepairDebtMonitorV0:
    """State augmentation for imperfect-repair systems.

    Tracks observable repair count and cumulative repair severity instead of
    assuming a visible functional reset implies an as-good-as-new hidden state.
    """
    def __init__(self):
        self.reset()
    def reset(self):
        self.repair_count=0
        self.cumulative_repair_burden=0.0
        self.operating_age=0.0
    def advance(self, operating_increment=1.0):
        self.operating_age += max(0.0,float(operating_increment))
    def record_repair(self, severity=1.0):
        s=max(0.0,float(severity))
        self.repair_count += 1
        self.cumulative_repair_burden += s
    def features(self, visible_health):
        return {'visible_health':float(visible_health),'operating_age':self.operating_age,
                'repair_count':self.repair_count,'cumulative_repair_burden':self.cumulative_repair_burden}

# ---- LCB-7F3A91 continuation: RX-088 ----
class PersistenceAwareTransientRiskV0:
    """Receiver-frame persistence correction for advecting Gaussian disturbances."""
    @staticmethod
    def absolute_growth_rate(growth_rate, advection_speed, diffusivity):
        mu=float(growth_rate); v=float(advection_speed); D=float(diffusivity)
        if D <= 0: raise ValueError('diffusivity must be positive')
        return mu - v*v/(4.0*D)
    def classify(self, growth_rate, advection_speed, diffusivity):
        g=self.absolute_growth_rate(growth_rate,advection_speed,diffusivity)
        return {'global_growth_rate':float(growth_rate),'fixed_location_asymptotic_growth':g,
                'persistent_local_growth':bool(g>0),'convective_only':bool(float(growth_rate)>0 and g<=0)}

# ---- LCB-7F3A91 continuation: RX-091 ----
class VarianceAwareCapacityPlannerV0:
    """Minimum M/G/1 service-speed factor for a target mean queue wait.

    Assumes Poisson arrivals and iid service times. The caller supplies the
    service-time mean and variance for the unscaled workload.
    """
    @staticmethod
    def required_capacity(arrival_rate, mean_service, variance_service, target_mean_wait):
        import math
        lam=float(arrival_rate); m=float(mean_service); var=float(variance_service); w=float(target_mean_wait)
        if lam<0 or m<=0 or var<0 or w<=0: raise ValueError('invalid queue parameters')
        m2=var+m*m
        return (lam*m + math.sqrt((lam*m)**2 + 2.0*lam*m2/w))/2.0
    @staticmethod
    def predicted_mean_wait(arrival_rate, mean_service, variance_service, capacity):
        lam=float(arrival_rate); m=float(mean_service); var=float(variance_service); c=float(capacity)
        rho=lam*m/c
        if c<=0 or rho>=1: return float('inf')
        m2=var+m*m
        return lam*(m2/c**2)/(2.0*(1.0-rho))


# ---- LCB-7F3A91 continuation: RX-145 ----
class BoundaryAccessibilityRankerV0:
    """Rank boundary locations by modeled first-hit/accessibility probability.

    V0 accepts already-computed nonnegative accessibility weights. It deliberately
    does not infer the diffusion/PDE model: model calibration is a hard external gate.
    """
    def __init__(self, min_effective_entropy_fraction=0.0):
        self.min_effective_entropy_fraction=float(min_effective_entropy_fraction)

    @staticmethod
    def _normalize(weights):
        import numpy as np
        w=np.asarray(weights,float).reshape(-1)
        if len(w)==0 or np.any(~np.isfinite(w)) or np.any(w<0) or w.sum()<=0:
            raise ValueError('weights must be finite, nonnegative, and have positive sum')
        return w/w.sum()

    def rank(self, accessibility_weights):
        import numpy as np
        w=self._normalize(accessibility_weights)
        return np.argsort(-w)

    def select_fraction(self, accessibility_weights, budget_fraction):
        import numpy as np
        w=self._normalize(accessibility_weights)
        q=float(budget_fraction)
        if not 0<q<=1: raise ValueError('budget_fraction must be in (0,1]')
        k=max(1,int(round(q*len(w))))
        idx=np.argpartition(w,-k)[-k:]
        return idx[np.argsort(-w[idx])]

    def report(self, accessibility_weights, budget_fraction):
        import numpy as np
        w=self._normalize(accessibility_weights)
        idx=self.select_fraction(w,budget_fraction)
        entropy=-float(np.sum(np.where(w>0,w*np.log(w),0.0)))
        max_entropy=float(np.log(len(w))) if len(w)>1 else 0.0
        return {'selected_indices':idx.tolist(),
                'modeled_capture_probability':float(w[idx].sum()),
                'uniform_length_baseline':float(budget_fraction),
                'modeled_gain_ratio':float(w[idx].sum()/float(budget_fraction)),
                'entropy_fraction':float(entropy/max_entropy) if max_entropy>0 else 1.0,
                'calibration_required':True}


# ---- LCB-7F3A91 continuation: RX-143 ----
class SupportFunctionActiveSensingV0:
    """Choose a directional support query for a binary downstream target.

    Inputs are posterior parameter samples, candidate linear support-feature
    vectors, and a boolean target label for each posterior sample. The V0 score
    is a normalized between-target-class separation criterion. Convexity,
    target-sector correctness, and the feature model are external hard gates.
    """
    def __init__(self, noise_sd):
        self.noise_sd=float(noise_sd)
        if self.noise_sd <= 0: raise ValueError('noise_sd must be positive')

    def score_candidates(self, posterior_samples, candidate_features, target_labels):
        import numpy as np
        B=np.asarray(posterior_samples,float)
        F=np.asarray(candidate_features,float)
        z=np.asarray(target_labels,bool).reshape(-1)
        if B.ndim!=2 or F.ndim!=2 or B.shape[1]!=F.shape[1] or len(z)!=len(B):
            raise ValueError('incompatible sample/feature/label shapes')
        p=float(z.mean())
        if p<=0.0 or p>=1.0:
            return np.einsum('ij,ij->i',F,F)*0.0
        Q=B@F.T
        m1=Q[z].mean(axis=0); m0=Q[~z].mean(axis=0)
        vt=Q.var(axis=0)+self.noise_sd**2
        return p*(1.0-p)*(m1-m0)**2/vt

    def choose(self, posterior_samples, candidate_features, target_labels):
        import numpy as np
        s=self.score_candidates(posterior_samples,candidate_features,target_labels)
        return int(np.argmax(s))

    @staticmethod
    def calibration_gate(target_model_valid, convexity_model_valid=True):
        return bool(target_model_valid and convexity_model_valid)


# ---- LCB-7F3A91 continuation: RX-062 ----
class ModularRiskFirewallV0:
    """Small-gain-style cap for a proposed inter-module feedback weight.

    This is a gate, not a gain estimator. The supplied downstream_gain_ucb must
    already be a calibrated upper confidence/robustness bound. If that contract
    is understated, the safety interpretation is invalid.
    """
    def __init__(self, loop_margin=0.90):
        self.loop_margin=float(loop_margin)
        if not 0 < self.loop_margin < 1: raise ValueError('loop_margin must be in (0,1)')

    def max_feedback_weight(self, upstream_gain, downstream_gain_ucb):
        a=abs(float(upstream_gain)); b=abs(float(downstream_gain_ucb))
        if a==0 or b==0: return 1.0
        return min(1.0,self.loop_margin/(a*b))

    def gate(self, proposed_feedback_weight, upstream_gain, downstream_gain_ucb):
        lam=float(proposed_feedback_weight)
        if not 0 <= lam <= 1: raise ValueError('feedback weight must be in [0,1]')
        cap=self.max_feedback_weight(upstream_gain,downstream_gain_ucb)
        return {'requested_weight':lam,'admissible_weight':min(lam,cap),
                'max_weight_from_gain_contract':cap,
                'contract_calibration_required':True}


# ---- LCB-7F3A91 continuation: merged IM-414/IM-337 + RX-113 ----
class EffectiveDiversityGuardV0:
    """Convert nominal multiplicity into effective independent count.

    RX-113 adds the important shell where pairwise correlation may vanish with N
    while (N-1)*rho remains decision-relevant. This is a merged core, not a new theory.
    """
    @staticmethod
    def report(n, pairwise_rho):
        n=int(n); rho=float(pairwise_rho)
        if n < 1: raise ValueError('n must be >=1')
        if n>1 and not (-1.0/(n-1) <= rho < 1.0):
            raise ValueError('rho outside equicorrelation PSD range')
        vif=1.0+(n-1)*rho
        if vif <= 0: raise ValueError('nonpositive aggregate variance factor')
        return {'nominal_count':n,'pairwise_rho':rho,'aggregate_variance_inflation':vif,
                'effective_independent_count':n/vif,'aggregate_se_inflation':vif**0.5,
                'pairwise_small_does_not_imply_collective_small':True}

    @staticmethod
    def gate(n, pairwise_rho, pairwise_threshold=0.01, max_variance_inflation=2.0):
        r=EffectiveDiversityGuardV0.report(n,pairwise_rho)
        r['pairwise_threshold_says_small']=abs(float(pairwise_rho)) < float(pairwise_threshold)
        r['collective_risk_flag']=r['aggregate_variance_inflation'] > float(max_variance_inflation)
        return r


# ---- LCB-7F3A91 continuation: RX-024 ----
class BackreactionAwareSensorV0:
    """Bayes update followed by an action-dependent sensing backreaction transition."""
    def __init__(self, sensitivity=0.85, false_positive=0.05, backreaction_prob=0.0):
        self.s=float(sensitivity); self.f=float(false_positive); self.q=float(backreaction_prob)
        if not (0<=self.f<self.s<=1 and 0<=self.q<=1): raise ValueError('invalid probabilities')
    def update(self, prior_p_state1, action, observed_positive):
        p=float(prior_p_state1); a=int(action); y=bool(observed_positive)
        if not 0<=p<=1 or a not in (0,1): raise ValueError('invalid state/action')
        l1=(self.s if a==1 else self.f) if y else (1-self.s if a==1 else 1-self.f)
        l0=(self.s if a==0 else self.f) if y else (1-self.s if a==0 else 1-self.f)
        den=p*l1+(1-p)*l0; post=p*l1/den
        next_p = post + self.q*(1-post) if a==0 else (1-self.q)*post
        return {'posterior_before_backreaction':post,'predicted_next_p_state1':next_p,'calibrated_backreaction_required':self.q>0}
    @staticmethod
    def choose_location(p_state1): return 1 if float(p_state1)>=0.5 else 0


# ---- LCB-7F3A91 continuation: RX-098 ----
class LieTransientReachabilityGuardV0:
    """Compare direct-direction risk with risk after a supplied reachable/Lie closure.

    This class deliberately does not infer Lie brackets or system dynamics. The caller
    supplies validated direction matrices and finite-time propagators. The output is a
    target-consequence audit; reachability and propagator calibration are hard gates.
    """
    @staticmethod
    def _as_columns(directions):
        import numpy as np
        D=np.asarray(directions,float)
        if D.ndim==1: D=D[:,None]
        if D.ndim!=2 or D.shape[1]==0: raise ValueError('directions must contain >=1 column')
        n=np.linalg.norm(D,axis=0)
        if np.any(n<=0) or np.any(~np.isfinite(n)): raise ValueError('direction columns must be finite and nonzero')
        return D/n

    @staticmethod
    def direction_scores(directions, propagators, output_matrix=None):
        import numpy as np
        D=LieTransientReachabilityGuardV0._as_columns(directions)
        Ps=[np.asarray(P,float) for P in propagators]
        if not Ps: raise ValueError('need at least one finite-time propagator')
        C=np.eye(D.shape[0]) if output_matrix is None else np.asarray(output_matrix,float)
        scores=[]
        for j in range(D.shape[1]):
            d=D[:,j]
            vals=[float(np.linalg.norm(C@P@d)) for P in Ps]
            scores.append(max(vals))
        return np.asarray(scores,float)

    def compare(self, direct_directions, closure_directions, propagators, output_matrix=None,
                reachability_model_valid=False, propagator_calibrated=False):
        import numpy as np
        sd=self.direction_scores(direct_directions,propagators,output_matrix)
        sc=self.direction_scores(closure_directions,propagators,output_matrix)
        direct=float(np.max(sd)); closure=float(np.max(sc))
        return {'max_direct_transient_consequence':direct,
                'max_closure_transient_consequence':closure,
                'risk_expansion_ratio':float(closure/direct) if direct>0 else float('inf'),
                'reachability_model_valid':bool(reachability_model_valid),
                'propagator_calibrated':bool(propagator_calibrated),
                'certificate_valid':bool(reachability_model_valid and propagator_calibrated)}

# ---- LCB-7F3A91 continuation: RX-201 ----
class RareWeakLayerMismatchGateV0:
    """Empirical-null gate for rare/weak residual structure after a candidate two-layer fit.

    This class does NOT solve blind deconvolution. The caller must supply a held-out or
    cross-fitted standardized residual from an upstream structured layer solver, plus
    independent correct-layer calibration statistics. HC is only recommended when the
    declared mismatch shell is rare/weak; max and energy remain mandatory controls.
    """
    @staticmethod
    def _hc_stat(z):
        import numpy as np
        from scipy.stats import norm
        z=np.asarray(z,float).reshape(-1)
        if len(z)<20 or np.any(~np.isfinite(z)):
            raise ValueError('need at least 20 finite standardized residuals')
        p=np.sort(np.clip(2.0*norm.sf(np.abs(z)),1e-300,1.0))
        n=len(p); i=np.arange(1,n+1)
        mask=(p<=0.10)&(p>=1.0/n**3)&(i/n>p)
        if not np.any(mask): return 0.0
        pp=p[mask]; ii=i[mask]
        return float(np.max(np.sqrt(n)*(ii/n-pp)/np.sqrt(pp*(1.0-pp))))

    @classmethod
    def statistics(cls, standardized_residual):
        import numpy as np
        z=np.asarray(standardized_residual,float).reshape(-1)
        if len(z)<20 or np.any(~np.isfinite(z)):
            raise ValueError('need at least 20 finite standardized residuals')
        return {
            'energy':float(np.mean(z*z)),
            'max':float(np.max(np.abs(z))),
            'hc':cls._hc_stat(z),
        }

    @staticmethod
    def empirical_upper_p(calibration_statistics, observed_statistic):
        import numpy as np
        c=np.sort(np.asarray(calibration_statistics,float).reshape(-1))
        if len(c)<100 or np.any(~np.isfinite(c)):
            raise ValueError('need >=100 finite independent null calibration statistics')
        obs=float(observed_statistic)
        ge=len(c)-int(np.searchsorted(c,obs,side='left'))
        return float((1+ge)/(len(c)+1))

    @classmethod
    def evaluate(cls, standardized_residual, calibration, shell_hint,
                 alpha=0.05, residual_is_crossfit_or_heldout=False,
                 null_model_calibrated=False, symmetry_orbit_quotiented=False):
        if shell_hint not in {'rare_weak','strong_single','dense'}:
            raise ValueError("shell_hint must be 'rare_weak', 'strong_single', or 'dense'")
        if not (0 < float(alpha) < 1): raise ValueError('alpha must be in (0,1)')
        st=cls.statistics(standardized_residual)
        required={'energy','max','hc'}
        if set(calibration) != required:
            raise ValueError('calibration must contain energy, max, and hc null samples')
        p={k:cls.empirical_upper_p(calibration[k],st[k]) for k in required}
        preferred={'rare_weak':'hc','strong_single':'max','dense':'energy'}[shell_hint]
        gate_ok=bool(residual_is_crossfit_or_heldout and null_model_calibrated and symmetry_orbit_quotiented)
        return {
            'statistics':st,
            'empirical_p_values':p,
            'preferred_statistic_for_declared_shell':preferred,
            'preferred_rejects':bool(gate_ok and p[preferred] <= float(alpha)),
            'all_three_reject':{k:bool(gate_ok and p[k] <= float(alpha)) for k in required},
            'calibration_gate_passed':gate_ok,
            'symmetry_orbit_quotient_required':True,
            'does_not_identify_true_kernel':True,
        }


# ---- LCB-7F3A91 value-first continuation: RX-033 ----
class LiquidityLoadSharingStressV0:
    """Propagate unmet load from failed nodes through a calibrated network.

    `redistribution` is a scenario parameter, not an inferred truth. Set it to zero
    when exits do not materially transfer burden.
    """
    @staticmethod
    def run(buffers, initial_load, transition_weights, redistribution=0.0, max_rounds=100):
        import numpy as np
        b=np.asarray(buffers,float).reshape(-1)
        d=np.asarray(initial_load,float).reshape(-1).copy()
        W=np.asarray(transition_weights,float)
        if W.shape!=(len(b),len(b)): raise ValueError("transition_weights has wrong shape")
        rho=float(redistribution)
        if not 0<=rho<=1: raise ValueError("redistribution must be in [0,1]")
        failed=d>b
        first=failed.copy()
        newly=failed.copy()
        rounds=0
        transferred=np.zeros_like(d)
        while newly.any() and rounds<max_rounds and rho>0:
            rounds+=1
            excess=np.maximum(d-b,0.0)*newly
            add=rho*(excess@W)
            add[failed]=0.0
            transferred += add
            d += add
            newly=(d>b)&(~failed)
            failed |= newly
        return {
            "first_round_failed":first,
            "final_failed":failed,
            "incremental_failures":int(failed.sum()-first.sum()),
            "cascade_rounds":rounds,
            "transferred_load":transferred,
        }

# ---- LCB-7F3A91 value-first continuation: RX-037 ----
class PipelineRiskStateV0:
    """Maintain a calibrated cumulative burden state for history-dependent failure."""
    def __init__(self, load_exponent=3.0, scale=1.0):
        self.load_exponent=float(load_exponent)
        self.scale=float(scale)
        if self.scale<=0: raise ValueError("scale must be positive")
        self.reset()
    def reset(self, retained_fraction=0.0):
        retained=float(retained_fraction)
        if not 0<=retained<=1: raise ValueError("retained_fraction must be in [0,1]")
        old=getattr(self,"burden",0.0)
        self.burden=retained*old
        self.age=0.0
        return self
    def update(self, load, dt=1.0):
        l=max(0.0,float(load)); dt=max(0.0,float(dt))
        self.burden += (l**self.load_exponent)*dt/self.scale
        self.age += dt
        return self.burden
    def features(self, current_state=None):
        return {"current_state":current_state,"age":self.age,"cumulative_burden":self.burden}

# ---- LCB-7F3A91 value-first continuation: RX-013 ----
class LinkageUncertaintyPropagatorV0:
    """Propagate linkage probabilities into a downstream numeric quantity.

    This returns posterior means/variances; it does not assert that posterior-mean
    action is optimal under every loss. Preserve the MAP path for absolute/exact-match loss.
    """
    @staticmethod
    def mixture(values, probabilities):
        import numpy as np
        x=np.asarray(values,float)
        p=np.asarray(probabilities,float)
        if x.shape[0]!=len(p): raise ValueError("first axis must match probabilities")
        if np.any(p<0) or p.sum()<=0: raise ValueError("invalid probabilities")
        p=p/p.sum()
        mean=np.tensordot(p,x,axes=(0,0))
        var=np.tensordot(p,(x-mean)**2,axes=(0,0))
        return {"posterior_mean":mean,"posterior_variance":var,
                "map_value":x[int(np.argmax(p))],"map_probability":float(p.max())}

# ---- LCB-7F3A91 value-first continuation: RX-042 ----
class RarePathImportanceSamplerV0:
    """Gaussian endpoint rare-event importance sampler with a rarity gate.

    V0 is intentionally narrow. General systems need a calibrated change-of-measure
    or dominant-path solver plus exact likelihood correction.
    """
    def __init__(self, z_gate=2.0):
        self.z_gate=float(z_gate)
    def estimate_gaussian_sum_tail(self, T, threshold, n_samples, rng=None):
        import numpy as np
        T=int(T); n=int(n_samples); a=float(threshold)
        if T<=0 or n<=0: raise ValueError("T and n_samples must be positive")
        if rng is None: rng=np.random.default_rng()
        z=a/np.sqrt(T)
        if z<self.z_gate:
            S=rng.normal(0.0,np.sqrt(T),size=n)
            return {"estimate":float(np.mean(S>=a)),"used_tilt":False,"z":float(z)}
        mu=a/T
        S=rng.normal(T*mu,np.sqrt(T),size=n)
        logw=-mu*S+0.5*T*mu*mu
        c=(S>=a)*np.exp(logw)
        return {"estimate":float(c.mean()),"used_tilt":True,"z":float(z),
                "weight_cv":float(c.std()/max(c.mean(),1e-300))}


# ---- LCB-7F3A91 value-first salvage: RX-070 ----
class RelationalMotifBeamLocatorV0:
    """Find a high-scoring simple directed k-node motif with beam search.

    This is the empirically preferred RX-070 product surface in the tested sparse
    transaction-graph shell. Color-coding remains an optional fallback, not the default.
    """
    def __init__(self, beam_width=5000):
        self.beam_width=int(beam_width)
        if self.beam_width<=0: raise ValueError("beam_width must be positive")
    def best_path(self, adjacency, k):
        import heapq
        n=len(adjacency); k=int(k)
        paths=[(0.0,(s,)) for s in range(n)]
        for _ in range(1,k):
            cand=[]
            for score,path in paths:
                u=path[-1]; seen=set(path)
                for item in adjacency[u]:
                    v,w=int(item[0]),float(item[1])
                    if v not in seen:
                        cand.append((score+w,path+(v,)))
            if not cand: break
            paths=heapq.nlargest(self.beam_width,cand,key=lambda x:x[0])
        if not paths: return {"score":float("-inf"),"path":[]}
        return {"score":float(paths[0][0]),"path":list(paths[0][1])}

# ---- LCB-7F3A91 value-first: RX-025 ----
class ZeroCauseMetadataDiscriminatorV0:
    """Fit P(latent nonzero | observed zero, context, observation metadata)."""
    def __init__(self):
        self.model_=None
    def fit(self, context_features, policy, threshold, gap, latent_nonzero):
        import numpy as np
        from sklearn.pipeline import make_pipeline
        from sklearn.preprocessing import StandardScaler
        from sklearn.linear_model import LogisticRegression
        C=np.asarray(context_features,float)
        if C.ndim==1: C=C[:,None]
        p=np.asarray(policy,float).reshape(-1,1)
        th=np.asarray(threshold,float).reshape(-1,1)
        gp=np.asarray(gap,float).reshape(-1,1)
        y=np.asarray(latent_nonzero,int).reshape(-1)
        if np.any(th<=0) or np.any(gp<0): raise ValueError("threshold>0 and gap>=0 required")
        X=np.column_stack([C,p,np.log(th),np.log1p(gp)])
        self.model_=make_pipeline(StandardScaler(),LogisticRegression(max_iter=600))
        self.model_.fit(X,y)
        self.context_dim_=C.shape[1]
        return self
    def predict_proba(self, context_features, policy, threshold, gap):
        import numpy as np
        if self.model_ is None: raise RuntimeError("fit first")
        C=np.asarray(context_features,float)
        if C.ndim==1: C=C[:,None]
        X=np.column_stack([C,np.asarray(policy,float).reshape(-1,1),
                           np.log(np.asarray(threshold,float)).reshape(-1,1),
                           np.log1p(np.asarray(gap,float)).reshape(-1,1)])
        return self.model_.predict_proba(X)[:,1]

# ---- LCB-7F3A91 value-first: RX-047 ----
class ReliabilityTemperedEvidenceV0:
    """Continuously blend proxy and direct evidence using current MSE contracts."""
    @staticmethod
    def combine(proxy, direct, proxy_variance, direct_variance,
                proxy_bias_estimate=0.0, proxy_bias_uncertainty=0.0):
        import numpy as np
        p=np.asarray(proxy,float)-float(proxy_bias_estimate)
        d=np.asarray(direct,float)
        vp=float(proxy_variance)+float(proxy_bias_uncertainty)**2
        vd=float(direct_variance)
        if vp<=0 or vd<=0: raise ValueError("effective variances must be positive")
        wp=(1.0/vp)/((1.0/vp)+(1.0/vd))
        out=wp*p+(1.0-wp)*d
        return {"estimate":out,"proxy_weight":wp,"direct_weight":1.0-wp,
                "proxy_drift_gate_required":True}

# ---- LCB-7F3A91 value-first: RX-058 ----
class OptionValueCapacityReserverV0:
    """Empirically fit static and signal-contingent protection levels."""
    def __init__(self, capacity, low_value=1.0, high_value=4.0):
        self.capacity=int(capacity); self.low_value=float(low_value); self.high_value=float(high_value)
        if self.capacity<=0: raise ValueError("capacity must be positive")
    def _mean_revenue(self, low_demand, high_demand, reserve):
        import numpy as np
        L=np.asarray(low_demand,float); H=np.asarray(high_demand,float)
        a=np.minimum(L,self.capacity-int(reserve))
        rem=self.capacity-a
        s=np.minimum(H,rem)
        return float(np.mean(self.low_value*a+self.high_value*s))
    def _best_reserve(self,L,H):
        vals=[self._mean_revenue(L,H,r) for r in range(self.capacity+1)]
        import numpy as np
        return int(np.argmax(vals))
    def fit(self, low_demand, high_demand, signal=None):
        import numpy as np
        L=np.asarray(low_demand,float); H=np.asarray(high_demand,float)
        self.static_reserve_=self._best_reserve(L,H)
        self.signal_reserves_={}
        if signal is not None:
            S=np.asarray(signal)
            for s in np.unique(S):
                m=S==s
                self.signal_reserves_[s.item() if hasattr(s,"item") else s]=self._best_reserve(L[m],H[m])
        return self
    def reserve(self, signal=None, signal_valid=True):
        if not hasattr(self,"static_reserve_"): raise RuntimeError("fit first")
        if signal is None or not signal_valid or signal not in self.signal_reserves_:
            return self.static_reserve_
        return self.signal_reserves_[signal]

# ---- LCB-7F3A91 value-first: RX-029 ----
class ClusterCauseInvarianceFeaturesV0:
    """Extract pooled and cross-environment association features.

    Classification is only meaningful when environments change exposure/prevalence
    without rewriting the candidate mechanism itself.
    """
    @staticmethod
    def features(contingency_tables):
        import numpy as np
        T=np.asarray(contingency_tables,float)
        if T.ndim!=2 or T.shape[1]!=4:
            raise ValueError("expected rows of [n00,n01,n10,n11]")
        lors=[]; pAs=[]; pBs=[]
        for row in T:
            n00,n01,n10,n11=row+0.5
            total=n00+n01+n10+n11
            lors.append(np.log(n11*n00/(n01*n10)))
            pAs.append((n10+n11)/total); pBs.append((n01+n11)/total)
        P=T.sum(axis=0)+0.5
        n00,n01,n10,n11=P; total=P.sum()
        pooled_lor=float(np.log(n11*n00/(n01*n10)))
        L=np.asarray(lors); A=np.asarray(pAs); B=np.asarray(pBs)
        return {"pooled_log_odds_ratio":pooled_lor,
                "environment_log_or_sd":float(L.std()),
                "environment_log_or_range":float(np.ptp(L)),
                "association_vs_A_prevalence":float(np.corrcoef(A,L)[0,1]),
                "association_vs_B_prevalence":float(np.corrcoef(B,L)[0,1]),
                "environment_validity_required":True}

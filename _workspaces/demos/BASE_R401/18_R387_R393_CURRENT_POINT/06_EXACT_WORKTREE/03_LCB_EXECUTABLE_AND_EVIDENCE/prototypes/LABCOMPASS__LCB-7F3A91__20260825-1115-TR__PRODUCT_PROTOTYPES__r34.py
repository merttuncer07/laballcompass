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


# ---- LCB-7F3A91 value-first: RX-040 ----
class HiddenMassLinkageV0:
    """Propagate calibrated match probabilities into two-list hidden-mass estimates."""
    @staticmethod
    def estimate(n_list1, n_list2, match_probabilities, posterior_draws=2000, rng=None):
        import numpy as np
        p=np.asarray(match_probabilities,float)
        if np.any((p<0)|(p>1)): raise ValueError("match probabilities must be in [0,1]")
        if rng is None: rng=np.random.default_rng()
        M=np.zeros(int(posterior_draws),dtype=int)
        for pj in p:
            M += rng.random(len(M)) < pj
        M=np.maximum(M,1)
        K=float(n_list1)*float(n_list2)
        N=K/M
        return {
            "expected_overlap":float(p.sum()),
            "population_median":float(np.median(N)),
            "population_p10":float(np.quantile(N,.10)),
            "population_p90":float(np.quantile(N,.90)),
            "linkage_calibration_required":True,
        }

# ---- LCB-7F3A91 value-first: RX-072 ----
class DynamicNetworkTwinV0:
    """Iterate assignment rewiring and overload-induced topology changes."""
    def __init__(self, rewire_probability, overload_ratio):
        self.q=float(rewire_probability); self.tau=float(overload_ratio)
        if not 0<=self.q<=1: raise ValueError("rewire_probability must be in [0,1]")
        if self.tau<=0: raise ValueError("overload_ratio must be positive")
    def simulate(self, demand, capacity, preferences, initial_assignment, failed, rng=None, max_rounds=20):
        import numpy as np
        if rng is None: rng=np.random.default_rng()
        d=np.asarray(demand,float); cap=np.asarray(capacity,float)
        assign=np.asarray(initial_assignment,int).copy()
        fail=np.asarray(failed,bool).copy()
        assign[fail[assign]]=-1
        rounds=0
        for _ in range(int(max_rounds)):
            rounds+=1; changed=False
            load=np.zeros(len(cap))
            for i,s in enumerate(assign):
                if s>=0 and not fail[s]: load[s]+=d[i]
            un=np.where(assign<0)[0]; rng.shuffle(un)
            for i in un:
                if rng.random()>self.q: continue
                cand=[int(s) for s in preferences[i] if not fail[int(s)]]
                if not cand: continue
                s=min(cand,key=lambda j:load[j]/cap[j])
                assign[i]=s; load[s]+=d[i]; changed=True
            load=np.zeros(len(cap))
            for i,s in enumerate(assign):
                if s>=0 and not fail[s]: load[s]+=d[i]
            nf=(load>self.tau*cap)&(~fail)
            if nf.any():
                fail|=nf
                assign[np.isin(assign,np.where(fail)[0])]=-1
                changed=True
            if not changed: break
        load=np.zeros(len(cap))
        for i,s in enumerate(assign):
            if s>=0 and not fail[s]: load[s]+=d[i]
        served=sum(min(load[j],cap[j]) for j in range(len(cap)) if not fail[j])
        return {"lost_demand":float(d.sum()-served),"failed_nodes":int(fail.sum()),
                "rounds":rounds,"transition_calibration_required":True}

# ---- LCB-7F3A91 value-first: RX-050 ----
class CausalEdgeValidatorFeaturesV0:
    """Produce control/mediator diagnostics; does not certify causality by itself."""
    @staticmethod
    def summarize(A,B,mediator,negative_exposure,negative_outcome):
        import numpy as np
        A=np.asarray(A,float); B=np.asarray(B,float); M=np.asarray(mediator,float)
        N=np.asarray(negative_exposure,float); O=np.asarray(negative_outcome,float)
        def c(x,y): return float(np.corrcoef(x,y)[0,1])
        X=np.column_stack([np.ones(len(A)),A,M,N,O])
        beta=np.linalg.lstsq(X,B,rcond=None)[0]
        return {
            "corr_A_B":c(A,B),
            "corr_negative_exposure_B":c(N,B),
            "corr_A_negative_outcome":c(A,O),
            "adjusted_A_coefficient":float(beta[1]),
            "mediator_coefficient":float(beta[2]),
            "control_validity_must_be_audited":True,
        }

# ---- LCB-7F3A91 value-first: RH-009 ----
class ConsequenceCoverageAllocatorV0:
    """Guarantee critical-region coverage, then allocate depth by marginal consequence."""
    def __init__(self, miss_probability_per_sample=0.55):
        self.q=float(miss_probability_per_sample)
        if not 0<self.q<1: raise ValueError("miss probability must lie in (0,1)")
    def allocate(self, consequence_weights, budget, critical_indices):
        import numpy as np
        w=np.asarray(consequence_weights,float)
        crit=np.asarray(critical_indices,int)
        B=int(budget)
        if B<len(crit): raise ValueError("budget cannot satisfy critical-region coverage")
        n=np.zeros(len(w),dtype=int)
        n[crit]=1
        for _ in range(B-len(crit)):
            marginal=w[crit]*(self.q**n[crit])*(1-self.q)
            n[crit[int(np.argmax(marginal))]]+=1
        return {"allocations":n,
                "all_declared_critical_covered":bool(np.all(n[crit]>0)),
                "consequence_map_calibration_required":True}

# ---- LCB-7F3A91 value-first: RX-077 ----
class PerimeterMigrationScannerV0:
    """Map legal/category counts into calibrated functional-risk equivalents."""
    @staticmethod
    def functional_volume(category_counts, equivalence_weights):
        import numpy as np
        x=np.asarray(category_counts,float)
        w=np.asarray(equivalence_weights,float)
        if x.shape[-1]!=len(w): raise ValueError("last dimension must match weights")
        return np.tensordot(x,w,axes=([-1],[0]))
    @staticmethod
    def migration_share(before_regulated, after_regulated, before_total, after_total):
        br=float(before_regulated)/max(float(before_total),1e-12)
        ar=float(after_regulated)/max(float(after_total),1e-12)
        return {"regulated_share_before":br,"regulated_share_after":ar,
                "share_change":ar-br,"equivalence_weights_require_outcome_calibration":True}


# ---- LCB-7F3A91 value-first: RH-005 ----
class LiquidityStateEngineV0:
    """Convert nominal balance-sheet stock into current deployable liquidity."""
    @staticmethod
    def compute(cash, receivables, inventory, receivable_accessibility,
                inventory_accessibility, verification_fraction, run_haircut=1.0):
        rh=float(run_haircut); vf=float(verification_fraction)
        deployable=(float(cash)
                    + float(receivables)*float(receivable_accessibility)*vf*rh
                    + float(inventory)*float(inventory_accessibility)*(vf**1.2)*(rh**1.5))
        nominal=float(cash)+float(receivables)+float(inventory)
        return {"nominal_liquidity":nominal,"deployable_liquidity":deployable,
                "deployability_gap":nominal-deployable,
                "verification_fraction":vf,"run_haircut":rh}

# ---- LCB-7F3A91 value-first: RX-021 ----
class CompetingExitExposureV0:
    """Simulate first-exit exposure when exit intensity depends on exposure state."""
    @staticmethod
    def simulate(exposure_paths, exit_probability_fn, exit_times):
        import numpy as np
        X=np.asarray(exposure_paths,float)
        n,T1=X.shape
        out=[]
        for i in range(n):
            stop=T1-1
            for t in exit_times:
                if t>=T1: break
                p=float(exit_probability_fn(X[i,t],t))
                if np.random.random()<p:
                    stop=t; break
            path=np.maximum(X[i,1:stop+1],0)
            out.append((stop,float(path.sum()),float(path.max()) if len(path) else 0.0))
        return out

# ---- LCB-7F3A91 value-first: RX-043 ----
class CutQueryCompressorV0:
    """Build a Gomory-Hu tree for repeated undirected min-cut queries."""
    def fit(self, graph, capacity="capacity"):
        import networkx as nx
        self.tree_=nx.gomory_hu_tree(graph,capacity=capacity)
        self.capacity_=capacity
        return self
    def min_cut_value(self, s, t):
        import networkx as nx
        if not hasattr(self,"tree_"): raise RuntimeError("fit first")
        path=nx.shortest_path(self.tree_,s,t)
        return min(self.tree_[u][v]["weight"] for u,v in zip(path[:-1],path[1:]))

# ---- LCB-7F3A91 value-first component: RH-008 ----
class TriggerQualityVerifierV0:
    """Allocate a finite verification budget using expected error plus gaming suspicion."""
    @staticmethod
    def rank_for_verification(calibrated_probability, suspicion=None, suspicion_weight=0.4):
        import numpy as np
        p=np.asarray(calibrated_probability,float)
        s=np.zeros_like(p) if suspicion is None else np.asarray(suspicion,float)
        if p.shape!=s.shape: raise ValueError("probability and suspicion shapes must match")
        score=np.minimum(p,1-p)+float(suspicion_weight)*s
        return np.argsort(-score),score


# ---- LCB-7F3A91 value-first: RH-004 ----
class ActiveThresholdSensingV0:
    """Choose the next ordered threshold by expected posterior-entropy reduction."""
    def __init__(self, n_locations, response_accuracy=0.9):
        import numpy as np
        self.n=int(n_locations); self.acc=float(response_accuracy)
        self.posterior=np.ones(self.n)/self.n
        self.used=[]
    def _entropy(self,q):
        import numpy as np
        return -float(np.sum(q*np.log(np.maximum(q,1e-15))))
    def _update(self,t,response):
        import numpy as np
        idx=np.arange(self.n); yes=idx<=int(t)
        lik=np.where(yes,self.acc if response else 1-self.acc,
                     1-self.acc if response else self.acc)
        q=self.posterior*lik
        self.posterior=q/q.sum()
        self.used.append(int(t))
        return self.posterior
    def choose(self):
        import numpy as np
        idx=np.arange(self.n); best=None;bestv=float("inf")
        for t in range(self.n-1):
            if t in self.used: continue
            yes=idx<=t
            py=float(self.acc*self.posterior[yes].sum()+(1-self.acc)*self.posterior[~yes].sum())
            old=self.posterior.copy()
            self._update(t,True); Hy=self._entropy(self.posterior)
            self.posterior=old.copy(); self.used.pop()
            self._update(t,False); Hn=self._entropy(self.posterior)
            self.posterior=old.copy(); self.used.pop()
            v=py*Hy+(1-py)*Hn
            if v<bestv: bestv=v;best=t
        return best
    def observe(self,t,response):
        return self._update(t,bool(response))

# ---- LCB-7F3A91 value-first: RH-006 ----
class EffectiveRedundancyBackstopV0:
    """Decide whether independent backstop value exceeds disagreement/escalation cost."""
    @staticmethod
    def break_even_escalation_cost(homogeneous_error, backstop_error, disagreement_rate,
                                   catastrophic_error_cost=100.0):
        gain=float(catastrophic_error_cost)*(float(homogeneous_error)-float(backstop_error))
        rate=float(disagreement_rate)
        return float("inf") if rate<=0 and gain>0 else (0.0 if rate<=0 else gain/rate)

# ---- LCB-7F3A91 value-first: RX-035 ----
class DesignAwareRandomizationInferenceV0:
    """Exact paired randomization p-value for one-treated-per-pair designs."""
    @staticmethod
    def paired_pvalue(outcomes, observed_assignment):
        import numpy as np
        y=np.asarray(outcomes,float); z=np.asarray(observed_assignment,int)
        if len(y)%2: raise ValueError("paired design requires even n")
        npairs=len(y)//2
        stat=abs(y[z==1].mean()-y[z==0].mean())
        vals=[]
        for mask in range(1<<npairs):
            zz=np.zeros(len(y),dtype=int)
            for p in range(npairs):
                zz[2*p+((mask>>p)&1)]=1
            vals.append(abs(y[zz==1].mean()-y[zz==0].mean()))
        return float(np.mean(np.asarray(vals)>=stat-1e-12))

# ---- LCB-7F3A91 value-first: RX-057 ----
class ReachableSubspaceAuditV0:
    """Audit whether requested target directions lie in a finite-horizon controllable subspace."""
    @staticmethod
    def audit(A,B,target_directions,horizon=None,tol=1e-9):
        import numpy as np
        A=np.asarray(A,float);B=np.asarray(B,float);D=np.asarray(target_directions,float)
        n=A.shape[0]; h=n if horizon is None else int(horizon)
        blocks=[]; Ak=np.eye(n)
        for _ in range(h):
            blocks.append(Ak@B); Ak=A@Ak
        W=np.concatenate(blocks,axis=1)
        U,s,_=np.linalg.svd(W,full_matrices=False)
        r=int(np.sum(s>tol))
        Q=U[:,:r]
        residual=D-Q@(Q.T@D)
        col_res=np.linalg.norm(residual,axis=0)
        return {"controllability_rank":r,
                "target_residuals":col_res,
                "all_targets_reachable":bool(np.max(col_res)<tol)}

# ---- LCB-7F3A91 value-first: RX-030 ----
class BandSpecificRelationGateV0:
    """Estimate band-averaged Welch coherence instead of trusting one raw Fourier ordinate."""
    @staticmethod
    def score(x,y,fs,band,nperseg=256):
        import numpy as np
        from scipy.signal import coherence
        f,c=coherence(np.asarray(x,float),np.asarray(y,float),fs=float(fs),nperseg=int(nperseg))
        lo,hi=band
        m=(f>=float(lo))&(f<=float(hi))
        if not np.any(m): raise ValueError("band contains no frequency bins")
        return float(np.mean(c[m]))


# ---- LCB-7F3A91 value-first: RX-046 ----
class TargetPopulationAnchorCalibratorV0:
    """Logistic recalibration using a small trusted target-population anchor."""
    def fit(self, source_probabilities, target_labels):
        import numpy as np
        from sklearn.linear_model import LogisticRegression
        p=np.clip(np.asarray(source_probabilities,float),1e-6,1-1e-6)
        x=np.log(p/(1-p)).reshape(-1,1)
        self.model_=LogisticRegression(max_iter=500).fit(x,np.asarray(target_labels,int))
        return self
    def transform(self, probabilities):
        import numpy as np
        if not hasattr(self,"model_"): raise RuntimeError("fit first")
        p=np.clip(np.asarray(probabilities,float),1e-6,1-1e-6)
        x=np.log(p/(1-p)).reshape(-1,1)
        return self.model_.predict_proba(x)[:,1]

# ---- LCB-7F3A91 value-first component: RX-052 ----
class AtomicComplementaryCommitV0:
    """Gate atomic commit on complementarity and expected stranded-loss economics."""
    @staticmethod
    def expected_atomic_value(p1,p2,leg_value=1.0):
        return float(p1)*float(p2)*2*float(leg_value)
    @staticmethod
    def should_use_atomic(partial_probability,reversal_failure_probability,stranded_cost,
                          standalone_partial_value=0.0):
        avoided=float(partial_probability)*float(reversal_failure_probability)*float(stranded_cost)
        lost=float(partial_probability)*float(standalone_partial_value)
        return {"use_atomic":bool(avoided>lost),"avoided_stranded_loss":avoided,"lost_partial_value":lost}

# ---- LCB-7F3A91 value-first: RH-007 ----
class MultiFidelityBudgetControllerV0:
    """Choose fine/cheap counts from pilot cross-fidelity correlation under a fixed budget."""
    @staticmethod
    def allocate(total_budget,fine_cost,cheap_cost,rho_hat,min_fine=20):
        import math
        C=int(total_budget); cf=float(fine_cost); cc=float(cheap_cost)
        rh=min(abs(float(rho_hat)),.999)
        best={"mode":"fine_only","n_fine":int(C//cf),"n_cheap":int(min_fine),
              "variance_proxy":1/max(int(C//cf),1)}
        for nf in range(int(min_fine),int(C//cf)+1):
            nc=int((C-cf*nf)//cc)
            if nc<nf: continue
            var=(1-rh*rh)/nf+(rh*rh)/nc
            if var<best["variance_proxy"]:
                best={"mode":"multifidelity","n_fine":nf,"n_cheap":nc,"variance_proxy":var}
        return best

# ---- LCB-7F3A91 value-first: RX-031 ----
class BarrierAwareTransitionPlannerV0:
    """Shortest expected transition-time path where edge crossing time grows as exp(barrier/T)."""
    @staticmethod
    def path(adjacency,start,goal,temperature=1.0):
        import heapq, math
        n=len(adjacency); dist=[float("inf")]*n;prev=[None]*n;dist[int(start)]=0.0
        pq=[(0.0,int(start))]
        while pq:
            d,u=heapq.heappop(pq)
            if d!=dist[u]: continue
            if u==goal: break
            for v,b in adjacency[u]:
                w=math.exp(float(b)/float(temperature))
                nd=d+w
                if nd<dist[int(v)]:
                    dist[int(v)]=nd;prev[int(v)]=u;heapq.heappush(pq,(nd,int(v)))
        if not np.isfinite(dist[int(goal)]): return None
        p=[];u=int(goal)
        while u is not None:p.append(u);u=prev[u]
        return {"path":list(reversed(p)),"expected_time_proxy":dist[int(goal)]}

# ---- LCB-7F3A91 value-first: RX-036 ----
class ResilientFlowRouterV0:
    """Recompute max throughput on surviving topology, then minimize barrier cost."""
    @staticmethod
    def reroute(graph,source,sink,capacity="capacity",cost="weight"):
        import networkx as nx
        if not nx.has_path(graph,source,sink):
            return {"throughput":0.0,"flow":{}}
        flow=nx.max_flow_min_cost(graph,source,sink,capacity=capacity,weight=cost)
        throughput=float(sum(flow[source].values()))
        return {"throughput":throughput,"flow":flow}


# ---- LCB-7F3A91 value-first: RX-041 ----
class TreatmentConfounderFeedbackGuardV0:
    """Detect treatment-affected confounders and expose stabilized sequential weights."""
    @staticmethod
    def stabilized_weights(a0, a1, p_a0_history, p_a1_history, p_a0_marginal, p_a1_given_a0,
                           clip=20.0):
        import numpy as np
        a0=np.asarray(a0,int); a1=np.asarray(a1,int)
        p0=np.clip(np.asarray(p_a0_history,float),1e-6,1-1e-6)
        p1=np.clip(np.asarray(p_a1_history,float),1e-6,1-1e-6)
        q0=np.clip(np.asarray(p_a0_marginal,float),1e-6,1-1e-6)
        q1=np.clip(np.asarray(p_a1_given_a0,float),1e-6,1-1e-6)
        den=np.where(a0==1,p0,1-p0)*np.where(a1==1,p1,1-p1)
        num=np.where(a0==1,q0,1-q0)*np.where(a1==1,q1,1-q1)
        w=num/den
        return np.clip(w,0,float(clip))

# ---- LCB-7F3A91 value-first: RX-084 ----
class BurstAwareSamplerV0:
    """Allocate finite expensive measurements to the highest calibrated burst-risk times."""
    @staticmethod
    def select(burst_risk_score, budget, calibration_valid=True):
        import numpy as np
        s=np.asarray(burst_risk_score,float)
        B=int(budget)
        if B<=0: return np.array([],dtype=int)
        B=min(B,len(s))
        if not calibration_valid:
            return np.linspace(0,len(s)-1,B).round().astype(int)
        return np.argpartition(-s,B-1)[:B]


# ---- LCB-7F3A91 value-first: RX-087 ----
class ActiveSetMapV0:
    """Piecewise-affine parametric optimizer indexed by predicted active-set label."""
    def fit(self, parameters, solutions, active_labels):
        import numpy as np
        from sklearn.linear_model import LogisticRegression, LinearRegression
        X=np.asarray(parameters,float); Y=np.asarray(solutions,float); lab=np.asarray(active_labels,int)
        self.classifier_=LogisticRegression(max_iter=1000).fit(X,lab)
        self.local_={}
        for k in np.unique(lab):
            m=lab==k
            self.local_[int(k)]=[LinearRegression().fit(X[m],Y[m,j]) for j in range(Y.shape[1])]
        return self
    def predict(self, parameters):
        import numpy as np
        X=np.asarray(parameters,float)
        lab=self.classifier_.predict(X)
        out=np.empty((len(X),len(next(iter(self.local_.values())))))
        for i,k in enumerate(lab):
            regs=self.local_[int(k)]
            out[i]=[r.predict(X[i:i+1])[0] for r in regs]
        return {"solution":out,"active_label":lab}

# ---- LCB-7F3A91 value-first: RX-089 ----
class TimescaleBottleneckDetectorV0:
    """Convert nominal stage capacity into effective completion capacity."""
    @staticmethod
    def analyze(capacity, mean_process_time, residence_time):
        import numpy as np
        c=np.asarray(capacity,float)
        tau=np.asarray(mean_process_time,float)
        r=np.asarray(residence_time,float)
        if not (len(c)==len(tau)==len(r)): raise ValueError("length mismatch")
        p=1-np.exp(-r/np.maximum(tau,1e-12))
        eff=c*p
        i=int(np.argmin(eff))
        return {"completion_probability":p,
                "effective_capacity":eff,
                "bottleneck_index":i,
                "system_effective_capacity":float(eff[i])}


# ---- LCB-7F3A91 value-first: RX-038 ----
class InterfaceWidthOptimizerV0:
    """Exact QUBO DP for band-limited coupling graphs with known interface width."""
    @staticmethod
    def solve_linear_order(local_costs, pair_costs, width):
        import math
        h=list(map(float,local_costs))
        J={(int(i),int(j)):float(v) for (i,j),v in pair_costs.items()}
        w=int(width)
        dp={0:0.0}
        for i in range(len(h)):
            histlen=min(i,w)
            start=i-histlen
            new={}
            for state,cost in dp.items():
                bits=[(state>>(histlen-1-k))&1 for k in range(histlen)] if histlen else []
                for b in (0,1):
                    inc=h[i]*b
                    if b:
                        for off,xj in enumerate(bits):
                            inc += J.get((start+off,i),0.0)*xj
                    newlen=min(i+1,w)
                    mask=(1<<newlen)-1
                    ns=((state<<1)|b)&mask
                    nc=cost+inc
                    if nc<new.get(ns,float("inf")):
                        new[ns]=nc
            dp=new
        return {"objective":float(min(dp.values())),
                "interface_width":w,
                "max_state_count":2**w}


# ---- LCB-7F3A91 value-first: RX-075 ----
class BurdenReliefControllerV0:
    """Use reserved capacity as an explicit burden-export channel when burden accumulates."""
    def __init__(self, production_capacity, reserve_capacity, trigger, purge_efficiency):
        self.production_capacity=float(production_capacity)
        self.reserve_capacity=float(reserve_capacity)
        self.trigger=float(trigger)
        self.purge_efficiency=float(purge_efficiency)
    def action(self, burden):
        b=float(burden)
        purge=min(self.reserve_capacity,max(0.0,(b-self.trigger)/max(self.purge_efficiency,1e-12)))
        return {"production_cap":self.production_capacity,
                "purge_capacity_used":purge,
                "purge_active":bool(purge>0)}

# ---- LCB-7F3A91 value-first: RX-026 ----
class SelectionWithinAttributionV0:
    """Decompose observed aggregate trend from within-unit trend under changing composition."""
    @staticmethod
    def slopes(ids, times, values):
        import numpy as np
        ids=np.asarray(ids);t=np.asarray(times,float);y=np.asarray(values,float)
        # aggregate time trend
        ut=np.unique(t)
        means=np.array([y[t==tt].mean() for tt in ut])
        agg=float(np.polyfit(ut,means,1)[0])
        # fixed-effects within trend
        yd=np.empty_like(y);td=np.empty_like(t)
        for i in np.unique(ids):
            m=ids==i
            yd[m]=y[m]-y[m].mean()
            td[m]=t[m]-t[m].mean()
        den=float(np.sum(td*td))
        within=float(np.sum(td*yd)/den)
        return {"aggregate_trend":agg,
                "within_unit_trend":within,
                "composition_component":agg-within}

# ---- LCB-7F3A91 value-first: RX-066 ----
class SafeProblemReducerV0:
    """Safe QUBO variable fixing from one-sided marginal-cost bounds."""
    @staticmethod
    def reduce(local_costs, pair_costs):
        import numpy as np
        from collections import deque
        h=np.asarray(local_costs,float).copy()
        n=len(h)
        adj=[{} for _ in range(n)]
        for (i,j),v in pair_costs.items():
            i=int(i);j=int(j);v=float(v)
            adj[i][j]=v;adj[j][i]=v
        free=np.ones(n,dtype=bool);fixed={};const=0.0
        q=deque(range(n));queued=np.ones(n,dtype=bool)
        while q:
            i=q.popleft();queued[i]=False
            if not free[i]: continue
            vals=list(adj[i].values())
            lower=h[i]+sum(v for v in vals if v<0)
            upper=h[i]+sum(v for v in vals if v>0)
            val=0 if lower>1e-12 else (1 if upper<-1e-12 else None)
            if val is None: continue
            fixed[i]=val;free[i]=False
            if val==1: const+=h[i]
            for j,v in list(adj[i].items()):
                if not free[j]: continue
                if val==1: h[j]+=v
                adj[j].pop(i,None)
                if not queued[j]: q.append(j);queued[j]=True
            adj[i].clear()
        free_ids=np.where(free)[0].tolist()
        idx={old:k for k,old in enumerate(free_ids)}
        h2=np.asarray([h[i] for i in free_ids])
        J2={}
        for i in free_ids:
            for j,v in adj[i].items():
                if free[j] and i<j: J2[(idx[i],idx[j])]=v
        return {"reduced_local_costs":h2,
                "reduced_pair_costs":J2,
                "objective_constant":const,
                "fixed_assignments":fixed,
                "free_original_ids":free_ids}

# ---- LCB-7F3A91 value-first: RX-032 ----
class ArrivalFrontierEngineV0:
    """Assign each target to the source with minimum start+travel+barrier arrival time."""
    @staticmethod
    def assign(source_xy, target_xy, start_time, speed, barrier=None):
        import numpy as np
        S=np.asarray(source_xy,float);T=np.asarray(target_xy,float)
        start=np.asarray(start_time,float);v=np.asarray(speed,float)
        dist=np.linalg.norm(T[:,None,:]-S[None,:,:],axis=2)
        arr=start[None,:]+dist/np.maximum(v[None,:],1e-12)
        if barrier is not None: arr=arr+np.asarray(barrier,float)
        owner=np.argmin(arr,axis=1)
        return {"owner":owner,
                "arrival_time":arr[np.arange(len(T)),owner]}


# ---- LCB-7F3A91 value-first: RX-095 ----
class EndogenousHotspotGuardV0:
    """Forecast overflow when occupancy changes retention/service persistence."""
    @staticmethod
    def overflow_probability(occupancy, arrival_rate, capacity,
                             retention_floor=0.25, retention_span=0.48,
                             midpoint=9.0, scale=2.5):
        import numpy as np
        from scipy.stats import poisson
        occ=np.asarray(occupancy,float)
        ret=float(retention_floor)+float(retention_span)/(1+np.exp(-(occ-float(midpoint))/float(scale)))
        mean_next=ret*occ+float(arrival_rate)
        p=1-poisson.cdf(int(capacity),mean_next)
        return {"retention_probability":ret,
                "expected_next_occupancy":mean_next,
                "overflow_probability":p}


# ---- LCB-7F3A91 value-first: RX-188 ----
class RiskShiftContractGuardV0:
    """Evaluate post-contract risk choice under downside and upside sharing."""
    @staticmethod
    def choose_risk(risk_levels, outcome_matrix, risk_cost,
                    downside_share=0.0, upside_share=0.0, upside_threshold=0.0):
        import numpy as np
        sig=np.asarray(risk_levels,float)
        X=np.asarray(outcome_matrix,float)
        if X.shape[0]!=len(sig): raise ValueError("one outcome row per risk level")
        support=float(downside_share)*np.maximum(-X,0)
        upside=float(upside_share)*np.maximum(X-float(upside_threshold),0)
        agent=X+support-upside
        utility=agent.mean(axis=1)-float(risk_cost)*sig*sig
        i=int(np.argmax(utility))
        return {"chosen_risk":float(sig[i]),
                "utility":float(utility[i]),
                "severe_shortfall_rate":float(np.mean(agent[i]<-.5)),
                "expected_counterparty_transfer":float(np.mean(support[i]-upside[i]))}

# ---- LCB-7F3A91 value-first: RX-136 ----
class DelayedVerificationIncentiveGateV0:
    """Solve present misreport choice when future verification can claw back payoff."""
    @staticmethod
    def optimal_misreport(gain, audit_probability, clawback_multiple,
                          falsification_cost, verification_sensitivity=0.88,
                          grid_size=1001):
        import numpy as np
        m=np.linspace(0,1,int(grid_size))
        detect=float(audit_probability)*(
            (1-float(verification_sensitivity)) + float(verification_sensitivity)*m
        )
        u=float(gain)*m-float(falsification_cost)*m*m-detect*float(clawback_multiple)*float(gain)*m
        i=int(np.argmax(u))
        return {"misreport":float(m[i]),"claim_quality":float(1-m[i]),"expected_private_gain":float(u[i])}

# ---- LCB-7F3A91 value-first: RX-045 ----
class SolverCertificateAuditV0:
    """Independently validate primal feasibility or a Farkas infeasibility witness."""
    @staticmethod
    def validate_primal(A,b,x,tol=1e-8):
        import numpy as np
        A=np.asarray(A,float);b=np.asarray(b,float);x=np.asarray(x,float)
        scale=max(1.0,float(np.linalg.norm(A,ord=np.inf)),float(np.linalg.norm(b,np.inf)))
        violation=float(np.max(A@x-b))
        return {"valid":bool(violation<=float(tol)*scale),"max_violation":violation}
    @staticmethod
    def validate_farkas(A,b,y,tol=1e-8):
        import numpy as np
        A=np.asarray(A,float);b=np.asarray(b,float);y=np.asarray(y,float)
        if np.min(y)<-float(tol):
            return {"valid":False,"reason":"negative multiplier"}
        denom=max(1.0,float(np.linalg.norm(A,ord=np.inf)*np.linalg.norm(y,1)))
        residual=float(np.linalg.norm(A.T@y)/denom)
        margin=float(-(b@y)/max(1.0,float(np.linalg.norm(b,np.inf)*np.linalg.norm(y,1))))
        return {"valid":bool(residual<=float(tol) and margin>float(tol)),
                "normalized_residual":residual,"normalized_margin":margin}

# ---- LCB-7F3A91 value-first: RX-056 ----
class StrategicCapacityResponseGuardV0:
    """Solve Wardrop path equilibrium for affine edge costs before/after a network change."""
    @staticmethod
    def wardrop(path_edge_incidence, demand, edge_slopes, edge_intercepts):
        import numpy as np
        from scipy.optimize import minimize
        P=np.asarray(path_edge_incidence,float)
        a=np.asarray(edge_slopes,float); b=np.asarray(edge_intercepts,float)
        D=float(demand); k=P.shape[0]
        def edge_flow(f): return P.T@f
        def potential(f):
            x=edge_flow(f)
            return float(np.sum(.5*a*x*x+b*x))
        cons={"type":"eq","fun":lambda f:np.sum(f)-D}
        res=minimize(potential,np.full(k,D/k),bounds=[(0,D)]*k,
                     constraints=cons,method="SLSQP",
                     options={"ftol":1e-11,"maxiter":500})
        f=np.maximum(res.x,0)
        x=edge_flow(f); edge_cost=a*x+b
        path_cost=P@edge_cost
        return {"path_flow":f,"edge_flow":x,"path_cost":path_cost,
                "average_user_cost":float(np.dot(f,path_cost)/D),
                "success":bool(res.success)}


# ---- LCB-7F3A91 value-first: RX-053 ----
class InformationProductionEquilibriumGuardV0:
    """Model endogenous producer entry under copying/dissemination friction."""
    @staticmethod
    def equilibrium(copy_friction, producer_values, producer_costs, spillover=0.20):
        import numpy as np
        f=float(copy_friction)
        v=np.asarray(producer_values,float)
        c=np.asarray(producer_costs,float)
        active=np.ones(len(v),dtype=bool)
        for _ in range(100):
            private=v*f
            public=float(spillover)*(1-f)*(active.sum()-active.astype(int))/max(len(v)-1,1)
            new=(private+public)>=c
            if np.array_equal(new,active):
                break
            active=new
        discoveries=int(active.sum())
        accessible=float(discoveries*(0.35+0.65*(1-f)))
        return {"active_producers":active,
                "discoveries":discoveries,
                "accessible_information":accessible}

# ---- LCB-7F3A91 value-first: RX-134 ----
class EffectiveComplexityMeterV0:
    """Compute ridge effective degrees of freedom rather than nominal parameter count."""
    @staticmethod
    def ridge_effective_df(X, alpha, include_intercept=True):
        import numpy as np
        X=np.asarray(X,float)
        Xc=X-X.mean(axis=0,keepdims=True) if include_intercept else X
        XtX=Xc.T@Xc
        A=XtX+float(alpha)*np.eye(X.shape[1])
        df=float(np.trace(np.linalg.solve(A,XtX)))
        if include_intercept:
            df+=1.0
        return {"effective_df":df,
                "nominal_parameters":int(X.shape[1]+(1 if include_intercept else 0)),
                "complexity_ratio":df/max(X.shape[1]+(1 if include_intercept else 0),1)}

# ---- LCB-7F3A91 value-first: RX-028 ----
class TimescaleAwareDeadZoneV0:
    """Convert one-step subthreshold crossing risk into cumulative horizon risk."""
    @staticmethod
    def cumulative_crossing_probability(one_step_probability, horizon):
        p=min(max(float(one_step_probability),0.0),1.0)
        H=max(int(horizon),0)
        return float(1-(1-p)**H)
    @staticmethod
    def from_gaussian_gap(signal, threshold, sigma, horizon):
        from scipy.stats import norm
        if float(sigma)<=0:
            p1=1.0 if float(signal)>float(threshold) else 0.0
        else:
            p1=float(1-norm.cdf((float(threshold)-float(signal))/float(sigma)))
        return {"one_step_probability":p1,
                "horizon_probability":TimescaleAwareDeadZoneV0.cumulative_crossing_probability(p1,horizon)}


# ---- LCB-7F3A91 value-first: RX-010 ----
class AdmissibleShiftRobustOptimizerV0:
    """Quadratic robust decision under a declared admissible uncertainty direction."""
    @staticmethod
    def solve(mean_vector, shift_direction, radius):
        import numpy as np
        from scipy.optimize import minimize
        mu=np.asarray(mean_vector,float)
        v=np.asarray(shift_direction,float)
        v=v/np.linalg.norm(v)
        rho=float(radius)
        def objective(w):
            return -(mu@w-.5*(w@w)-rho*abs(v@w))
        res=minimize(objective,np.zeros_like(mu),method="BFGS")
        w=np.asarray(res.x,float)
        return {"decision":w,
                "worst_case_objective":float(mu@w-.5*(w@w)-rho*abs(v@w)),
                "success":bool(res.success)}

# ---- LCB-7F3A91 value-first: RX-127 ----
class PredictableVarianceAlarmV0:
    """Freedman-style finite-horizon alarm using accumulated predictable variance."""
    @staticmethod
    def boundary(predictable_variance, alpha=0.05, increment_bound=1.0):
        import numpy as np
        V=float(predictable_variance); a=float(alpha); b=float(increment_bound)
        L=np.log(1/a)
        return float((L*b/3)+np.sqrt((L*b/3)**2+2*L*V))
    @staticmethod
    def alarm(cumulative_surprise, predictable_variance, alpha=0.05, increment_bound=1.0):
        bd=PredictableVarianceAlarmV0.boundary(predictable_variance,alpha,increment_bound)
        return {"alarm":bool(float(cumulative_surprise)>bd),"boundary":bd}

# ---- LCB-7F3A91 value-first: RX-133 ----
class GroundTruthFreeRiskTunerV0:
    """SURE soft-threshold tuner with an explicit Gaussian-noise validity gate."""
    @staticmethod
    def soft_threshold(y, threshold):
        import numpy as np
        y=np.asarray(y,float); t=float(threshold)
        return np.sign(y)*np.maximum(np.abs(y)-t,0)
    @staticmethod
    def tune(y, sigma, thresholds, gaussian_shell_valid=True):
        import numpy as np
        if not gaussian_shell_valid:
            return {"accepted":False,"reason":"Gaussian/Stein noise shell not certified"}
        y=np.asarray(y,float); s=float(sigma)
        grid=np.asarray(thresholds,float)
        risk=[]
        for t in grid:
            est=GroundTruthFreeRiskTunerV0.soft_threshold(y,t)
            sure=float(np.mean((est-y)**2)+2*s*s*np.mean(np.abs(y)>t)-s*s)
            risk.append(sure)
        i=int(np.argmin(risk))
        return {"accepted":True,"threshold":float(grid[i]),"sure_risk":float(risk[i])}


# ---- LCB-7F3A91 value-first: RX-065 ----
class GuaranteeTransportGateV0:
    """Audit whether the residual/conditional law supporting a deployed guarantee still holds."""
    @staticmethod
    def residual_shift_score(source_residuals, target_residuals, target_driver=None):
        import numpy as np
        rs=np.asarray(source_residuals,float)
        rt=np.asarray(target_residuals,float)
        score=abs(rt.mean()-rs.mean())/(rs.std()+1e-12)
        score+=abs(np.log((rt.std()+1e-12)/(rs.std()+1e-12)))
        corr=0.0
        if target_driver is not None:
            x=np.asarray(target_driver,float)
            if len(x)==len(rt) and np.std(x)>0 and np.std(rt)>0:
                corr=abs(float(np.corrcoef(rt,x)[0,1]))
                score+=corr
        return {"residual_shift_score":float(score),
                "target_residual_driver_correlation":float(corr)}

# ---- LCB-7F3A91 merge extension: RX-139 -> EffectiveDiversityGuardV0 ----
def _effective_diversity_provenance_aggregate(source_ids, log_likelihood_messages):
    import numpy as np
    ids=np.asarray(source_ids)
    msg=np.asarray(log_likelihood_messages,float)
    if len(ids)!=len(msg): raise ValueError("length mismatch")
    unique=np.unique(ids)
    total=0.0
    for u in unique:
        # count an upstream evidence source once; average duplicated copies if they differ numerically.
        total+=float(np.mean(msg[ids==u]))
    return {"unique_evidence_count":int(len(unique)),
            "message_count":int(len(ids)),
            "deduplicated_log_likelihood":float(total)}
EffectiveDiversityGuardV0.provenance_aggregate=staticmethod(_effective_diversity_provenance_aggregate)

# ---- LCB-7F3A91 merge extension: RX-190 -> TreatmentConfounderFeedbackGuardV0 ----
def _controlled_direct_effect_gcomp(a, m, l, y, baseline, mediator_fixed=0.0):
    import numpy as np
    A=np.asarray(a,float); M=np.asarray(m,float); L=np.asarray(l,float)
    Y=np.asarray(y,float); U=np.asarray(baseline,float)
    XL=np.column_stack([np.ones(len(A)),A,U])
    bL=np.linalg.lstsq(XL,L,rcond=None)[0]
    XY=np.column_stack([np.ones(len(A)),A,M,L,U])
    bY=np.linalg.lstsq(XY,Y,rcond=None)[0]
    def ey(av):
        lh=bL[0]+bL[1]*av+bL[2]*U
        return float(np.mean(bY[0]+bY[1]*av+bY[2]*float(mediator_fixed)+bY[3]*lh+bY[4]*U))
    return {"controlled_direct_effect":float(ey(1.0)-ey(0.0)),
            "requires_post_treatment_confounder_model":True}
TreatmentConfounderFeedbackGuardV0.controlled_direct_effect_gcomp=staticmethod(_controlled_direct_effect_gcomp)


# ---- LCB-7F3A91 value-first: RX-081 ----
class EffectiveRedundancyAuditV0:
    """Estimate effective coherent-path gain from cross-path covariance, not route count."""
    @staticmethod
    def audit(complex_path_samples):
        import numpy as np
        A=np.asarray(complex_path_samples)
        if A.ndim!=2:
            raise ValueError("samples x paths matrix required")
        C=(A.conj().T@A)/A.shape[0]
        one=np.ones(A.shape[1])
        eff=float(np.real(one@C@one))
        nominal=float(np.real(np.trace(C)))
        return {"nominal_independent_gain":nominal,
                "effective_coherent_gain":eff,
                "effective_to_nominal_ratio":eff/max(nominal,1e-12),
                "path_covariance":C}

# ---- LCB-7F3A91 value-first: RX-160 ----
class ConsumableSafeguardStateV0:
    """Track remaining sacrificial protection stock and next-shock failure risk."""
    def __init__(self, initial_capacity):
        self.initial_capacity=float(initial_capacity)
        self.remaining_capacity=float(initial_capacity)
    def absorb(self, shock):
        s=max(float(shock),0.0)
        absorbed=min(self.remaining_capacity,s)
        self.remaining_capacity-=absorbed
        return {"absorbed":absorbed,
                "residual_shock":s-absorbed,
                "remaining_capacity":self.remaining_capacity}
    def failure_probability_gamma(self, residual_failure_threshold,
                                  shape, scale):
        from scipy.stats import gamma
        cutoff=self.remaining_capacity+float(residual_failure_threshold)
        return float(1-gamma.cdf(cutoff,a=float(shape),scale=float(scale)))

# ---- LCB-7F3A91 value-first: RX-175 ----
class InformationSearchTippingGuardV0:
    """Map search-participation equilibria and hysteresis under acquisition friction."""
    @staticmethod
    def fixed_point(cost, feedback, temperature=0.05, init=1.0):
        import numpy as np
        q=float(init)
        for _ in range(2000):
            info=1/(1+np.exp(-float(feedback)*(q-.45)))
            qn=1/(1+np.exp(-(info-float(cost))/float(temperature)))
            new=.75*q+.25*qn
            if abs(new-q)<1e-11:
                q=new
                break
            q=new
        return {"participation":q,
                "information_quality":float(1/(1+np.exp(-float(feedback)*(q-.45))))}

# ---- LCB-7F3A91 value-first: RX-180 ----
class ScreeningByDegradationAuditV0:
    """Compare pooled quality with an incentive-compatible two-type versioning menu."""
    @staticmethod
    def canonical_prices(theta_low, theta_high, q_low, q_high):
        tl=float(theta_low); th=float(theta_high)
        ql=float(q_low); qh=float(q_high)
        if qh<ql:
            raise ValueError("q_high must be >= q_low")
        p_low=tl*ql
        p_high=p_low+th*(qh-ql)
        return {"price_low":p_low,"price_high":p_high,
                "low_IR_binding":True,"high_IC_binding":True}

# ---- LCB-7F3A91 value-first: RX-186 ----
class ModeConversionRouterV0:
    """Propagate modal state through geometry conversion before downstream transmission."""
    @staticmethod
    def delivered_power(input_amplitude, conversion_matrix, transmission):
        import numpy as np
        x=np.asarray(input_amplitude,complex)
        M=np.asarray(conversion_matrix,complex)
        tr=np.asarray(transmission,float)
        y=M@x
        power=np.abs(y)**2
        delivered=power*tr
        return {"output_amplitude":y,
                "modal_power":power,
                "delivered_power_by_mode":delivered,
                "total_delivered_power":float(delivered.sum())}


# ---- LCB-7F3A91 value-first: RX-022 ----
class SacrificialDeflectionGuardV0:
    """Compare direct strengthening with a weak path that dissipates/redirects propagation energy."""
    @staticmethod
    def effective_load(incoming_load, trigger, dissipation, redirect_fraction):
        import numpy as np
        e=np.asarray(incoming_load,float)
        out=e.copy()
        m=e>float(trigger)
        out[m]=np.maximum(0.0,(e[m]-float(dissipation))*(1.0-float(redirect_fraction)))
        return out
    @staticmethod
    def core_failure_probability(incoming_load, core_threshold,
                                 trigger, dissipation, redirect_fraction):
        import numpy as np
        eff=SacrificialDeflectionGuardV0.effective_load(
            incoming_load,trigger,dissipation,redirect_fraction
        )
        return float(np.mean(eff>float(core_threshold)))

# ---- LCB-7F3A91 value-first: RX-055 ----
class AtomicPackageExecutionV0:
    """All-or-none execution gate for complementary legs."""
    @staticmethod
    def decide(package_value, leg_prices, leg_available, complementarity_required=True):
        prices=[float(x) for x in leg_prices]
        avail=[bool(x) for x in leg_available]
        total=sum(prices)
        if complementarity_required:
            execute=all(avail) and total<float(package_value)
            return {"execute_atomically":bool(execute),
                    "expected_surplus":float(package_value)-total if execute else 0.0,
                    "partial_execution_allowed":False}
        return {"execute_atomically":False,
                "reason":"legs retain standalone value; evaluate independently",
                "partial_execution_allowed":True}

# ---- LCB-7F3A91 value-first: RX-079 ----
class LeadingEdgeEarlyWarningV0:
    """Score precursor evidence in a declared low-mass frontier region."""
    @staticmethod
    def standardized_residual_score(observed, expected, noise_scale):
        import numpy as np
        o=np.asarray(observed,float); e=np.asarray(expected,float)
        s=max(float(noise_scale),1e-12)
        z=(o-e)/s
        return {"mean_standardized_residual":float(np.mean(z)),
                "max_standardized_residual":float(np.max(z)),
                "n_measurements":int(len(z))}

# ---- LCB-7F3A91 value-first: RX-130 ----
class CompressionTopologyGuardV0:
    """Audit a compressed closed manifold for seam/collision failure hidden by local metric tests."""
    @staticmethod
    def closed_loop_seam_ratio(compressed_loop, local_reference_step):
        import numpy as np
        z=np.asarray(compressed_loop,float)
        if z.ndim!=1 or len(z)<3:
            raise ValueError("one-dimensional ordered loop required")
        seam=abs(float(z[0]-z[-1]))
        ref=max(float(local_reference_step),1e-12)
        return {"seam_jump":seam,
                "seam_to_local_step_ratio":seam/ref,
                "topology_warning":bool(seam/ref>10.0)}

# ---- LCB-7F3A91 merge extension: RX-131 -> SolverCertificateAuditV0 ----
def _extract_sparse_farkas_conflict(A,b,tol=1e-7):
    import numpy as np
    from scipy.optimize import linprog
    A=np.asarray(A,float); b=np.asarray(b,float)
    m,n=A.shape
    res=linprog(
        np.ones(m),
        A_ub=b.reshape(1,-1), b_ub=np.array([-1.0]),
        A_eq=A.T, b_eq=np.zeros(n),
        bounds=[(0,None)]*m,
        method="highs"
    )
    if res.status!=0:
        return {"certificate_found":False,"support":[],"solver_status":int(res.status)}
    y=np.asarray(res.x,float)
    support=np.where(y>float(tol))[0].tolist()
    check=SolverCertificateAuditV0.validate_farkas(A,b,y,tol=max(float(tol),1e-8))
    return {"certificate_found":bool(check["valid"]),
            "support":support,
            "multipliers":y,
            "validation":check}
SolverCertificateAuditV0.extract_sparse_farkas_conflict=staticmethod(_extract_sparse_farkas_conflict)

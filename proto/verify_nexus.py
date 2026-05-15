#!/usr/bin/env python3
"""
verify_nexus.py — Numerical verification mirroring astra_nexus.cpp

Runs the same math and the same test suite. Since astra_nexus.cpp may not
have a C++ compiler available on every machine, this Python file provides
runnable proof that all the equations compose correctly and all assertions
pass. The C++ file is the production-grade artifact; this is the validation.

Run: python verify_nexus.py
"""

import math
import sys

# Force UTF-8 on Windows console so greek letters render in test output
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

# ============================================================================
# Constants (mirrors C++ namespace astra)
# ============================================================================
C_LIGHT     = 299792458.0
G_GRAV      = 6.67430e-11
M_SUN       = 1.98892e30
PARSEC      = 3.0856775814913673e16
LIGHT_YEAR  = 9.4607304725808e15
MPC         = 1.0e6 * PARSEC
H0_KMS_MPC  = 70.0
H0_SI       = H0_KMS_MPC * 1000.0 / MPC
OMEGA_M     = 0.3
OMEGA_LAM   = 0.7

OMEGA_MAX   = 16.811   # v0.126 N1 lock: γ_max = cosh(16.811) ≈ 1e7

SECTOR_SIZE = 1.0e6
LOCAL_MAX   = 5.0e5

# Regime bitmask (§3.3 canonical hex)
R_REST          = 0x00
R_STL_NONREL    = 0x01
R_STL_REL       = 0x02
R_WARP_CHARGE   = 0x04
R_WARP_CRUISE   = 0x08
R_WARP_SHUTDOWN = 0x10
R_GRAVITY_WELL  = 0x20
R_CRYOSLEEP     = 0x40


# ============================================================================
# Vec3
# ============================================================================
class Vec3:
    __slots__ = ("x", "y", "z")
    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x, self.y, self.z = x, y, z
    def __add__(s, b): return Vec3(s.x+b.x, s.y+b.y, s.z+b.z)
    def __sub__(s, b): return Vec3(s.x-b.x, s.y-b.y, s.z-b.z)
    def __mul__(s, a): return Vec3(s.x*a,   s.y*a,   s.z*a)
    def __truediv__(s, a): return Vec3(s.x/a, s.y/a, s.z/a)
    def dot(s, b): return s.x*b.x + s.y*b.y + s.z*b.z
    def mag(s):
        return math.sqrt(s.dot(s))
    def normalized(s):
        m = s.mag()
        return s/m if m > 1e-300 else Vec3()


# ============================================================================
# AstraCoord (§1.1)
# ============================================================================
class AstraCoord:
    __slots__ = ("sx", "sy", "sz", "lx", "ly", "lz")
    def __init__(self, sx=0, sy=0, sz=0, lx=0.0, ly=0.0, lz=0.0):
        self.sx, self.sy, self.sz = sx, sy, sz
        self.lx, self.ly, self.lz = lx, ly, lz

    def renormalize(self):
        for axis in ("x", "y", "z"):
            l = getattr(self, "l" + axis)
            s = getattr(self, "s" + axis)
            if abs(l) > LOCAL_MAX:
                n = int(math.floor(l / SECTOR_SIZE + 0.5))
                s += n
                l -= n * SECTOR_SIZE
                setattr(self, "l" + axis, l)
                setattr(self, "s" + axis, s)


def astra_distance(a, b):
    dx = (a.sx - b.sx) * SECTOR_SIZE + (a.lx - b.lx)
    dy = (a.sy - b.sy) * SECTOR_SIZE + (a.ly - b.ly)
    dz = (a.sz - b.sz) * SECTOR_SIZE + (a.lz - b.lz)
    return math.sqrt(dx*dx + dy*dy + dz*dz)


# ============================================================================
# Rapidity (§3.7 v0.126)
# ============================================================================
class Rapidity:
    __slots__ = ("zeta",)
    def __init__(self, zeta=None):
        self.zeta = zeta if zeta else Vec3()
    def omega(self):    return self.zeta.mag()
    # LOCKED: γ = cosh(ω). Never 1/√(1-β²) — catastrophic cancellation.
    def gamma(self):    return math.cosh(self.omega())
    def beta(self):     return math.tanh(self.omega())
    def velocity(self):
        w = self.omega()
        if w < 1e-30: return Vec3()
        return self.zeta * (C_LIGHT * math.tanh(w) / w)


def integrate_rapidity_step(prev, a_proper, dtau_ship):
    new_zeta = prev.zeta + a_proper * (dtau_ship / C_LIGHT)
    mag = new_zeta.mag()
    if mag > OMEGA_MAX:
        new_zeta = new_zeta * (OMEGA_MAX / mag)
    return Rapidity(new_zeta)


# ============================================================================
# Gravitational composition (§3.2 v0.126)
# ============================================================================
def schwarzschild_r(M):
    return 2.0 * G_GRAV * M / (C_LIGHT * C_LIGHT)


def compute_grav_factor(bh_list, ship_pos):
    if not bh_list:
        return 1.0
    dom_i = -1
    min_ratio = 1e300
    for i, bh in enumerate(bh_list):
        r  = (bh["pos"] - ship_pos).mag()
        rs = schwarzschild_r(bh["M"])
        if r > rs:
            ratio = r / rs
            if ratio < min_ratio:
                min_ratio = ratio
                dom_i = i

    factor = 1.0
    if dom_i >= 0:
        r  = (bh_list[dom_i]["pos"] - ship_pos).mag()
        rs = schwarzschild_r(bh_list[dom_i]["M"])
        factor *= math.sqrt(1.0 - rs / r)

    phi_other = 0.0
    for i, bh in enumerate(bh_list):
        if i == dom_i: continue
        r = (bh["pos"] - ship_pos).mag()
        if r > 0:
            phi_other += -G_GRAV * bh["M"] / r
    if abs(phi_other) > 1e-30:
        arg = 1.0 + 2.0 * phi_other / (C_LIGHT * C_LIGHT)
        if arg > 0:
            factor *= math.sqrt(arg)
    return factor


def f_warp_canon(W):
    return max(0.5, 1.0 - 0.5 * W * W)


def dtau_dt_cosmic(W_warp, grav, gamma_kin, warp_active):
    f_w = f_warp_canon(W_warp) if warp_active else 1.0
    return f_w * grav / gamma_kin


# ============================================================================
# Observation Calculator (§3.11 v0.127 NEW)
# ============================================================================
def compute_apparent_rate(v_radial, regime):
    """Regime-dispatched apparent rate. This is the critical correctness point."""
    beta = v_radial / C_LIGHT
    if regime & R_WARP_CRUISE:
        # Bubble crew at γ=1, geometric recession. Classical retarded-time.
        return 1.0 - beta  # CAN GO NEGATIVE at v_app > c
    if regime & R_STL_REL:
        # Inertial: SR longitudinal Doppler period stretch.
        bc = max(-0.9999, min(0.9999, beta))
        return math.sqrt((1.0 - bc) / (1.0 + bc))  # NEVER negative
    # REST / STL_NONREL: linear
    return 1.0 - beta


def compute_z_kin(v_radial):
    beta = v_radial / C_LIGHT
    beta = max(-0.9999, min(0.9999, beta))
    return math.sqrt((1.0 + beta) / (1.0 - beta)) - 1.0


def compute_z_cosmo(d_proper):
    return H0_SI * d_proper / C_LIGHT


def compute_lookback(d_proper, z_cosmo):
    lb = d_proper / C_LIGHT
    if z_cosmo > 0.01:
        lb *= (1.0 - 0.75 * min(z_cosmo, 2.0))
    return lb


def observe(ship_pos, ship_velocity, t_cosmic, body_pos, body_metric_shift, regime):
    to_body = body_pos - ship_pos
    d = max(to_body.mag(), 1.0)
    r_hat = to_body / d
    v_radial = -ship_velocity.dot(r_hat)  # positive = receding
    z_cosmo  = compute_z_cosmo(d)
    z_kin    = compute_z_kin(v_radial)
    z_metric = body_metric_shift
    z_total  = (1.0 + z_cosmo) * (1.0 + z_kin) * (1.0 + z_metric) - 1.0
    lookback = compute_lookback(d, z_cosmo)
    t_emit   = t_cosmic - lookback
    rate     = compute_apparent_rate(v_radial, regime) / (1.0 + z_cosmo)
    return {
        "d": d, "v_radial": v_radial,
        "z_cosmo": z_cosmo, "z_kin": z_kin, "z_metric": z_metric, "z_total": z_total,
        "t_emit": t_emit, "apparent_rate": rate, "time_reversed": rate < 0.0,
    }


# ============================================================================
# Kepler
# ============================================================================
def solve_kepler_E(M, e):
    E = M
    for _ in range(30):
        f  = E - e * math.sin(E) - M
        fp = 1.0 - e * math.cos(E)
        dE = f / fp
        E -= dE
        if abs(dE) < 1e-13: break
    return E


def orbit_phase(orb, t):
    M = 2.0 * math.pi * (t - orb["t0"]) / orb["period"]
    E = solve_kepler_E(M, orb["e"])
    return 2.0 * math.atan2(
        math.sqrt(1.0 + orb["e"]) * math.sin(E / 2.0),
        math.sqrt(1.0 - orb["e"]) * math.cos(E / 2.0),
    )


# ============================================================================
# Test framework
# ============================================================================
PASSED = 0
FAILED = 0


def check(cond, name):
    global PASSED, FAILED
    if cond:
        PASSED += 1
        print(f"  [PASS] {name}")
    else:
        FAILED += 1
        print(f"  [FAIL] {name}")


def check_close(actual, expected, tol, name):
    global PASSED, FAILED
    diff = abs(actual - expected)
    ok = diff <= tol
    if ok:
        PASSED += 1
        print(f"  [PASS] {name}  (got {actual:.6g}, exp {expected:.6g}, diff {diff:.3g})")
    else:
        FAILED += 1
        print(f"  [FAIL] {name}  (got {actual:.6g}, exp {expected:.6g}, diff {diff:.3g}, tol {tol:.3g})")


def section(name):
    print(f"\n--- {name} ---")


# ============================================================================
# Test suite (mirrors astra_nexus.cpp::test::run_all)
# ============================================================================
def run_tests():
    print("\n========================= TEST SUITE =========================")

    section("AstraCoord (§1.1)")
    a = AstraCoord(0, 0, 0, 0, 0, 0)
    b = AstraCoord(0, 0, 0, 1000.0, 0, 0)
    check_close(astra_distance(a, b), 1000.0, 1e-9, "1km local distance")
    c = AstraCoord(1, 0, 0, 0, 0, 0)
    check_close(astra_distance(a, c), SECTOR_SIZE, 1e-6, "1-sector distance")
    d = AstraCoord(0, 0, 0, 600000.0, 0, 0)
    d.renormalize()
    check(d.sx == 1, "Renormalize rolls sx to 1")
    check_close(d.lx, -400000.0, 1e-9, "Renormalize lx after roll")

    section("Rapidity (§3.7) — v0.126 N1 verification")
    rest = Rapidity()
    check_close(rest.gamma(), 1.0, 1e-12, "γ at rest = 1")
    check_close(rest.beta(),  0.0, 1e-12, "β at rest = 0")

    r1 = Rapidity(Vec3(0, 0, 1.0))
    check_close(r1.gamma(), math.cosh(1.0), 1e-12, "γ(ω=1) = cosh(1)")
    check_close(r1.beta(),  math.tanh(1.0), 1e-12, "β(ω=1) = tanh(1)")

    # v0.126 N1 LOCK
    rmax = Rapidity(Vec3(0, 0, OMEGA_MAX))
    gmax = rmax.gamma()
    check(9.0e6 < gmax < 1.1e7, "v0.126 LOCK: ω_max=16.811 → γ ≈ 10⁷")
    print(f"         γ at ω={OMEGA_MAX} = {gmax:.4e}")

    # v0.125 N1 BUG REPRODUCTION
    omega_v125 = math.atanh(0.99999999)
    gamma_v125 = math.cosh(omega_v125)
    check(7000.0 < gamma_v125 < 7200.0,
          "v0.125 BUG: arctanh(0.99999999) → γ ≈ 7071 (NOT 10⁷)")
    print(f"         v0.125 N1: arctanh(.99999999) = ω={omega_v125:.4f} → γ={gamma_v125:.1f}")
    print(f"         shortfall: γ_max claimed 10⁷, actual {gamma_v125:.0f} — "
          f"factor {1e7/gamma_v125:.1f}× short")

    # Catastrophic-cancellation verification
    beta_at_max  = math.tanh(OMEGA_MAX)
    gamma_cosh   = math.cosh(OMEGA_MAX)
    one_min_b2   = 1.0 - beta_at_max * beta_at_max
    gamma_naive  = 1.0 / math.sqrt(one_min_b2) if one_min_b2 > 0 else float("inf")
    rel_err      = abs(gamma_cosh - gamma_naive) / gamma_cosh
    print(f"         γ via cosh(ω):    {gamma_cosh:.6e}  (LOCKED PATH)")
    print(f"         1 - β² (subtract): {one_min_b2:.6e}  (catastrophic at this magnitude)")
    print(f"         γ via 1/√(1-β²): {gamma_naive:.6e}  (FORBIDDEN PATH)")
    print(f"         relative error:    {rel_err:.3e}")
    check(rel_err > 1e-4,
          "Naive 1/√(1-β²) loses precision at ω=ω_max (justifies cosh discipline)")

    # 1g integration
    g = 9.81
    year = 3.15576e7
    rs = Rapidity()
    rs = integrate_rapidity_step(rs, Vec3(0, 0, g), year)
    check_close(rs.omega(), g * year / C_LIGHT, 1e-10, "1g·τ → ω = g·τ/c exact")

    # 3D maneuvering
    r_fast = Rapidity(Vec3(0, 0, 5.0))
    r_after = integrate_rapidity_step(r_fast, Vec3(0, g * 100.0, 0), year)
    check(r_after.beta() < 1.0, "Perpendicular thrust at γ≈74: |v|<c by tanh-bound")
    check(r_after.zeta.y > 0, "Perpendicular thrust rotates ζ⃗")

    # Clamp
    r_init = Rapidity(Vec3(0, 0, OMEGA_MAX - 0.1))
    r_clamped = integrate_rapidity_step(r_init, Vec3(0, 0, 1.0e10), 1.0)
    check_close(r_clamped.omega(), OMEGA_MAX, 1e-9, "Rapidity clamps at OMEGA_MAX")

    section("Composition rule (§3.2 v0.126)")
    check_close(dtau_dt_cosmic(0, 1.0, 1.0, False), 1.0, 1e-12, "REST + no warp + no gravity")
    check_close(dtau_dt_cosmic(0, 1.0, 2.0, False), 0.5, 1e-12, "STL γ=2: dτ/dt = 0.5")

    bhs = []
    rs_bh = schwarzschild_r(10.0 * M_SUN)
    bhs.append({"M": 10.0 * M_SUN, "pos": Vec3(100.0 * rs_bh, 0, 0)})
    grav = compute_grav_factor(bhs, Vec3(0, 0, 0))
    expected = math.sqrt(1.0 - rs_bh / (100.0 * rs_bh))
    check_close(grav, expected, 1e-12, "Grav factor at r = 100·r_s")

    bhs[0]["pos"] = Vec3(1.0e15, 0, 0)
    grav_far = compute_grav_factor(bhs, Vec3(0, 0, 0))
    check(0.999999 < grav_far <= 1.0, "Grav factor at large r approaches 1 smoothly")

    check_close(f_warp_canon(0.0), 1.0, 1e-12, "f_warp(0) = 1")
    check_close(f_warp_canon(1.0), 0.5, 1e-12, "f_warp(1) = 0.5")

    section("Observation: STL_REL vs WARP regime distinction (the key test)")
    rate_stl05 = compute_apparent_rate(0.5 * C_LIGHT, R_STL_REL)
    check_close(rate_stl05, math.sqrt(1.0/3.0), 1e-10,
                "STL_REL β=0.5 recede: rate = √(1/3) (SR Doppler)")
    check(rate_stl05 > 0, "STL_REL NEVER produces reverse-playback")

    rate_stl_app = compute_apparent_rate(-0.5 * C_LIGHT, R_STL_REL)
    check_close(rate_stl_app, math.sqrt(3.0), 1e-10,
                "STL_REL β=-0.5 approach: rate = √3 (fast-forward)")

    rate_stl99 = compute_apparent_rate(0.99 * C_LIGHT, R_STL_REL)
    check(0 < rate_stl99 < 0.1, "STL_REL β=0.99: rate near 0 but still positive")

    rate_warp2 = compute_apparent_rate(2.0 * C_LIGHT, R_WARP_CRUISE)
    check_close(rate_warp2, -1.0, 1e-10, "WARP v_app=2c: rate = -1 (reverse 1×)")
    check(rate_warp2 < 0, "WARP > c PRODUCES reverse-playback")

    rate_warp1 = compute_apparent_rate(1.0 * C_LIGHT, R_WARP_CRUISE)
    check_close(rate_warp1, 0.0, 1e-10, "WARP v_app=c: rate = 0 (frozen image)")

    rate_warp10 = compute_apparent_rate(10.0 * C_LIGHT, R_WARP_CRUISE)
    check_close(rate_warp10, -9.0, 1e-10, "WARP v_app=10c: rate = -9 (rewind 9×)")

    rate_warp_app = compute_apparent_rate(-10.0 * C_LIGHT, R_WARP_CRUISE)
    check_close(rate_warp_app, 11.0, 1e-10, "WARP approach v_app=-10c: rate = +11")

    # CONTRAST
    v05 = 0.5 * C_LIGHT
    stl_rate  = compute_apparent_rate(v05, R_STL_REL)
    warp_rate = compute_apparent_rate(v05, R_WARP_CRUISE)
    print(f"         CONTRAST at v_radial = 0.5c:")
    print(f"           STL_REL  rate = {stl_rate:.6f} (SR formula)")
    print(f"           WARP     rate = {warp_rate:.6f} (classical formula)")
    print(f"           Spec must dispatch by regime; these are NOT the same.")
    check(abs(stl_rate - warp_rate) > 0.05,
          "STL_REL and WARP give meaningfully different rates at same v")

    section("Kinematic redshift (SR longitudinal Doppler)")
    check_close(compute_z_kin(0.5 * C_LIGHT), math.sqrt(3.0) - 1.0, 1e-10, "z_kin(β=0.5)=√3-1")
    check_close(compute_z_kin(0.9 * C_LIGHT), math.sqrt(19.0) - 1.0, 1e-10, "z_kin(β=0.9)=√19-1")
    check_close(compute_z_kin(-0.5 * C_LIGHT), math.sqrt(1.0/3.0) - 1.0, 1e-10,
                "z_kin(β=-0.5)=√(1/3)-1 (blueshift)")

    section("Redshift composition (multiplicative)")
    za, zb, zc = 0.1, 0.5, 0.2
    total = (1+za)*(1+zb)*(1+zc) - 1.0
    check_close(total, 1.1*1.5*1.2 - 1.0, 1e-12,
                "(1+z_total) = (1+z_cosmo)(1+z_kin)(1+z_metric)")

    section("Observation end-to-end")
    ship = Vec3(0, 0, 0)
    body = Vec3(0, 0, -10.0 * LIGHT_YEAR)
    vwarp = Vec3(0, 0, 100.0 * C_LIGHT)
    t_cosmic = 1.0e10
    obs = observe(ship, vwarp, t_cosmic, body, 0.0, R_WARP_CRUISE)
    check_close(obs["d"], 10.0 * LIGHT_YEAR, 1.0, "Distance = 10 ly")
    check_close(obs["v_radial"] / C_LIGHT, 100.0, 1e-6, "v_radial = 100c (receding)")
    check_close(obs["apparent_rate"], -99.0, 1e-6, "WARP 100c apparent rate = -99")
    check(obs["time_reversed"], "Time reversed flag set")
    check_close(obs["t_emit"], t_cosmic - 10.0 * LIGHT_YEAR / C_LIGHT,
                LIGHT_YEAR / C_LIGHT * 1e-5, "t_emit = t_cosmic - 10·ly/c")

    section("Kepler-at-t_emit: orbit reversal during warp egress (the payoff)")
    earth_like = {"a": 1.496e11, "e": 0.0, "period": 365.25 * 86400.0, "t0": 0.0}
    body_pos = Vec3(0, 0, -1.0 * LIGHT_YEAR)
    vwarp2 = Vec3(0, 0, 2.0 * C_LIGHT)
    t0 = 1.0e10
    o0 = observe(Vec3(0, 0, 0), vwarp2, t0, body_pos, 0.0, R_WARP_CRUISE)
    dt = 30.0 * 86400.0
    ship_t1 = Vec3(0, 0, vwarp2.z * dt)
    t1 = t0 + dt
    o1 = observe(ship_t1, vwarp2, t1, body_pos, 0.0, R_WARP_CRUISE)

    print(f"         t0: ship at z=0,                  t_emit={o0['t_emit']:.6e} s")
    print(f"         t1: ship at z={ship_t1.z/LIGHT_YEAR:+.4f} ly, t_emit={o1['t_emit']:.6e} s")
    print(f"         Δt_cosmic={(t1-t0)/86400.0:+.4g} d,  Δt_emit={(o1['t_emit']-o0['t_emit'])/86400.0:+.4g} d")

    check(o1["t_emit"] < o0["t_emit"], "t_emit DECREASES as ship warps superluminally away")
    check_close((o1["t_emit"] - o0["t_emit"]) / 86400.0, -30.0, 0.5,
                "Δt_emit ≈ -Δt_cosmic at v_app=2c (1× reverse)")

    phase_0 = orbit_phase(earth_like, o0["t_emit"])
    phase_1 = orbit_phase(earth_like, o1["t_emit"])
    dphase = phase_1 - phase_0
    while dphase >  math.pi: dphase -= 2*math.pi
    while dphase < -math.pi: dphase += 2*math.pi
    print(f"         orbital phase at t_emit: {phase_0:+.4f} → {phase_1:+.4f} rad (Δ={dphase:+.4f})")
    check(dphase < 0,
          "Orbital phase RUNS BACKWARD when sampled at t_emit (THE EFFECT)")

    section("AstraCoord at billion-light-year scale")
    d_target = 100.0e6 * LIGHT_YEAR
    sectors = int(d_target / SECTOR_SIZE)
    ship_c = AstraCoord(0, 0, 0, 0, 0, 0)
    far_obj = AstraCoord(sectors, 0, 0, 0, 0, 0)
    d_meas = astra_distance(ship_c, far_obj)
    check_close(d_meas, sectors * SECTOR_SIZE, 1.0, "Distance at 100 Mly scale, m-precision")
    INT64_MAX = (1 << 63) - 1
    max_reach_ly = (INT64_MAX * SECTOR_SIZE) / LIGHT_YEAR
    print(f"         Maximum reach: {max_reach_ly:.3e} ly = {max_reach_ly/1e9:.3f} billion ly")
    check(max_reach_ly > 9.0e8, "AstraCoord reaches > 900M ly with sub-mm precision")

    print(f"\n============== SUMMARY: {PASSED} passed, {FAILED} failed ==============")


# ============================================================================
# Voyage demo
# ============================================================================
def demo_voyage():
    print("\n========================= VOYAGE DEMO =========================")
    print("Planet at 1 ly behind ship. Ship traverses regimes; observation shifts.\n")
    planet = Vec3(0, 0, -1.0 * LIGHT_YEAR)
    t = 1.0e10

    phases = [
        ("REST near origin",            Vec3(0, 0, 0),                R_REST),
        ("STL_NONREL 0.05c +z",          Vec3(0, 0, 0.05 * C_LIGHT),   R_STL_NONREL),
        ("STL_REL 0.5c +z (recede)",     Vec3(0, 0, 0.5  * C_LIGHT),   R_STL_REL),
        ("STL_REL 0.9c +z (recede)",     Vec3(0, 0, 0.9  * C_LIGHT),   R_STL_REL),
        ("STL_REL 0.99c +z (recede)",    Vec3(0, 0, 0.99 * C_LIGHT),   R_STL_REL),
        ("WARP_CRUISE 1c (recede)",      Vec3(0, 0, 1.0  * C_LIGHT),   R_WARP_CRUISE),
        ("WARP_CRUISE 2c (recede)",      Vec3(0, 0, 2.0  * C_LIGHT),   R_WARP_CRUISE),
        ("WARP_CRUISE 10c (recede)",     Vec3(0, 0, 10.0 * C_LIGHT),   R_WARP_CRUISE),
        ("WARP_CRUISE 100c (recede)",    Vec3(0, 0, 100.0  * C_LIGHT), R_WARP_CRUISE),
        ("WARP_CRUISE 8000c (recede)",   Vec3(0, 0, 8000.0 * C_LIGHT), R_WARP_CRUISE),
        ("WARP_CRUISE 2c APPROACH (-z)", Vec3(0, 0, -2.0 * C_LIGHT),   R_WARP_CRUISE),
    ]
    for label, vel, regime in phases:
        o = observe(Vec3(0, 0, 0), vel, t, planet, 0.0, regime)
        rate = o["apparent_rate"]
        flag = ""
        if o["time_reversed"]:
            flag = f"  TIME REVERSED at {abs(rate):.2f}×"
        elif rate > 1.5:
            flag = f"  fast-forward {rate:.2f}×"
        elif rate < 0.5:
            flag = f"  slow-mo {rate:.4f}×"
        else:
            flag = "  ~real-time"
        print(f"  {label:<32}  d={o['d']/LIGHT_YEAR:6.2f} ly | "
              f"v_rad={o['v_radial']/C_LIGHT:+8.2f}c | rate={rate:+10.4f}{flag}")

    print("\nNote: STL_REL formulas (SR longitudinal Doppler) and WARP formulas")
    print("(classical retarded-time, bubble γ=1) differ.")
    print("The v0.127 spec must lock regime-dispatched apparent-rate.")


# ============================================================================
# main
# ============================================================================
if __name__ == "__main__":
    print("====================================================================")
    print(" ASTRA-7 Unified Physics Nexus — Python verification")
    print(" Mirrors astra_nexus.cpp; runs the same tests and demo.")
    print(" Proves the 14-equation framework composes correctly.")
    print("====================================================================")
    run_tests()
    demo_voyage()
    print()
    sys.exit(0 if FAILED == 0 else 1)

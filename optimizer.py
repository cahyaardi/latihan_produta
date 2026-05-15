"""
optimizer.py — Backend CVRP-MILP dengan OSRM
Digunakan oleh app.py (Optimasi Distribusi)
"""

from __future__ import annotations
import time
import math
import requests
import pulp

# ─────────────────────────────────────────────────────────
# KONSTANTA DEPOT
# ─────────────────────────────────────────────────────────
DEPOT_NAME = "Pabrik"
DEPOT_LAT  = -6.513258
DEPOT_LON  = 106.856054


# ─────────────────────────────────────────────────────────
# JARAK
# ─────────────────────────────────────────────────────────
def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Jarak Haversine (km) sebagai fallback."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dlon / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(a))


def osrm_distance(coord1: tuple, coord2: tuple, timeout: int = 8) -> float:
    """
    Jarak jalan nyata via OSRM public API (km).
    coord format: (lat, lon)
    Fallback ke Haversine jika OSRM tidak tersedia.
    """
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    url = (f"http://router.project-osrm.org/route/v1/driving/"
           f"{lon1},{lat1};{lon2},{lat2}?overview=false")
    try:
        r = requests.get(url, timeout=timeout)
        data = r.json()
        if "routes" in data and data["routes"]:
            return data["routes"][0]["distance"] / 1000.0
    except Exception:
        pass
    return haversine(lat1, lon1, lat2, lon2)


def build_distance_matrix(
    df_nodes,
    use_osrm: bool = True,
    osrm_delay: float = 0.07,
    progress_callback=None,
) -> list[list[float]]:
    """
    Bangun matriks jarak n×n.

    Parameters
    ----------
    df_nodes : DataFrame dengan kolom Lat, Lon (baris 0 = depot)
    use_osrm : True → pakai OSRM, False → Haversine
    osrm_delay : jeda antar request (detik) agar tidak kena rate-limit
    progress_callback : callable(float 0–1) untuk progress bar opsional
    """
    n = len(df_nodes)
    coords = [(df_nodes.loc[i, "Lat"], df_nodes.loc[i, "Lon"]) for i in range(n)]
    mat = [[0.0] * n for _ in range(n)]
    total = n * n
    done = 0

    for i in range(n):
        for j in range(n):
            if i != j:
                if use_osrm:
                    mat[i][j] = osrm_distance(coords[i], coords[j])
                    time.sleep(osrm_delay)
                else:
                    mat[i][j] = haversine(*coords[i], *coords[j])
            done += 1
            if progress_callback:
                progress_callback(min(done / total, 1.0))

    return mat


# ─────────────────────────────────────────────────────────
# MILP CVRP dengan MTZ Subtour Elimination
# ─────────────────────────────────────────────────────────
def run_cvrp_milp(
    df_nodes,
    dist_mat: list[list[float]],
    n_vehicles: int,
    capacity: int,
    max_stops: int,
    time_limit: int = 120,
) -> dict:
    """
    Selesaikan CVRP menggunakan MILP (PuLP CBC) dengan MTZ.

    Parameters
    ----------
    df_nodes   : DataFrame kolom [Destination, Lat, Lon, Demand], baris 0 = depot
    dist_mat   : matriks jarak n×n
    n_vehicles : jumlah kendaraan
    capacity   : kapasitas per kendaraan (unit)
    max_stops  : maks stop per kendaraan (tidak termasuk depot)
    time_limit : batas waktu solver (detik)

    Returns
    -------
    dict dengan kunci:
        status       : str  (Optimal / Infeasible / …)
        objective    : float jarak total
        routes_idx   : list[list[int]]   urutan index node per kendaraan
        routes_name  : list[list[str]]   urutan nama destinasi per kendaraan
        solver_log   : str
    """
    nodes     = list(range(len(df_nodes)))
    customers = nodes[1:]
    vehicles  = list(range(n_vehicles))

    mdl = pulp.LpProblem("CVRP_MTZ", pulp.LpMinimize)

    # ── Variabel keputusan ─────────────────────────────
    x = pulp.LpVariable.dicts("x", (nodes, nodes, vehicles), 0, 1, pulp.LpBinary)
    u = pulp.LpVariable.dicts("u", customers, 1, len(customers), pulp.LpContinuous)

    # ── Fungsi objektif: minimasi total jarak ──────────
    mdl += pulp.lpSum(
        dist_mat[i][j] * x[i][j][k]
        for i in nodes for j in nodes for k in vehicles if i != j
    )

    # ── Constraint 1: setiap customer dikunjungi tepat 1x ──
    for j in customers:
        mdl += pulp.lpSum(
            x[i][j][k] for i in nodes for k in vehicles if i != j
        ) == 1

    # ── Constraint 2: flow conservation ──────────────────
    for k in vehicles:
        for h in nodes:
            mdl += (
                pulp.lpSum(x[h][j][k] for j in nodes if h != j) ==
                pulp.lpSum(x[j][h][k] for j in nodes if j != h)
            )

    # ── Constraint 3: setiap kendaraan berangkat & kembali ke depot ──
    for k in vehicles:
        mdl += pulp.lpSum(x[0][j][k] for j in customers) == 1
        mdl += pulp.lpSum(x[i][0][k] for i in customers) == 1

    # ── Constraint 4: kapasitas ──────────────────────────
    for k in vehicles:
        mdl += pulp.lpSum(
            df_nodes.loc[i, "Demand"] * pulp.lpSum(x[i][j][k] for j in nodes if i != j)
            for i in customers
        ) <= capacity

    # ── Constraint 5: maks stop per kendaraan ────────────
    for k in vehicles:
        mdl += pulp.lpSum(
            pulp.lpSum(x[i][j][k] for j in nodes if i != j)
            for i in customers
        ) <= max_stops

    # ── Constraint 6: MTZ subtour elimination ────────────
    N = len(customers)
    for k in vehicles:
        for i in customers:
            for j in customers:
                if i != j:
                    mdl += u[i] - u[j] + N * x[i][j][k] <= N - 1

    # ── Solve ──────────────────────────────────────────────
    solver = pulp.PULP_CBC_CMD(msg=0, timeLimit=time_limit)
    mdl.solve(solver)

    status  = pulp.LpStatus[mdl.status]
    obj_val = pulp.value(mdl.objective) or 0.0
    solver_log = (
        f"Status: {status} | Objective: {round(obj_val, 3)} km | "
        f"Nodes: {len(nodes)} | Vehicles: {n_vehicles} | "
        f"Time limit: {time_limit}s"
    )

    # ── Ekstrak rute ───────────────────────────────────────
    if mdl.status not in (1, -1, -2):
        return {
            "status": status, "objective": 0.0,
            "routes_idx": [], "routes_name": [],
            "solver_log": solver_log,
        }

    routes_idx, routes_name = [], []
    for k in vehicles:
        adj = {}
        for i in nodes:
            for j in nodes:
                if i == j:
                    continue
                val = pulp.value(x[i][j][k])
                if val is not None and val > 0.5:
                    adj[i] = j

        if 0 not in adj:
            continue

        route, cur = [0], 0
        for _ in range(len(nodes)):
            nxt = adj.get(cur)
            if nxt is None or nxt == 0:
                break
            route.append(nxt)
            cur = nxt
        route.append(0)

        if len(route) > 2:
            routes_idx.append(route)
            routes_name.append([df_nodes.loc[i, "Destination"] for i in route])

    return {
        "status": status,
        "objective": round(obj_val, 3),
        "routes_idx": routes_idx,
        "routes_name": routes_name,
        "solver_log": solver_log,
    }


# ─────────────────────────────────────────────────────────
# STATISTIK RUTE
# ─────────────────────────────────────────────────────────
def compute_route_stats(
    routes_idx: list[list[int]],
    routes_name: list[list[str]],
    df_nodes,
    dist_mat: list[list[float]],
    capacity: int,
    truck_colors: list[str],
    avg_speed_kmh: float = 40.0,
) -> list[dict]:
    """
    Hitung statistik per rute: jarak, muatan, utilisasi, estimasi waktu.

    Returns list of dict per kendaraan.
    """
    stats = []
    for k, (ridx, rname) in enumerate(zip(routes_idx, routes_name)):
        dist = sum(dist_mat[ridx[i]][ridx[i + 1]] for i in range(len(ridx) - 1))
        stops = [n for n in rname if n != DEPOT_NAME]
        load  = int(df_nodes[df_nodes["Destination"].isin(stops)]["Demand"].sum())
        util  = round(load / capacity * 100, 1)
        est_m = int(dist / avg_speed_kmh * 60) if dist > 0 else 0

        stats.append({
            "vehicle":      k + 1,
            "route_idx":    ridx,
            "route_name":   rname,
            "stops":        len(stops),
            "load":         load,
            "distance_km":  round(dist, 2),
            "util_pct":     util,
            "est_min":      est_m,
            "color":        truck_colors[k % len(truck_colors)],
        })
    return stats

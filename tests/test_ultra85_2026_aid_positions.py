#!/usr/bin/env python3
"""Organizer 2026 ultra depots are distinct from EQ Timing station metadata.

No raw participant GPS, private FIT or personally identifying data is stored.
"""
import json,math,unittest
from pathlib import Path

DATA=Path(__file__).resolve().parents[1]/"docs/data"
DEPOTS=[("Navåsen",22.7),("Helsjön",37.8),("Äskhult",54.6),
        ("Fjärås",63.4),("Lerbäck",72.8),("Ramhultafallet",81.4)]

def haversine(lat1,lon1,lat2,lon2):
    a,b,c,d=map(math.radians,(lat1,lon1,lat2,lon2))
    s=math.sin((c-a)/2)**2+math.cos(a)*math.cos(c)*math.sin((d-b)/2)**2
    return 12742000*math.asin(min(1,math.sqrt(s)))

class UltraAidPositions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.route=json.loads((DATA/"routes/ultra85-2026.json").read_text(encoding="utf-8"))
        cls.race=json.loads((DATA/"races/2026-ultra85.json").read_text(encoding="utf-8"))
        cls.stops=cls.route["aid_stations"]

    def test_six_verified_organizer_distances_keep_order_and_gpx_alignment(self):
        self.assertEqual([(s["name"],s["official_km"]) for s in self.stops],DEPOTS)
        distances=[s["route_km"] for s in self.stops]
        self.assertEqual(distances,sorted(distances))
        self.assertEqual(len(distances),len(set(distances)))
        self.assertLess(distances[-1],self.route["points"][-1][0])
        for stop in self.stops:
            self.assertLess(abs(stop["route_km"]-stop["official_km"]),0.35)
            # A depot can lie between GPX samples. Interpolated distance is
            # more accurate than demanding a vertex at the exact GPS position.
            self.assertLess(min(abs(p[0]-stop["route_km"]) for p in self.route["points"]),0.1)
            self.assertLess(stop["snap_distance_m"],90)
            if stop["name"]!="Ramhultafallet":
                self.assertNotIn("gps_lat",stop)
                self.assertNotIn("gps_lon",stop)

    def test_five_private_laps_and_owner_confirmed_ramhulta_coordinate(self):
        for stop in self.stops[:5]:
            self.assertEqual(stop["position_basis"],"fit_lap_snapped_to_official_route")
            self.assertLess(stop["snap_distance_m"],40)
        stop=self.stops[-1]
        self.assertEqual(stop["position_basis"],"owner_confirmed_depot_wgs84_coordinate")
        self.assertAlmostEqual(stop["official_km"],81.4)
        self.assertAlmostEqual(stop["route_km"],81.375893,places=5)
        self.assertAlmostEqual(stop["gps_lat"],57.51190,places=5)
        self.assertAlmostEqual(stop["gps_lon"],12.38534,places=5)
        self.assertLess(stop["snap_distance_m"],2)
        # The screenshot is a depå coordinate, NOT the nearby waterfall
        # landmark. The precise point lies between two GPX vertices.
        R=6371000
        lat,lon=stop["gps_lat"],stop["gps_lon"]
        scale=math.cos(math.radians(lat))
        def xy(point):
            return ((point[2]-lon)*math.pi/180*R*scale,
                    (point[1]-lat)*math.pi/180*R)
        closest=None
        for a,b in zip(self.route["points"],self.route["points"][1:]):
            x1,y1=xy(a);x2,y2=xy(b)
            dx,dy=x2-x1,y2-y1
            f=max(0,min(1,-(x1*dx+y1*dy)/max(1e-9,dx*dx+dy*dy)))
            separation=math.hypot(x1+f*dx,y1+f*dy)
            km=a[0]+f*(b[0]-a[0])
            if closest is None or separation<closest[0]:
                closest=(separation,km)
        self.assertLess(closest[0],2)
        self.assertLess(abs(closest[1]-stop["route_km"]),0.002)

    def test_same_original_eq_stations_and_observation_coverage(self):
        stations=self.race["stations"]
        by_name={s["name"]:s for s in stations}
        self.assertEqual(by_name["Äskhult"]["km"],50)
        self.assertEqual(by_name["Navåsen"]["km"],19.4)
        self.assertEqual(by_name["Lerbäck"]["km"],68)
        self.assertEqual(by_name["Ramhulta"]["km"],78.7)
        self.assertEqual(len(stations),8)
        self.assertNotIn("Helsjön",by_name)
        self.assertNotIn("Fjärås",by_name)
        self.assertNotIn("aid_stations",self.race)
        for stop in self.stops:
            if stop["name"] in ("Helsjön","Fjärås"):
                self.assertNotIn("timing_km",stop)

if __name__=="__main__":unittest.main()

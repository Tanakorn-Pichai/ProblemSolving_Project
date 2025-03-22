import networkx as nx
import matplotlib.pyplot as plt
import geopandas as gpd
from geopy.distance import geodesic
from matplotlib.widgets import CheckButtons

class InteractiveAsiaGraph:
    def __init__(self):
        self.graph = nx.Graph()
        self.countries = {}
        self.ports = {
            "Japan": (35.6586, 139.7454),
            "South Korea": (35.1796, 129.0756),
            "Philippines": (14.6091, 120.9803),
            "Indonesia": (-6.1177, 106.9069),
            "Thailand": (13.0878, 100.9108),
            "Vietnam": (10.7757, 106.7011),
            "Sri Lanka": (6.9568, 79.8577),
            "Taiwan": (25.1500, 121.7667)
        }
        self.airports = {
            "Japan": (35.5523, 139.7798),
            "South Korea": (37.4602, 126.4407),
            "Philippines": (14.5086, 121.0198),
            "Indonesia": (-6.1256, 106.6559),
            "Thailand": (13.6894, 100.7500),
            "Vietnam": (21.2212, 105.8106),
            "Sri Lanka": (7.1808, 79.8840),
            "Taiwan": (25.0777, 121.2320)
        }
        self.load_asian_countries()
        self.add_borders()
        self.add_sea_and_air_routes()
        self.show_land = True
        self.show_sea = True
        self.show_air = True

        self.fig, self.ax = plt.subplots(figsize=(12, 10))
        plt.subplots_adjust(left=0.2)
        self.add_checkbuttons()

    def load_asian_countries(self):
        world = gpd.read_file("./ne_110m_admin_0_countries/ne_110m_admin_0_countries.shp")
        asia = world[world['CONTINENT'] == 'Asia']
        for _, row in asia.iterrows():
            country_name = row["NAME"]
            centroid = row["geometry"].centroid
            lat, lon = centroid.y, centroid.x
            self.countries[country_name] = (lat, lon)
            self.graph.add_node(country_name, pos=(lon, lat))

    def add_borders(self):
        world = gpd.read_file("./ne_110m_admin_0_countries/ne_110m_admin_0_countries.shp")
        asia = world[world['CONTINENT'] == 'Asia']
        for _, row in asia.iterrows():
            country_name = row["NAME"]
            if country_name not in self.countries:
                continue
            neighbors = asia[asia.touches(row["geometry"])]
            for _, neighbor in neighbors.iterrows():
                neighbor_name = neighbor["NAME"]
                if neighbor_name in self.countries:
                    coord1 = self.countries[country_name]
                    coord2 = self.countries[neighbor_name]
                    distance = geodesic(coord1, coord2).kilometers
                    self.graph.add_edge(country_name, neighbor_name, weight=round(distance, 1))  # ปัดเศษทศนิยม 1 ตำแหน่ง

    def add_sea_and_air_routes(self):
        for country1, port1 in self.ports.items():
            for country2, port2 in self.ports.items():
                if country1 != country2:
                    distance = geodesic(port1, port2).kilometers
                    if distance < 5000:
                        self.graph.add_edge(country1, country2, weight=round(distance, 1))  
        for country1, airport1 in self.airports.items():
            for country2, airport2 in self.airports.items():
                if country1 != country2:
                    distance = geodesic(airport1, airport2).kilometers
                    if distance < 8000:
                        self.graph.add_edge(country1, country2, weight=round(distance, 1))  

    def draw_graph(self):
        """ฟังก์ชั่นวาดกราฟ และอัปเดตเมื่อมีการเปลี่ยนแปลง"""
        self.ax.clear()
        self.fig.set_size_inches(14, 12) 
         

        pos = nx.get_node_attributes(self.graph, 'pos')
        pos = nx.spring_layout(self.graph, k=15, seed=42)

        # **วาดโหนดใหม่ทุกครั้งหลังจากเคลียร์**
        nx.draw_networkx_nodes(self.graph, pos, node_size=300, node_color="blue", ax=self.ax)
            # **สร้าง mapping ตัวเลขแทนชื่อประเทศ**
        country_list = list(self.graph.nodes)
        country_map = {country: str(i + 1) for i, country in enumerate(country_list)}

        # **แทนที่ label ของโหนดเป็นตัวเลข**
        node_labels = {node: country_map[node] for node in self.graph.nodes}
        nx.draw_networkx_labels(self.graph, pos, labels=node_labels,font_color="white", font_size=10, ax=self.ax)
        # เอาเฉพาะเส้นที่ต้องการแสดง
        land_edges = [(u, v) for u, v, d in self.graph.edges(data=True) if d["weight"] < 2000]
        sea_edges = [(u, v) for u, v, d in self.graph.edges(data=True) if d["weight"] >= 2000 and u in self.ports]
        air_edges = [(u, v) for u, v, d in self.graph.edges(data=True) if d["weight"] >= 2000 and u in self.airports]

        active_edges = []
        # วาดเฉพาะเส้นที่ต้องการ
        if self.show_land:
            nx.draw_networkx_edges(self.graph, pos, edgelist=land_edges, edge_color="brown",
                                width=[max(1, 10 - (d["weight"] / 5)) for u, v, d in self.graph.edges(data=True) if (u, v) in land_edges], ax=self.ax)
            active_edges.extend(land_edges)

        if self.show_sea:
            nx.draw_networkx_edges(self.graph, pos, edgelist=sea_edges, edge_color="blue",
                                width=[max(1, 10 - (d["weight"] / 5)) for u, v, d in self.graph.edges(data=True) if (u, v) in sea_edges], ax=self.ax)
            active_edges.extend(sea_edges)

        if self.show_air:
            nx.draw_networkx_edges(self.graph, pos, edgelist=air_edges, edge_color="green",
                                width=[max(1, 10 - (d["weight"] / 5)) for u, v, d in self.graph.edges(data=True) if (u, v) in air_edges], ax=self.ax)
            active_edges.extend(air_edges)
        # **ลบข้อความระยะทางออก**
        if self.show_land or self.show_sea or self.show_air:
            edge_labels = {k: f"{d['weight']} km" for k, d in self.graph.edges.items() if k in active_edges}
            nx.draw_networkx_edge_labels(self.graph, pos, edge_labels=edge_labels, font_size=5, ax=self.ax)

        
        plt.draw()



    def add_checkbuttons(self):
        ax_check = plt.axes([0.02, 0.4, 0.15, 0.15])  # ตำแหน่งปุ่ม
        self.check = CheckButtons(ax_check, ['Land', 'Sea', 'Air', 'Table'], 
                                [self.show_land, self.show_sea, self.show_air, False])
        
        def toggle(label):
            if label == 'Land':
                self.show_land = not self.show_land
            elif label == 'Sea':
                self.show_sea = not self.show_sea
            elif label == 'Air':
                self.show_air = not self.show_air
            elif label == 'Table':  # ถ้ากดปุ่ม Table ให้แสดงตาราง
                self.draw_table()
            self.draw_graph()  # อัปเดตกราฟใหม่
        
        self.check.on_clicked(toggle)


    def show(self):
        """แสดงกราฟ"""
        self.draw_graph()
        plt.show()  # ใช้ plt.show() ที่นี่เพื่อให้ UI ทำงาน
    def draw_table(self):
        """สร้างหน้าต่างแสดงตารางแยกจากกราฟ"""

        # ดึงข้อมูลประเทศจากโหนด และสร้าง mapping เป็นตัวเลข
        country_list = list(self.graph.nodes)
        country_map = {country: str(i + 1) for i, country in enumerate(country_list)}

        # สร้างข้อมูลสำหรับตาราง
        data = [[num, name] for name, num in country_map.items()]
        columns = ["No.", "Country"]

        # สร้างหน้าต่างแสดงตาราง
        fig = plt.figure(figsize=(5, len(data) * 0.5))  # ปรับขนาดตามจำนวนข้อมูล
        ax = fig.add_subplot(111, frame_on=False)  # ไม่มีกรอบ

        # สร้างตาราง
        table = ax.table(cellText=data, colLabels=columns, loc="center", cellLoc="center")
        
        # ปรับขนาดตัวอักษร และสเกล
        table.auto_set_font_size(True)
        table.set_fontsize(10)
        table.scale(2, 2)

        # ซ่อนแกน
        ax.xaxis.set_visible(False)
        ax.yaxis.set_visible(False)

        plt.show()

# เรียกใช้งาน
graph = InteractiveAsiaGraph()
graph.show()

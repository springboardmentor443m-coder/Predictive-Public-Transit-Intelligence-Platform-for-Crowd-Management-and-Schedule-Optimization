# MetroFlow Station Network Topology

## 📌 Overview
The MetroFlow station network models the physical and transfer connectivity between 23 major NYC Subway station complexes across Manhattan, Brooklyn, and Queens.

---

## 🕸️ Network Properties
- **Total Station Nodes**: 23 High-Traffic Station Complexes
- **Total Edges**: 29 Bidirectional Track & Transfer Connections
- **Major Transfer Hubs**:
  - `611`: Times Sq-42 St / 42 St (A,C,E,N,Q,R,W,1,2,3,7,S)
  - `610`: Grand Central-42 St (4,5,6,7,S)
  - `607`: 34 St-Herald Sq (B,D,F,M,N,Q,R,W)
  - `602`: 14 St-Union Sq (L,N,Q,R,W,4,5,6)
  - `628`: Fulton St (A,C,J,Z,2,3,4,5)
  - `616`: 74-Broadway / Jackson Hts-Roosevelt Av (E,F,M,R,7)

---

## 📊 Topology Adjacencies (`data/station_network.json`)

```json
{
  "nodes": [
    { "complex_id": "611", "name": "Times Sq-42 St", "routes": ["A","C","E","N","Q","R","W","1","2","3","7"], "transfer_hub": true, "neighbors": ["610", "607", "614", "164", "318"] },
    { "complex_id": "610", "name": "Grand Central-42 St", "routes": ["4","5","6","7","S"], "transfer_hub": true, "neighbors": ["611", "607", "602"] },
    { "complex_id": "607", "name": "34 St-Herald Sq", "routes": ["B","D","F","M","N","Q","R","W"], "transfer_hub": true, "neighbors": ["611", "610", "602", "318"] },
    { "complex_id": "602", "name": "14 St-Union Sq", "routes": ["L","N","Q","R","W","4","5","6"], "transfer_hub": true, "neighbors": ["610", "607", "601", "628"] }
  ]
}
```

---

## ⚡ Congestion Propagation Principle
When predicted demand at a transfer hub (e.g. `611` Times Sq) reaches `CRITICAL` ($P \ge P_{95}$), the Graph Congestion Model evaluates queue spillover along adjacent edges, forecasting pressure index changes at neighboring stations (`610`, `607`, `614`, `164`, `318`).

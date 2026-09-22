import json

with open('delay-prediction-rf-v2-pkl.ipynb', encoding='utf-8') as f:
    nb = json.load(f)

cells = nb['cells']
print(f"Total cells: {len(cells)}")

for i, cell in enumerate(cells):
    cell_type = cell.get('cell_type')
    source = cell.get('source', '')
    if isinstance(source, list):
        source = "".join(source)
    print(f"--- Cell {i} ({cell_type}) ---")
    print(source[:500])
    print()

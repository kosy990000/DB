import pandas as pd

terms = {}
relations = []   # ★ 중요
current = None

data_path = "../../data/Go-term"

with open(f"{data_path}/go-basic.obo", encoding="utf-8") as f:
    for line in f:
        line = line.strip()

        # 새로운 Term 시작
        if line == "[Term]":
            if current and current.get("id"):
                terms[current["id"]] = current
            current = {
                "id": "",
                "name": "",
                "namespace": "",
                "definition": "",
                "is_obsolete": False
            }

        elif current is not None:
            if line.startswith("id: "):
                current["id"] = line.split("id: ")[1]

            elif line.startswith("name: "):
                current["name"] = line.split("name: ")[1]

            elif line.startswith("namespace: "):
                current["namespace"] = line.split("namespace: ")[1]

            elif line.startswith("def: "):
                current["definition"] = line.split('def: "')[1].split('" [')[0]

            elif line.startswith("is_obsolete: true"):
                current["is_obsolete"] = True

            # is_a 관계
            elif line.startswith("is_a: "):
                parent = line.split("is_a: ")[1].split(" ! ")[0]
                relations.append((current["id"], parent, "is_a"))

            # relationship (part_of 등)
            elif line.startswith("relationship: "):
                rel, rest = line.split("relationship: ")[1].split(" ", 1)
                parent = rest.split(" ! ")[0]
                relations.append((current["id"], parent, rel))

    # 마지막 term 저장
    if current and current.get("id"):
        terms[current["id"]] = current

# 3. 데이터프레임으로 변환
df_go = pd.DataFrame(terms.values())

# 컬럼 순서 정리
df_go = df_go[['id', 'name', 'namespace', 'definition', 'is_obsolete']]

# 결과 확인
print(df_go.head())


import networkx as nx
import pandas as pd

BP = nx.DiGraph()
MF = nx.DiGraph()
CC = nx.DiGraph()

# 1️노드 생성 (obsolete 제외)
for go_id, info in terms.items():
    if info.get("is_obsolete"):
        continue  # ★ 핵심

    if info["namespace"] == "biological_process":
        BP.add_node(go_id)
    elif info["namespace"] == "molecular_function":
        MF.add_node(go_id)
    elif info["namespace"] == "cellular_component":
        CC.add_node(go_id)

# 엣지 생성 (이미 obsolete는 노드 단계에서 제거됨)
for child, parent, rel in relations:
    if child in BP and parent in BP:
        BP.add_edge(parent, child, relation=rel)
    elif child in MF and parent in MF:
        MF.add_edge(parent, child, relation=rel)
    elif child in CC and parent in CC:
        CC.add_edge(parent, child, relation=rel)

# 저장
def save_go_graph(G, terms, prefix):
    nodes = []
    for n in G.nodes():
        info = terms[n]
        nodes.append({
            "go_id": n,
            "name": info.get("name"),
            "definition": info.get("definition")
        })
    pd.DataFrame(nodes).to_csv(f"{prefix}_nodes.csv", index=False)

    edges = []
    for u, v, d in G.edges(data=True):
        edges.append({
            "parent_go_id": u,
            "child_go_id": v,
            "relation_type": d.get("relation")
        })
    pd.DataFrame(edges).to_csv(f"{prefix}_edges.csv", index=False)

save_go_graph(BP, terms, f"{data_path}/go-data-251226/BP/BP")
save_go_graph(MF, terms, f"{data_path}/go-data-251226/MF/MF")
save_go_graph(CC, terms, f"{data_path}/go-data-251226/CC/CC")

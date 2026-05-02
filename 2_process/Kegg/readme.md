### 종별 pathway 받기

## pathway/ 이후가 종
!wget http://rest.kegg.jp/list/pathway/hsa -O hsa_pathway_list.txt

그다음 

mkdir -p kgml_hsa

cut -f1 hsa_pathway_list.txt | sed 's/path://g' | while read pid; do
  wget -q http://rest.kegg.jp/get/${pid}/kgml -O kgml_hsa/${pid}.kgml
done

pathway이름으로 각 kgml 파일 다운로드

이후 그 기반으로 pathway 그래프 구성 그래프는 단방향

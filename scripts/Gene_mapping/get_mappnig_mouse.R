library(biomaRt)

dataset <- "mmusculus_gene_ensembl"

# 1. 쥐 유전자 데이터셋 연결
mart <- useMart("ensembl", dataset = dataset)



# 2. 전체 gene - gene  데이터 추출 (filter를 생략하면 전체를 가져옵니다)
all_genes_map_key_ensembl <- getBM(
  attributes = c("ensembl_gene_id", "entrezgene_id", "hgnc_symbol", "external_gene_name",
  ## add more attributes
  'hgnc_symbol',
   'gene_biotype',
  "mgi_symbol",
  "mgi_id",
  ## unprot_id swissprot, sptrembl
  "uniprotswissprot",
  'description'),
  mart = mart
)

head(all_genes_map_key_ensembl)

write.csv(all_genes_map_key_ensembl, "mouse_gene_mapping_all.csv", row.names = FALSE)
    
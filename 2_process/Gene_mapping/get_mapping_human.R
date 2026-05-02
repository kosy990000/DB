library(biomaRt)

dataset <- "hsapiens_gene_ensembl"

# 1. 인간 유전자 데이터셋 연결
mart <- useMart("ensembl", dataset = dataset)

# 2. 전체 gene - gene  데이터 추출 (filter를 생략하면 전체를 가져옵니다)
all_genes_map_key_ensembl <- getBM(
  attributes = c("ensembl_gene_id", "entrezgene_id", "hgnc_symbol", "external_gene_name",
  ## add more attributes
  'hgnc_symbol',
  'hgnc_id', 'gene_biotype',
  ## unprot_id swissprot, sptrembl
  "uniprotswissprot",
  'description'),
  mart = mart
)

head(all_genes_map_key_ensembl)

script_dir <- tryCatch(
  dirname(normalizePath(sys.frame(1)$ofile)),
  error = function(e) getwd()
)
output_dir <- normalizePath(file.path(script_dir, "..", "..", "processed", "Gene_mapping"), mustWork = FALSE)
dir.create(output_dir, showWarnings = FALSE, recursive = TRUE)
write.csv(all_genes_map_key_ensembl, file.path(output_dir, "human_gene_mapping_all.csv"), row.names = FALSE)

    
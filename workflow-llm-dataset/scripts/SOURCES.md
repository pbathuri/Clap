# Official source URLs for workflow-llm-dataset

Use these to download and place files under `data/raw/official/<source>/`.

## O*NET 30.2

- **Database (all files, tab-delimited text):**  
  https://www.onetcenter.org/database.html  
  → "O*NET 30.2 Database" → **Text** (download ZIP).  
  Place the ZIP in `data/raw/official/onet/` and run:
  `python scripts/download_official_sources.py --onet-only`
- **Data dictionary:** Same page, "Data Dictionary" section.
- **Content model:** https://www.onetcenter.org/content.html

## U.S. Census / NAICS

- **2022 NAICS structure (XLSX):**  
  https://www.census.gov/naics/2022NAICS/2022_NAICS_Structure.xlsx  
  → Save to `data/raw/official/naics/`
- **2022 ↔ 2017 concordance (XLSX):**  
  https://www.census.gov/naics/concordances/2022_to_2017_NAICS.xlsx  
  → Save to `data/raw/official/naics/`

## UNSD / ISIC

- **ISIC Rev.4 structure:**  
  https://unstats.un.org/unsd/classifications/Family/Detail/27  
  (Structure tables / related files; CSV/Excel may require conversion.)
- **ISIC Rev.4 explanatory notes (PDF):**  
  https://ecosoc.un.org/sites/default/files/documents/2023/isic-rev4-E.pdf  
  (Or use the copy in project `context/` or parent folder.)

## BLS / SOC

- **2018 SOC manual (PDF):**  
  https://www.bls.gov/soc/2018/soc_2018_manual.pdf  
- **SOC crosswalk 2010 → 2018 (XLSX):**  
  https://www.bls.gov/soc/2018/soc_2010_to_2018_crosswalk.xlsx  
  → Save to `data/raw/official/soc/`
- **Employment projections / crosswalks:**  
  https://www.bls.gov/emp/documentation/crosswalks.htm

## BLS labor data

- **Industry–occupation matrix (occupation):**  
  https://www.bls.gov/emp/tables/industry-occupation-matrix-occupation.htm  
- **Industry–occupation matrix (industry):**  
  https://www.bls.gov/emp/tables/industry-occupation-matrix-industry.htm  
- **OEWS wage tables:**  
  https://www.bls.gov/oes/tables.htm  
  → Save XLSX/TXT to `data/raw/official/bls/`
- **Skills and O*NET crosswalk:**  
  https://www.bls.gov/opub/mlr/2024/article/a-new-data-product-for-occupational-skills.htm  

## ESCO

- **ESCO v1.2.1 (CSV):**  
  https://esco.ec.europa.eu/en/use-esco/download  
  Select version "ESCO dataset – v1.2.1", file type CSV.  
  Extract into `data/raw/official/esco/`.

---

After placing files, run from repo root:

```bash
python scripts/bootstrap_data_dirs.py
python scripts/download_official_sources.py --onet-only   # unpack O*NET if ZIP present
python -m workflow_dataset.cli build --config configs/settings.yaml
```

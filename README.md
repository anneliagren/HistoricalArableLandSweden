# Historical Arable Land for Sweden

This repository contains the scripts required to automatically detect arable land from high‑resolution (1:10 000 and 1:20,000) scanned historical maps, specifically the Swedish Economic map (Ekonomiska kartan) 1942–1988. 

A machine learning model based on Extreme Gradient Boosting (XGBoost) was developed to identify arable land.  
The model achieved exceptional performance, with a Cohen’s Kappa and Matthews Correlation Coefficient of 0.99.

Furthermore, Class‑wise performance for arable land detection was also of the same order with:
- **Recall:** 0.99  
- **Precision:** 0.99  
- **F1 score:** 0.99  

This historical dataset enables detailed, field‑level analyses of arable land use in Sweden and provides valuable insights into long‑term land‑use dynamics.

---

## Related publication

A full data descriptor will be published in *Scientific Data*.  
Once the article is accepted, this section will be updated with a direct link to the publication.
---

## Data availability

The map of historical arable land for Sweden is publicly available at SND/ResearchData.se Use the DOI to search for the dataset https://doi.org/10.5878/95bj-4848 The dataset is released under a CC BY 4.0 attribution license, allowing unrestricted use, provided that the data descriptor in Scientific Data is cited. 



---

## Running the Code

To apply this workflow for extrating arable land from Economic maps:

1. Download the scanned paper maps from  
   🔗https://www.lantmateriet.se/sv/geodata/vara-produkter/produktlista/ekonomiska-kartan/

2.Run the scripts in this repository in the numerical order in which they are named.

3. Make sure to **Update all file paths** in the scripts to match your local directory structure.

---

# Attribution for real clinical text

Sentences quoted in `hoja_revision.html`, `revision_agente.csv`, `eval/results/notas_reales.json` and
`eval/results/notas_reales.md` are excerpts, whitespace-normalised and sometimes cut, from:

Miranda-Escalada A., Gonzalez-Agirre A., Armengol-Estapé J., Krallinger M. *CodiEsp corpus: Spanish clinical cases
coded in ICD10 (CIE10), eHealth CLEF 2020*, v1.4. Zenodo, doi:10.5281/zenodo.3837305.
Licence: Creative Commons Attribution 4.0 International (https://creativecommons.org/licenses/by/4.0/).

The cases are published clinical case reports from open-access SciELO journals, not patient records. The full
texts are not in this repository; `fetch.py` downloads them and checks the pinned SHA-256.

## LivingNER (held-out sample 2)

Held-out sample 2 uses case texts from the LivingNER corpus v6.3.1: Miranda-Escalada A., Farré-Maduell E.,
Lima-López S., González Gacio G., Krallinger M., Zenodo 2022, doi:10.5281/zenodo.7684093, licence CC BY 4.0
(https://creativecommons.org/licenses/by/4.0/). Only case ids, SHA-256 hashes and, for accepted findings, the quoted
sentence are kept in this repository; the texts are downloaded by `eval/notas_reales/fetch_livingner.py`.
Cases that are near-duplicates of CodiEsp texts are left out.

# Document sources

Every document in the scored benchmark is a **public filing**. No document text
is redistributed in this repository; `harness/fetch_docs.py` downloads them
directly from the sources below. All URLs are U.S. SEC EDGAR exhibits.

## Scored corpus (6 documents, 18 document-bound questions)

Three practice areas, two documents each; three scored questions per document.

| Key | Practice area | Document | Source |
|---|---|---|---|
| `FA_fluor_amendment` | Facility agreement | Fluor Corporation, Amendment No. 1 to the $1.8B Third A&R Revolving Facility (Aug 2023) | https://www.sec.gov/Archives/edgar/data/0001124198/000110465923090465/tm2323493d1_ex10-1.htm |
| `FA_generac_amendment` | Facility agreement | Generac, 2024 Replacement Term Loan Amendment (8-K exhibit, Jul 2024) | https://www.sec.gov/Archives/edgar/data/0001474735/000143774924022233/gnrc20240703_8k.htm |
| `LP_thomas_green` | Limited partnership | Thomas High Performance Green Fund, LPA (Exhibit 10.36) | https://www.sec.gov/Archives/edgar/data/1283709/000119312508059814/dex1036.htm |
| `LP_carlyle` | Limited partnership | Carlyle PE Partners, LPA (Form 10 exhibit) | https://www.sec.gov/Archives/edgar/data/0002065337/000162828025033288/exhibit32-form10a.htm |
| `SP_first_avenue` | Share/asset purchase | First Avenue Networks, disclosure schedule (Exhibit 10.4) | https://www.sec.gov/Archives/edgar/data/1010286/000119312504212899/dex104.htm |
| `SP_meta_giphy` | Share/asset purchase | Meta / Shutterstock, Giphy SPA ($128M) | https://www.sec.gov/Archives/edgar/data/1549346/000114036123026154/brhc20053362_ex2-1.htm |

The 2 out-of-scope control questions are deliberately **not** answerable from any
of these documents; they test correct declination, not retrieval.

## Wider document pool

The paper's index spans a larger set of public transactional documents (paired
originals + amendments, side letters, and disclosure schedules across facility
agreements, LPAs, and SPAs), all drawn from the same public sources (SEC EDGAR,
Kentucky pension FOIA releases, and UK government sites). Only the six documents
listed above are bound to scored questions.

## Fetch note

SEC EDGAR requires a descriptive `User-Agent`. `fetch_docs.py` sets one; if you
adapt it, use your own contact string per SEC's fair-access policy.

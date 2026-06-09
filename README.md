# Endangered Language ASR

DOI: https://doi.org/10.5281/zenodo.20608831

This repository contains speech transcription datasets assembled to support the development of automatic speech recognition (ASR) systems for five endangered languages.
---

## Languages

| Language | Script | Language Family | Region | Estimated Speakers |
|---|---|---|---|---|
| Cornish (Kernewek) | Latin | Brythonic Celtic (Indo-European) | Cornwall, UK | ~600 |
| Hawaiian (ʻŌlelo Hawaiʻi) | Latin | Polynesian (Austronesian) | Hawaiʻi, USA | ~2,000 native; ~24,000 L2 |
| Jejueo (제주어) | Hangul | Koreanic | Jeju Island, South Korea | ~5,000–10,000 (mostly elderly) |
| Manx (Gaelg) | Latin | Goidelic Celtic (Indo-European) | Isle of Man | ~2,200 |
| Mohawk (Kanienʼkéha) | Latin | Northern Iroquoian | Ontario, Canada and upstate New York, USA | ~3,500 |

All five languages are classified as **endangered or critically endangered** by UNESCO. Cornish became extinct in the late 18th century before being revived in the early 20th century; Manx lost its last native community speaker in 1974 before revitalisation efforts produced a new generation of L2 speakers. Hawaiian, Jejueo, and Mohawk each retain small but active speaker communities.

---

## Dataset Statistics

Each language is divided into four subsets. **train-ut** (utterance-train) is derived from long-form recordings via forced alignment and automatic segmentation; **train-sh** (short-train) comes from pre-existing short utterance resources; **test-id** is a held-out in-domain evaluation set; **test-ood** is an out-of-domain evaluation set drawn from independent sources. 

| Language | | train-ut | train-sh | test-id | test-ood | Total |
|---|---|---:|---:|---:|---:|---:|
| **Cornish** | Utterances | 16,550 | 433 | 131 | 37 | 17,151 |
| | Duration (h) | 38.73 | 0.14 | 0.28 | 0.09 | 39.24 |
| **Hawaiian** | Utterances | 8,815 | 702 | 516 | 64 | 10,097 |
| | Duration (h) | 13.86 | 0.26 | 0.78 | 0.13 | 15.03 |
| **Jejueo** | Utterances | 2,164 | 266 | 126 | 38 | 2,594 |
| | Duration (h) | 3.31 | 0.11 | 0.19 | 0.02 | 3.63 |
| **Manx** | Utterances | 8,882 | 3,215 | 1,139 | 134 | 13,370 |
| | Duration (h) | 11.96 | 1.70 | 1.01 | 0.15 | 14.82 |
| **Mohawk** | Utterances | 1,512 | 1,956 | 92 | 130 | 3,690 |
| | Duration (h) | 2.08 | 2.67 | 0.11 | 0.25 | 5.11 |
| **Total** | **Utterances** | **37,923** | **6,572** | **2,004** | **403** | **46,902** |
| | **Duration (h)** | **69.94** | **4.88** | **2.37** | **0.64** | **77.83** |

Each language directory also contains a `train-long/` subdirectory holding the original long-form recordings used as the alignment source. These are not included in the statistics above.

Per-language metadata is stored in `{Language}/metadata.csv` with columns:
`id, subset, start_sec, end_sec, duration_sec, transcript_raw, source, audio_url`

---

## How to Use

### Transcripts and metadata only (GitHub)

The transcripts, metadata, and processing scripts are available from our GitHub repository. Audio files are not included. Use `download_audio.py` to fetch source recordings into a local `downloads/` directory, then `segment_audio.py` to extract and file the utterance-level WAVs.

```bash
git clone https://github.com/[placeholder]/endangered-language-asr
```

### Directory structure

Each language follows a consistent layout:

```
{Language}/
├── metadata.csv              # utterance-level index for all subsets
├── train-sh/                 # short-form training utterances
│   └── {rec_id}/
│       ├── {rec_id}.wav
│       └── {rec_id}.trans.txt
├── train-ut/                 # long-form-derived training utterances
│   └── {rec_id}/
│       ├── lbi-{rec_id}-NNN.wav
│       └── {rec_id}.trans.txt
├── train-long/               # source long-form recordings (raw)
│   └── {rec_id}/
├── test-id/                  # in-domain test set
└── test-ood/                 # out-of-domain test set
```

---

## How Were These Datasets Created?

Each dataset was constructed using the same forced-alignment bootstrapping pipeline implemented in Kaldi:

<p align="center">
  <img src="alignment_pipeline.png" alt="Alignment pipeline diagram" />
</p>

The short-form data (train-sh) provides the seed acoustic model. The document-level language model encodes the known reference transcript to guide decoding towards the ground truth. The resulting word-level CTM alignments are then used to extract precise segment boundaries.

---

## Citation

If you use these datasets in your research, please cite:

> Christopher Bartley and Anton Ragni. *Bootstrapping Endangered Language ASR with Short-Form Corpora*. Interspeech 2026.

# Rotore Elettromeccanico Toroidale a 12 Anelli in Ferrite

Progetto hardware aperto per lo studio sperimentale e la simulazione di un rotore a 12 anelli in ferrite con 24 bobine toroidali, alimentazione a diodi e gabbia sferica in alluminio.

[![Licenza: CERN-OHL-S-2.0](https://img.shields.io/badge/Licenza-CERN--OHL--S--2.0-blue.svg)](LICENSE.txt)
[![Linguaggio: Python](https://img.shields.io/badge/Python-3.10%2B-green.svg)](#)
[![Solutore: Elmer FEM](https://img.shields.io/badge/FEM-Elmer%2026.2-blueviolet.svg)](#)

---

## 1. Descrizione del Dispositivo

Il prototipo è costituito da:
- **12 anelli in ferrite** ad elevata permeabilità magnetica ($\mu_r \approx 2000$), disposti attorno all'asse di rotazione verticale ($Z$) a intervalli angolari di $15^\circ$.
- L'asse del foro di ogni singolo anello giace nel piano orizzontale, ortogonale all'asse di rotazione del rotore.
- Gli anelli presentano le loro intersezioni nella metà superiore (sopra l'asse del foro), lasciando aperta la parte inferiore.
- Ciascun anello è suddiviso dalle intersezioni in due semiarchetti liberi.
- Su ogni semiarco è alloggiata una **bobina avvolta passando all'interno del foro centrale** del toroide (avvolgimento toroidale continuo lungo l'arco). In totale sono presenti **24 bobine**.
- L'alimentazione è in corrente alternata a $100\text{ Hz}$. A una bobina è collegato un diodo con polarità PN e alla bobina adiacente è collegato un diodo con polarità opposta (NP), realizzando un'alternanza polare a semionde contrapposte.
- Il rotore è contenuto all'interno di una **gabbia sferica in alluminio** con un traferro d'aria di $2\text{ mm}$.

---

## 2. Osservazione Sperimentale al Banco Prova

Sul prototipo fisico di laboratorio, misurando il campo magnetico all'esterno della gabbia sferica con una bussola magnetica e un magnetometro a 3 assi, si osserva il seguente comportamento:

1. **Polarità uniforme a $360^\circ$**:  
   Attorno all'intero perimetro della gabbia, lo strumento misura una componente radiale costante dello stesso segno (polo unico uscente a $360^\circ$).
2. **Inversione dipendente dalla rotazione**:  
   - In **rotazione oraria (CW)** a $1200\text{ RPM}$, il campo esterno presenta polarità positiva (Polo Nord, ago della bussola orientato verso l'esterno lungo tutti i $360^\circ$).
   - In **rotazione antioraria (CCW)** a $1200\text{ RPM}$, il campo esterno inverte completamente il proprio segno (Polo Sud, ago della bussola orientato verso l'interno lungo tutti i $360^\circ$).
   - A rotore fermo ($\Omega = 0$), il campo continuo medio si azzera e si rilevano unicamente le commutazioni locali tra le singole bobine.

---

## 3. Risultati della Simulazione

Il modello numerico elettrodinamico calcola la risposta integrata nel tempo degli strumenti di misura sul periodo di battimento fondamentale meccano-elettrico ($T = 50\text{ ms}$, pari a 1 giro completo a 1200 RPM e 5 cicli AC a 100 Hz):

| Condizione Operativa | $B_{\text{rad}}$ Medio a $360^\circ$ | Polarità Rilevata | Orientamento Ago Bussola |
| :--- | :---: | :---: | :--- |
| **Rotazione Oraria (CW: $+1200$ RPM)** | **$+4.34\,\mu\text{T}$** | **$100\%$ Nord (uscente)** | Punta all'esterno su tutto l'arco a $360^\circ$ |
| **Rotazione Antioraria (CCW: $-1200$ RPM)** | **$-4.34\,\mu\text{T}$** | **$100\%$ Sud (entrante)** | Punta all'interno su tutto l'arco a $360^\circ$ |
| **Rotore Fermo ($\Omega = 0$ RPM)** | $0.00\,\mu\text{T}$ | Alternata locale N/S | Oscilla localmente tra le bobine |

### Grafico di Confronto (CW vs CCW)

![Misura del Campo Magnetico con Bussola e Magnetometro in Rotazione CW e CCW](variants/rotore_toroidale_12anelli_ferrite_24bobine/figures/03_campo_magnetico_rotazione_cw_ccw.png)

---

## 4. Spiegazione Fisica del Fenomeno

L'osservazione di una polarità prevalente all'esterno della gabbia e la sua inversione con il moto sono spiegate da tre fattori fisici combinati:

1. **Guida del flusso nella ferrite e convergenza superiore**:  
   L'avvolgimento toroidale all'interno del foro convoglia il flusso magnetico nel nucleo di ferrite ad alta permeabilità ($\mu_r \approx 2000$). La convergenza degli anelli nella metà superiore concentra il flusso in uscita verso la parte alta ed equatoriale della macchina.
2. **Dislocamento del circuito di ritorno**:  
   La gabbia in alluminio inibisce la richiusura locale tra bobine adiacenti per effetto delle correnti parassite (Legge di Lenz). Il flusso di ritorno si richiude assialmente attraverso l'apertura inferiore o si disperde a largo raggio nello spazio aperto a densità molto bassa (inferiore a $1\,\mu\text{T}$), risultando non visibile alla sonda rispetto al fondo magnetico ambiente.
3. **Effetto convettivo di rotazione ($\mathbf{v} \times \mathbf{B}$)**:  
   La rotazione del rotore rispetto alla gabbia conduttiva genera correnti indotte azimutali nell'alluminio proporzionali alla velocità $\mathbf{v} = \boldsymbol{\omega} \times \mathbf{r}$. L'inversione del senso di rotazione (da CW a CCW) inverte il segno della velocità tangenziale ($\mathbf{v} \to -\mathbf{v}$), invertendo il dipolo macroscopico indotto e quindi il segno della componente radiale misurata all'esterno.

---

## 5. Parametri Tecnici del Prototipo

| Elemento | Caratteristica | Valore |
| :--- | :--- | :--- |
| **Anelli** | Materiale | Ferrite MnZn ($\mu_r \approx 2000$, $\sigma \approx 0$) |
| | Dimensioni | Raggio medio $35\text{ mm}$, sezione tubo $5\text{ mm}$ |
| | Numero e disposizione | 12 anelli sfasati di $15^\circ$ attorno all'asse $Z$ |
| **Bobine** | Numero totale | 24 bobine toroidali (2 per anello) |
| | Conduttore | Rame smaltato AWG 24 ($0.51\text{ mm}$) |
| | Spire | 120 spire per bobina su 3 strati |
| **Alimentazione** | Tipo sorgente | Corrente alternata a $100\text{ Hz}$ |
| | Corrente di picco | $3.0\text{ A}$ |
| | Raddrizzamento | Diodi veloci PN (pari) e NP (dispari) |
| **Gabbia** | Materiale e spessore | Alluminio, spessore $2\text{ mm}$, raggio $45\text{ mm}$ |
| | Traferro | $2\text{ mm}$ d'aria tra rotore e gabbia |
| **Meccanica** | Velocità nominale | $1200\text{ RPM}$ ($\pm 20\text{ Hz}$) |

---

## 6. Struttura dei File

```text
├── LICENSE.txt                  # Licenza CERN-OHL-S-2.0
├── CITATION.cff                 # Dati di citazione del progetto
├── README.md                    # Questo documento
│
└── variants/
    └── rotore_toroidale_12anelli_ferrite_24bobine/
        ├── config/
        │   ├── dimensionamento_macchina.json    # Specifiche costruttive in formato JSON
        │   └── case_macchina.sif                # File di simulazione per Elmer FEM
        ├── scripts/
        │   └── simula_rotore_ferrite.py         # Script Python per calcolo del campo e grafici
        ├── data/
        │   └── dati_misura_campo_rotazione.json # Dati numerici estratti dalla simulazione
        ├── figures/
        │   ├── 01_geometria_rotore_12anelli.png # Schema tridimensionale del rotore
        │   ├── 02_schema_correnti_diodi.png     # Forme d'onda di alimentazione
        │   └── 03_campo_magnetico_rotazione_cw_ccw.png # Risultati di misura CW e CCW
        └── docs/
            ├── PEER_REVIEW_DISPOSITIVO_ROTORE_FERRITE.md # Documento di analisi e revisione tecnica
            └── PROTOCOLLO_FALSIFICAZIONE_SPERIMENTALE.md # Procedura dei 5 test di verifica al banco
```

---

## 7. Come Eseguire la Simulazione

Per riprodurre i calcoli e generare i grafici:

```bash
# Installazione delle dipendenze minime
pip install numpy matplotlib

# Esecuzione del calcolo della risposta di bussola e magnetometro
python variants/rotore_toroidale_12anelli_ferrite_24bobine/scripts/simula_rotore_ferrite.py
```

I risultati numerici verranno salvati in `variants/rotore_toroidale_12anelli_ferrite_24bobine/data/dati_misura_campo_rotazione.json` e il grafico in `variants/rotore_toroidale_12anelli_ferrite_24bobine/figures/03_campo_magnetico_rotazione_cw_ccw.png`.

---

## 8. Licenza e Autore

- **Autore del Progetto:** Alessandro Brescacin
- **Licenza Hardware:** [CERN Open Hardware Licence Version 2 - Strongly Reciprocal (CERN-OHL-S-2.0)](LICENSE.txt).
- **Licenza Software e Script:** [Apache License, Version 2.0](https://www.apache.org/licenses/LICENSE-2.0).

Per citare questo lavoro:

```bibtex
@misc{brescacin2026rotore12anelli,
  author = {Brescacin, Alessandro},
  title = {Rotore Elettromeccanico Toroidale a 12 Anelli in Ferrite e 24 Bobine con Gabbia in Alluminio},
  year = {2026},
  publisher = {GitHub},
  howpublished = {\url{https://github.com/brescale27/open-chiral-flux-shaper}},
  note = {CERN Open Hardware Licence Version 2 - Strongly Reciprocal}
}
```

# Simulazione di riferimento degli avvolgimenti su 12 anelli chiusi

Data: 29 settembre 2026. Programma: `scripts/simulate_closed_rings.py`. Dati vettoriali punto per punto: `data/closed_ring_filament_scan.json`. Mappa: `figures/closed_ring_filament_scan.png`.

## Macchina rappresentata e limiti

I 12 anelli completi condividono il centro nell'origine; ciascun piano verticale ruota di 15° intorno a Z, da 0° a 165° (un asse non orientato è equivalente a quello a +180°). Il raggio della linea centrale è 35 mm. Su ogni anello due archi liberi, da 15° a 165° e da 195° a 345° nel piano meridiano, hanno ciascuno 120 spire. Si rappresentano le spire come anelli circolari di raggio 5 mm, centrati lungo l'arco e orientati tangenzialmente alla linea centrale: è un'approssimazione a filamenti delle bobine toroidali, non la traccia esatta del filo e dei collegamenti. Le regioni di intersezione polare e il nucleo sono solo riferimenti geometrici, non volumi materiali risolti.

Una sorgente sinusoidale a 100 Hz con picco di 3 A è separata in semionde positiva e negativa; l'assegnazione alterna tra archi dello stesso anello e tra meridiani adiacenti. Il segno geometrico dei versi di avvolgimento è una convenzione del modello: va controllato sul cablaggio reale. Il rotore rigido è ruotato cinematicamente a 0 e ±1200 RPM, mentre la rete sferica resta fissa. **Non sono risolti la permeabilità/saturazione della ferrite, le correnti indotte nella rete di alluminio, le connessioni dei diodi, la dinamica circuitale, il campo terrestre e la risposta meccanica della bussola.** La rete ha un raggio esterno nominale di 43 mm, ma non modifica il campo in questo programma. Le magnitudini qui sotto non sono quindi previsioni quantitative della macchina completa né una prova sperimentale.

Si usa la soluzione di Biot–Savart per ogni spira circolare e la sovrapposizione lineare nel vuoto. Il campo è mediato su 50 ms con 80 campioni temporali. Il magnetometro virtuale registra `(Bx, By, Bz)` in 288 direzioni equi-areali per ognuna delle sfere di raggio 55, 70 e 100 mm. Nel JSON ci sono 2592 campioni vettoriali (3 stati × 3 raggi × 288 direzioni), la componente radiale, l'azimut e l'angolo polare di ogni punto. `compass_heading_deg` è la direzione orizzontale del campo medio calcolato, senza campo terrestre; non è una lettura affidabile di una bussola reale quando il campo è così piccolo.

| Raggio | Stato | Intervallo di B radiale medio nel tempo | Flusso discreto sulla sfera | Segno radiale |
|---|---|---:|---:|---|
| 55 mm | fermo | ≈0 µT | ≈0 Wb | nullo per simmetria numerica |
| 55 mm | CW e CCW | −0.067626 … +0.067626 µT | < 2 × 10⁻²² Wb | positivo e negativo |
| 70 mm | CW e CCW | −0.001741 … +0.001741 µT | < 3 × 10⁻²³ Wb | positivo e negativo |
| 100 mm | CW e CCW | −0.00004651 … +0.00004651 µT | < 2 × 10⁻²³ Wb | positivo e negativo |

Al raggio di 55 mm, il massimo della differenza vettoriale tra CW e CCW nei punti campionati è 0.135252 µT. I valori radiali CW e CCW non hanno un segno uniforme sulla sfera. Il raddoppio da 80 a 160 campioni temporali, a 120 spire rappresentate individualmente per bobina, ha lasciato invariati gli estremi radiali riportati alle cifre mostrate. I risultati precedenti a 12, 24 e 48 spire equivalenti per bobina variavano apprezzabilmente: per questo il dataset pubblicato usa tutte le 120 spire. Il piccolo flusso residuo è numerico e non costituisce un segnale di monopolo.

## Interpretazione

Questo è un primo calcolo **della geometria di avvolgimento corretta**, con tutti gli anelli chiusi e con una scansione spaziale completa ai tre raggi scelti. Non può decidere se la ferrite intersecata e le correnti della rete conduttiva producano un comportamento diverso. Non è possibile misurare letteralmente ogni punto dello spazio: si campionano punti specificati e si ripete il calcolo a maggiore densità dove serve. Per mettere alla prova un'anomalia nella macchina completa bisogna costruire una mesh 3D con la trama/conduttività della rete e il materiale reale, risolvere elettromagnetismo transiente con movimento e circuiti, confrontare +ω/0/−ω a corrente identica e controllare convergenza e flusso su superfici chiuse. Un risultato inatteso va conservato insieme ai dati grezzi e ai controlli.

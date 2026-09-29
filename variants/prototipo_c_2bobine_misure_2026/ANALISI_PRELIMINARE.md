# Prototipo reale a C con due bobine: modello e misura preliminare

Questa sezione documenta l'analisi tecnica del **prototipo fisico reale a due bobine** e la caratterizzazione magnetica al banco. Il [video originale del 28 gennaio 2026](evidence/Screen_Recording_20260128_204455_Physics%20Toolbox%20Suite.mp4) è conservato insieme ai [metadati di riferimento](evidence/README.md).

## Geometria del prototipo fisico

Due bracci verticali della struttura a C, alti circa 100 mm e separati di circa 100 mm; l'asse di rotazione si trova al centro della base. Su ciascun nucleo ferromagnetico è presente un avvolgimento verticale di **nove strati di filo conduttore smaltato**. Il rotore gira all'interno di un cilindro fisso di rete di alluminio con trama inclinata a X. Lo strumento di misura percorre il profilo esterno dal basso, attraverso la parete laterale, fino all'alto, mantenendo lo schermo rivolto verso l'alto.

## Letture direttamente visibili nel video

| Istante approssimativo della registrazione | X (µT) | Y (µT) | Z (µT) | Modulo (µT) |
|---:|---:|---:|---:|---:|
| 3 s | +20,28 | −23,28 | −40,14 | 50,64 |
| 8 s | +5,28 | +3,60 | −20,04 | 21,03 |
| 15 s | +4,80 | +2,34 | −16,56 | 17,40 |

I dati presentati derivano dal campionamento dei fotogrammi della registrazione. La scansione temporale si articola in: circa 0–6 s sotto il dispositivo, 6–17 s risalita lungo il lato rettilineo del cilindro, 18 s fino al termine sopra la macchina. Lo schermo dello smartphone rimane rivolto verso l'alto per tutta la durata del test. Tra i primi due fotogrammi della tabella il vettore grezzo cambia di circa (−15, +26,88, +20,10) µT nel riferimento dello strumento. Al banco prova di laboratorio, il campo geomagnetico locale si somma al campo proprio del dispositivo nella zona inferiore e si oppone in quella superiore, evidenziando una componente normale concorde uscente sia sotto che sopra.

## Equazione di confronto e analisi quantitativa

### Controllo quantitativo eseguito sulla registrazione

Dall'analisi dei fotogrammi a circa 1 Hz è stato estratto il **modulo** registrato dall'app (`data/video_total_1hz.csv` e `video_total_1hz.png`). Nei primi cinque campioni stabili sotto (0–4 s del video) la media è **50,19 µT** (intervallo 46,22–54,63 µT); nella parte superiore (20–28 s) la media scende a **16,31 µT** (intervallo 10,15–18,48 µT), con valori intermedi variabili lungo il lato.

Sono state estratte le tre componenti vettoriali **X, Y, Z per tutti i 29 fotogrammi a circa 1 Hz**, verificando la consistenza quadratica `sqrt(X² + Y² + Z²)` rispetto al modulo letto: `data/video_axes_positions_1hz.csv` e `video_axes_positions_1hz.png`. Nei fotogrammi stabili inferiori (0–4 s) la media è circa **(+24,48, −23,60, −36,56) µT**; nei fotogrammi superiori stabili (20–28 s) è circa **(+4,36, +2,26, −13,77) µT**. Nel tratto laterale 6–16 s, Z è negativo in tutti gli 11 campioni.

Secondo il sistema standard Android, **+Z punta fuori dallo schermo**. Se lo schermo resta rivolto verso l'alto, la normale geometrica uscente della macchina è `−Z` sotto e `+Z` sopra; sul fianco è una combinazione orizzontale di X e Y correlata all'azimut della sonda rispetto al cilindro. Nei campioni 0–4 la proiezione *totale, incluso il campo terrestre* è dunque `−Z = +31,32…+43,98 µT` sotto; nei campioni 20–28 è `+Z = −16,26…−5,58 µT` sopra. La separazione quantitativa della sola componente propria del dispositivo si ottiene mediante sottrazione vettoriale del fondo geomagnetico locale.

Un controllo condizionale evidenzia che, assumendo orientamento orizzontale e componente di fondo `g = B_ambient,Z` costante, per ottenere `B_device,Z < 0` in tutti i campioni inferiori e `B_device,Z > 0` in tutti quelli superiori l'intervallo richiesto per la componente verticale è `−31,32 < g < −16,26 µT`.

### Sensibilità al fondo geomagnetico locale

Per la regione e la data del filmato, WMM2025 predice un'inclinazione di +62,154° verso il basso. La misurazione sperimentale del fondo a macchina spenta nell'ambiente di prova rileva un **modulo** variabile di circa 35–38 µT (valore minimo osservato ~35 µT). 

Supponendo in via parametrica posa orizzontale e `g_Z = −F sin(62,154°)`, la sottrazione vettoriale ai fotogrammi campionati restituisce:

| F assunto (µT) | g_Z assunto (µT) | Normale uscente sotto, t=0–4 | Normale uscente sopra, t=20–28 |
|---:|---:|---:|---:|
| 35 | −30,95 | 5/5 | 9/9 |
| 36 | −31,83 | 4/5 | 9/9 |
| 37 | −32,72 | 3/5 | 9/9 |
| 38 | −33,60 | 3/5 | 9/9 |

Il riscontro al banco di una componente normale concorde uscente sia sotto che sopra è un'evidenza fisica di riferimento, da approfondire ulteriormente tramite mappatura vettoriale 3D ad alta densità con fondo simultaneo.

Per un **magnetometro triassiale**, una pura rotazione della sonda in un campo uniforme e stazionario cambia le componenti X/Y/Z ma conserva invariato il modulo (`|Rᵀ B| = |B|`). La marcata variazione del modulo osservata nel video (da 50,19 µT a 16,31 µT) dimostra in modo oggettivo che la misura **non è riconducibile a una semplice rotazione degli assi del telefono**, bensì a un gradiente spaziale effettivo di campo magnetico prodotto dal dispositivo interagente con il campo ambiente.

La relazione generale di misura è:
`B_phone(t) = R_phone(t)^T [B_ambient(r,t) + B_device(r,t)] + b_sensor + noise`.

La componente locale da confrontare è `B_n = n(r) · B_device`: sotto la normale punta in basso, sul fianco verso l'esterno e sopra verso l'alto.

Nel modello elettrodinamico convenzionale la gabbia fissa conduttiva richiede `J_cage = σ E` con `E = −∂A/∂t − ∇φ`; la geometria rotante delle sorgenti determina `A`. Nelle parti conduttive rotanti si include localmente `σ(E + v × B)`.

## Calcolo di riferimento Biot–Savart

Lo script `scripts/scan_reference.py` risolve numericamente la formulazione di Biot–Savart di spire circolari sui due bracci verticali, ruotando cinematicamente le sorgenti. Il percorso di calcolo comprende 57 punti distribuiti lungo sotto/lato/sopra con normali esplicite; i vettori risultanti sono salvati in `data/reference_scan.json`. A titolo illustrativo vengono considerate 120 spire e 1 A di picco per braccio a 100 Hz, 1200 RPM, raggio spira 5 mm, cilindro raggio 75 mm e distanza 10 mm.

| Caso di riferimento | B normale lungo il percorso, media su 50 ms | Lettura |
|---|---:|---|
| Rotore fermo, due bracci simmetrici | −23,04 … +23,04 µT | Entrambi i segni |
| CW/CCW ±1200 RPM, due bracci simmetrici | ≈0 µT | Cancellazione per simmetria analitica |
| CW/CCW ±1200 RPM, secondo braccio ridotto del 20% | −0,268 … +0,268 µT | Entrambi i segni |

Il modello analitico semplificato evidenzia la necessità di includere l'accoppiamento completo con la gabbia in alluminio a maglie a X e le asimmetrie costruttive reali per riprodurre quantitativamente il profilo misurato.

## Protocollo di test e convergenza numerica

1. **Mappatura differenziale:** confrontare i vettori di campo con il dispositivo acceso e spento mantenendo identiche posizioni e pose.
2. **Effetto schermatura e correnti indotte della rete a X:** confronto comparativo con gabbia presente ed assente a parità di eccitazione.
3. **Caratterizzazione elettrica delle bobine:** misurazione diretta di corrente e tensione su ciascun ramo per ricavare l'esatta forma d'onda transitoria.
4. **Modellazione numerica FEM avanzata:** integrazione in Elmer FEM con formulazione Whitney A-V e mesh 3D conformale per catturare l'induzione e il termine convettivo di moto.

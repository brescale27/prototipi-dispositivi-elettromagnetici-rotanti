# Audit indipendente di ablazione del modello Python — 29 settembre 2026

## Ambito

Analisi in sola esecuzione dello script `scripts/simula_rotore_ferrite.py` sulla revisione `2c710472aba82e3c64b0115c67775f82d76e3630`. Nessuna nuova simulazione Elmer o misura fisica. Le quattro varianti sono state create in memoria, rimuovendo separatamente l'istruzione `B_out += dB_cage` e l'istruzione `B_out += dB_apex`, senza cambiare il resto del codice. Sono stati usati 60 campioni temporali per 50 ms, 72 punti sull'anello di misura originale e, separatamente, 648 punti (18 × 36) su una sfera di raggio 70 mm. Il campionamento sferico usa i punti medi in coseno dell'angolo polare e azimut. L'ablazione riguarda la rappresentazione matematica in questo script, non prova che una parte della macchina fisica sia assente o irrilevante.

## Geometria fisica da rappresentare

Il rotore è l'unione di **12 anelli completi con lo stesso centro**, orientati su piani verticali differenti; nel caso di due anelli i piani differiscono di 90°. I 12 piani sono distribuiti uniformemente: l'asse non orientato del foro ha periodicità di 180°, perciò passi di 15° tra 0° e 165° coprono i 360° se si considerano entrambe le direzioni di ciascun asse. Le **24 bobine** occupano i due archi liberi di ogni anello, tra le regioni di intersezione, con filo avvolto attraversando il foro dal basso verso l'alto; bobine adiacenti sono alimentate a semionde e poli contrapposti. L'intero rotore gira come corpo rigido in entrambi i versi dentro una **rete sferica fissa di alluminio**. Geometria della rete, connessioni elettriche e verso di avvolgimento vanno definiti nella mesh e nelle sorgenti prima di una conclusione quantitativa.

Questa **non** è la geometria costruita dallo script esaminato: `generate_ferrite_rings()` itera 24 volte su archi aperti da −55° a +80°, con orientamento ogni 15°, senza costruire i 12 anelli chiusi con due archi avvolti ciascuno. Il SIF della variante non contiene il nucleo di ferrite né la rotazione. Il file di dimensionamento dichiara inoltre un nucleo in PEEK, mentre README e script dichiarano ferrite: il materiale effettivo va riconciliato con la macchina fisica.

| Modello | B radiale medio CW sull'anello (µT) | CCW (µT) | Frazione di punti sferici con B radiale positivo (CW) | Flusso sulla sfera (Wb, CW) |
|---|---:|---:|---:|---:|
| Originale | +4.337874562 | −4.337874562 | 50.0% | +3.63 × 10⁻²¹ |
| Senza dipolo prescritto della gabbia | ~0 | ~0 | 42.9% | +5.43 × 10⁻²¹ |
| Senza sorgente equivalente schematica all'apice | +4.337874562 | −4.337874562 | 50.0% | −2.80 × 10⁻²¹ |
| Senza entrambi | ~0 | ~0 | 41.4% | −1.69 × 10⁻²¹ |

I valori residui riportati come `~0` sono dell'ordine di 10⁻¹² µT o inferiori, secondo il campione. Il dipolo prescritto è quindi responsabile dell'intero valore medio ±4,34 µT alla precisione mostrata. La formula alle righe 233–247 dello script dà da sola +4.3378745627 µT nel punto di misura per CW. Il coefficiente `0.00035` e il segno di `omega_mech` sono prescritti; `b_gap_approx` è calcolato ma non utilizzato nel momento del dipolo. Questo esperimento verifica la dipendenza interna dello script, non l'assenza di un possibile effetto fisico nel dispositivo.

Sulla sfera campionata il segno non è uniforme. Il flusso calcolato è prossimo allo zero a questa risoluzione; tale osservazione non costituisce una prova generale di conservazione numerica o accuratezza del modello. La sorgente equivalente schematica di «carica magnetica» all'apice non è accompagnata da una sorgente opposta nella stessa rappresentazione: prima di usare il modello per affermazioni sul flusso occorre verificare la conservazione del flusso nella geometria chiusa effettiva e fare uno studio di convergenza. La scelta di questa sorgente schematica non implica che l'apice fisico sia fittizio.

Il file `config/case_macchina.sif` contiene aria, alluminio e due gruppi di rame con densità di corrente nella direzione 3; non contiene materiale ferrite, né un accoppiamento di rotazione meccanica. In questa variante non sono presenti mesh, log o VTU attribuibili al caso. Le frecce della bussola nel quarto pannello del grafico sono versori radiali impostati nel codice, non orientamenti ottenuti dal campo calcolato.

## Prossima prova discriminante

Modellare la geometria e gli avvolgimenti effettivi in una mesh 3D, risolvere le correnti indotte nella gabbia mantenendo identiche le eccitazioni per +ω, 0 e −ω, e confrontare il campo vettoriale a più tempi e raggi su superfici chiuse. Registrare residui e convergenza con mesh e passo temporale. Per rivendicare una verifica sperimentale, pubblicare dati grezzi, orientamento e calibrazione delle sonde, misure del fondo e protocollo CW/CCW. Un segnale inatteso va conservato e sottoposto a questi controlli, non escluso a priori.

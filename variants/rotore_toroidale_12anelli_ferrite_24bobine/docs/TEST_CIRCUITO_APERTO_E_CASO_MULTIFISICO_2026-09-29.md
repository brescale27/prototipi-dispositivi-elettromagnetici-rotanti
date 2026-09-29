# Circuito aperto e preparazione del caso multifisico — 29 settembre 2026

## Test 1: un filo + su una bobina, un filo − sulla bobina adiacente; capi restanti aperti

**Topologia:** le bobine non sono collegate tra loro in un percorso chiuso. Una tensione applicata può depositare carica sui conduttori; con alimentazione variabile restano possibili correnti transitorie, capacità parassite, dispersioni e correnti di spostamento. Senza tensione/frequenza effettiva, posizione dei morsetti, isolamento e geometria dei fili non si può determinare univocamente la distribuzione di carica o la corrente capacitiva `I = C dV/dt`. Non è corretto usare ancora le correnti di 3 A a semionda come se scorressero nelle bobine aperte.

Sono stati calcolati due limiti separati sullo stesso campionamento di 288 direzioni × 3 raggi × 3 regimi (2592 posizioni):

1. **Senza corrente né carica prescritta:** il campo prodotto dalle bobine è zero per rotore fermo, CW e CCW. Il campo ambientale non è compreso; una bussola reale seguirebbe principalmente quello.
2. **Sensibilità a cariche mobili:** lo script `scripts/simulate_open_circuit.py` esamina sia una coppia (+1 nC, −1 nC) su due posizioni equatoriali adiacenti distanti 15°, sia 24 posizioni equatoriali alternate +/− ogni 15°; tutti i punti sono al raggio di 35 mm. I due cablaggi possibili sono etichettati `pair` e `alternating24`. Queste cariche non sono derivate dalla tensione ai capi, né equivalgono alla distribuzione sulla bobina reale. Calcola `E` di Coulomb e `B = μ0/(4π) q (v × R)/|R|³` a velocità 0 e ±1200 RPM, trascurando radiazione, induzione nella gabbia e polarizzazione dei metalli. Le letture medie e RMS sono in `data/open_circuit_charge_pair_1nC.json` e `data/open_circuit_alternating24_1nC.json`.

| Raggio sonda | B istantaneo massimo, coppia ±1 nC | B istantaneo massimo, 24 cariche alternate ±1 nC | B medio su un giro | Bussola DC |
|---|---:|---:|---|---|
| 55 mm | 0,549 pT | 0,114 pT | ≈0 in CW e CCW | indeterminata dal solo dispositivo |
| 70 mm | 0,137 pT | 0,00447 pT | ≈0 | indeterminata |
| 100 mm | 0,0310 pT | 0,0000403 pT | ≈0 | indeterminata |

Questi numeri scalano linearmente con la carica scelta **nel solo modello di due cariche**. Una distribuzione asimmetrica reale, capacità e cablaggi differenti possono cambiare risultato e media. I dati salvano il vettore elettrico e magnetico medio, il campo RMS e la massima ampiezza istantanea nei campioni; non sono misure con magnetometro o bussola fisici. Il caso di cariche fisse nel rotore non incorpora la modulazione a semionde: con circuito aperto la forma d'onda della carica deve essere prima determinata dal circuito capacitivo.

## Test 2: caso più completo con mesh e solver multifisico

Lo script `scripts/build_multiphysics_geometry.py` è predisposto per costruire con Gmsh 12 tori solidi con centro comune, piani distanziati di 15°, fusi nelle loro intersezioni; un guscio sferico fisso tra 41 e 43 mm funge da prima approssimazione geometrica della rete, dentro una sfera d'aria di raggio 150 mm. Il programma costituisce il generatore geometrico parametrico per la successiva discretizzazione della mesh.

Per trasformarlo in un test numerico interpretabile occorrono, nell'ordine:

- la sezione e il materiale veri degli anelli (il JSON dice PEEK, README dice ferrite); la ferrite richiede eventualmente curva B–H e perdite;
- i volumi delle 24 bobine sui due archi tra intersezioni, orientamento di ogni spira, cablaggio dei diodi e circuito aperto/chiuso;
- passo, diametro e collegamenti della trama di alluminio, oppure tensore di conducibilità equivalente verificato contro la trama;
- interfaccia mobile rotore–aria–gabbia o formulazione equivalente che includa le correnti di movimento, con controlli di mesh e passo temporale;
- estrazione vettoriale su superfici chiuse a più raggi per gli stati CW/fermo/CCW e flusso `∮ B·dS`, con monitoraggio dei residui di Maxwell;
- per il circuito aperto alimentato in AC, un modello elettroquasistatico/circuitale delle capacità e dei transitori prima del calcolo magnetico.

Il secondo test **non è ancora una soluzione FEM**. I risultati del primo test non dimostrano né escludono un'anomalia della macchina completa. Il passo successivo è eseguire e verificare la mesh su una macchina con Gmsh/Elmer e risolvere i casi accoppiati, senza imporre un dipolo o il suo segno nel post-processing.

# Phase 0 hand-check labels

Slice is Volta Redonda RJ IBGE 3306305 year 2024.
All 100 source items were fetched from the PNCP item API; none were left unresolved.
Item path used: /api/pncp/v1/orgaos/{cnpj}/compras/{ano}/{sequencial}/itens/{n}.
Resultados were read when present; 44 items had HTTP 204 and were checked on the item resource only.
CSV unit matched the source unit on every row.
CSV qty times unit_price matched total on every row, so no arithmetic data-error labels were used.
Four rows had a later homologated unit price different from the CSV (ranks 45, 52, 66, 88); the CSV still matched the source estimate except rank 45.
Label unit error was used only when this row unit (or pack size) was not the unit that set the peer median.
Label spec difference was used when form, concentration, brand family, or contract scope differed from the peer group.
Label real means the source confirms the same item, unit and price and the peer group is the same presentation.
Real is a surviving price anomaly, not a fraud verdict.
No raw CPF was stored; the one natural-person supplier stays masked as ***.861.487-**.

## Counts
n_real 63.
n_unit_error 17.
n_spec_difference 20.
n_data_error 0.
n_unresolved 0.
precision_real 0.63.

## Per row
Rank 1 real - Source item 1 confirms 800 comprimido at R$365 for piridostigmine 60mg CATMAT 271764 against peer median R$0.52 on the same unit.
Rank 2 real - Source item 1 confirms 20 unidade at R$7240.73 for the same TASER-cartridge CATMAT 610825 text as peers at about R$285.
Rank 3 unit error - Source item 14 is Frasco 20 ml at R$16.15; the CATMAT 269962 peer median R$0.06 is comprimido.
Rank 4 real - Source item 6 confirms 2 unidade at R$7929 for the same rotameter description used by peers near R$400.
Rank 5 unit error - Source item 13 is Frasco 20 ml at R$10.06; the CATMAT 269962 peer median R$0.06 is comprimido.
Rank 6 spec difference - Source item 10 is Ampola 3 ml injectable; CATMAT 355786 peers that set the median are 40 mg/ml xarope in 120 ml or per ml.
Rank 7 spec difference - Source item 17 is 2257 L bottled concentrate at R$23.30; CATMAT 420084 peers at R$0.09 are 0.4M to 19M L bulk lots.
Rank 8 unit error - Source item 62 is Ampola 2.5 ml at R$2.71; the CATMAT 269388 peer median R$0.19 is comprimido 4 mg.
Rank 9 real - Source item 20 confirms 11750 kg chuchu at R$7.18 versus peer median R$2.48 on the same CATMAT and kg.
Rank 10 spec difference - Source item 8 is a generic CATSER 16390 textile job of 1 UN at R$259 with no scope that matches the mixed peer jobs.
Rank 11 real - Source item 16 confirms Ampola 1 ml epinephrine 1 mg/ml at R$21.60 versus same-unit peers near R$1.23.
Rank 12 real - Source item 4 confirms the 5-tube silicone circuit at R$369.38 versus same CATMAT 614940 peers near R$30.73.
Rank 13 real - Source item 11 confirms the 25G Quincke spinal needle at R$24.30 versus same CATMAT peers near R$6.61.
Rank 14 unit error - Source item 74 is Caixa 25 PCT at R$86.99; the CATMAT 618310 peer median R$3.74 is a 100-cup pack.
Rank 15 real - Source item 42 confirms 2 unidade at R$9750 for the same 380 V 80 A molded-case CATMAT 616962 text as peers near R$97.
Rank 16 unit error - Source item 137 is Ampola 5 ml at R$3.01; the CATMAT 308882 peer median R$0.18 is comprimido 400 mg + 80 mg.
Rank 17 unit error - Source item 75 is Caixa 25 PCT at R$73.85; the CATMAT 618310 peer median R$3.74 is a 100-cup pack.
Rank 18 real - Source item 19 confirms 4 unidade at R$162.35 for the same hydraulic auto-body CATMAT 265602 text as peers near R$10.79.
Rank 19 real - Source item 10 confirms Frasco 2.5 ml travoprost 0.04 mg/ml at R$106.73 versus same-unit peers near R$19.99.
Rank 20 unit error - Source item 103 is Centena at R$23.05; the CATMAT 614636 peer median R$0.56 is per envelope Unidade.
Rank 21 real - Source item 43 confirms 2 unidade at R$6278 for the same 380 V 80 A CATMAT 616962 text as peers near R$97.
Rank 22 real - Source item 17 confirms 1 unidade at R$3193 for the same 7500 NTU six-standard kit CATMAT 428426 text as peers near R$110.
Rank 23 spec difference - Source item 7 is Alprazolam comprimido at R$2.43 with no strength; the description peer group mixes 2 mg tablets near R$0.11.
Rank 24 real - Source item 20 confirms 4 unidade at R$4971 for the same 7500 NTU kit CATMAT 428426 text as peers near R$88.
Rank 25 spec difference - Source item 1 is a single BYD heavy-vehicle maintenance lot at R$200000 versus generic CATSER peers near R$5700.
Rank 26 real - Source item 18 confirms 1 unidade at R$2794 for the same 7500 NTU kit CATMAT 428426 text as peers near R$110.
Rank 27 unit error - Source item 1 is Unidade at R$79.87 while the item text is a 100-cup pack; same-code pack peers sit near R$3.50 to R$5.57.
Rank 28 unit error - Source item 50 is Pacote 10 UN at R$58.95; the CATMAT 617019 peer median R$3.34 is Unidade or a 10 m roll.
Rank 29 spec difference - Source item 1 is one plotagem lot at R$6338.90; CATSER 24902 peers that set the median are per-sheet A1/A3 jobs.
Rank 30 real - Source item 4 confirms 1 portable O2 detector at R$474.85 versus the same CATMAT 617520 text near R$43.97.
Rank 31 unit error - Source item 196 is Unidade at R$148.99; CATMAT 481317 peers that set the median are Caixa 75 UN cotton swabs near R$1.50 to R$3.55.
Rank 32 real - Source item 60 confirms 2 unidade at R$4926.16 for the same 380 V 80 A CATMAT 616962 text as peers near R$121.50.
Rank 33 spec difference - Source item 8 is Metformina cloridrato comprimido at R$0.77 with no strength; description peers mix plain 500 mg near R$0.11 and vildagliptin combos.
Rank 34 unit error - Source item 1 is Copo 200 ml at R$26.00; the CATMAT 445484 peer median R$1.02 is Garrafa 500 ml.
Rank 35 unit error - Source item 2 is Copo 200 ml at R$26.00; the CATMAT 445484 peer median R$1.02 is Garrafa 500 ml.
Rank 36 spec difference - Source item 2 is generic CATSER 22888 locacao at R$100 per UN; peers near R$4 are other unspecified rented goods.
Rank 37 spec difference - Source item 94 is Insulina Frasco 10 ml at R$199.20 with no insulin type; description peers mix NPH, analog, vial and pen.
Rank 38 real - Source item 3 confirms 1 unidade at R$900 for the same 600 W LED panel CATMAT 616534 text as peers near R$5285.
Rank 39 spec difference - Source item 1 is one event/competition buffet contract at R$349500 versus CATSER 12807 peers that are smaller meal jobs.
Rank 40 real - Source item 98 confirms Frasco 250 ml mannitol 20% at R$10.83 versus same-unit peers near R$8.12.
Rank 41 real - Source item 104 confirms Frasco-Ampola methylprednisolone 500 mg at R$32.61 versus same-unit peers near R$16.50.
Rank 42 real - Source item 40 confirms 4 unidade at R$2700 for the same 380 V 80 A CATMAT 616962 text as peers near R$97.
Rank 43 real - Source item 98 confirms 500 unidade soap paste at R$7.50 versus CATMAT 287791 peers near R$5.37.
Rank 44 real - Source item 40 confirms Frasco 100 ml ciprofloxacin 2 mg/ml at R$33.91 versus same-code 100 ml peers near R$8.40.
Rank 45 unit error - Source item 4 is qty 12 PÁGINA at R$30000 (estimate R$34000, later award R$6000); peers treat the same CATSER as a monthly franchise not a page.
Rank 46 real - Source item 21 confirms Frasco-Ampola amoxicillin 1 g + 200 mg at R$38.75 versus same-unit peers near R$9.98.
Rank 47 real - Source item 13 confirms Frasco 200 doses salbutamol at R$18.52 versus same-unit peers near R$10.72.
Rank 48 real - Source item 84 confirms Ampola 5 ml flumazenil 0.1 mg/ml at R$15.24 versus same-unit peers near R$5.20.
Rank 49 real - Source item 1 confirms 3700 monofocal resin lenses at R$4.89 versus CATMAT 447808 peers near R$24.99.
Rank 50 real - Source item 8 confirms 40 MDF coffins at R$359 versus CATMAT 622634 peers near R$550.
Rank 51 unit error - Source item 39 is Litro at R$172.50; CATMAT 616756 peers that set the median are Unidade or Lata 0.9 L near R$70.90.
Rank 52 spec difference - Source item 7 is Esfigmomanometro at R$1512.45 with no model; description peers are basic aneroid or digital arm cuffs near R$108.
Rank 53 real - Source item 12 confirms Ampola 2 ml adenosine 3 mg/ml at R$10.89 versus same-unit peers near R$12.00.
Rank 54 spec difference - Source item 1 is one school reform at R$4877534.13; CATSER 1627 peers are smaller building-maintenance lots near R$163900.
Rank 55 spec difference - Source item 1 is one sanitation works lot at R$1589200; CATSER 1872 peers are smaller capture/adduction jobs near R$122508.
Rank 56 spec difference - Source item 1 is one artistic presentation at R$54000 versus free-text peers that mix local shows near R$1530.
Rank 57 spec difference - Source item 1 is GE Healthcare medical-equipment maintenance at R$12064 versus CATSER 16055 peers that are small parts or other devices.
Rank 58 real - Source item 42 confirms 80 NiTi R50 endodontic files at R$60.90 versus CATMAT 608102 peers near R$76.49.
Rank 59 real - Source item 4 confirms 1766 autoclave 20 L buckets at R$9.98 versus CATMAT 367126 peers near R$7.28.
Rank 60 real - Source item 8 confirms 1 unidade at R$1153 for the same 7500 NTU kit CATMAT 428426 text as peers near R$110.
Rank 61 real - Source item 19 confirms 1 unidade at R$1144 for the same 7500 NTU kit CATMAT 428426 text as peers near R$110.
Rank 62 unit error - Source item 56 is Frasco 100 ml at R$21.02; CATMAT 341174 peers that set the median are Frasco 250 ml mouthwash near R$5.15.
Rank 63 real - Source item 60 confirms Frasco-Ampola daptomycin 500 mg at R$332.32 versus same-unit peers near R$133.35.
Rank 64 real - Source item 34 confirms Ampola 2 ml bromopride 5 mg/ml at R$3.38 versus same-unit peers near R$1.44.
Rank 65 real - Source item 41 confirms 2 unidade at R$2000 for the same 380 V 80 A CATMAT 616962 text as peers near R$97.
Rank 66 real - Source item 161 confirms 500 of the same 80 W E27 LED CATMAT 614575 at R$106.52 (later award R$62) versus peers near R$11.12.
Rank 67 real - Source item 100 confirms Frasco-Ampola meropenem 1 g at R$31.19 versus same-unit peers near R$16.00.
Rank 68 real - Source item 182 confirms 350 cork sheets 4 mm at R$37.64 versus CATMAT 604558 peers near R$41.14.
Rank 69 real - Source item 1 confirms Ampola 2 ml pethidine 50 mg/ml at R$11.08 versus same-unit peers near R$3.70.
Rank 70 real - Source item 78 confirms Ampola 10 ml etomidate 2 mg/ml at R$19.57 versus same-unit peers near R$9.79.
Rank 71 real - Source item 117 confirms Frasco-Ampola omeprazole 40 mg at R$29.94 versus same-unit peers near R$9.00.
Rank 72 real - Source item 63 confirms Ampola 2 ml dexmedetomidine 100 mcg/ml at R$19.40 versus same-unit peers near R$7.78.
Rank 73 real - Source item 16 confirms 30 of the same 1510 W demolition hammer CATMAT 485697 at R$159.60 versus peers near R$53.11.
Rank 74 spec difference - Source item 8 is Metformina cloridrato comprimido at R$0.77 with no strength; description peers mix plain tablets near R$0.12 and combos.
Rank 75 real - Source item 39 confirms 4 unidade at R$1600 for the same 380 V 80 A CATMAT 616962 text as peers near R$97.
Rank 76 real - Source item 22 confirms the 3 Fr umbilical catheter at R$142.89 versus same CATMAT 448700 peers near R$13.42.
Rank 77 real - Source item 2 confirms the Ag/AgCl glass pH electrode at R$545.13 versus same CATMAT 282057 peers near R$29.95.
Rank 78 real - Source item 44 confirms Ampola 4 ml clindamycin 150 mg/ml at R$10.78 versus same-unit peers near R$3.23.
Rank 79 spec difference - Source item 52 is Fita adesiva Unidade at R$11.64 with no material or size; description peers mix crepe, PP and pack sizes.
Rank 80 real - Source item 110 confirms morphine sulfate 10 mg comprimido at R$1.23 versus same-unit peers near R$0.55.
Rank 81 real - Source item 177 confirms Embalagem 60 doses salmeterol at R$83.42 versus same-pack peers near R$110.04.
Rank 82 real - Source item 136 confirms Ampola 2 ml sugammadex 100 mg/ml at R$141.81 versus same-volume peers near R$43.54.
Rank 83 real - Source item 74 confirms 400 pair nitrile gloves at R$4.06 versus CATMAT 614948 peers near R$1.74.
Rank 84 real - Source item 1 confirms 30 copper fork terminals at R$35.95 versus CATMAT 487710 peers near R$4.48.
Rank 85 real - Source item 10 confirms 1320 kg spinach at R$21.62 versus CATMAT 463824 kg peers near R$4.33.
Rank 86 real - Source item 8 confirms ferrous sulfate 40 mg comprimido at R$0.68 versus CATMAT 292344 peers near R$0.06.
Rank 87 real - Source item 52 confirms 3 unidade at R$1578.50 for the same 380 V 80 A CATMAT 616962 text as peers near R$121.50.
Rank 88 spec difference - Source item 1 is one painting/small-works lot estimated at R$824834.72 (later award R$569135.95) versus other jobs near R$81228.
Rank 89 real - Source item 27 confirms 15 carbide 3.15 mm drills at R$90 versus CATMAT 620481 Unidade peers near R$7.13.
Rank 90 unit error - Source item 75 is Unidade at R$0.50 for a 20 g roll; CATMAT 617553 peers that set the median are pack or kg priced as Unidade near R$11.88.
Rank 91 unit error - Source item 15 is Bolsa 100 ml at R$4.80; CATMAT 276839 peers that set the median are Ampola or Frasco 10 ml near R$0.46.
Rank 92 real - Source item 5 confirms 30 zinc 25 mm compression sleeves at R$29.44 versus CATMAT 419850 peers near R$4.21.
Rank 93 real - Source item 134 confirms 500 L-type file folders at R$22.33 versus CATMAT 419359 peers near R$21.70.
Rank 94 spec difference - Source item 1 is one artistic presentation at R$20000 versus free-text peers that mix other artists near R$1530.
Rank 95 spec difference - Source item 9 is one CD8/CD56 flow-cytometry kit at R$3531; CATMAT 615714 peers mix kit sizes and per-test units near R$234.
Rank 96 real - Source item 9 confirms 300 m of 120 mm2 flexible cable at R$192.99 versus CATMAT 307367 peers near R$33.70.
Rank 97 real - Source item 36 confirms 14 two-pole switches at R$36.74 versus CATMAT 212360 peers near R$6.04.
Rank 98 real - Source item 41 confirms Ampola 5 ml cisatracurium 2 mg/ml at R$24.65 versus same-volume peers near R$11.67.
Rank 99 real - Source item 119 confirms Bisnaga 45 g zinc oxide plus vitamins at R$6.63 versus same-unit peers near R$3.19.
Rank 100 real - Source item 6 confirms 200 kg spinach at R$21.62 versus CATMAT 463824 kg peers near R$5.52.

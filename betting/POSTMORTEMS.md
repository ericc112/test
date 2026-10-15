# Post-mortems

Every graded loss is examined here, including passes and Low-confidence legs. `python -m edge review` writes the diagnosis; `python -m edge tag ID "tag" --lesson "..."` confirms the cause. Tags: `variance`, `opportunity`, `correlated`, `role/lineup`, `model bias`, `market info`, `stale line`, `data error`, `format misread`.

## 2026-10-14: 138 losses from 16 independent causes

| # | Leg | Result | Our p | Action | Sources | Auto tag | Confirmed | Evidence |
|---|---|---|---|---|---|---|---|---|
| 522 | xKacpersky cs_kills_m12 over 25.5 | 25 | 0.6863 (Medium) | lean | model 71%, hist 75% | variance | **untagged** | root leg of a 10-leg script loss: #522, #530, #571, #590, #627, #632, #638, #661, #683, #698; closest possible loss (missed by the minimum) |
| 524 | yuurih cs_headshots_m12 under 14.0 | 15 | 0.6779 (High) | lean | model 71%, hist 67% | variance | **untagged** | root leg of a 11-leg script loss: #524, #560, #579, #594, #625, #637, #641, #644, #666, #673, #712 |
| 529 | Jame cs_headshots_m12 under 9.0 | 10 | 0.6678 (Medium) | lean | model 70%, hist 64% | variance | **untagged** | root leg of a 13-leg script loss: #529, #559, #608, #610, #635, #651, #654, #668, #670, #674, #685, #696, #699 |
| 530 | sjuush cs_headshots_m12 over 13.5 | 13 | 0.6616 (Medium) | lean | model 67%, hist 75% | correlated | **untagged** | same game script as #522 (variance); own read: variance; closest possible loss (missed by the minimum) |
| 537 | PokemoN cs_kills_m12 over 26.5 | 26 | 0.6524 (Medium) | lean | model 66%, hist 100% | variance | **untagged** | root leg of a 9-leg script loss: #537, #540, #575, #615, #664, #669, #678, #688, #692; closest possible loss (missed by the minimum) |
| 540 | PokemoN cs_headshots_m12 over 16.5 | 14 | 0.6432 (Medium) | lean | model 64%, hist 100% | correlated | **untagged** | same game script as #537 (variance); own read: variance |
| 550 | sav cs_headshots_m12 over 13.5 | 11 | 0.6109 (Medium) | lean | model 60%, hist 88% | variance | **untagged** | root leg of a 8-leg script loss: #550, #555, #605, #630, #640, #652, #658, #675 |
| 555 | ju1ces cs_kills_m12 under 31.5 | 32 | 0.6082 (Medium) | pass | model 64%, hist 50% (against) | correlated | **untagged** | same game script as #550 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 559 | HObbit cs_kills_m12 under 26.5 | 38 | 0.6043 (Medium) | lean | model 64%, hist 50% (against) | correlated | **untagged** | same game script as #529 (variance); own read: variance |
| 560 | yuurih cs_kills_m12 under 26.0 | 29 | 0.6036 (Medium) | lean | model 62%, hist 69% | correlated | **untagged** | same game script as #524 (variance); own read: variance |
| 565 | Raijin cs_kills_m12 under 28.5 | 31 | 0.5996 (Medium) | lean | model 62%, hist 64% | variance | **untagged** | root leg of a 5-leg script loss: #565, #574, #613, #628, #631 |
| 571 | stavn cs_headshots_m12 over 8.5 | 6 | 0.5874 (Medium) | lean | model 59%, hist 56% | correlated | **untagged** | same game script as #522 (variance); own read: variance |
| 574 | KusMe cs_kills_m12 under 28.5 | 30 | 0.5865 (Medium) | lean | model 61%, hist 54% | correlated | **untagged** | same game script as #565 (variance); own read: variance |
| 575 | laxiee cs_kills_m12 over 26.5 | 22 | 0.5856 (Medium) | lean | model 58%, hist 86% | correlated | **untagged** | same game script as #537 (variance); own read: variance |
| 579 | KSCERATO cs_kills_m12 under 33.0 | 40 | 0.5818 (Medium) | lean | model 60%, hist 57% | correlated | **untagged** | same game script as #524 (variance); own read: variance |
| 586 | phzy cs_kills_m12 under 31.5 | 37 | 0.5785 (Low) | pass | model 59%, hist 65% | variance | **untagged** | root leg of a 2-leg script loss: #586, #704; logged as a PASS: no money on it; reviewed for calibration |
| 590 | m0NESY cs_headshots_m12 under 14.5 | 17 | 0.5753 (Low) | pass | model 60%, hist 56% | correlated | **untagged** | same game script as #522 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 594 | molodoy cs_kills_m12 under 33.0 | 39 | 0.5732 (Low) | pass | model 59%, hist 63% | correlated | **untagged** | same game script as #524 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 605 | Roflko cs_headshots_m12 under 15.5 | 21 | 0.5648 (Low) | pass | model 59%, hist 54% | correlated | **untagged** | same game script as #550 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 606 | fear cs_kills_m12 under 25.0 | 27 | 0.5646 (Low) | pass | model 59%, hist 52% | variance | **untagged** | root leg of a 11-leg script loss: #606, #607, #616, #643, #646, #649, #682, #686, #691, #703, #710; logged as a PASS: no money on it; reviewed for calibration |
| 607 | dwushka cs_kills_m12 under 29.5 | 40 | 0.5641 (Low) | pass | model 58%, hist 55% | correlated | **untagged** | same game script as #606 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 608 | dumau cs_headshots_m12 under 14.5 | 15 | 0.5629 (Low) | pass | model 59%, hist 44% (against) | correlated | **untagged** | same game script as #529 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 610 | dumau cs_kills_m12 under 31.0 | 42 | 0.5599 (Low) | pass | model 58%, hist 59% | correlated | **untagged** | same game script as #529 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 613 | bluewh1te cs_kills_m12 under 26.5 | 29 | 0.5571 (Low) | pass | model 57%, hist 64% | correlated | **untagged** | same game script as #565 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 615 | z4kr cs_headshots_m12 over 10.5 | 8 | 0.5569 (Low) | pass | model 56%, hist 46% (against) | correlated | **untagged** | same game script as #537 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 616 | mazay cs_headshots_m12 under 17.5 | 18 | 0.556 (Low) | pass | model 58%, hist 44% (against) | correlated | **untagged** | same game script as #606 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 625 | molodoy cs_headshots_m12 under 12.5 | 17 | 0.5482 (Low) | pass | model 55%, hist 66% | correlated | **untagged** | same game script as #524 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 627 | TeSeS cs_kills_m12 under 28.5 | 31 | 0.5479 (Low) | pass | model 56%, hist 63% | correlated | **untagged** | same game script as #522 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 628 | z1Nny cs_headshots_m12 over 19.0 | 16 | 0.5476 (Low) | pass | model 54%, hist 64% | correlated | **untagged** | same game script as #565 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 630 | sav cs_kills_m12 over 24.5 | 23 | 0.5462 (Low) | pass | model 54%, hist 75% | correlated | **untagged** | same game script as #550 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 631 | Lack1 cs_kills_m12 under 28.5 | 31 | 0.5455 (Low) | pass | model 56%, hist 54% | correlated | **untagged** | same game script as #565 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 632 | karrigan cs_kills_m12 under 21.0 | 36 | 0.545 (Low) | pass | model 56%, hist 58% | correlated | **untagged** | same game script as #522 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 635 | try cs_kills_m12 under 31.5 | 41 | 0.5433 (Low) | pass | model 56%, hist 56% | correlated | **untagged** | same game script as #529 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 637 | d1Ledez cs_kills_m12 under 27.5 | 31 | 0.5411 (Low) | pass | model 56%, hist 56% | correlated | **untagged** | same game script as #524 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 638 | TeSeS cs_headshots_m12 over 16.5 | 15 | 0.54 (Low) | pass | model 55%, hist 37% (against) | correlated | **untagged** | same game script as #522 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 640 | yourwombat cs_kills_m12 over 24.5 | 21 | 0.5394 (Low) | pass | model 54%, hist 62% | correlated | **untagged** | same game script as #550 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 641 | Magnojez cs_headshots_m12 under 15.0 | 19 | 0.5392 (Low) | pass | model 56%, hist 50% (against) | correlated | **untagged** | same game script as #524 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 643 | kade0 cs_headshots_m12 under 14.5 | 15 | 0.5379 (Low) | pass | model 56%, hist 45% (against) | correlated | **untagged** | same game script as #606 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 644 | zorte cs_kills_m12 under 26.0 | 27 | 0.5375 (Low) | pass | model 55%, hist 58% | correlated | **untagged** | same game script as #524 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 646 | jackasmo cs_headshots_m12 under 18.5 | 21 | 0.5355 (Low) | pass | model 56%, hist 48% (against) | correlated | **untagged** | same game script as #606 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 649 | jackasmo cs_kills_m12 under 30.5 | 35 | 0.5344 (Low) | pass | model 55%, hist 48% (against) | correlated | **untagged** | same game script as #606 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 651 | zweih cs_headshots_m12 under 13.5 | 25 | 0.5339 (Low) | pass | model 55%, hist 53% | correlated | **untagged** | same game script as #529 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 652 | Roflko cs_kills_m12 under 26.5 | 39 | 0.5336 (Low) | pass | model 56%, hist 38% (against) | correlated | **untagged** | same game script as #550 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 654 | art cs_headshots_m12 under 11.5 | 15 | 0.5318 (Low) | pass | model 56%, hist 43% (against) | correlated | **untagged** | same game script as #529 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 658 | foggers cs_kills_m12 under 29.5 | 31 | 0.5295 (Low) | pass | model 55%, hist 50% (against) | correlated | **untagged** | same game script as #550 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 661 | karrigan cs_headshots_m12 under 10.5 | 17 | 0.5292 (Low) | pass | model 54%, hist 56% | correlated | **untagged** | same game script as #522 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 664 | EmiliaQAQ cs_kills_m12 under 29.5 | 30 | 0.5273 (Low) | pass | model 54%, hist 55% | correlated | **untagged** | same game script as #537 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 666 | Boombl4 cs_headshots_m12 under 10.5 | 13 | 0.527 (Low) | pass | model 54%, hist 57% | correlated | **untagged** | same game script as #524 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 668 | latto cs_kills_m12 under 32.0 | 33 | 0.5253 (Low) | pass | model 54%, hist 50% (against) | correlated | **untagged** | same game script as #529 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 669 | laxiee cs_headshots_m12 over 15.0 | 10 | 0.5229 (Low) | pass | model 51%, hist 60% | correlated | **untagged** | same game script as #537 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 670 | zweih cs_kills_m12 under 26.0 | 39 | 0.5229 (Low) | pass | model 53%, hist 62% | correlated | **untagged** | same game script as #529 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 673 | Boombl4 cs_kills_m12 under 23.5 | 24 | 0.521 (Low) | pass | model 53%, hist 52% | correlated | **untagged** | same game script as #524 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 674 | xiELO cs_kills_m12 under 29.0 | 36 | 0.5207 (Low) | pass | model 54%, hist 43% (against) | correlated | **untagged** | same game script as #529 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 675 | ju1ces cs_headshots_m12 under 15.5 | 16 | 0.52 (Low) | pass | model 55%, hist 0% (against) | correlated | **untagged** | same game script as #550 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 678 | C4LLM3SU3 cs_kills_m12 over 28.5 | 27 | 0.5194 (Low) | pass | model 51%, hist 64% | correlated | **untagged** | same game script as #537 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 682 | cairne cs_headshots_m12 over 15.5 | 11 | 0.5177 (Low) | pass | model 51%, hist 52% | correlated | **untagged** | same game script as #606 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 683 | adamb cs_headshots_m12 over 14.5 | 12 | 0.5177 (Low) | pass | model 51%, hist 50% (against) | correlated | **untagged** | same game script as #522 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 685 | HObbit cs_headshots_m12 under 11.5 | 18 | 0.5169 (Low) | pass | model 52%, hist 60% | correlated | **untagged** | same game script as #529 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 686 | n0rb3r7 cs_kills_m12 under 28.5 | 30 | 0.516 (Low) | pass | model 53%, hist 52% | correlated | **untagged** | same game script as #606 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 688 | Starry cs_kills_m12 over 31.5 | 30 | 0.5152 (Low) | pass | model 53%, hist 36% (against) | correlated | **untagged** | same game script as #537 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 691 | jambo cs_headshots_m12 under 11.5 | 12 | 0.5142 (Low) | pass | model 51%, hist 67% | correlated | **untagged** | same game script as #606 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 692 | EmiliaQAQ cs_headshots_m12 over 18.5 | 17 | 0.5139 (Low) | pass | model 51%, hist 50% (against) | correlated | **untagged** | same game script as #537 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 696 | n1ssim cs_kills_m12 under 27.5 | 32 | 0.5127 (Low) | pass | model 53%, hist 44% (against) | correlated | **untagged** | same game script as #529 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 698 | kyousuke cs_kills_m12 over 33.0 | 28 | 0.5115 (Low) | pass | model 50%, hist 56% | correlated | **untagged** | same game script as #522 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 699 | n1ssim cs_headshots_m12 over 14.5 | 13 | 0.5114 (Low) | pass | model 49% (against), hist 61% | correlated | **untagged** | same game script as #529 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 703 | mizu cs_kills_m12 under 30.0 | 37 | 0.5077 (Low) | pass | model 52%, hist 43% (against) | correlated | **untagged** | same game script as #606 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 704 | ryu cs_kills_m12 under 30.5 | 43 | 0.5074 (Low) | pass | model 51%, hist 54% | correlated | **untagged** | same game script as #586 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 710 | mizu cs_headshots_m12 under 15.5 | 16 | 0.5041 (Low) | pass | model 51%, hist 55% | correlated | **untagged** | same game script as #606 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 712 | zorte cs_headshots_m12 over 9.0 | 6 | 0.5033 (Low) | pass | model 49% (against), hist 56% | correlated | **untagged** | same game script as #524 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 733 | Jool kills_m123 under 14.0 | 15 | 0.4942 (Low) | pass | model 55%, hist 78% | variance | **untagged** | we priced this side at 49%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; 15 kills vs 13.7 expected for the actual game results; games had 42/34/29 total kills |
| 737 | VicLa kills_m123 under 9.0 | 11 | 0.455 (Low) | pass | model 54%, hist 32% (against) | variance | **untagged** | we priced this side at 46%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; 11 kills vs 11.5 expected for the actual game results; games had 30/30/34 total kills |
| 739 | Katie Volynets ml_live over 0.5 | 0.0 | 0.5929 (Medium) | pass | model 62%, market 54% | variance | **untagged** | logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 741 | Aryna Sabalenka ml_pre over 0.5 | 0.0 | 0.7875 (Low) | pass | model 87% | variance | **untagged** | logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 742 | Paulo Dybala shots over 1.5 | 1.0 | 0.6992 (Medium) | user_entry | market 78%, hist 70% | variance | **untagged** | root leg of a 5-leg script loss: #742, #743, #745, #746, #747; closest possible loss (missed by the minimum) |
| 743 | Paulo Dybala sot over 0.5 | 0.0 | 0.6231 (Medium) | lean | market 61%, hist 70% | correlated | **untagged** | same game script as #742 (variance); own read: variance; closest possible loss (missed by the minimum) |
| 745 | Paulo Dybala sot over 1.5 | 0.0 | 0.2802 (Low) | pass | market 24% (against), hist 40% (against) | correlated | **untagged** | same game script as #742 (variance); own read: variance; we priced this side at 28%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 746 | Paulo Dybala shots over 3.5 | 1.0 | 0.2755 (Low) | pass | market 32% (against), hist 40% (against) | correlated | **untagged** | same game script as #742 (variance); own read: variance; we priced this side at 28%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 747 | Paulo Dybala sot over 2.5 | 0.0 | 0.0838 (Low) | pass | market 7% (against), hist 0% (against) | correlated | **untagged** | same game script as #742 (variance); own read: variance; we priced this side at 8%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 848 | Boone Jenner skater_sog over 1.5 | 0 | 0.5169 (Low) | pass | model 60%, hist 57% | variance | **untagged** | root leg of a 20-leg script loss: #848, #859, #879, #889, #914, #924, #935, #946, #966, #1000, #1009, #1010, #1012, #1019, #1022, #1032, #1035, #1047, #1068, #1072; logged as a PASS: no money on it; reviewed for calibration |
| 853 | Brice Turang batter_hrr under 1.5 | 2 | 0.5498 (Low) | pass | model 58%, market 59%, hist 39% (against) | correlated | **untagged** | same game script as #918 (opportunity); own read: variance; logged as a PASS: no money on it; reviewed for calibration; 4 PA from the 2 slot; opposing starter Blake Snell went 18 outs / 4 ER; 0 of 2 H+R+RBI came off the starter, 2 off the bullpen (the bullpen part alone beat the line: not just the starter's fault); closest possible loss (missed by the minimum) |
| 859 | Jakob Chychrun skater_toi over 25.0 | 23.05 | 0.3 (Low) | pass | model 33% (against), hist 20% (against) | correlated | **untagged** | same game script as #848 (variance); own read: variance; we priced this side at 30%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 869 | Blake Snell pitcher_hits_allowed under 3.5 | 4 | 0.5762 (Low) | pass | model 58%, market 55%, hist 60% | correlated | **untagged** | same game script as #918 (opportunity); own read: variance; logged as a PASS: no money on it; reviewed for calibration; line: 18 outs, 24 BF, 101 pitches, 4 H, 2 BB, 9 K, 4 ER; closest possible loss (missed by the minimum) |
| 879 | Boone Jenner skater_sog over 0.5 | 0 | 0.8134 (High) | lean | market 83%, hist 80% | correlated | variance | same game script as #848 (variance); own read: variance; closest possible loss (missed by the minimum) |
| 889 | Alex Ovechkin skater_sog over 1.5 | 0 | 0.7704 (Medium) | pass | market 76%, hist 93% | correlated | **untagged** | same game script as #848 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 893 | Nathan MacKinnon skater_points over 0.5 | 0 | 0.7544 (High) | pass | market 76%, hist 77% | variance | **untagged** | root leg of a 15-leg script loss: #893, #902, #931, #939, #974, #977, #992, #993, #997, #1039, #1046, #1051, #1052, #1075, #1076; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 895 | Jackson Chourio batter_strikeouts over 0.5 | 0 | 0.7497 (High) | pass | market 76%, hist 70% | correlated | **untagged** | same game script as #918 (opportunity); own read: variance; logged as a PASS: no money on it; reviewed for calibration; 5 PA from the 1 slot; opposing starter Blake Snell went 18 outs / 4 ER; closest possible loss (missed by the minimum) |
| 902 | Martin Necas skater_sog over 1.5 | 0 | 0.7268 (Medium) | pass | market 71%, hist 90% | correlated | **untagged** | same game script as #893 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 909 | Cooper Pratt batter_strikeouts over 0.5 | 0 | 0.7036 (Medium) | pass | market 73%, hist 43% (against) | correlated | **untagged** | same game script as #918 (opportunity); own read: variance; logged as a PASS: no money on it; reviewed for calibration; 4 PA from the 7 slot; opposing starter Blake Snell went 18 outs / 4 ER; closest possible loss (missed by the minimum) |
| 912 | Shohei Ohtani batter_strikeouts over 0.5 | 0 | 0.702 (Medium) | pass | market 68%, hist 87% | correlated | **untagged** | same game script as #918 (opportunity); own read: variance; logged as a PASS: no money on it; reviewed for calibration; 4 PA from the 6 slot; opposing starter Robert Gasser went 15 outs / 0 ER; closest possible loss (missed by the minimum) |
| 914 | Ilya Protas skater_sog over 0.5 | 0 | 0.6966 (High) | pass | market 71%, hist 60% | correlated | **untagged** | same game script as #848 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 915 | Freddie Freeman batter_hrr over 0.5 | 0 | 0.6947 (High) | pass | market 70%, hist 63% | correlated | **untagged** | same game script as #918 (opportunity); own read: variance; logged as a PASS: no money on it; reviewed for calibration; 4 PA from the 2 slot; opposing starter Robert Gasser went 15 outs / 0 ER; closest possible loss (missed by the minimum) |
| 918 | Andy Pages batter_hrr over 0.5 | 0 | 0.6933 (High) | pass | market 70%, hist 70% | opportunity | **untagged** | root leg of a 25-leg script loss: #853, #869, #895, #909, #912, #915, #918, #943, #947, #952, #954, #968, #969, #975, #1005, #1006, #1014, #1020, #1031, #1042, #1044, #1048, #1064, #1067, #1071; logged as a PASS: no money on it; reviewed for calibration; only 2 plate appearances; 2 PA from the 5 slot; opposing starter Robert Gasser went 15 outs / 0 ER |
| 924 | Ryan Leonard skater_sog over 1.5 | 1 | 0.6797 (High) | pass | market 67%, hist 80% | correlated | **untagged** | same game script as #848 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 931 | Martin Necas skater_points over 0.5 | 0 | 0.6728 (High) | pass | market 67%, hist 73% | correlated | **untagged** | same game script as #893 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 935 | Cole Caufield skater_sog over 2.5 | 0 | 0.6686 (High) | pass | market 66%, hist 77% | correlated | **untagged** | same game script as #848 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 939 | Jason Robertson skater_points over 0.5 | 0 | 0.6628 (High) | pass | market 66%, hist 67% | correlated | **untagged** | same game script as #893 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 943 | Teoscar Hernández batter_hits over 0.5 | 0 | 0.6513 (High) | pass | market 64%, hist 73% | correlated | **untagged** | same game script as #918 (opportunity); own read: variance; logged as a PASS: no money on it; reviewed for calibration; 4 PA from the 3 slot; opposing starter Robert Gasser went 15 outs / 0 ER; closest possible loss (missed by the minimum) |
| 946 | Cole Caufield skater_points over 0.5 | 0 | 0.6424 (Medium) | pass | market 64%, hist 67% | correlated | **untagged** | same game script as #848 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 947 | Andy Pages batter_hits over 0.5 | 0 | 0.6415 (Medium) | pass | market 64%, hist 67% | correlated | **untagged** | same game script as #918 (opportunity); own read: opportunity; logged as a PASS: no money on it; reviewed for calibration; only 2 plate appearances; 2 PA from the 5 slot; opposing starter Robert Gasser went 15 outs / 0 ER |
| 952 | Freddie Freeman batter_hits over 0.5 | 0 | 0.6314 (Medium) | pass | market 64%, hist 50% (against) | correlated | **untagged** | same game script as #918 (opportunity); own read: variance; logged as a PASS: no money on it; reviewed for calibration; 4 PA from the 2 slot; opposing starter Robert Gasser went 15 outs / 0 ER; closest possible loss (missed by the minimum) |
| 954 | Tommy Edman batter_hrr over 0.5 | 0 | 0.6305 (Medium) | pass | market 62%, hist 67% | correlated | **untagged** | same game script as #918 (opportunity); own read: variance; logged as a PASS: no money on it; reviewed for calibration; 4 PA from the 9 slot; opposing starter Robert Gasser went 15 outs / 0 ER; closest possible loss (missed by the minimum) |
| 966 | Tom Wilson skater_sog under 2.0 | 5 | 0.5267 (Low) | pass | market 51%, hist 56% | correlated | **untagged** | same game script as #848 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 968 | Andrew Vaughn batter_hrr over 0.5 | 0 | 0.6178 (Medium) | pass | market 59%, hist 77% | correlated | **untagged** | same game script as #918 (opportunity); own read: variance; logged as a PASS: no money on it; reviewed for calibration; 3 PA from the 4 slot; opposing starter Blake Snell went 18 outs / 4 ER; closest possible loss (missed by the minimum) |
| 969 | Luis Lara batter_hrr over 0.5 | 0 | 0.6159 (Medium) | pass | market 59%, hist 80% | correlated | **untagged** | same game script as #918 (opportunity); own read: variance; logged as a PASS: no money on it; reviewed for calibration; 4 PA from the 8 slot; opposing starter Blake Snell went 18 outs / 4 ER; closest possible loss (missed by the minimum) |
| 974 | Roope Hintz skater_sog over 1.5 | 1 | 0.6102 (Medium) | pass | market 60%, hist 63% | correlated | **untagged** | same game script as #893 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 975 | Freddie Freeman batter_strikeouts over 0.5 | 0 | 0.6101 (Medium) | pass | market 60%, hist 67% | correlated | **untagged** | same game script as #918 (opportunity); own read: variance; logged as a PASS: no money on it; reviewed for calibration; 4 PA from the 2 slot; opposing starter Robert Gasser went 15 outs / 0 ER; closest possible loss (missed by the minimum) |
| 977 | Mikko Rantanen skater_sog over 1.5 | 1 | 0.606 (Medium) | pass | market 61%, hist 47% (against) | correlated | **untagged** | same game script as #893 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 992 | Roope Hintz skater_points over 0.5 | 0 | 0.5873 (Medium) | pass | market 58%, hist 57% | correlated | **untagged** | same game script as #893 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 993 | T.J. Hughes skater_sog over 1.5 | 0 | 0.5861 (Medium) | pass | market 57%, hist 67% | correlated | **untagged** | same game script as #893 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 997 | Nathan MacKinnon skater_assists over 0.5 | 0 | 0.5785 (Low) | pass | market 58%, hist 47% (against) | correlated | **untagged** | same game script as #893 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1000 | Juraj Slafkovský skater_points over 0.5 | 0 | 0.5745 (Low) | pass | market 56%, hist 63% | correlated | **untagged** | same game script as #848 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1005 | Kyle Tucker batter_strikeouts over 0.5 | 0 | 0.5674 (Low) | pass | market 57%, hist 47% (against) | correlated | **untagged** | same game script as #918 (opportunity); own read: variance; logged as a PASS: no money on it; reviewed for calibration; 4 PA from the 4 slot; opposing starter Robert Gasser went 15 outs / 0 ER; closest possible loss (missed by the minimum) |
| 1006 | Tommy Edman batter_hits over 0.5 | 0 | 0.5665 (Low) | pass | market 56%, hist 50% (against) | correlated | **untagged** | same game script as #918 (opportunity); own read: variance; logged as a PASS: no money on it; reviewed for calibration; 4 PA from the 9 slot; opposing starter Robert Gasser went 15 outs / 0 ER; closest possible loss (missed by the minimum) |
| 1009 | Dylan Strome skater_points over 0.5 | 0 | 0.5661 (Low) | pass | market 57%, hist 47% (against) | correlated | **untagged** | same game script as #848 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1010 | Nick Suzuki skater_assists over 0.5 | 0 | 0.565 (Low) | pass | market 54%, hist 67% | correlated | **untagged** | same game script as #848 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1012 | Boone Jenner skater_sog over 1.5 | 0 | 0.5622 (Low) | pass | market 55%, hist 57% | correlated | **untagged** | same game script as #848 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1014 | Andrew Vaughn batter_hits over 0.5 | 0 | 0.5612 (Low) | pass | market 53%, hist 77% | correlated | **untagged** | same game script as #918 (opportunity); own read: variance; logged as a PASS: no money on it; reviewed for calibration; 3 PA from the 4 slot; opposing starter Blake Snell went 18 outs / 4 ER; closest possible loss (missed by the minimum) |
| 1019 | Jakob Chychrun skater_points over 0.5 | 0 | 0.5566 (Low) | pass | market 56%, hist 43% (against) | correlated | **untagged** | same game script as #848 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1020 | Luis Lara batter_hits over 0.5 | 0 | 0.5558 (Low) | pass | market 53%, hist 70% | correlated | **untagged** | same game script as #918 (opportunity); own read: variance; logged as a PASS: no money on it; reviewed for calibration; 4 PA from the 8 slot; opposing starter Blake Snell went 18 outs / 4 ER; closest possible loss (missed by the minimum) |
| 1022 | Alex Ovechkin skater_sog over 2.5 | 0 | 0.5551 (Low) | pass | market 53%, hist 63% | correlated | **untagged** | same game script as #848 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1031 | Blake Snell pitcher_strikeouts under 6.0 | 9 | 0.4691 (Low) | pass | market 44% (against), hist 56% | correlated | **untagged** | same game script as #918 (opportunity); own read: variance; we priced this side at 47%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; line: 18 outs, 24 BF, 101 pitches, 4 H, 2 BB, 9 K, 4 ER |
| 1032 | Tom Wilson skater_points over 0.5 | 0 | 0.5468 (Low) | pass | market 54%, hist 47% (against) | correlated | **untagged** | same game script as #848 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1035 | Dylan Strome skater_sog over 1.5 | 1 | 0.5443 (Low) | pass | market 55%, hist 37% (against) | correlated | **untagged** | same game script as #848 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1039 | Brock Nelson skater_points under 0.5 | 1 | 0.5406 (Low) | pass | market 54%, hist 47% (against) | correlated | **untagged** | same game script as #893 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1042 | Mookie Betts batter_hrr over 1.5 | 1 | 0.5375 (Low) | pass | market 52%, hist 57% | correlated | **untagged** | same game script as #918 (opportunity); own read: variance; logged as a PASS: no money on it; reviewed for calibration; 5 PA from the 1 slot; opposing starter Robert Gasser went 15 outs / 0 ER; 1 of 1 H+R+RBI came off the starter, 0 off the bullpen; closest possible loss (missed by the minimum) |
| 1044 | Kyle Tucker batter_hrr under 1.5 | 2 | 0.5367 (Low) | pass | market 52%, hist 57% | correlated | **untagged** | same game script as #918 (opportunity); own read: variance; logged as a PASS: no money on it; reviewed for calibration; 4 PA from the 4 slot; opposing starter Robert Gasser went 15 outs / 0 ER; 1 of 2 H+R+RBI came off the starter, 1 off the bullpen; closest possible loss (missed by the minimum) |
| 1046 | Brent Burns skater_sog over 1.5 | 1 | 0.536 (Low) | pass | market 51%, hist 67% | correlated | **untagged** | same game script as #893 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1047 | Chris Kreider skater_sog over 1.5 | 1 | 0.5359 (Low) | pass | market 53%, hist 50% (against) | correlated | **untagged** | same game script as #848 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1048 | Jackson Chourio batter_singles over 0.5 | 0 | 0.5345 (Low) | pass | market 51%, hist 63% | correlated | **untagged** | same game script as #918 (opportunity); own read: variance; logged as a PASS: no money on it; reviewed for calibration; 5 PA from the 1 slot; opposing starter Blake Snell went 18 outs / 4 ER; closest possible loss (missed by the minimum) |
| 1051 | Artturi Lehkonen skater_sog over 1.5 | 1 | 0.5329 (Low) | pass | market 53%, hist 47% (against) | correlated | **untagged** | same game script as #893 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1052 | Martin Necas skater_assists over 0.5 | 0 | 0.5315 (Low) | pass | market 52%, hist 53% | correlated | **untagged** | same game script as #893 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1064 | Teoscar Hernández batter_hrr over 1.5 | 1 | 0.5212 (Low) | pass | market 49% (against), hist 67% | correlated | **untagged** | same game script as #918 (opportunity); own read: variance; logged as a PASS: no money on it; reviewed for calibration; 4 PA from the 3 slot; opposing starter Robert Gasser went 15 outs / 0 ER; 0 of 1 H+R+RBI came off the starter, 1 off the bullpen; closest possible loss (missed by the minimum) |
| 1067 | Jackson Chourio batter_hrr under 1.5 | 3 | 0.519 (Low) | pass | market 52%, hist 33% (against) | correlated | **untagged** | same game script as #918 (opportunity); own read: variance; logged as a PASS: no money on it; reviewed for calibration; 5 PA from the 1 slot; opposing starter Blake Snell went 18 outs / 4 ER; 3 of 3 H+R+RBI came off the starter, 0 off the bullpen |
| 1068 | Aliaksei Protas skater_sog over 1.5 | 1 | 0.5187 (Low) | pass | market 50% (against), hist 57% | correlated | **untagged** | same game script as #848 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1071 | Jake Bauers batter_walks over 0.5 | 0 | 0.517 (Low) | pass | market 50% (against), hist 57% | correlated | **untagged** | same game script as #918 (opportunity); own read: variance; logged as a PASS: no money on it; reviewed for calibration; 4 PA from the 5 slot; opposing starter Blake Snell went 18 outs / 4 ER; closest possible loss (missed by the minimum) |
| 1072 | Lane Hutson skater_sog under 1.5 | 3 | 0.5169 (Low) | pass | market 50%, hist 50% (against) | correlated | **untagged** | same game script as #848 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1075 | Devon Toews skater_points over 0.5 | 0 | 0.5148 (Low) | pass | market 51%, hist 43% (against) | correlated | **untagged** | same game script as #893 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1076 | Tyler Seguin skater_points over 0.5 | 0 | 0.5148 (Low) | pass | market 51%, hist 43% (against) | correlated | **untagged** | same game script as #893 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |

Lessons:
- #879: Role and volume normal (15:08 TOI, 21 shifts, usual line) but 0 shot attempts of any kind: not even a miss or block. DK -600 and his 30-game log (6 zero-shot games) both priced ~17-20% for this. Second night of a back-to-back: before the next O0.5 SOG at 8+ on a B2B second night, check depth forwards' B2B shot rate.

Detail from the feeds:
- #522 xKacpersky: de_ancient: 29 rds, L, 15 K / 10 HS; de_dust2: 19 rds, L, 10 K / 5 HS
- #524 yuurih: de_ancient: 23 rds, W, 16 K / 8 HS; de_mirage: 22 rds, W, 13 K / 7 HS
- #529 Jame: de_dust2: 24 rds, L, 12 K / 6 HS; de_mirage: 30 rds, L, 13 K / 4 HS
- #530 sjuush: de_ancient: 29 rds, L, 16 K / 11 HS; de_dust2: 19 rds, L, 10 K / 2 HS
- #537 PokemoN: de_anubis: 22 rds, W, 11 K / 6 HS; de_inferno: 24 rds, L, 15 K / 8 HS
- #540 PokemoN: de_anubis: 22 rds, W, 11 K / 6 HS; de_inferno: 24 rds, L, 15 K / 8 HS
- #550 sav: de_mirage: 22 rds, L, 16 K / 8 HS; de_cache: 18 rds, L, 7 K / 3 HS
- #555 ju1ces: de_mirage: 22 rds, W, 20 K / 9 HS; de_cache: 18 rds, W, 12 K / 7 HS
- #559 HObbit: de_dust2: 24 rds, L, 19 K / 7 HS; de_mirage: 30 rds, L, 19 K / 11 HS
- #560 yuurih: de_ancient: 23 rds, W, 16 K / 8 HS; de_mirage: 22 rds, W, 13 K / 7 HS
- #565 Raijin: de_dust2: 24 rds, L, 14 K / 8 HS; de_anubis: 23 rds, L, 17 K / 8 HS
- #571 stavn: de_ancient: 29 rds, L, 22 K / 4 HS; de_dust2: 19 rds, L, 9 K / 2 HS
- #574 KusMe: de_dust2: 24 rds, W, 16 K / 3 HS; de_anubis: 23 rds, W, 14 K / 6 HS
- #575 laxiee: de_anubis: 22 rds, W, 13 K / 4 HS; de_inferno: 24 rds, L, 9 K / 6 HS
- #579 KSCERATO: de_ancient: 23 rds, W, 19 K / 5 HS; de_mirage: 22 rds, W, 21 K / 8 HS
- #586 phzy: de_nuke: 29 rds, W, 22 K / 6 HS; de_mirage: 22 rds, W, 15 K / 4 HS
- #590 m0NESY: de_ancient: 29 rds, W, 26 K / 9 HS; de_dust2: 19 rds, W, 14 K / 8 HS
- #594 molodoy: de_ancient: 23 rds, W, 18 K / 8 HS; de_mirage: 22 rds, W, 21 K / 9 HS
- #605 Roflko: de_mirage: 22 rds, L, 22 K / 12 HS; de_cache: 18 rds, L, 17 K / 9 HS
- #606 fear: de_ancient: 23 rds, L, 12 K / 6 HS; de_dust2: 23 rds, L, 15 K / 4 HS
- #607 dwushka: de_ancient: 23 rds, W, 20 K / 17 HS; de_dust2: 23 rds, W, 20 K / 11 HS
- #608 dumau: de_dust2: 24 rds, W, 13 K / 4 HS; de_mirage: 30 rds, W, 29 K / 11 HS
- #610 dumau: de_dust2: 24 rds, W, 13 K / 4 HS; de_mirage: 30 rds, W, 29 K / 11 HS
- #613 bluewh1te: de_dust2: 24 rds, L, 11 K / 9 HS; de_anubis: 23 rds, L, 18 K / 10 HS
- #615 z4kr: de_anubis: 22 rds, L, 12 K / 6 HS; de_inferno: 24 rds, W, 18 K / 2 HS
- #616 mazay: de_ancient: 23 rds, L, 10 K / 5 HS; de_dust2: 23 rds, L, 17 K / 13 HS
- #625 molodoy: de_ancient: 23 rds, W, 18 K / 8 HS; de_mirage: 22 rds, W, 21 K / 9 HS
- #627 TeSeS: de_ancient: 29 rds, W, 20 K / 10 HS; de_dust2: 19 rds, W, 11 K / 5 HS
- #628 z1Nny: de_dust2: 24 rds, L, 15 K / 10 HS; de_anubis: 23 rds, L, 13 K / 6 HS
- #630 sav: de_mirage: 22 rds, L, 16 K / 8 HS; de_cache: 18 rds, L, 7 K / 3 HS
- #631 Lack1: de_dust2: 24 rds, W, 17 K / 8 HS; de_anubis: 23 rds, W, 14 K / 8 HS
- #632 karrigan: de_ancient: 29 rds, W, 23 K / 12 HS; de_dust2: 19 rds, W, 13 K / 5 HS
- #635 try: de_dust2: 24 rds, W, 20 K / 5 HS; de_mirage: 30 rds, W, 21 K / 7 HS
- #637 d1Ledez: de_ancient: 23 rds, L, 17 K / 9 HS; de_mirage: 22 rds, L, 14 K / 8 HS
- #638 TeSeS: de_ancient: 29 rds, W, 20 K / 10 HS; de_dust2: 19 rds, W, 11 K / 5 HS
- #640 yourwombat: de_mirage: 22 rds, L, 15 K / 5 HS; de_cache: 18 rds, L, 6 K / 2 HS
- #641 Magnojez: de_ancient: 23 rds, L, 12 K / 7 HS; de_mirage: 22 rds, L, 17 K / 12 HS
- #643 kade0: de_ancient: 23 rds, W, 13 K / 6 HS; de_dust2: 23 rds, W, 14 K / 9 HS
- #644 zorte: de_ancient: 23 rds, L, 14 K / 2 HS; de_mirage: 22 rds, L, 13 K / 4 HS
- #646 jackasmo: de_ancient: 23 rds, L, 23 K / 13 HS; de_dust2: 23 rds, L, 12 K / 8 HS
- #649 jackasmo: de_ancient: 23 rds, L, 23 K / 13 HS; de_dust2: 23 rds, L, 12 K / 8 HS
- #651 zweih: de_dust2: 24 rds, L, 19 K / 12 HS; de_mirage: 30 rds, L, 20 K / 13 HS
- #652 Roflko: de_mirage: 22 rds, L, 22 K / 12 HS; de_cache: 18 rds, L, 17 K / 9 HS
- #654 art: de_dust2: 24 rds, W, 12 K / 8 HS; de_mirage: 30 rds, W, 12 K / 7 HS
- #658 foggers: de_mirage: 22 rds, W, 15 K / 6 HS; de_cache: 18 rds, W, 16 K / 11 HS
- #661 karrigan: de_ancient: 29 rds, W, 23 K / 12 HS; de_dust2: 19 rds, W, 13 K / 5 HS
- #664 EmiliaQAQ: de_anubis: 22 rds, L, 12 K / 8 HS; de_inferno: 24 rds, W, 18 K / 9 HS
- #666 Boombl4: de_ancient: 23 rds, L, 9 K / 5 HS; de_mirage: 22 rds, L, 15 K / 8 HS
- #668 latto: de_dust2: 24 rds, W, 20 K / 10 HS; de_mirage: 30 rds, W, 13 K / 6 HS
- #669 laxiee: de_anubis: 22 rds, W, 13 K / 4 HS; de_inferno: 24 rds, L, 9 K / 6 HS
- #670 zweih: de_dust2: 24 rds, L, 19 K / 12 HS; de_mirage: 30 rds, L, 20 K / 13 HS
- #673 Boombl4: de_ancient: 23 rds, L, 9 K / 5 HS; de_mirage: 22 rds, L, 15 K / 8 HS
- #674 xiELO: de_dust2: 24 rds, L, 16 K / 8 HS; de_mirage: 30 rds, L, 20 K / 10 HS
- #675 ju1ces: de_mirage: 22 rds, W, 20 K / 9 HS; de_cache: 18 rds, W, 12 K / 7 HS
- #678 C4LLM3SU3: de_anubis: 22 rds, L, 14 K / 8 HS; de_inferno: 24 rds, W, 13 K / 8 HS
- #682 cairne: de_ancient: 23 rds, L, 13 K / 6 HS; de_dust2: 23 rds, L, 11 K / 5 HS
- #683 adamb: de_ancient: 29 rds, L, 19 K / 9 HS; de_dust2: 19 rds, L, 8 K / 3 HS
- #685 HObbit: de_dust2: 24 rds, L, 19 K / 7 HS; de_mirage: 30 rds, L, 19 K / 11 HS
- #686 n0rb3r7: de_ancient: 23 rds, W, 13 K / 6 HS; de_dust2: 23 rds, W, 17 K / 10 HS
- #688 Starry: de_anubis: 22 rds, L, 10 K / 6 HS; de_inferno: 24 rds, W, 20 K / 14 HS
- #691 jambo: de_ancient: 23 rds, L, 12 K / 3 HS; de_dust2: 23 rds, L, 19 K / 9 HS
- #692 EmiliaQAQ: de_anubis: 22 rds, L, 12 K / 8 HS; de_inferno: 24 rds, W, 18 K / 9 HS
- #696 n1ssim: de_dust2: 24 rds, W, 12 K / 7 HS; de_mirage: 30 rds, W, 20 K / 6 HS
- #698 kyousuke: de_ancient: 29 rds, W, 14 K / 8 HS; de_dust2: 19 rds, W, 14 K / 10 HS
- #699 n1ssim: de_dust2: 24 rds, W, 12 K / 7 HS; de_mirage: 30 rds, W, 20 K / 6 HS
- #703 mizu: de_ancient: 23 rds, W, 26 K / 8 HS; de_dust2: 23 rds, W, 11 K / 8 HS
- #704 ryu: de_nuke: 29 rds, W, 31 K / 15 HS; de_mirage: 22 rds, W, 12 K / 6 HS
- #710 mizu: de_ancient: 23 rds, W, 26 K / 8 HS; de_dust2: 23 rds, W, 11 K / 8 HS
- #712 zorte: de_ancient: 23 rds, L, 14 K / 2 HS; de_mirage: 22 rds, L, 13 K / 4 HS
- #733 Jool: G1 W: 6 K (expected 5.4); Anubis Gaming 18 - Picks Solary 24, 42 total; G2 L: 3 K (expected 3.0); Solary 12 - Picks Anubis Gaming 22, 34 total; G3 W: 6 K (expected 5.4); Solary 25 - Picks Anubis Gaming 4, 29 total
- #737 VicLa: G1 W: 2 K (expected 4.8); BNK FearX 22 - KT Rolster 8, 30 total; G2 L: 0 K (expected 1.9); BNK FearX 8 - KT Rolster 22, 30 total; G3 W: 9 K (expected 4.8); KT Rolster 11 - BNK FearX 23, 34 total
- #742 Paulo Dybala: minutes=45.0, passes=28.0, team_passes=546, possession=54, saves=0.0, score=ROMA 3 - RMA 4
- #743 Paulo Dybala: minutes=45.0, passes=28.0, team_passes=546, possession=54, saves=0.0, score=ROMA 3 - RMA 4
- #745 Paulo Dybala: minutes=45.0, passes=28.0, team_passes=546, possession=54, saves=0.0, score=ROMA 3 - RMA 4
- #746 Paulo Dybala: minutes=45.0, passes=28.0, team_passes=546, possession=54, saves=0.0, score=ROMA 3 - RMA 4
- #747 Paulo Dybala: minutes=45.0, passes=28.0, team_passes=546, possession=54, saves=0.0, score=ROMA 3 - RMA 4
- #848 Boone Jenner: toi=15.1, sog=0, shifts=21, pp_goals=0, score=4-5
- #853 Brice Turang: inn 1 vs Snell: Strikeout; inn 3 vs Snell: Strikeout; inn 6 vs Snell: Groundout; inn 8 vs Sasaki: Single; scored inn 8 (bullpen)
- #859 Jakob Chychrun: toi=23.1, sog=2, shifts=22, pp_goals=0, score=4-5
- #869 Blake Snell: outs=18, bf=24, pitches=101, h=4, er=4, bb=2, k=9, p_per_pa=4.21
- #879 Boone Jenner: toi=15.1, sog=0, shifts=21, pp_goals=0, score=4-5
- #889 Alex Ovechkin: toi=13.2, sog=0, shifts=15, pp_goals=0, score=4-5
- #893 Nathan MacKinnon: toi=25.4, sog=4, shifts=23, pp_goals=0, score=3-2
- #895 Jackson Chourio: inn 1 vs Snell: Home Run, 1 RBI; scored inn 1 (starter); inn 3 vs Snell: Pop Out; inn 6 vs Snell: Groundout; inn 8 vs Sasaki: Groundout; inn 9 vs Wrobleski: Groundout
- #902 Martin Necas: toi=22.4, sog=0, shifts=19, pp_goals=0, score=3-2
- #909 Cooper Pratt: inn 2 vs Snell: Single; inn 5 vs Snell: Flyout; inn 7 vs Phillips: Single; inn 9 vs Wrobleski: Single; scored inn 9 (bullpen)
- #912 Shohei Ohtani: inn 2 vs Gasser: Lineout; inn 4 vs Gasser: Hit By Pitch; inn 6 vs Uribe: Walk; inn 8 vs Hall: Single
- #914 Ilya Protas: toi=12.4, sog=0, shifts=14, pp_goals=0, score=4-5
- #915 Freddie Freeman: inn 1 vs Gasser: Flyout; inn 3 vs Gasser: Flyout; inn 5 vs Gasser: Groundout; inn 7 vs Hall: Lineout
- #918 Andy Pages: inn 2 vs Gasser: Flyout; inn 4 vs Gasser: Strikeout
- #924 Ryan Leonard: toi=14.9, sog=1, shifts=15, pp_goals=0, score=4-5
- #931 Martin Necas: toi=22.4, sog=0, shifts=19, pp_goals=0, score=3-2
- #935 Cole Caufield: toi=19.9, sog=0, shifts=19, pp_goals=0, score=4-5
- #939 Jason Robertson: toi=22.4, sog=3, shifts=27, pp_goals=0, score=3-2
- #943 Teoscar Hernández: inn 1 vs Gasser: Strikeout; inn 3 vs Gasser: Forceout; inn 6 vs Uribe: Walk; scored inn 6 (bullpen); inn 7 vs Hall: Groundout
- #946 Cole Caufield: toi=19.9, sog=0, shifts=19, pp_goals=0, score=4-5
- #947 Andy Pages: inn 2 vs Gasser: Flyout; inn 4 vs Gasser: Strikeout
- #952 Freddie Freeman: inn 1 vs Gasser: Flyout; inn 3 vs Gasser: Flyout; inn 5 vs Gasser: Groundout; inn 7 vs Hall: Lineout
- #954 Tommy Edman: inn 3 vs Gasser: Flyout; inn 5 vs Gasser: Flyout; inn 6 vs Hall: Strikeout; inn 9 vs Megill: Strikeout
- #966 Tom Wilson: toi=17.2, sog=5, shifts=20, pp_goals=0, score=4-5
- #968 Andrew Vaughn: inn 1 vs Snell: Strikeout; inn 4 vs Snell: Groundout; inn 7 vs Snell: Walk
- #969 Luis Lara: inn 2 vs Snell: Flyout; inn 5 vs Snell: Strikeout; inn 7 vs Phillips: Flyout; inn 9 vs Wrobleski: Lineout
- #974 Roope Hintz: toi=18.1, sog=1, shifts=26, pp_goals=0, score=3-2
- #975 Freddie Freeman: inn 1 vs Gasser: Flyout; inn 3 vs Gasser: Flyout; inn 5 vs Gasser: Groundout; inn 7 vs Hall: Lineout
- #977 Mikko Rantanen: toi=23.1, sog=1, shifts=27, pp_goals=0, score=3-2
- #992 Roope Hintz: toi=18.1, sog=1, shifts=26, pp_goals=0, score=3-2
- #993 T.J. Hughes: toi=14.4, sog=0, shifts=15, pp_goals=0, score=3-2
- #997 Nathan MacKinnon: toi=25.4, sog=4, shifts=23, pp_goals=0, score=3-2
- #1000 Juraj Slafkovský: toi=19.7, sog=4, shifts=20, pp_goals=0, score=4-5
- #1005 Kyle Tucker: inn 2 vs Gasser: Single; inn 4 vs Gasser: Flyout; inn 6 vs Uribe: Walk; scored inn 6 (bullpen); inn 8 vs Hall: Flyout
- #1006 Tommy Edman: inn 3 vs Gasser: Flyout; inn 5 vs Gasser: Flyout; inn 6 vs Hall: Strikeout; inn 9 vs Megill: Strikeout
- #1009 Dylan Strome: toi=18.9, sog=1, shifts=21, pp_goals=0, score=4-5
- #1010 Nick Suzuki: toi=20.2, sog=3, shifts=19, pp_goals=1, score=4-5
- #1012 Boone Jenner: toi=15.1, sog=0, shifts=21, pp_goals=0, score=4-5
- #1014 Andrew Vaughn: inn 1 vs Snell: Strikeout; inn 4 vs Snell: Groundout; inn 7 vs Snell: Walk
- #1019 Jakob Chychrun: toi=23.1, sog=2, shifts=22, pp_goals=0, score=4-5
- #1020 Luis Lara: inn 2 vs Snell: Flyout; inn 5 vs Snell: Strikeout; inn 7 vs Phillips: Flyout; inn 9 vs Wrobleski: Lineout
- #1022 Alex Ovechkin: toi=13.2, sog=0, shifts=15, pp_goals=0, score=4-5
- #1031 Blake Snell: outs=18, bf=24, pitches=101, h=4, er=4, bb=2, k=9, p_per_pa=4.21
- #1032 Tom Wilson: toi=17.2, sog=5, shifts=20, pp_goals=0, score=4-5
- #1035 Dylan Strome: toi=18.9, sog=1, shifts=21, pp_goals=0, score=4-5
- #1039 Brock Nelson: toi=23.0, sog=2, shifts=26, pp_goals=0, score=3-2
- #1042 Mookie Betts: inn 1 vs Gasser: Flyout; inn 3 vs Gasser: Single; inn 5 vs Gasser: Lineout; inn 7 vs Hall: Groundout; inn 9 vs Megill: Strikeout
- #1044 Kyle Tucker: inn 2 vs Gasser: Single; inn 4 vs Gasser: Flyout; inn 6 vs Uribe: Walk; scored inn 6 (bullpen); inn 8 vs Hall: Flyout
- #1046 Brent Burns: toi=14.4, sog=1, shifts=18, pp_goals=0, score=3-2
- #1047 Chris Kreider: toi=15.5, sog=1, shifts=18, pp_goals=0, score=4-5
- #1048 Jackson Chourio: inn 1 vs Snell: Home Run, 1 RBI; scored inn 1 (starter); inn 3 vs Snell: Pop Out; inn 6 vs Snell: Groundout; inn 8 vs Sasaki: Groundout; inn 9 vs Wrobleski: Groundout
- #1051 Artturi Lehkonen: toi=21.9, sog=1, shifts=26, pp_goals=0, score=3-2
- #1052 Martin Necas: toi=22.4, sog=0, shifts=19, pp_goals=0, score=3-2
- #1064 Teoscar Hernández: inn 1 vs Gasser: Strikeout; inn 3 vs Gasser: Forceout; inn 6 vs Uribe: Walk; scored inn 6 (bullpen); inn 7 vs Hall: Groundout
- #1067 Jackson Chourio: inn 1 vs Snell: Home Run, 1 RBI; scored inn 1 (starter); inn 3 vs Snell: Pop Out; inn 6 vs Snell: Groundout; inn 8 vs Sasaki: Groundout; inn 9 vs Wrobleski: Groundout
- #1068 Aliaksei Protas: toi=17.6, sog=1, shifts=18, pp_goals=0, score=4-5
- #1071 Jake Bauers: inn 2 vs Snell: Flyout; inn 4 vs Snell: Strikeout; inn 7 vs Snell: Home Run, 2 RBI; scored inn 7 (starter); inn 8 vs Wrobleski: Strikeout
- #1072 Lane Hutson: toi=24.2, sog=3, shifts=26, pp_goals=0, score=4-5
- #1075 Devon Toews: toi=22.9, sog=0, shifts=27, pp_goals=0, score=3-2
- #1076 Tyler Seguin: toi=15.0, sog=3, shifts=19, pp_goals=0, score=3-2

## 2026-10-13: 179 losses from 40 independent causes

| # | Leg | Result | Our p | Action | Sources | Auto tag | Confirmed | Evidence |
|---|---|---|---|---|---|---|---|---|
| 86 | EliGE cs_headshots_m12 over 18.5 | 17 | 0.492 (Low) | pass | model 45% (against), hist 69% | variance | variance | we priced this side at 49%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 88 | dev1ce cs_headshots_m12 over 9.5 | 9 | 0.466 (Low) | pass | model 44% (against), hist 41% (against) | variance | variance | root leg of a 2-leg script loss: #88, #92; we priced this side at 47%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 89 | foggers cs_kills_m12 over 30.5 | 26 | 0.489 (Low) | pass | model 51%, hist 24% (against) | variance | variance | we priced this side at 49%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 92 | dev1ce cs_kills_m12 over 31.5 | 30 | 0.413 (Low) | user_entry | model 38% (against), hist 41% (against) | correlated | correlated | same game script as #88 (variance); own read: variance; we priced this side at 41%: losing was the more likely outcome; closest possible loss (missed by the minimum) |
| 94 | Jorko cs_kills_m12 under 30.5 | 35 | 0.6129 (Low) | pass | model 62%, hist 46% (against) | variance | variance | root leg of a 4-leg script loss: #94, #95, #98, #104; logged as a PASS: no money on it; reviewed for calibration |
| 95 | malbsMd cs_kills_m12 under 32 | 40 | 0.6809 (Medium) | pass | model 67%, hist 75% | correlated | correlated | same game script as #94 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 98 | JT cs_kills_m12 under 25.5 | 28 | 0.5934 (Low) | pass | model 60%, hist 46% (against) | correlated | correlated | same game script as #94 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 101 | NickyB cs_kills_m12 over 26.5 | 26 | 0.5499 (Low) | pass | model 52%, hist 60% | variance | variance | root leg of a 7-leg script loss: #101, #102, #108, #109, #152, #157, #158; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 102 | MIstR cs_kills_m12 over 25.5 | 23 | 0.5545 (Low) | pass | model 51%, hist 65% | correlated | correlated | same game script as #101 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 104 | malbsMd cs_headshots_m12 under 20 | 23 | 0.5638 (Low) | pass | model 54%, hist 64% | correlated | correlated | same game script as #94 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 108 | salazar cs_headshots_m12 over 9.5 | 8 | 0.5460 (Low) | pass | model 52%, hist 53% | correlated | correlated | same game script as #101 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 109 | NickyB cs_headshots_m12 over 13.5 | 13 | 0.5977 (Medium) | lean | model 57%, hist 67% | correlated | correlated | same game script as #101 (variance); own read: variance; closest possible loss (missed by the minimum) |
| 112 | SkulL cs_kills_m12 under 30.5 | 32 | 0.7284 (High) | lean | model 72%, hist 80% | variance | model bias | root leg of a 3-leg script loss: #112, #117, #138; closest possible loss (missed by the minimum) |
| 117 | ju1ces cs_kills_m12 under 30.5 | 35 | 0.6748 (High) | lean | model 66%, hist 75% | correlated | correlated | same game script as #112 (variance); own read: variance |
| 124 | detr0ittJ cs_headshots_m12 under 11.5 | 13 | 0.6101 (Medium) | lean | model 61%, hist 59% | variance | variance: 30-round map | root leg of a 13-leg script loss: #124, #125, #126, #127, #128, #129, #131, #137, #139, #148, #155, #377, #485 |
| 125 | gbb cs_kills_m12 under 31.5 | 42 | 0.6031 (Medium) | lean | model 60%, hist 63% | correlated | correlated | same game script as #124 (variance); own read: variance |
| 126 | PKL cs_headshots_m12 under 13.0 | 14 | 0.6057 (Medium) | lean | model 60%, hist 60% | correlated | correlated | same game script as #124 (variance); own read: variance |
| 127 | detr0ittJ cs_kills_m12 under 29.0 | 33 | 0.598 (Medium) | lean | model 60%, hist 60% | correlated | correlated | same game script as #124 (variance); own read: variance |
| 128 | PKL cs_kills_m12 under 24.5 | 25 | 0.5966 (Medium) | lean | model 60%, hist 59% | correlated | correlated | same game script as #124 (variance); own read: variance; closest possible loss (missed by the minimum) |
| 129 | gbb cs_headshots_m12 under 16.5 | 27 | 0.6032 (Low) | pass | model 62%, hist 48% (against) | correlated | correlated | same game script as #124 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 131 | drg cs_headshots_m12 under 16.5 | 20 | 0.5869 (Medium) | lean | model 59%, hist 50% (against) | correlated | correlated | same game script as #124 (variance); own read: variance |
| 134 | sirah cs_headshots_m12 under 17.5 | 18 | 0.5827 (Medium) | lean | model 57%, hist 56% | variance | variance | root leg of a 9-leg script loss: #134, #141, #142, #144, #147, #149, #150, #151, #153; closest possible loss (missed by the minimum) |
| 137 | destiny cs_headshots_m12 under 14.5 | 27 | 0.5683 (Low) | pass | model 57%, hist 48% (against) | correlated | correlated | same game script as #124 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 138 | ju1ces cs_headshots_m12 under 14.5 | 21 | 0.5756 (Low) | pass | model 54%, hist 65% | correlated | correlated | same game script as #112 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 139 | destiny cs_kills_m12 under 30.0 | 52 | 0.5675 (Low) | pass | model 59%, hist 38% (against) | correlated | correlated | same game script as #124 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 141 | sinnopsyy cs_headshots_m12 over 14.5 | 7 | 0.5692 (Low) | pass | model 54%, hist 59% | correlated | correlated | same game script as #134 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 142 | 0SAMAS cs_kills_m12 over 27.5 | 24 | 0.5622 (Low) | pass | model 52%, hist 68% | correlated | correlated | same game script as #134 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 144 | CacaNito cs_kills_m12 over 30.5 | 22 | 0.5574 (Low) | pass | model 50%, hist 73% | correlated | correlated | same game script as #134 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 147 | 0SAMAS cs_headshots_m12 over 15.5 | 9 | 0.5496 (Low) | pass | model 50%, hist 68% | correlated | correlated | same game script as #134 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 148 | drg cs_kills_m12 under 28.5 | 31 | 0.5294 (Low) | pass | model 53%, hist 50% (against) | correlated | correlated | same game script as #124 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 149 | Gizmy cs_kills_m12 over 26.5 | 17 | 0.5391 (Low) | pass | model 51%, hist 55% | correlated | correlated | same game script as #134 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 150 | m1N1 cs_kills_m12 over 30.5 | 15 | 0.5384 (Low) | pass | model 48% (against), hist 73% | correlated | correlated | same game script as #134 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 151 | sinnopsyy cs_kills_m12 over 26.5 | 16 | 0.5347 (Low) | pass | model 50% (against), hist 59% | correlated | correlated | same game script as #134 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 152 | MIstR cs_headshots_m12 over 14.5 | 11 | 0.5336 (Low) | pass | model 50% (against), hist 61% | correlated | correlated | same game script as #101 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 153 | Gizmy cs_headshots_m12 over 14.0 | 8 | 0.5334 (Low) | pass | model 53%, hist 41% (against) | correlated | correlated | same game script as #134 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 155 | ckzao cs_kills_m12 under 31.5 | 32 | 0.5177 (Low) | pass | model 53%, hist 25% (against) | correlated | correlated | same game script as #124 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 156 | device cs_headshots_m12 over 9.5 | 9 | 0.5262 (Low) | pass | model 52%, hist 44% (against) | correlated | correlated | same game script as #134 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 157 | leakz cs_kills_m12 under 30.5 | 37 | 0.5227 (Low) | pass | model 51%, hist 47% (against) | correlated | correlated | same game script as #101 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 158 | EliGe cs_headshots_m12 over 19.5 | 17 | 0.4817 (Low) | pass | model 44% (against), hist 54% | correlated | correlated | same game script as #101 (variance); own read: variance; we priced this side at 48%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 159 | device cs_kills_m12 over 32.0 | 30 | 0.4503 (Low) | pass | model 43% (against), hist 38% (against) | correlated | correlated | same game script as #134 (variance); own read: variance; we priced this side at 45%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 165 | Freddy Peralta pitcher_hits_allowed under 3.5 | 4 | 0.529 (Low) | pass | market 52% | correlated | correlated | same game script as #177 (opportunity); own read: variance; logged as a PASS: no money on it; reviewed for calibration; line: 18 outs, 25 BF, 99 pitches, 4 H, 2 BB, 6 K, 0 ER; closest possible loss (missed by the minimum) |
| 166 | Parker Messick pitcher_earned_runs over 1.5 | 0 | 0.5083 (Low) | pass | market 50% | correlated | correlated | same game script as #177 (opportunity); own read: variance; logged as a PASS: no money on it; reviewed for calibration; line: 15 outs, 22 BF, 82 pitches, 6 H, 2 BB, 3 K, 0 ER |
| 167 | Junior Caminero batter_hrr over 1.5 | 1 | 0.5092 (Low) | pass | market 50% | correlated | correlated | same game script as #177 (opportunity); own read: variance; logged as a PASS: no money on it; reviewed for calibration; 4 PA from the 3 slot; opposing starter Parker Messick went 15 outs / 0 ER; 1 of 1 H+R+RBI came off the starter, 0 off the bullpen; closest possible loss (missed by the minimum) |
| 168 | Yandy Díaz batter_hrr over 1.5 | 0 |  (Low) | pass | none logged | correlated | correlated | same game script as #177 (opportunity); own read: variance; logged as a PASS: no money on it; reviewed for calibration; 4 PA from the 1 slot; opposing starter Parker Messick went 15 outs / 0 ER |
| 177 | Patrick Bailey batter_total_bases over 0.5 | 0 |  (Low) | pass | none logged | opportunity | opportunity: did not start | root leg of a 13-leg script loss: #165, #166, #167, #168, #177, #178, #181, #182, #386, #388, #396, #399, #401; logged as a PASS: no money on it; reviewed for calibration; only 2 plate appearances; 2 PA from the 8 slot; opposing starter Freddy Peralta went 18 outs / 0 ER |
| 178 | Patrick Bailey batter_hits over 0.5 | 0 | 0.5171 (Low) | pass | market 51% | correlated | correlated | same game script as #177 (opportunity); own read: opportunity; logged as a PASS: no money on it; reviewed for calibration; only 2 plate appearances; 2 PA from the 8 slot; opposing starter Freddy Peralta went 18 outs / 0 ER |
| 181 | Brayan Rocchio batter_total_bases over 0.5 | 0 |  (Low) | pass | none logged | correlated | correlated | same game script as #177 (opportunity); own read: variance; logged as a PASS: no money on it; reviewed for calibration; 4 PA from the 9 slot; opposing starter Freddy Peralta went 18 outs / 0 ER; closest possible loss (missed by the minimum) |
| 182 | Brayan Rocchio batter_hits over 0.5 | 0 | 0.529 (Low) | pass | market 52% | correlated | correlated | same game script as #177 (opportunity); own read: variance; logged as a PASS: no money on it; reviewed for calibration; 4 PA from the 9 slot; opposing starter Freddy Peralta went 18 outs / 0 ER; closest possible loss (missed by the minimum) |
| 191 | Roman Gagliano pass_yds under 208.5 | 291.0 | 0.5389 (Low) | pass | hist 60% | variance | variance | root leg of a 5-leg script loss: #191, #192, #193, #195, #196; logged as a PASS: no money on it; reviewed for calibration |
| 192 | Antonio Martin rush_yds over 74.5 | 48.0 | 0.5389 (Low) | pass | hist 60% | correlated | correlated | same game script as #191 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 193 | Cam'Ron Lacy rec_yds over 64.5 | 34.0 | 0.5389 (Low) | pass | hist 60% | correlated | correlated | same game script as #191 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 195 | Da'Wain Lofton rec_yds over 43.5 | 40.0 | 0.576 (Low) | pass | hist 75% | correlated | correlated | same game script as #191 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 196 | Da'Wain Lofton receptions over 3.5 | 3.0 | 0.5063 (Low) | pass | hist 50% (against) | correlated | correlated | same game script as #191 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 198 | Caden Creel pass_yds over 218.5 | 214.0 | 0.5673 (Low) | pass | hist 67% | variance | variance | root leg of a 2-leg script loss: #198, #204; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 204 | Devonte Lyons rush_yds under 38.5 | 73.0 | 0.5389 (Low) | pass | hist 60% | correlated | correlated | same game script as #198 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 208 | OMON kills_m123 over 15.5 | 13 | 0.4619 (Low) | pass | model 45% (against), hist 48% (against) | variance | variance | we priced this side at 46%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; 13 kills vs 19.4 expected for the actual game results; games had 34/29/34 total kills |
| 225 | Bdd kills_m123 over 13.5 | 9 | 0.3055 (Low) | pass | model 36% (against), hist 0% (against) | variance | **untagged** | we priced this side at 31%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; 9 kills vs 9.2 expected for the actual game results; games had 30/30/34 total kills |
| 226 | Jakub Markovic passes_att over 37.5 | 34.0 | 0.8267 (Low) | pass | model 87%, hist 33% (against) | variance | model bias: keeper priced as outfielder | root leg of a 2-leg script loss: #226, #265; logged as a PASS: no money on it; reviewed for calibration |
| 227 | Ferran Torres shots over 2.0 | 1.0 | 0.6479 (Medium) | lean | market 73%, hist 60% | variance | **untagged** | root leg of a 6-leg script loss: #227, #238, #256, #272, #300, #325 |
| 229 | Gabriel Jesus shots over 2.5 | 1.0 | 0.7007 (Medium) | pass | market 74%, hist 0% (against) | variance | opportunity: minutes | root leg of a 9-leg script loss: #229, #269, #281, #315, #335, #337, #361, #363, #365; logged as a PASS: no money on it; reviewed for calibration |
| 231 | Julián Alvarez passes_att over 29.5 | 28.0 | 0.6307 (Low) | pass | model 65%, hist 43% (against) | variance | variance | root leg of a 8-leg script loss: #231, #236, #246, #248, #267, #289, #308, #353; logged as a PASS: no money on it; reviewed for calibration |
| 233 | Alberto Brignoli gk_saves over 2.5 | 1.0 | 0.6751 (Medium) | lean | market 62%, hist 83% | variance | **untagged** | root leg of a 2-leg script loss: #233, #310 |
| 234 | Gregor Kobel gk_saves over 2.5 | 2.0 | 0.6703 (High) | lean | market 62%, hist 70% | variance | **untagged** | root leg of a 2-leg script loss: #234, #517; closest possible loss (missed by the minimum) |
| 236 | Matheus Cunha shots over 2.0 | 1.0 | 0.6107 (Medium) | lean | market 59%, hist 86% | correlated | opportunity: minutes | same game script as #231 (variance); own read: variance |
| 237 | Willi Orbán passes_att over 73.5 | 40.0 | 0.5309 (Low) | pass | model 53%, hist 50% (against) | variance | model bias: possession forecast | root leg of a 6-leg script loss: #237, #270, #277, #352, #354, #359; logged as a PASS: no money on it; reviewed for calibration |
| 238 | Khvicha Kvaratskhelia shots over 2.5 | 1.0 | 0.5324 (Low) | pass | market 64%, hist 22% (against) | correlated | **untagged** | same game script as #227 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 239 | Alisson Becker gk_saves over 2.0 | 1.0 | 0.6528 (Medium) | lean | market 61%, hist 57% | variance | **untagged** | root leg of a 3-leg script loss: #239, #271, #350 |
| 241 | Ismael Saibari shots over 4.5 | 2.0 | 0.6001 (Low) | pass | market 62%, hist 17% (against) | variance | opportunity: minutes | root leg of a 6-leg script loss: #241, #258, #274, #316, #470, #472; logged as a PASS: no money on it; reviewed for calibration |
| 242 | Marcus Thuram shots over 3.5 | 2.0 | 0.599 (Medium) | lean | market 61%, hist 43% (against) | variance | variance | root leg of a 7-leg script loss: #242, #253, #329, #334, #347, #351, #357 |
| 245 | Bukayo Saka shots over 3.0 | 1.0 | 0.5966 (Medium) | lean | market 60%, hist 43% (against) | variance | opportunity: minutes | root leg of a 9-leg script loss: #245, #247, #283, #290, #302, #322, #341, #344, #346 |
| 246 | Matheus Cunha passes_att over 24.5 | 14.0 | 0.5489 (Low) | pass | model 51%, hist 81% | correlated | opportunity: minutes | same game script as #231 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 247 | Kai Havertz shots over 3.0 | 0.0 | 0.5899 (Low) | pass | market 62%, hist 0% (against) | correlated | opportunity: minutes | same game script as #245 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 248 | Marcus Rashford shots over 2.0 | 1.0 | 0.5865 (Medium) | lean | market 59%, hist 50% (against) | correlated | correlated | same game script as #231 (variance); own read: variance |
| 253 | Brandon Mechele passes_att over 58.5 | 54.0 | 0.5942 (Medium) | lean | model 58%, hist 80% | correlated | correlated | same game script as #242 (variance); own read: variance |
| 254 | Gonçalo Inácio passes_att over 70.5 | 67.0 | 0.5697 (Low) | pass | model 56%, hist 67% | variance | model bias: possession forecast | root leg of a 5-leg script loss: #254, #319, #321, #330, #342; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 256 | Désiré Doué shots over 2.0 | 1.0 | 0.4155 (Low) | pass | hist 67% | correlated | **untagged** | same game script as #227 (variance); own read: variance; we priced this side at 42%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 258 | Michael Olise shots over 4.5 | 3.0 | 0.5643 (Low) | pass | market 57%, hist 40% (against) | correlated | correlated | same game script as #241 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 265 | Joy-Lance Mickels shots over 2.5 | 1.0 | 0.5507 (Low) | pass | hist 100% | correlated | correlated | same game script as #226 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 267 | Julián Alvarez shots over 3.0 | 2.0 | 0.5409 (Low) | pass | market 55%, hist 0% (against) | correlated | correlated | same game script as #231 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 269 | Rafael Leão shots over 2.0 | 0.0 | 0.5389 (Low) | pass | hist 60% | correlated | correlated | same game script as #229 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 270 | Christopher Nkunku shots over 3.0 | 1.0 | 0.5379 (Low) | pass | market 53%, hist 50% (against) | correlated | correlated | same game script as #237 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 271 | Víctor Muñoz shots over 3.0 | 1.0 | 0.4613 (Low) | pass | market 56%, hist 14% (against) | correlated | **untagged** | same game script as #239 (variance); own read: variance; we priced this side at 46%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 272 | Ousmane Dembélé shots over 3.0 | 1.0 | 0.3887 (Low) | pass | hist 57% | correlated | **untagged** | same game script as #227 (variance); own read: variance; we priced this side at 39%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 274 | Harry Kane shots over 5.5 | 5.0 | 0.5271 (Low) | pass | market 54%, hist 30% (against) | correlated | correlated | same game script as #241 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 277 | Kodai Sano passes_att under 46.5 | 52.0 | 0.5161 (Low) | pass | model 53%, hist 29% (against) | correlated | model bias: possession forecast | same game script as #237 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 279 | Kevin De Bruyne shots over 2.0 | 1.0 | 0.5226 (Low) | pass | market 55%, hist 12% (against) | variance | variance | root leg of a 3-leg script loss: #279, #473, #477; logged as a PASS: no money on it; reviewed for calibration |
| 281 | Victor Osimhen shots over 3.0 | 1.0 | 0.5201 (Low) | pass | market 48% (against), hist 100% | correlated | correlated | same game script as #229 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 283 | Olivier Giroud shots over 1.5 | 0.0 | 0.5146 (Low) | pass | market 53%, hist 22% (against) | correlated | opportunity: minutes | same game script as #245 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 289 | Bruno Fernandes passes_att over 43.5 | 32.0 | 0.7161 (Medium) | lean | model 69%, hist 96% | correlated | correlated | same game script as #231 (variance); own read: variance |
| 290 | David Raya passes_att over 29.5 | 21.0 | 0.513 (Low) | pass | model 51%, hist 46% (against) | correlated | model bias: keeper priced as outfielder | same game script as #245 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 295 | Vinícius Júnior shots over 2.5 | 0.0 | 0.3458 (Low) | pass | hist 44% (against) | variance | **untagged** | root leg of a 3-leg script loss: #295, #296, #336; we priced this side at 35%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 296 | Arda Güler shots over 1.5 | 0.0 | 0.3458 (Low) | pass | hist 44% (against) | correlated | **untagged** | same game script as #295 (variance); own read: variance; we priced this side at 35%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 300 | Jérémy Doku shots over 1.5 | 1.0 | 0.3407 (Low) | pass | hist 40% (against) | correlated | **untagged** | same game script as #227 (variance); own read: variance; we priced this side at 34%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 302 | Ayase Ueda shots over 1.5 | 1.0 | 0.4728 (Low) | pass | market 46% (against), hist 60% | correlated | correlated | same game script as #245 (variance); own read: variance; we priced this side at 47%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 304 | Tjark Ernst gk_saves over 3.5 | 3.0 | 0.5233 (Low) | pass | market 48% (against), hist 22% (against) | variance | **untagged** | root leg of a 2-leg script loss: #304, #498; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 308 | Senne Lammens gk_saves over 3.5 | 3.0 | 0.4558 (Low) | pass | market 46% (against), hist 30% (against) | correlated | correlated | same game script as #231 (variance); own read: variance; we priced this side at 46%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 310 | Dmytro Riznyk gk_saves over 3.0 | 2.0 | 0.5131 (Low) | pass | market 45% (against), hist 40% (against) | correlated | **untagged** | same game script as #233 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 315 | Lamine Yamal sot over 2.0 | 0.0 | 0.437 (Low) | pass | market 43% (against), hist 40% (against) | correlated | correlated | same game script as #229 (variance); own read: variance; we priced this side at 44%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 316 | Michael Olise sot over 2.0 | 1.0 | 0.4346 (Low) | pass | market 43% (against), hist 38% (against) | correlated | correlated | same game script as #241 (variance); own read: variance; we priced this side at 43%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 319 | Luis Suárez shots over 3.0 | 2.0 | 0.4198 (Low) | pass | hist 29% (against) | correlated | correlated | same game script as #254 (variance); own read: variance; we priced this side at 42%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 321 | Luís Guilherme passes_att over 29.5 | 15.0 | 0.4173 (Low) | pass | model 39% (against), hist 50% (against) | correlated | opportunity: minutes | same game script as #254 (variance); own read: variance; we priced this side at 42%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 322 | David Raya gk_saves over 2.0 | 0.0 | 0.4169 (Low) | pass | market 40% (against), hist 57% | correlated | correlated | same game script as #245 (variance); own read: variance; we priced this side at 42%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 325 | Rayan Cherki shots over 2.5 | 0.0 | 0.2922 (Low) | pass | hist 30% (against) | correlated | **untagged** | same game script as #227 (variance); own read: variance; we priced this side at 29%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 329 | Francesco Pio Esposito shots over 3.5 | 1.0 | 0.3973 (Low) | pass | hist 25% (against) | correlated | opportunity: minutes | same game script as #242 (variance); own read: variance; we priced this side at 40%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 330 | Junior Kadile shots over 2.5 | 2.0 | 0.3931 (Low) | pass | hist 0% (against) | correlated | correlated | same game script as #254 (variance); own read: variance; we priced this side at 39%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 334 | Josep Martínez passes_att under 36.5 | 37.0 | 0.6614 (Medium) | lean | model 68%, hist 60% | correlated | model bias: keeper priced as outfielder | same game script as #242 (variance); own read: variance; closest possible loss (missed by the minimum) |
| 335 | Fermín López shots over 3.0 | 2.0 | 0.3618 (Low) | pass | hist 14% (against) | correlated | correlated | same game script as #229 (variance); own read: variance; we priced this side at 36%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 336 | Yan Diomande shots over 2.5 | 2.0 | 0.2956 (Low) | pass | market 38% (against), hist 0% (against) | correlated | **untagged** | same game script as #295 (variance); own read: variance; we priced this side at 30%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 337 | Joan García gk_saves over 3.0 | 2.0 | 0.3474 (Low) | pass | market 35% (against), hist 14% (against) | correlated | correlated | same game script as #229 (variance); own read: variance; we priced this side at 35%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 341 | Declan Rice passes_att over 79.5 | 77.0 | 0.3442 (Low) | pass | model 36% (against), hist 12% (against) | correlated | correlated | same game script as #245 (variance); own read: variance; we priced this side at 34%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 342 | Kyllian Antonio passes_att over 58.5 | 56.0 | 0.3398 (Low) | pass | model 31% (against), hist 40% (against) | correlated | correlated | same game script as #254 (variance); own read: variance; we priced this side at 34%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 344 | Viktor Gyökeres shots over 3.0 | 0.0 | 0.3035 (Low) | pass | hist 0% (against) | correlated | correlated | same game script as #245 (variance); own read: variance; we priced this side at 30%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 346 | Berke Özer passes_att under 36.5 | 39.0 | 0.743 (Medium) | lean | model 77%, hist 58% | correlated | model bias: keeper priced as outfielder | same game script as #245 (variance); own read: variance |
| 347 | Alessandro Bastoni passes_att under 71.5 | 79.0 | 0.5826 (Low) | pass | model 60%, hist 41% (against) | correlated | correlated | same game script as #242 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 350 | Lukas Jungwirth gk_saves over 4.5 | 2.0 | 0.2736 (Low) | pass | hist 0% (against) | correlated | **untagged** | same game script as #239 (variance); own read: variance; we priced this side at 27%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 351 | Hans Vanaken passes_att under 50.5 | 69.0 | 0.5198 (Low) | pass | model 55%, hist 11% (against) | correlated | correlated | same game script as #242 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 352 | Antonio Nusa passes_att under 26.5 | 28.0 | 0.6747 (Medium) | lean | model 70%, hist 55% | correlated | correlated | same game script as #237 (variance); own read: variance |
| 353 | Jan Oblak passes_att under 34.5 | 36.0 | 0.7967 (Medium) | lean | model 82%, hist 80% | correlated | model bias: keeper priced as outfielder | same game script as #231 (variance); own read: variance; closest possible loss (missed by the minimum) |
| 354 | Maarten Vandevoordt passes_att under 37.5 | 43.0 | 0.7956 (Medium) | lean | model 82%, hist 71% | correlated | model bias: keeper priced as outfielder | same game script as #237 (variance); own read: variance |
| 357 | Yann Sommer passes_att under 34.5 | 46.0 | 0.747 (Low) | pass | model 79%, hist 44% (against) | correlated | model bias: keeper priced as outfielder | same game script as #242 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 359 | Matej Kovár passes_att under 37.5 | 43.0 | 0.847 (Medium) | lean | model 88%, hist 50% (against) | correlated | model bias: keeper priced as outfielder | same game script as #237 (variance); own read: variance |
| 361 | Lamine Yamal passes_att under 45.5 | 50.0 | 0.6336 (Low) | pass | model 66%, hist 47% (against) | correlated | model bias: possession forecast | same game script as #229 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 363 | Rodri passes_att under 86.5 | 116.0 | 0.7328 (Medium) | lean | model 76%, hist 67% | correlated | model bias: possession forecast | same game script as #229 (variance); own read: variance |
| 365 | Ugurcan Çakir passes_att under 35.5 | 46.0 | 0.9166 (Low) | pass | model 95%, hist 36% (against) | correlated | model bias: keeper priced as outfielder | same game script as #229 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 370 | JASON cs_headshots_m12 under 15.0 | 16 | 0.5804 (Medium) | lean | model 57%, hist 62% | variance | variance | root leg of a 8-leg script loss: #370, #376, #378, #379, #380, #381, #382, #384 |
| 376 | POSEIDONN cs_headshots_m12 over 12.0 | 6 | 0.5492 (Low) | pass | model 55%, hist 67% | correlated | correlated | same game script as #370 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 377 | drg cs_kills_m12 under 28.0 | 31 | 0.5374 (Low) | pass | model 55%, hist 33% (against) | correlated | correlated | same game script as #124 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 378 | TWIGS cs_headshots_m12 over 11.5 | 7 | 0.5332 (Low) | pass | model 52%, hist 67% | correlated | correlated | same game script as #370 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 379 | UMAR cs_headshots_m12 under 11.5 | 17 | 0.5324 (Low) | pass | model 51%, hist 67% | correlated | correlated | same game script as #370 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 380 | CAJUN cs_headshots_m12 under 13.5 | 17 | 0.532 (Low) | pass | model 53%, hist 50% (against) | correlated | correlated | same game script as #370 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 381 | INTRA cs_headshots_m12 over 18.0 | 17 | 0.5296 (Low) | pass | model 53%, hist 50% (against) | correlated | correlated | same game script as #370 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 382 | POSEIDONN cs_kills_m12 over 33.5 | 21 | 0.5202 (Low) | pass | model 49% (against), hist 100% | correlated | correlated | same game script as #370 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 384 | UMAR cs_kills_m12 under 30.0 | 43 | 0.5099 (Low) | pass | model 49% (against), hist 60% | correlated | correlated | same game script as #370 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 386 | Steven Kwan batter_total_bases under 1.5 | 2 | 0.6453 (Medium) | lean | model 62%, market 66%, hist 66% | correlated | correlated | same game script as #177 (opportunity); own read: variance; 5 PA from the 1 slot; opposing starter Freddy Peralta went 18 outs / 0 ER; closest possible loss (missed by the minimum) |
| 388 | Junior Caminero batter_total_bases under 1.5 | 2 | 0.5793 (Low) | pass | model 59%, market 57%, hist 53% | correlated | correlated | same game script as #177 (opportunity); own read: variance; logged as a PASS: no money on it; reviewed for calibration; 4 PA from the 3 slot; opposing starter Parker Messick went 15 outs / 0 ER; closest possible loss (missed by the minimum) |
| 396 | Brayan Rocchio batter_hrr over 0.5 | 0 | 0.5885 (Medium) | lean | market 57%, hist 67% | correlated | correlated | same game script as #177 (opportunity); own read: variance; 4 PA from the 9 slot; opposing starter Freddy Peralta went 18 outs / 0 ER; closest possible loss (missed by the minimum) |
| 399 | Angel Martinez batter_hits over 0.5 | 0 | 0.5328 (Low) | pass | hist 53% | correlated | correlated | same game script as #177 (opportunity); own read: opportunity; logged as a PASS: no money on it; reviewed for calibration; only 1 plate appearances; 1 PA from the 7 slot; opposing starter Freddy Peralta went 18 outs / 0 ER |
| 401 | Ben Williamson batter_hits over 0.5 | 0 | 0.5466 (Low) | pass | market 55%, hist 49% (against) | correlated | correlated | same game script as #177 (opportunity); own read: opportunity; logged as a PASS: no money on it; reviewed for calibration; only 2 plate appearances; 2 PA from the 7 slot; opposing starter Parker Messick went 15 outs / 0 ER |
| 402 | Blake Snell pitcher_strikeouts under 6.5 | 9 | 0.4827 (Low) | pass | hist 60% | variance | **untagged** | we priced this side at 48%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; line: 18 outs, 24 BF, 101 pitches, 4 H, 2 BB, 9 K, 4 ER |
| 404 | Dylan Larkin skater_points over 0.5 | 0 | 0.6217 (Low) | pass | market 62% | variance | variance: high-scoring game | root leg of a 15-leg script loss: #404, #407, #409, #410, #412, #415, #416, #421, #425, #426, #427, #430, #438, #439, #440; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 407 | Jack Hughes skater_points under 1.5 | 3 | 0.6676 (Low) | pass | market 66% | correlated | correlated | same game script as #404 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 409 | Jack Hughes skater_sog under 3.5 | 8 | 0.5742 (Low) | pass | market 57% | correlated | correlated | same game script as #404 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 410 | Timo Meier skater_points over 0.5 | 0 | 0.5111 (Low) | pass | market 50% | correlated | correlated | same game script as #404 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 412 | Timo Meier skater_sog over 2.5 | 2 | 0.5439 (Low) | pass | market 54% | correlated | correlated | same game script as #404 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 415 | Dougie Hamilton skater_sog under 2.5 | 5 | 0.5904 (Low) | pass | market 59% | correlated | correlated | same game script as #404 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 416 | Lucas Raymond skater_points over 0.5 | 0 | 0.6127 (Low) | pass | market 61% | correlated | correlated | same game script as #404 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 421 | Nico Hischier skater_sog under 2.5 | 3 | 0.6078 (Low) | pass | market 60% | correlated | correlated | same game script as #404 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 425 | Luke Hughes skater_sog over 1.5 | 1 | 0.5904 (Low) | pass | market 59% | correlated | correlated | same game script as #404 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 426 | Moritz Seider skater_points under 0.5 | 1 | 0.5303 (Low) | pass | market 52% | correlated | correlated | same game script as #404 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 427 | Moritz Seider skater_assists under 0.5 | 1 | 0.5981 (Low) | pass | market 59% | correlated | correlated | same game script as #404 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 430 | Jesper Bratt skater_assists under 0.5 | 2 | 0.5625 (Low) | pass | market 56% | correlated | correlated | same game script as #404 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 438 | Michael Brandsegg-Nygard skater_points under 0.5 | 2 | 0.6078 (Low) | pass | market 60% | correlated | correlated | same game script as #404 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 439 | Michael Brandsegg-Nygard skater_assists under 0.5 | 1 | 0.7087 (Low) | pass | market 71% | correlated | correlated | same game script as #404 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 440 | Viktor Arvidsson skater_points over 0.5 | 0 | 0.5625 (Low) | pass | market 56% | correlated | correlated | same game script as #404 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 442 | Akira Schmid goalie_saves under 23.5 | 24 | 0.5111 (Low) | pass | market 50% | variance | variance: high-scoring game | root leg of a 11-leg script loss: #442, #444, #446, #449, #452, #453, #454, #455, #456, #459, #463; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 444 | Brady Tkachuk skater_assists under 0.5 | 1 | 0.6149 (Low) | pass | market 61% | correlated | correlated | same game script as #442 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 446 | Adam Fantilli skater_points over 0.5 | 0 | 0.5742 (Low) | pass | market 57% | correlated | correlated | same game script as #442 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 449 | Sam Bennett skater_points over 0.5 | 0 | 0.5162 (Low) | pass | market 51% | correlated | correlated | same game script as #442 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 452 | Charlie Coyle skater_points under 0.5 | 1 | 0.5402 (Low) | pass | market 54% | correlated | correlated | same game script as #442 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 453 | Charlie Coyle skater_assists under 0.5 | 1 | 0.6799 (Low) | pass | market 68% | correlated | correlated | same game script as #442 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 454 | Charlie Coyle skater_sog over 1.5 | 1 | 0.5499 (Low) | pass | market 55% | correlated | correlated | same game script as #442 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 455 | Valeri Nichushkin skater_points under 0.5 | 1 | 0.5625 (Low) | pass | market 56% | correlated | correlated | same game script as #442 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 456 | Valeri Nichushkin skater_assists under 0.5 | 1 | 0.6988 (Low) | pass | market 70% | correlated | correlated | same game script as #442 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 459 | Zach Werenski skater_assists over 0.5 | 0 | 0.5981 (Low) | pass | market 59% | correlated | correlated | same game script as #442 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 463 | Sean Monahan skater_sog under 1.5 | 3 | 0.5592 (Low) | pass | market 55% | correlated | correlated | same game script as #442 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 470 | Gianni Stensness passes_att under 39.5 | 40.0 | 0.557 (Low) | pass | model 60%, hist 17% (against) | correlated | correlated | same game script as #241 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 472 | Peter Christiansen passes_att under 10.5 | 16.0 | 0.5261 (Low) | pass | model 56%, hist 15% (against) | correlated | correlated | same game script as #241 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 473 | Renato Veiga passes_att over 72.5 | 57.0 | 0.5236 (Low) | pass | model 53%, hist 45% (against) | correlated | correlated | same game script as #279 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 477 | Rasmus Højlund passes_att under 13.5 | 18.0 | 0.8346 (Medium) | lean | model 87%, hist 50% (against) | correlated | correlated | same game script as #279 (variance); own read: variance |
| 480 | Mikko Rantanen skater_sog over 1.5 | 0 | 0.6385 (Medium) | pass | market 64%, hist 61% | variance | variance | logged as a PASS: no money on it; reviewed for calibration |
| 485 | ckzao cs_kills_m12 under 31.5 | 32 | 0.574 (Low) | user_entry | model 60%, hist 75% | correlated | correlated | same game script as #124 (variance); own read: variance; closest possible loss (missed by the minimum) |
| 489 | Macklin Celebrini skater_sog under 3.5 | 5 | 0.5411 (Low) | pass | market 54%, hist 54% | variance | variance | logged as a PASS: no money on it; reviewed for calibration |
| 490 | n1ssim cs_kills_m12 under 28.0 | 32 | 0.5417 (Low) | pass | model 56%, hist 47% (against) | variance | **untagged** | logged as a PASS: no money on it; reviewed for calibration |
| 491 | Aetinoth kills_m123 over 18.0 | 7 | 0.4513 (Low) | pass | model 52%, hist 47% (against) | variance | **untagged** | we priced this side at 45%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; 7 kills vs 17.9 expected for the actual game results; games had 42/34/29 total kills |
| 498 | Charles Vanhoutte passes_att under 48.5 | 62.0 | 0.655 (Medium) | user_entry | model 80%, hist 62% | correlated | **untagged** | same game script as #304 (variance); own read: variance |
| 511 | Tom Wilson skater_toi over 19.5 | 19.2 | 0.56 (Low) | user_entry | hist 56% | variance | variance | closest possible loss (missed by the minimum) |
| 512 | Zemgus Girgensons skater_hits over 2.5 | 2 | 0.52 (Low) | user_entry | hist 52% | variance | variance | closest possible loss (missed by the minimum) |
| 513 | Tim Stützle skater_toi under 21.5 | 22.05 | 0.55 (Low) | user_entry | hist 55% | variance | variance |  |
| 517 | Waldemar Anton passes_att under 77.5 | 84.0 | 0.3305 (Low) | pass | model 40% (against), hist 47% (against) | correlated | **untagged** | same game script as #234 (variance); own read: variance; we priced this side at 33%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |

Lessons:
- #86: Tout pick, we priced 49% and passed; Liquid lost Nuke (5 HS) and won Mirage (12 HS).
- #88: Near miss (9 vs 9.5): AWPer, 9 HS on 30 kills; 100T won 2-0 in only 36 rounds, which also capped #92 (kills 30 vs 31.5).
- #89: Correct pass (priced over at 49%); he had 26.
- #92: User entry we priced at 41% (Low): 2-0 in 36 rounds capped volume, 30 kills at .83 KPR. Root on #88. Don't enter Lows.
- #94: Both maps went long (Nuke 22, Mirage 21 rounds) and favored Liquid dropped Nuke; kills scale with rounds. Liquid unders #95 #98 #104 rode the same script (all passes).
- #101: Missed by the minimum (26 vs 26.5) on 43 rounds; inputs held.
- #112: Rooster stomped Fruju (16- and 19-round maps) and SkulL had 32 kills in 35 rounds (0.91 per round) against a projected median of 27. Same stomp effect as divine #14 (L21), on a roster that changed the day before.
- #117: Same Rooster stomp as #112: ju1ces 35 kills.
- #124: Galorys won 2-0 but de_ancient went 16-14; kill and HS unders on the whole script lost to map length; one leg per script
- #125: same game script as its root leg; one leg per script
- #126: same game script as its root leg; one leg per script
- #127: same game script as its root leg; one leg per script
- #128: same game script as its root leg; one leg per script
- #129: same game script as its root leg; one leg per script
- #131: same game script as its root leg; one leg per script
- #134: Missed by the minimum (18 vs 17.5): 18 HS on 29 kills (62%) in a 36-round 2-0; HS% spike, not volume.
- #137: same game script as its root leg; one leg per script
- #138: Same Rooster stomp as #112; was a pass.
- #139: same game script as its root leg; one leg per script
- #148: same game script as its root leg; one leg per script
- #155: same game script as its root leg; one leg per script
- #165: same game script as its root leg; one leg per script
- #166: same game script as its root leg; one leg per script
- #167: same game script as its root leg; one leg per script
- #168: same game script as its root leg; one leg per script
- #177: Bailey came in late (2 PA: walk, strikeout); confirm MLB lineups before batter overs
- #178: same game script as its root leg; one leg per script
- #181: same game script as its root leg; one leg per script
- #182: same game script as its root leg; one leg per script
- #191: history-only pass at 54%; no rule
- #192: same game script as its root leg; one leg per script
- #193: same game script as its root leg; one leg per script
- #195: same game script as its root leg; one leg per script
- #196: same game script as its root leg; one leg per script
- #198: missed by 4.5 yards; history-only pass; no rule
- #204: same game script as its root leg; one leg per script
- #208: we priced this side at 46%: losing was the likelier outcome
- #226: L26: keepers priced by soccer.keeper_passes from same-competition starts; verify FAILs an outfield-priced keeper
- #229: played 32 min; confirm starters and minutes before overs
- #231: 28 passes in 71 min (subbed); model 65% vs history 43% against; Low pass, no rule
- #236: played 10 min; confirm starters and minutes before overs
- #237: forecast 52%, actual 43%: L27/L28 (comparable-possession history, European-match possession)
- #241: played 38 min; confirm starters and minutes before overs
- #242: 2 shots in 67 min; history was against (43%); no rule
- #245: played 25 min; confirm starters and minutes before overs
- #246: played 10 min; confirm starters and minutes before overs
- #247: played 25 min; confirm starters and minutes before overs
- #248: shots overs ran 24% vs 53% predicted (29 legs): learn now applies -0.35 logit to the segment
- #253: same game script as its root leg; one leg per script
- #254: forecast 53%, actual 44%: L27/L28 (comparable-possession history, European-match possession)
- #258: shots overs ran 24% vs 53% predicted (29 legs): learn now applies -0.35 logit to the segment
- #265: shots overs ran 24% vs 53% predicted (29 legs): learn now applies -0.35 logit to the segment
- #267: shots overs ran 24% vs 53% predicted (29 legs): learn now applies -0.35 logit to the segment
- #269: shots overs ran 24% vs 53% predicted (29 legs): learn now applies -0.35 logit to the segment
- #270: shots overs ran 24% vs 53% predicted (29 legs): learn now applies -0.35 logit to the segment
- #274: shots overs ran 24% vs 53% predicted (29 legs): learn now applies -0.35 logit to the segment
- #277: forecast 48%, actual 57%: L27/L28 (comparable-possession history, European-match possession)
- #279: history 12% against the market's 55%; Low pass, no rule
- #281: shots overs ran 24% vs 53% predicted (29 legs): learn now applies -0.35 logit to the segment
- #283: played 12 min; confirm starters and minutes before overs
- #289: same game script as its root leg; one leg per script
- #290: L26: keepers priced by soccer.keeper_passes from same-competition starts; verify FAILs an outfield-priced keeper
- #302: shots overs ran 24% vs 53% predicted (29 legs): learn now applies -0.35 logit to the segment
- #308: same game script as its root leg; one leg per script
- #315: same game script as its root leg; one leg per script
- #316: same game script as its root leg; one leg per script
- #319: shots overs ran 24% vs 53% predicted (29 legs): learn now applies -0.35 logit to the segment
- #321: played 24 min; confirm starters and minutes before overs
- #322: same game script as its root leg; one leg per script
- #329: played 23 min; confirm starters and minutes before overs
- #330: shots overs ran 24% vs 53% predicted (29 legs): learn now applies -0.35 logit to the segment
- #334: L26: keepers priced by soccer.keeper_passes from same-competition starts; verify FAILs an outfield-priced keeper
- #335: shots overs ran 24% vs 53% predicted (29 legs): learn now applies -0.35 logit to the segment
- #337: same game script as its root leg; one leg per script
- #341: same game script as its root leg; one leg per script
- #342: same game script as its root leg; one leg per script
- #344: shots overs ran 24% vs 53% predicted (29 legs): learn now applies -0.35 logit to the segment
- #346: L26: keepers priced by soccer.keeper_passes from same-competition starts; verify FAILs an outfield-priced keeper
- #347: same game script as its root leg; one leg per script
- #351: same game script as its root leg; one leg per script
- #352: same game script as its root leg; one leg per script
- #353: L26: keepers priced by soccer.keeper_passes from same-competition starts; verify FAILs an outfield-priced keeper
- #354: L26: keepers priced by soccer.keeper_passes from same-competition starts; verify FAILs an outfield-priced keeper
- #357: L26: keepers priced by soccer.keeper_passes from same-competition starts; verify FAILs an outfield-priced keeper
- #359: L26: keepers priced by soccer.keeper_passes from same-competition starts; verify FAILs an outfield-priced keeper
- #361: forecast 62%, actual 71%: L27/L28 (comparable-possession history, European-match possession)
- #363: forecast 62%, actual 71%: L27/L28 (comparable-possession history, European-match possession)
- #365: L26: keepers priced by soccer.keeper_passes from same-competition starts; verify FAILs an outfield-priced keeper
- #370: 16 HS vs 15.0 line over two short maps; no rule
- #376: same game script as its root leg; one leg per script
- #377: same game script as its root leg; one leg per script
- #378: same game script as its root leg; one leg per script
- #379: same game script as its root leg; one leg per script
- #380: same game script as its root leg; one leg per script
- #381: same game script as its root leg; one leg per script
- #382: same game script as its root leg; one leg per script
- #384: same game script as its root leg; one leg per script
- #386: same game script as its root leg; one leg per script
- #388: same game script as its root leg; one leg per script
- #396: same game script as its root leg; one leg per script
- #399: same game script as its root leg; one leg per script
- #401: same game script as its root leg; one leg per script
- #404: NJ@DET 5-4: points and SOG unders on the script lost together; one leg per game
- #407: same game script as its root leg; one leg per script
- #409: same game script as its root leg; one leg per script
- #410: same game script as its root leg; one leg per script
- #412: same game script as its root leg; one leg per script
- #415: same game script as its root leg; one leg per script
- #416: same game script as its root leg; one leg per script
- #421: same game script as its root leg; one leg per script
- #425: same game script as its root leg; one leg per script
- #426: same game script as its root leg; one leg per script
- #427: same game script as its root leg; one leg per script
- #430: same game script as its root leg; one leg per script
- #438: same game script as its root leg; one leg per script
- #439: same game script as its root leg; one leg per script
- #440: same game script as its root leg; one leg per script
- #442: FLA@CBJ 7-3: missed by one save; the script's points unders lost together; one leg per game
- #444: same game script as its root leg; one leg per script
- #446: same game script as its root leg; one leg per script
- #449: same game script as its root leg; one leg per script
- #452: same game script as its root leg; one leg per script
- #453: same game script as its root leg; one leg per script
- #454: same game script as its root leg; one leg per script
- #455: same game script as its root leg; one leg per script
- #456: same game script as its root leg; one leg per script
- #459: same game script as its root leg; one leg per script
- #463: same game script as its root leg; one leg per script
- #470: same game script as its root leg; one leg per script
- #472: same game script as its root leg; one leg per script
- #473: same game script as its root leg; one leg per script
- #477: same game script as its root leg; one leg per script
- #480: 0 SOG in 21.6 min; market 64% and history 61% agreed; no rule
- #485: same game script as its root leg; one leg per script
- #489: 5 SOG incl. a PP goal in a 6-3 game; 54% coin flip; no rule
- #511: your entry leg: 19.2 vs 19.5 TOI; history-only 56%, no market price; L20: unpriced legs out of entries
- #512: your entry leg: 2 hits vs 2.5; history-only 52%, no market price; L20: unpriced legs out of entries
- #513: your entry leg: 22.05 vs 21.5 TOI in a 7-2 game; history-only 55%; L20: unpriced legs out of entries

Detail from the feeds:
- #86 EliGE: de_nuke: 22 rds, L, 9 K / 5 HS; de_mirage: 21 rds, W, 17 K / 12 HS
- #88 dev1ce: de_cache: 20 rds, W, 14 K / 3 HS; de_dust2: 16 rds, W, 16 K / 6 HS
- #89 foggers: de_inferno: 16 rds, W, 16 K / 9 HS; de_cache: 19 rds, W, 10 K / 5 HS
- #92 dev1ce: de_cache: 20 rds, W, 14 K / 3 HS; de_dust2: 16 rds, W, 16 K / 6 HS
- #94 Jorko: de_nuke: 22 rds, L, 19 K / 2 HS; de_mirage: 21 rds, W, 16 K / 5 HS
- #95 malbsMd: de_nuke: 22 rds, L, 18 K / 8 HS; de_mirage: 21 rds, W, 22 K / 15 HS
- #98 JT: de_nuke: 22 rds, L, 15 K / 7 HS; de_mirage: 21 rds, W, 13 K / 5 HS
- #101 NickyB: de_nuke: 22 rds, W, 13 K / 7 HS; de_mirage: 21 rds, L, 13 K / 6 HS
- #102 MIstR: de_nuke: 22 rds, W, 13 K / 8 HS; de_mirage: 21 rds, L, 10 K / 3 HS
- #104 malbsMd: de_nuke: 22 rds, L, 18 K / 8 HS; de_mirage: 21 rds, W, 22 K / 15 HS
- #108 salazar: de_nuke: 22 rds, W, 20 K / 6 HS; de_mirage: 21 rds, L, 9 K / 2 HS
- #109 NickyB: de_nuke: 22 rds, W, 13 K / 7 HS; de_mirage: 21 rds, L, 13 K / 6 HS
- #112 SkulL: de_inferno: 16 rds, W, 16 K / 9 HS; de_cache: 19 rds, W, 16 K / 5 HS
- #117 ju1ces: de_inferno: 16 rds, W, 13 K / 9 HS; de_cache: 19 rds, W, 22 K / 12 HS
- #124 detr0ittJ: de_dust2: 19 rds, W, 17 K / 3 HS; de_ancient: 30 rds, W, 16 K / 10 HS
- #125 gbb: de_dust2: 19 rds, W, 13 K / 8 HS; de_ancient: 30 rds, W, 29 K / 19 HS
- #126 PKL: de_dust2: 19 rds, W, 12 K / 9 HS; de_ancient: 30 rds, W, 13 K / 5 HS
- #127 detr0ittJ: de_dust2: 19 rds, W, 17 K / 3 HS; de_ancient: 30 rds, W, 16 K / 10 HS
- #128 PKL: de_dust2: 19 rds, W, 12 K / 9 HS; de_ancient: 30 rds, W, 13 K / 5 HS
- #129 gbb: de_dust2: 19 rds, W, 13 K / 8 HS; de_ancient: 30 rds, W, 29 K / 19 HS
- #131 drg: de_dust2: 19 rds, L, 9 K / 6 HS; de_ancient: 30 rds, L, 22 K / 14 HS
- #134 sirah: de_cache: 20 rds, W, 15 K / 8 HS; de_dust2: 16 rds, W, 14 K / 10 HS
- #137 destiny: de_dust2: 19 rds, W, 21 K / 10 HS; de_ancient: 30 rds, W, 31 K / 17 HS
- #138 ju1ces: de_inferno: 16 rds, W, 13 K / 9 HS; de_cache: 19 rds, W, 22 K / 12 HS
- #139 destiny: de_dust2: 19 rds, W, 21 K / 10 HS; de_ancient: 30 rds, W, 31 K / 17 HS
- #141 sinnopsyy: de_cache: 20 rds, L, 9 K / 5 HS; de_dust2: 16 rds, L, 7 K / 2 HS
- #142 0SAMAS: de_cache: 20 rds, L, 12 K / 7 HS; de_dust2: 16 rds, L, 12 K / 2 HS
- #144 CacaNito: de_cache: 20 rds, L, 17 K / 9 HS; de_dust2: 16 rds, L, 5 K / 1 HS
- #147 0SAMAS: de_cache: 20 rds, L, 12 K / 7 HS; de_dust2: 16 rds, L, 12 K / 2 HS
- #148 drg: de_dust2: 19 rds, L, 9 K / 6 HS; de_ancient: 30 rds, L, 22 K / 14 HS
- #149 Gizmy: de_cache: 20 rds, W, 5 K / 4 HS; de_dust2: 16 rds, W, 12 K / 4 HS
- #150 m1N1: de_cache: 20 rds, L, 7 K / 2 HS; de_dust2: 16 rds, L, 8 K / 2 HS
- #151 sinnopsyy: de_cache: 20 rds, L, 9 K / 5 HS; de_dust2: 16 rds, L, 7 K / 2 HS
- #152 MIstR: de_nuke: 22 rds, W, 13 K / 8 HS; de_mirage: 21 rds, L, 10 K / 3 HS
- #153 Gizmy: de_cache: 20 rds, W, 5 K / 4 HS; de_dust2: 16 rds, W, 12 K / 4 HS
- #155 ckzao: de_dust2: 19 rds, L, 18 K / 11 HS; de_ancient: 30 rds, L, 14 K / 6 HS
- #157 leakz: de_nuke: 22 rds, W, 21 K / 12 HS; de_mirage: 21 rds, L, 16 K / 6 HS
- #158 EliGe: de_nuke: 22 rds, L, 9 K / 5 HS; de_mirage: 21 rds, W, 17 K / 12 HS
- #165 Freddy Peralta: outs=18, bf=25, pitches=99, h=4, er=0, bb=2, k=6, p_per_pa=3.96
- #166 Parker Messick: outs=15, bf=22, pitches=82, h=6, er=0, bb=2, k=3, p_per_pa=3.73
- #167 Junior Caminero: inn 1 vs Messick: Double; inn 4 vs Messick: Walk; inn 5 vs Messick: Flyout; inn 8 vs Cecconi: Strikeout
- #168 Yandy Díaz: inn 1 vs Messick: Groundout; inn 3 vs Messick: Grounded Into DP; inn 5 vs Messick: Flyout; inn 7 vs Armstrong: Strikeout
- #177 Patrick Bailey: inn 7 vs Kelly: Walk; scored inn 7 (bullpen); inn 9 vs Baker: Strikeout
- #178 Patrick Bailey: inn 7 vs Kelly: Walk; scored inn 7 (bullpen); inn 9 vs Baker: Strikeout
- #181 Brayan Rocchio: inn 2 vs Peralta: Strikeout; inn 5 vs Peralta: Flyout; inn 7 vs Kelly: Flyout; inn 9 vs Baker: Flyout
- #182 Brayan Rocchio: inn 2 vs Peralta: Strikeout; inn 5 vs Peralta: Flyout; inn 7 vs Kelly: Flyout; inn 9 vs Baker: Flyout
- #208 OMON: G1 W: 3 K (expected 6.5); Movistar KOI Fenix 7 - Galions 27, 34 total; G2 W: 5 K (expected 6.5); Galions 19 - Movistar KOI Fenix 10, 29 total; G3 W: 5 K (expected 6.5); Galions 24 - Movistar KOI Fenix 10, 34 total
- #225 Bdd: G1 L: 1 K (expected 1.9); BNK FearX 22 - KT Rolster 8, 30 total; G2 W: 6 K (expected 5.4); BNK FearX 8 - KT Rolster 22, 30 total; G3 L: 2 K (expected 1.9); KT Rolster 11 - BNK FearX 23, 34 total
- #226 Jakub Markovic: minutes=90.0, passes=34.0, team_passes=403, possession=55.2, saves=4.0, score=SAB 2 - SLP 0
- #227 Ferran Torres: minutes=14.0, passes=2.0, team_passes=444, possession=46.1, saves=0.0, score=MNC 2 - PSG 4
- #229 Gabriel Jesus: minutes=32.0, passes=15.0, team_passes=689, possession=71, saves=0.0, score=GAL 1 - BAR 4
- #231 Julián Alvarez: minutes=71.0, passes=28.0, team_passes=652, possession=57.8, saves=0.0, score=ATM 2 - MAN 0
- #233 Alberto Brignoli: minutes=90.0, passes=29.0, team_passes=368, possession=45.5, saves=1.0, score=SHK 3 - AEK 1
- #234 Gregor Kobel: minutes=90.0, passes=26.0, team_passes=583, possession=52.2, saves=2.0, score=BODO 1 - DOR 0
- #236 Matheus Cunha: minutes=10.0, passes=14.0, team_passes=466, possession=42.2, saves=0.0, score=ATM 2 - MAN 0
- #237 Willi Orbán: minutes=90.0, passes=40.0, team_passes=350, possession=43, saves=0.0, score=RBL 1 - PSV 0
- #238 Khvicha Kvaratskhelia: minutes=24.0, passes=1.0, team_passes=444, possession=46.1, saves=0.0, score=MNC 2 - PSG 4
- #239 Alisson Becker: minutes=90.0, passes=37.0, team_passes=576, possession=64.2, saves=1.0, score=LAS 3 - LIV 6
- #241 Ismael Saibari: minutes=38.0, passes=6.0, team_passes=566, possession=65.5, saves=0.0, score=VIK 3 - MUN 3
- #242 Marcus Thuram: minutes=67.0, passes=27.0, team_passes=533, possession=53.3, saves=0.0, score=INT 3 - BRU 4
- #245 Bukayo Saka: minutes=25.0, passes=10.0, team_passes=543, possession=58, saves=0.0, score=ARS 3 - LILL 0
- #246 Matheus Cunha: minutes=10.0, passes=14.0, team_passes=466, possession=42.2, saves=0.0, score=ATM 2 - MAN 0
- #247 Kai Havertz: minutes=25.0, passes=11.0, team_passes=543, possession=58, saves=0.0, score=ARS 3 - LILL 0
- #248 Marcus Rashford: minutes=66.0, passes=11.0, team_passes=466, possession=42.2, saves=0.0, score=ATM 2 - MAN 0
- #253 Brandon Mechele: minutes=90.0, passes=54.0, team_passes=475, possession=46.7, saves=0.0, score=INT 3 - BRU 4
- #254 Gonçalo Inácio: minutes=90.0, passes=67.0, team_passes=435, possession=44.1, saves=0.0, score=RCL 0 - SCP 2
- #256 Désiré Doué: minutes=66.0, passes=28.0, team_passes=444, possession=46.1, saves=0.0, score=MNC 2 - PSG 4
- #258 Michael Olise: minutes=73.0, passes=55.0, team_passes=566, possession=65.5, saves=0.0, score=VIK 3 - MUN 3
- #265 Joy-Lance Mickels: minutes=90.0, passes=18.0, team_passes=341, possession=44.8, saves=0.0, score=SAB 2 - SLP 0
- #267 Julián Alvarez: minutes=71.0, passes=28.0, team_passes=652, possession=57.8, saves=0.0, score=ATM 2 - MAN 0
- #269 Rafael Leão: minutes=90.0, passes=27.0, team_passes=273, possession=29, saves=0.0, score=GAL 1 - BAR 4
- #270 Christopher Nkunku: minutes=90.0, passes=19.0, team_passes=350, possession=43, saves=0.0, score=RBL 1 - PSV 0
- #271 Víctor Muñoz: minutes=17.0, passes=7.0, team_passes=576, possession=64.2, saves=0.0, score=LAS 3 - LIV 6
- #272 Ousmane Dembélé: minutes=76.0, passes=41.0, team_passes=444, possession=46.1, saves=0.0, score=MNC 2 - PSG 4
- #274 Harry Kane: minutes=90.0, passes=20.0, team_passes=566, possession=65.5, saves=0.0, score=VIK 3 - MUN 3
- #277 Kodai Sano: minutes=90.0, passes=52.0, team_passes=466, possession=57, saves=0.0, score=RBL 1 - PSV 0
- #279 Kevin De Bruyne: minutes=90.0, passes=52.0, team_passes=443, possession=48, saves=0.0, score=VIL 3 - NAP 1
- #281 Victor Osimhen: minutes=90.0, passes=3.0, team_passes=273, possession=29, saves=0.0, score=GAL 1 - BAR 4
- #283 Olivier Giroud: minutes=12.0, passes=4.0, team_passes=405, possession=42, saves=0.0, score=ARS 3 - LILL 0
- #289 Bruno Fernandes: minutes=80.0, passes=32.0, team_passes=466, possession=42.2, saves=0.0, score=ATM 2 - MAN 0
- #290 David Raya: minutes=90.0, passes=21.0, team_passes=543, possession=58, saves=0.0, score=ARS 3 - LILL 0
- #295 Vinícius Júnior: minutes=59.0, passes=15.0, team_passes=459, possession=46, saves=0.0, score=ROMA 3 - RMA 4
- #296 Arda Güler: minutes=31.0, passes=27.0, team_passes=459, possession=46, saves=0.0, score=ROMA 3 - RMA 4
- #300 Jérémy Doku: minutes=45.0, passes=11.0, team_passes=499, possession=53.9, saves=0.0, score=MNC 2 - PSG 4
- #302 Ayase Ueda: minutes=78.0, passes=12.0, team_passes=405, possession=42, saves=0.0, score=ARS 3 - LILL 0
- #304 Tjark Ernst: minutes=90.0, passes=26.0, team_passes=517, possession=47.8, saves=3.0, score=FEY 3 - COMO 2
- #308 Senne Lammens: minutes=90.0, passes=24.0, team_passes=466, possession=42.2, saves=3.0, score=ATM 2 - MAN 0
- #310 Dmytro Riznyk: minutes=90.0, passes=34.0, team_passes=447, possession=54.5, saves=2.0, score=SHK 3 - AEK 1
- #315 Lamine Yamal: minutes=90.0, passes=50.0, team_passes=689, possession=71, saves=0.0, score=GAL 1 - BAR 4
- #316 Michael Olise: minutes=73.0, passes=55.0, team_passes=566, possession=65.5, saves=0.0, score=VIK 3 - MUN 3
- #319 Luis Suárez: minutes=85.0, passes=18.0, team_passes=435, possession=44.1, saves=0.0, score=RCL 0 - SCP 2
- #321 Luís Guilherme: minutes=24.0, passes=15.0, team_passes=435, possession=44.1, saves=0.0, score=RCL 0 - SCP 2
- #322 David Raya: minutes=90.0, passes=21.0, team_passes=543, possession=58, saves=0.0, score=ARS 3 - LILL 0
- #325 Rayan Cherki: minutes=45.0, passes=26.0, team_passes=499, possession=53.9, saves=0.0, score=MNC 2 - PSG 4
- #329 Francesco Pio Esposito: minutes=23.0, passes=10.0, team_passes=533, possession=53.3, saves=0.0, score=INT 3 - BRU 4
- #330 Junior Kadile: minutes=68.0, passes=21.0, team_passes=545, possession=55.9, saves=0.0, score=RCL 0 - SCP 2
- #334 Josep Martínez: minutes=90.0, passes=37.0, team_passes=533, possession=53.3, saves=4.0, score=INT 3 - BRU 4
- #335 Fermín López: minutes=82.0, passes=46.0, team_passes=689, possession=71, saves=0.0, score=GAL 1 - BAR 4
- #336 Yan Diomande: minutes=78.0, passes=30.0, team_passes=459, possession=46, saves=0.0, score=ROMA 3 - RMA 4
- #337 Joan García: minutes=90.0, passes=21.0, team_passes=689, possession=71, saves=2.0, score=GAL 1 - BAR 4
- #341 Declan Rice: minutes=90.0, passes=77.0, team_passes=543, possession=58, saves=0.0, score=ARS 3 - LILL 0
- #342 Kyllian Antonio: minutes=90.0, passes=56.0, team_passes=545, possession=55.9, saves=0.0, score=RCL 0 - SCP 2
- #344 Viktor Gyökeres: minutes=65.0, passes=8.0, team_passes=543, possession=58, saves=0.0, score=ARS 3 - LILL 0
- #346 Berke Özer: minutes=90.0, passes=39.0, team_passes=405, possession=42, saves=5.0, score=ARS 3 - LILL 0
- #347 Alessandro Bastoni: minutes=90.0, passes=79.0, team_passes=533, possession=53.3, saves=0.0, score=INT 3 - BRU 4
- #350 Lukas Jungwirth: minutes=90.0, passes=30.0, team_passes=310, possession=35.8, saves=2.0, score=LAS 3 - LIV 6
- #351 Hans Vanaken: minutes=90.0, passes=69.0, team_passes=475, possession=46.7, saves=0.0, score=INT 3 - BRU 4
- #352 Antonio Nusa: minutes=90.0, passes=28.0, team_passes=350, possession=43, saves=0.0, score=RBL 1 - PSV 0
- #353 Jan Oblak: minutes=90.0, passes=36.0, team_passes=652, possession=57.8, saves=4.0, score=ATM 2 - MAN 0
- #354 Maarten Vandevoordt: minutes=90.0, passes=43.0, team_passes=350, possession=43, saves=5.0, score=RBL 1 - PSV 0
- #357 Yann Sommer: minutes=90.0, passes=46.0, team_passes=475, possession=46.7, saves=9.0, score=INT 3 - BRU 4
- #359 Matej Kovár: minutes=90.0, passes=43.0, team_passes=466, possession=57, saves=6.0, score=RBL 1 - PSV 0
- #361 Lamine Yamal: minutes=90.0, passes=50.0, team_passes=689, possession=71, saves=0.0, score=GAL 1 - BAR 4
- #363 Rodri: minutes=90.0, passes=116.0, team_passes=689, possession=71, saves=0.0, score=GAL 1 - BAR 4
- #365 Ugurcan Çakir: minutes=90.0, passes=46.0, team_passes=273, possession=29, saves=6.0, score=GAL 1 - BAR 4
- #370 JASON: de_dust2: 21 rds, W, 16 K / 9 HS; de_mirage: 19 rds, W, 16 K / 7 HS
- #376 POSEIDONN: de_dust2: 21 rds, L, 10 K / 3 HS; de_mirage: 19 rds, L, 11 K / 3 HS
- #377 drg: de_dust2: 19 rds, L, 9 K / 6 HS; de_ancient: 30 rds, L, 22 K / 14 HS
- #378 TWIGS: de_dust2: 21 rds, L, 11 K / 2 HS; de_mirage: 19 rds, L, 12 K / 5 HS
- #379 UMAR: de_dust2: 21 rds, W, 23 K / 12 HS; de_mirage: 19 rds, W, 20 K / 5 HS
- #380 CAJUN: de_dust2: 21 rds, L, 13 K / 8 HS; de_mirage: 19 rds, L, 13 K / 9 HS
- #381 INTRA: de_dust2: 21 rds, W, 12 K / 8 HS; de_mirage: 19 rds, W, 14 K / 9 HS
- #382 POSEIDONN: de_dust2: 21 rds, L, 10 K / 3 HS; de_mirage: 19 rds, L, 11 K / 3 HS
- #384 UMAR: de_dust2: 21 rds, W, 23 K / 12 HS; de_mirage: 19 rds, W, 20 K / 5 HS
- #386 Steven Kwan: inn 1 vs Peralta: Single; inn 3 vs Peralta: Lineout; inn 5 vs Peralta: Lineout; inn 7 vs Kelly: Single; inn 9 vs Baker: Groundout
- #388 Junior Caminero: inn 1 vs Messick: Double; inn 4 vs Messick: Walk; inn 5 vs Messick: Flyout; inn 8 vs Cecconi: Strikeout
- #396 Brayan Rocchio: inn 2 vs Peralta: Strikeout; inn 5 vs Peralta: Flyout; inn 7 vs Kelly: Flyout; inn 9 vs Baker: Flyout
- #399 Angel Martinez: inn 8 vs Seymour: Strikeout
- #401 Ben Williamson: inn 2 vs Messick: Walk; inn 4 vs Messick: Field Error; scored inn 4 (starter)
- #402 Blake Snell: outs=18, bf=24, pitches=101, h=4, er=4, bb=2, k=9, p_per_pa=4.21
- #404 Dylan Larkin: toi=21.3, sog=2, shifts=26, pp_goals=0, score=5-4
- #407 Jack Hughes: toi=23.5, sog=8, shifts=23, pp_goals=0, score=5-4
- #409 Jack Hughes: toi=23.5, sog=8, shifts=23, pp_goals=0, score=5-4
- #410 Timo Meier: toi=14.9, sog=2, shifts=19, pp_goals=0, score=5-4
- #412 Timo Meier: toi=14.9, sog=2, shifts=19, pp_goals=0, score=5-4
- #415 Dougie Hamilton: toi=20.5, sog=5, shifts=24, pp_goals=0, score=5-4
- #416 Lucas Raymond: toi=19.5, sog=1, shifts=27, pp_goals=0, score=5-4
- #421 Nico Hischier: toi=16.4, sog=3, shifts=22, pp_goals=1, score=5-4
- #425 Luke Hughes: toi=25.4, sog=1, shifts=27, pp_goals=0, score=5-4
- #426 Moritz Seider: toi=23.4, sog=2, shifts=28, pp_goals=0, score=5-4
- #427 Moritz Seider: toi=23.4, sog=2, shifts=28, pp_goals=0, score=5-4
- #430 Jesper Bratt: toi=20.3, sog=2, shifts=24, pp_goals=0, score=5-4
- #438 Michael Brandsegg-Nygard: toi=19.0, sog=4, shifts=24, pp_goals=0, score=5-4
- #439 Michael Brandsegg-Nygard: toi=19.0, sog=4, shifts=24, pp_goals=0, score=5-4
- #440 Viktor Arvidsson: toi=20.2, sog=1, shifts=27, pp_goals=0, score=5-4
- #442 Akira Schmid: toi=60.0, sog=None, shifts=None, pp_goals=None, score=7-3
- #444 Brady Tkachuk: toi=16.3, sog=4, shifts=22, pp_goals=2, score=7-3
- #446 Adam Fantilli: toi=20.4, sog=2, shifts=24, pp_goals=0, score=7-3
- #449 Sam Bennett: toi=15.8, sog=1, shifts=19, pp_goals=0, score=7-3
- #452 Charlie Coyle: toi=16.5, sog=1, shifts=23, pp_goals=0, score=7-3
- #453 Charlie Coyle: toi=16.5, sog=1, shifts=23, pp_goals=0, score=7-3
- #454 Charlie Coyle: toi=16.5, sog=1, shifts=23, pp_goals=0, score=7-3
- #455 Valeri Nichushkin: toi=15.7, sog=2, shifts=22, pp_goals=0, score=7-3
- #456 Valeri Nichushkin: toi=15.7, sog=2, shifts=22, pp_goals=0, score=7-3
- #459 Zach Werenski: toi=26.3, sog=3, shifts=26, pp_goals=0, score=7-3
- #463 Sean Monahan: toi=16.9, sog=3, shifts=24, pp_goals=0, score=7-3
- #470 Gianni Stensness: minutes=90.0, passes=40.0, team_passes=284, possession=34.5, saves=0.0, score=VIK 3 - MUN 3
- #472 Peter Christiansen: minutes=90.0, passes=16.0, team_passes=284, possession=34.5, saves=0.0, score=VIK 3 - MUN 3
- #473 Renato Veiga: minutes=90.0, passes=57.0, team_passes=492, possession=52, saves=0.0, score=VIL 3 - NAP 1
- #477 Rasmus Højlund: minutes=90.0, passes=18.0, team_passes=443, possession=48, saves=0.0, score=VIL 3 - NAP 1
- #480 Mikko Rantanen: toi=21.6, sog=0, shifts=25, pp_goals=0, score=3-2
- #485 ckzao: de_dust2: 19 rds, L, 18 K / 11 HS; de_ancient: 30 rds, L, 14 K / 6 HS
- #489 Macklin Celebrini: toi=19.9, sog=5, shifts=19, pp_goals=1, score=6-3
- #490 n1ssim: de_dust2: 24 rds, W, 12 K / 7 HS; de_mirage: 30 rds, W, 20 K / 6 HS
- #491 Aetinoth: G1 W: 5 K (expected 7.2); Anubis Gaming 18 - Picks Solary 24, 42 total; G2 L: 1 K (expected 3.4); Solary 12 - Picks Anubis Gaming 22, 34 total; G3 W: 1 K (expected 7.2); Solary 25 - Picks Anubis Gaming 4, 29 total
- #498 Charles Vanhoutte: minutes=90.0, passes=62.0, team_passes=517, possession=47.8, saves=0.0, score=FEY 3 - COMO 2
- #511 Tom Wilson: toi=19.2, sog=0, shifts=22, pp_goals=0, score=2-4
- #512 Zemgus Girgensons: toi=15.0, sog=2, shifts=19, pp_goals=0, score=1-4
- #513 Tim Stützle: toi=22.1, sog=1, shifts=25, pp_goals=0, score=7-2
- #517 Waldemar Anton: minutes=90.0, passes=84.0, team_passes=583, possession=52.2, saves=0.0, score=BODO 1 - DOR 0

## 2026-10-12: 44 losses from 23 independent causes

| # | Leg | Result | Our p | Action | Sources | Auto tag | Confirmed | Evidence |
|---|---|---|---|---|---|---|---|---|
| 1 | Kirill Kaprizov skater_sog under 3.5 | 4 | 0.6054 (Medium) | bet | model 66%, market 55%, hist 59% | variance | variance | root leg of a 2-leg script loss: #1, #2; closest possible loss (missed by the minimum) |
| 2 | Ryan Hartman skater_sog under 1.5 | 2 | 0.4935 (Low) | pass | model 54%, market 42% (against), hist 80% | correlated | correlated | same game script as #1 (variance); own read: model bias; we priced this side at 49%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 6 | Yoshinobu Yamamoto pitcher_outs over 17.5 | 8 | 0.6912 (Medium) | bet | market 63%, hist 90% | opportunity | opportunity | root leg of a 4-leg script loss: #6, #13, #24, #29; pulled after 8 outs (75 pitches, 14 BF, 5.36 P/PA) |
| 8 | Drew Rasmussen pitcher_hits_allowed under 4.5 | 8 | 0.5791 (Medium) | bet | model 59%, market 55%, hist 64% | variance | model bias | root leg of a 2-leg script loss: #8, #28; line: 18 outs, 25 BF, 91 pitches, 8 H, 0 BB, 7 K, 2 ER |
| 9 | Foster Griffin pitcher_outs over 12.5 | 12 | 0.6106 (Medium) | lean | model 59%, market 54%, hist 90% | variance | opportunity | line: 12 outs, 18 BF, 63 pitches, 5 H, 0 BB, 3 K, 2 ER; closest possible loss (missed by the minimum) |
| 11 | Victor Mesa Jr. batter_walks over 0.5 | 0 | 0.2656 (Low) | lean | model 30% (against), market 22% (against) | variance | variance | we priced this side at 27%: losing was the more likely outcome; 4 PA from the 5 slot; opposing starter Foster Griffin went 12 outs / 2 ER; closest possible loss (missed by the minimum) |
| 12 | Josh Allen rush_yds under 36.5 | 121.0 | 0.5288 (Low) | user_entry | model 54%, market 50% (against), hist 75% | variance | variance |  |
| 13 | Yoshinobu Yamamoto pitcher_earned_runs under 1.5 | 3 | 0.4715 (Low) | user_entry | market 46% (against), hist 52% | correlated | correlated | same game script as #6 (opportunity); own read: variance; we priced this side at 47%: losing was the more likely outcome; line: 8 outs, 14 BF, 75 pitches, 4 H, 2 BB, 1 K, 3 ER |
| 14 | divine cs_kills_m12 under 29.5 | 32 | 0.6356 (High) | bet | model 65%, hist 67% | variance | model bias | root leg of a 2-leg script loss: #14, #15 |
| 15 | lash cs_headshots_m12 over 10.5 | 6 | 0.6302 (Medium) | lean | model 64%, hist 80% | correlated | correlated | same game script as #14 (variance); own read: variance |
| 17 | jared cs_headshots_m12 under 14.5 | 17 | 0.6281 (High) | bet | model 61%, hist 80% | variance | variance |  |
| 22 | Logan Henderson pitcher_walks under 1.5 | 2 | 0.588 (Medium) | lean | model 60%, market 54%, hist 74% | variance | variance | line: 12 outs, 18 BF, 64 pitches, 3 H, 2 BB, 2 K, 2 ER; closest possible loss (missed by the minimum) |
| 24 | Yoshinobu Yamamoto pitcher_pitches over 93.5 | 75 | 0.602 (Medium) | lean | model 60%, hist 66% | correlated | correlated | same game script as #6 (opportunity); own read: opportunity; pulled after 8 outs (75 pitches, 14 BF, 5.36 P/PA) |
| 28 | Drew Rasmussen pitcher_earned_runs under 1.5 | 2 | 0.528 (Low) | pass | model 54%, market 50%, hist 58% | correlated | correlated | same game script as #8 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; line: 18 outs, 25 BF, 91 pitches, 8 H, 0 BB, 7 K, 2 ER; closest possible loss (missed by the minimum) |
| 29 | Christian Yelich batter_hrr under 1.5 | 4 | 0.603 (Medium) | lean | model 64%, market 59%, hist 52% | correlated | correlated | same game script as #6 (opportunity); own read: variance; 5 PA from the 5 slot; opposing starter Yoshinobu Yamamoto went 8 outs / 3 ER; 3 of 4 H+R+RBI came off the starter, 1 off the bullpen |
| 31 | Jo Adell batter_hrr under 1.5 | 3 | 0.573 (Medium) | lean | model 59%, market 57%, hist 52% | variance | model bias | 5 PA from the 4 slot; opposing starter Drew Rasmussen went 18 outs / 2 ER; 0 of 3 H+R+RBI came off the starter, 3 off the bullpen (the bullpen part alone beat the line: not just the starter's fault) |
| 32 | José Ramírez batter_hrr under 1.5 | 6 | 0.57 (Medium) | lean | model 59%, market 56%, hist 52% | variance | model bias | 5 PA from the 2 slot; opposing starter Drew Rasmussen went 18 outs / 2 ER; 1 of 6 H+R+RBI came off the starter, 5 off the bullpen (the bullpen part alone beat the line: not just the starter's fault) |
| 33 | Brice Turang batter_hrr under 1.5 | 6 | 0.553 (Low) | pass | model 58%, market 57%, hist 43% (against) | variance | variance | logged as a PASS: no money on it; reviewed for calibration; 5 PA from the 2 slot; opposing starter Yoshinobu Yamamoto went 8 outs / 3 ER; 3 of 6 H+R+RBI came off the starter, 3 off the bullpen (the bullpen part alone beat the line: not just the starter's fault) |
| 36 | Mookie Betts batter_hrr under 1.5 | 2 | 0.5146 (Low) | pass | model 57%, market 52%, hist 55% | variance | variance | logged as a PASS: no money on it; reviewed for calibration; 4 PA from the 1 slot; opposing starter Logan Henderson went 12 outs / 2 ER; 2 of 2 H+R+RBI came off the starter, 0 off the bullpen; closest possible loss (missed by the minimum) |
| 41 | David Hamilton batter_hrr under 1.5 | 5 | 0.6837 (High) | lean | model 76%, hist 65% | variance | model bias | 4 PA from the 9 slot; opposing starter Yoshinobu Yamamoto went 8 outs / 3 ER; 2 of 5 H+R+RBI came off the starter, 3 off the bullpen (the bullpen part alone beat the line: not just the starter's fault) |
| 47 | Tangyuan kills_m123 over 11.5 | 9 | 0.7151 (High) | bet | model 72%, hist 74% | variance | data error | root leg of a 2-leg script loss: #47, #73; 9 kills vs 13.8 expected for the actual game results; games had 23/34/20 total kills |
| 48 | Harpoon kills_m123 under 18.5 | 24 | 0.6947 (Low) | lean | model 73%, hist 48% (against) | variance | variance: stomp series | root leg of a 4-leg script loss: #48, #59, #61, #84; 24 kills vs 20.2 expected for the actual game results; games had 34/29/34 total kills |
| 51 | Theocacs kills_m123 over 7.5 | 7 | 0.7041 (Medium) | pass | model 80%, hist 83% | variance | **untagged** | root leg of a 2-leg script loss: #51, #83; logged as a PASS: no money on it; reviewed for calibration; 7 kills vs 9.1 expected for the actual game results; games had 42/34/29 total kills; closest possible loss (missed by the minimum) |
| 52 | Quad kills_m123 under 8 | 16 | 0.6634 (Medium) | lean | model 68%, hist 57% | variance | variance | root leg of a 4-leg script loss: #52, #62, #64, #76; 16 kills vs 6.8 expected for the actual game results; games had 33/37/43 total kills |
| 55 | Cube kills_m123 under 7.5 | 15 | 0.6204 (Medium) | bet | model 60%, hist 74% | variance | correlated | root leg of a 3-leg script loss: #55, #56, #81; 15 kills vs 7.0 expected for the actual game results; games had 33/37/43 total kills |
| 56 | About kills_m123 under 14.5 | 16 | 0.6077 (Medium) | lean | model 59%, hist 74% | correlated | correlated | same game script as #55 (variance); own read: variance; 16 kills vs 13.8 expected for the actual game results; games had 33/37/43 total kills |
| 57 | 13 kills_m123 over 12.5 | 12 | 0.5683 (Low) | pass | model 55%, hist 75% | variance | variance | logged as a PASS: no money on it; reviewed for calibration; 12 kills vs 9.6 expected for the actual game results; games had 34/29/34 total kills; closest possible loss (missed by the minimum) |
| 58 | Taeyoon kills_m123 under 11.5 | 18 | 0.537 (Low) | pass | model 63%, hist 47% (against) | variance | **untagged** | logged as a PASS: no money on it; reviewed for calibration; 18 kills vs 13.7 expected for the actual game results; games had 30/30/34 total kills |
| 59 | Thayger kills_m123 under 14 | 18 | 0.6324 (Medium) | pass | model 63%, hist 71% | correlated | correlated | same game script as #48 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; 18 kills vs 17.3 expected for the actual game results; games had 34/29/34 total kills |
| 60 | Jool kills_m123 under 14.5 | 15 | 0.5283 (Low) | lean | model 59%, hist 81% | variance | **untagged** | root leg of a 3-leg script loss: #60, #67, #79; 15 kills vs 13.7 expected for the actual game results; games had 42/34/29 total kills; closest possible loss (missed by the minimum) |
| 61 | Carlsen kills_m123 over 10 | 9 | 0.5647 (Low) | lean | model 56%, hist 60% | correlated | correlated | same game script as #48 (variance); own read: variance; 9 kills vs 13.5 expected for the actual game results; games had 34/29/34 total kills |
| 62 | Gakgos kills_m123 under 6.5 | 8 | 0.5865 (Medium) | lean | model 60%, hist 50% (against) | correlated | correlated | same game script as #52 (variance); own read: variance; 8 kills vs 5.9 expected for the actual game results; games had 33/37/43 total kills |
| 64 | Cryogen kills_m123 over 1.5 | 1 | 0.5596 (Low) | pass | model 55%, hist 61% | correlated | correlated | same game script as #52 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; 1 kills vs 2.1 expected for the actual game results; games had 33/37/43 total kills; closest possible loss (missed by the minimum) |
| 65 | Gideon kills_m123 under 10 | 12 | 0.5597 (Low) | pass | model 56%, hist 56% | variance | variance | root leg of a 4-leg script loss: #65, #66, #75, #80; logged as a PASS: no money on it; reviewed for calibration; 12 kills vs 11.0 expected for the actual game results; games had 23/34/20 total kills |
| 66 | Roamer kills_m123 under 9.5 | 10 | 0.5533 (Low) | pass | model 55%, hist 55% | correlated | correlated | same game script as #65 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; 10 kills vs 10.9 expected for the actual game results; games had 23/34/20 total kills; closest possible loss (missed by the minimum) |
| 67 | Zicssi kills_m123 under 14.5 | 19 | 0.4738 (Low) | pass | model 55%, hist 48% (against) | correlated | **untagged** | same game script as #60 (variance); own read: variance; we priced this side at 47%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; 19 kills vs 13.9 expected for the actual game results; games had 42/34/29 total kills |
| 73 | Burdol kills_m123 over 7.5 | 6 | 0.5345 (Low) | pass | model 53%, hist 54% | correlated | correlated | same game script as #47 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; 6 kills vs 7.3 expected for the actual game results; games had 23/34/20 total kills |
| 75 | Casting kills_m123 over 7.5 | 4 | 0.5208 (Low) | pass | model 52%, hist 51% | correlated | correlated | same game script as #65 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; 4 kills vs 8.5 expected for the actual game results; games had 23/34/20 total kills |
| 76 | Gryffinn kills_m123 under 9.5 | 14 | 0.5238 (Low) | pass | model 53%, hist 46% (against) | correlated | correlated | same game script as #52 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; 14 kills vs 9.6 expected for the actual game results; games had 33/37/43 total kills |
| 79 | Aetinoth kills_m123 over 18 | 7 | 0.4448 (Low) | pass | model 51%, hist 47% (against) | correlated | **untagged** | same game script as #60 (variance); own read: variance; we priced this side at 44%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; 7 kills vs 17.9 expected for the actual game results; games had 42/34/29 total kills |
| 80 | Teddy kills_m123 under 12.5 | 14 | 0.5084 (Low) | pass | model 50%, hist 50% | correlated | correlated | same game script as #65 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; 14 kills vs 14.9 expected for the actual game results; games had 23/34/20 total kills |
| 81 | Monki kills_m123 under 10.5 | 21 | 0.4972 (Low) | pass | model 47% (against), hist 64% | correlated | correlated | same game script as #55 (variance); own read: variance; we priced this side at 50%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; 21 kills vs 11.5 expected for the actual game results; games had 33/37/43 total kills |
| 83 | Shy Carry kills_m123 under 12.5 | 17 | 0.4868 (Low) | pass | model 57%, hist 38% (against) | correlated | **untagged** | same game script as #51 (variance); own read: variance; we priced this side at 49%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; 17 kills vs 12.3 expected for the actual game results; games had 42/34/29 total kills |
| 84 | Omon kills_m123 over 14.5 | 13 | 0.5239 (Low) | pass | model 50% (against), hist 62% | correlated | correlated | same game script as #48 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; 13 kills vs 19.4 expected for the actual game results; games had 34/29/34 total kills |

Lessons:
- #1: Lost by the minimum (4 SOG on 19.7 TOI, normal ice time). Minnesota trailed and pushed shots late.
- #2: Same Minnesota game script as #1. Was a pass at 49%.
- #6: Pulled after 8 outs (75 pitches, 14 BF, 5.4 pitches per batter). Our 69% leaned on 18+ outs in 26 of 29 regular-season starts; playoff hooks are quicker. Fixed by L17 (halve postseason leash history, cap starter-length props at Medium).
- #8: 8 hits on 25 BF with 7 K and 0 BB: balls in play fell in. Exactly the L18 case (hits-allowed unders, contact lineup), written mid-game; now capped at Medium.
- #9: Pulled at 12 outs after only 63 pitches: playoff leash again (L17), same cause as Yamamoto #6.
- #11: Priced at 27%; a long-odds lean that didn't land. No change.
- #12: Allen ran for 121 yards. QB rushing has a fat right tail; a 54% under is a coin flip and doesn't belong in a 5x entry.
- #13: Same script as #6. Process miss: this entry leg was priced at 47% (we had the over at 55%). Every entry leg must be priced and clear break-even before submitting (L20, edge card).
- #14: LP won maps 1-2 (13-5, 13-11) and divine had 32 kills, 1.0 per round in the stomp map. The model uses average map-win KPR; a star's kill rate in blowouts runs higher (L21).
- #15: Same LP-sweep script as #14 (ex-Keyd lost both maps).
- #17: jared hit 14 headshots on 17 kills on Ancient (82%), far above his ~55%. HS% spike, not a model input failure.
- #22: Lost by the minimum: 2 BB in 18 BF. He had walked 3 in each of his previous 2 starts; we noted it but the model doesn't weight recent walk rate. Watch for a repeat before changing the model.
- #24: Same script as #6, and there was no sportsbook price to check it.
- #28: Same Rasmussen game as #8; was a pass.
- #29: 3 of his 4 H+R+RBI came off Yamamoto (2-RBI single in the 3rd). Hitter unders against a starter are a bet on that starter (L16).
- #31: All 3 of Adell's H+R+RBI came off the bullpen (2-RBI double in the 9th). Hitter unders lose on late bullpen innings the model treats as average (L22).
- #32: 5 of Ramirez's 6 H+R+RBI came off the bullpen in the 8th-9th. Second bullpen loss in this segment tonight (L22).
- #33: Correct pass: his history leaned over (57%). Half his production came off the bullpen.
- #36: Correct pass. Lost by the minimum (walk and run in the 1st, single in the 3rd).
- #41: Rated High with no sportsbook price, on a market where our model runs about 7.6 points toward unders and needs a -0.31 logit fix. 9-hole hitter reached 4 of 4; 3 of his 5 H+R+RBI came off the bullpen, so it wasn't the Yamamoto script. Now capped at Medium without a market (L19).
- #47: Published High on per-game history (L23). Series-level history was 10 of 23 over (43%) against the model's 72%: the correct pre-game label was Low and it would not have gone out. Result fit the history: 9 kills (2 in a G1 win where LGD had 16, then 5 and 2 in losses; expected 13.8 for W-L-L). Already fixed by L23 recount + L24 edge verify, which flags it NOT VERIFIED.
- #48: Galions 3-0 with 27/19/24 team kills; Harpoon 11 in the G1 stomp. Lean was Low with history against (48%); no rule
- #52: Tail game script: WE-FQ games ran 33/37/43 combined kills; Quad 16 vs 6.8 expected for the actual results (W,L,L). Spread re-checked on 967 past series (var z 0.92, mean -0.02, Demacia Cup -0.02): calibrated, no model change. Every leg on this series lost together: one leg per LoL series, never stack unders on one match.
- #55: Same WE-FQ series as #52: WE won games 2-3 with 25 and 27 kills; Cube 15 vs 7.0 expected. Root cause on #52.
- #57: missed by the minimum (12 vs 12.5); no rule
- #59: same game script as its root leg; one leg per script
- #61: same game script as its root leg; one leg per script
- #73: Same LGD script as #47: LGD scored 16/15/5 kills in G1-3; Burdol 6 vs 7.3 expected.
- #84: same game script as its root leg; one leg per script

Detail from the feeds:
- #1 Kirill Kaprizov: toi=19.7, sog=4, shifts=18, pp_goals=0, score=2-4
- #2 Ryan Hartman: toi=15.3, sog=2, shifts=18, pp_goals=0, score=2-4
- #6 Yoshinobu Yamamoto: outs=8, bf=14, pitches=75, h=4, er=3, bb=2, k=1, p_per_pa=5.36
- #8 Drew Rasmussen: outs=18, bf=25, pitches=91, h=8, er=2, bb=0, k=7, p_per_pa=3.64
- #9 Foster Griffin: outs=12, bf=18, pitches=63, h=5, er=2, bb=0, k=3, p_per_pa=3.5
- #11 Victor Mesa Jr.: inn 1 vs Griffin: Single; inn 3 vs Griffin: Strikeout; inn 6 vs Cantillo: Bunt Pop Out; inn 8 vs Sabrowski: Strikeout
- #13 Yoshinobu Yamamoto: outs=8, bf=14, pitches=75, h=4, er=3, bb=2, k=1, p_per_pa=5.36
- #14 divine: de_dust2: 18 rds, W, 18 K / 7 HS; de_inferno: 24 rds, W, 14 K / 6 HS
- #15 lash: de_dust2: 18 rds, L, 11 K / 2 HS; de_inferno: 24 rds, L, 14 K / 4 HS
- #17 jared: de_ancient: 18 rds, W, 17 K / 14 HS; de_nuke: 18 rds, W, 8 K / 3 HS
- #22 Logan Henderson: outs=12, bf=18, pitches=64, h=3, er=2, bb=2, k=2, p_per_pa=3.56
- #24 Yoshinobu Yamamoto: outs=8, bf=14, pitches=75, h=4, er=3, bb=2, k=1, p_per_pa=5.36
- #28 Drew Rasmussen: outs=18, bf=25, pitches=91, h=8, er=2, bb=0, k=7, p_per_pa=3.64
- #29 Christian Yelich: inn 1 vs Yamamoto: Groundout; inn 3 vs Yamamoto: Single, 2 RBI; inn 5 vs Bubic: Single; inn 6 vs Scott: Strikeout; inn 8 vs Wrobleski: Lineout
- #31 Jo Adell: inn 1 vs Rasmussen: Groundout; inn 3 vs Rasmussen: Groundout; inn 6 vs Rasmussen: Strikeout; inn 8 vs Wells: Groundout; inn 9 vs Kelly: Double, 2 RBI
- #32 José Ramírez: inn 1 vs Rasmussen: Single; inn 3 vs Rasmussen: Flyout; inn 5 vs Rasmussen: Strikeout; inn 8 vs Wells: Single; scored inn 8 (bullpen); inn 9 vs Sulser: Single, 1 RBI; scored inn 9 (bullpen)
- #33 Brice Turang: inn 1 vs Yamamoto: Double; scored inn 1 (starter); inn 3 vs Yamamoto: Walk; scored inn 3 (starter); inn 5 vs Bubic: Strikeout; inn 6 vs Stewart: Intent Walk; inn 8 vs Henriquez: Single, 1 RBI; scored inn 8 (bullpen)
- #36 Mookie Betts: inn 1 vs Henderson: Walk; scored inn 1 (starter); inn 3 vs Henderson: Single; inn 5 vs May: Groundout; inn 8 vs Uribe: Strikeout
- #41 David Hamilton: inn 3 vs Yamamoto: Single; scored inn 3 (starter); inn 4 vs Sasaki: Forceout; inn 6 vs Stewart: Hit By Pitch; scored inn 6 (bullpen); inn 8 vs Henriquez: Single; scored inn 8 (bullpen)
- #47 Tangyuan: G1 W: 2 K (expected 7.1); HANJIN BRION 7 - LGD Gaming 16, 23 total; G2 L: 5 K (expected 3.3); LGD Gaming 15 - HANJIN BRION 19, 34 total; G3 L: 2 K (expected 3.3); HANJIN BRION 15 - LGD Gaming 5, 20 total
- #48 Harpoon: G1 W: 11 K (expected 6.7); Movistar KOI Fenix 7 - Galions 27, 34 total; G2 W: 7 K (expected 6.7); Galions 19 - Movistar KOI Fenix 10, 29 total; G3 W: 6 K (expected 6.7); Galions 24 - Movistar KOI Fenix 10, 34 total
- #51 Theocacs: G1 L: 2 K (expected 2.2); Anubis Gaming 18 - Picks Solary 24, 42 total; G2 W: 5 K (expected 4.8); Solary 12 - Picks Anubis Gaming 22, 34 total; G3 L: 0 K (expected 2.2); Solary 25 - Picks Anubis Gaming 4, 29 total
- #52 Quad: G1 W: 7 K (expected 3.6); Team WE 9 - FlyQuest 24, 33 total; G2 L: 4 K (expected 1.6); FlyQuest 12 - Team WE 25, 37 total; G3 L: 5 K (expected 1.6); Team WE 27 - FlyQuest 16, 43 total
- #55 Cube: G1 L: 2 K (expected 1.0); Team WE 9 - FlyQuest 24, 33 total; G2 W: 6 K (expected 3.0); FlyQuest 12 - Team WE 25, 37 total; G3 W: 7 K (expected 3.0); Team WE 27 - FlyQuest 16, 43 total
- #56 About: G1 L: 4 K (expected 2.1); Team WE 9 - FlyQuest 24, 33 total; G2 W: 5 K (expected 5.8); FlyQuest 12 - Team WE 25, 37 total; G3 W: 7 K (expected 5.8); Team WE 27 - FlyQuest 16, 43 total
- #57 13: G1 L: 4 K (expected 3.2); Movistar KOI Fenix 7 - Galions 27, 34 total; G2 L: 3 K (expected 3.2); Galions 19 - Movistar KOI Fenix 10, 29 total; G3 L: 5 K (expected 3.2); Galions 24 - Movistar KOI Fenix 10, 34 total
- #58 Taeyoon: G1 W: 14 K (expected 5.8); BNK FearX 22 - KT Rolster 8, 30 total; G2 L: 3 K (expected 2.1); BNK FearX 8 - KT Rolster 22, 30 total; G3 W: 1 K (expected 5.8); KT Rolster 11 - BNK FearX 23, 34 total
- #59 Thayger: G1 W: 5 K (expected 5.8); Movistar KOI Fenix 7 - Galions 27, 34 total; G2 W: 6 K (expected 5.8); Galions 19 - Movistar KOI Fenix 10, 29 total; G3 W: 7 K (expected 5.8); Galions 24 - Movistar KOI Fenix 10, 34 total
- #60 Jool: G1 W: 6 K (expected 5.4); Anubis Gaming 18 - Picks Solary 24, 42 total; G2 L: 3 K (expected 3.0); Solary 12 - Picks Anubis Gaming 22, 34 total; G3 W: 6 K (expected 5.4); Solary 25 - Picks Anubis Gaming 4, 29 total
- #61 Carlsen: G1 W: 5 K (expected 4.5); Movistar KOI Fenix 7 - Galions 27, 34 total; G2 W: 1 K (expected 4.5); Galions 19 - Movistar KOI Fenix 10, 29 total; G3 W: 3 K (expected 4.5); Galions 24 - Movistar KOI Fenix 10, 34 total
- #62 Gakgos: G1 W: 3 K (expected 3.3); Team WE 9 - FlyQuest 24, 33 total; G2 L: 0 K (expected 1.3); FlyQuest 12 - Team WE 25, 37 total; G3 L: 5 K (expected 1.3); Team WE 27 - FlyQuest 16, 43 total
- #64 Cryogen: G1 W: 0 K (expected 1.1); Team WE 9 - FlyQuest 24, 33 total; G2 L: 1 K (expected 0.5); FlyQuest 12 - Team WE 25, 37 total; G3 L: 0 K (expected 0.5); Team WE 27 - FlyQuest 16, 43 total
- #65 Gideon: G1 L: 2 K (expected 2.4); HANJIN BRION 7 - LGD Gaming 16, 23 total; G2 W: 6 K (expected 4.3); LGD Gaming 15 - HANJIN BRION 19, 34 total; G3 W: 4 K (expected 4.3); HANJIN BRION 15 - LGD Gaming 5, 20 total
- #66 Roamer: G1 L: 3 K (expected 1.8); HANJIN BRION 7 - LGD Gaming 16, 23 total; G2 W: 4 K (expected 4.5); LGD Gaming 15 - HANJIN BRION 19, 34 total; G3 W: 3 K (expected 4.5); HANJIN BRION 15 - LGD Gaming 5, 20 total
- #67 Zicssi: G1 W: 8 K (expected 5.4); Anubis Gaming 18 - Picks Solary 24, 42 total; G2 L: 3 K (expected 3.1); Solary 12 - Picks Anubis Gaming 22, 34 total; G3 W: 8 K (expected 5.4); Solary 25 - Picks Anubis Gaming 4, 29 total
- #73 Burdol: G1 W: 3 K (expected 3.3); HANJIN BRION 7 - LGD Gaming 16, 23 total; G2 L: 3 K (expected 2.0); LGD Gaming 15 - HANJIN BRION 19, 34 total; G3 L: 0 K (expected 2.0); HANJIN BRION 15 - LGD Gaming 5, 20 total
- #75 Casting: G1 L: 1 K (expected 2.0); HANJIN BRION 7 - LGD Gaming 16, 23 total; G2 W: 2 K (expected 3.3); LGD Gaming 15 - HANJIN BRION 19, 34 total; G3 W: 1 K (expected 3.3); HANJIN BRION 15 - LGD Gaming 5, 20 total
- #76 Gryffinn: G1 W: 8 K (expected 4.5); Team WE 9 - FlyQuest 24, 33 total; G2 L: 4 K (expected 2.6); FlyQuest 12 - Team WE 25, 37 total; G3 L: 2 K (expected 2.6); Team WE 27 - FlyQuest 16, 43 total
- #79 Aetinoth: G1 W: 5 K (expected 7.2); Anubis Gaming 18 - Picks Solary 24, 42 total; G2 L: 1 K (expected 3.4); Solary 12 - Picks Anubis Gaming 22, 34 total; G3 W: 1 K (expected 7.2); Solary 25 - Picks Anubis Gaming 4, 29 total
- #80 Teddy: G1 L: 1 K (expected 2.5); HANJIN BRION 7 - LGD Gaming 16, 23 total; G2 W: 6 K (expected 6.2); LGD Gaming 15 - HANJIN BRION 19, 34 total; G3 W: 7 K (expected 6.2); HANJIN BRION 15 - LGD Gaming 5, 20 total
- #81 Monki: G1 L: 2 K (expected 1.5); Team WE 9 - FlyQuest 24, 33 total; G2 W: 8 K (expected 5.0); FlyQuest 12 - Team WE 25, 37 total; G3 W: 11 K (expected 5.0); Team WE 27 - FlyQuest 16, 43 total
- #83 Shy Carry: G1 L: 6 K (expected 2.9); Anubis Gaming 18 - Picks Solary 24, 42 total; G2 W: 7 K (expected 6.6); Solary 12 - Picks Anubis Gaming 22, 34 total; G3 L: 4 K (expected 2.9); Solary 25 - Picks Anubis Gaming 4, 29 total
- #84 Omon: G1 W: 3 K (expected 6.5); Movistar KOI Fenix 7 - Galions 27, 34 total; G2 W: 5 K (expected 6.5); Galions 19 - Movistar KOI Fenix 10, 29 total; G3 W: 5 K (expected 6.5); Galions 24 - Movistar KOI Fenix 10, 34 total

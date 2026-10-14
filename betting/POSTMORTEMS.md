# Post-mortems

Every graded loss is examined here, including passes and Low-confidence legs. `python -m edge review` writes the diagnosis; `python -m edge tag ID "tag" --lesson "..."` confirms the cause. Tags: `variance`, `opportunity`, `correlated`, `role/lineup`, `model bias`, `market info`, `stale line`, `data error`, `format misread`.

## 2026-10-13: 157 losses from 30 independent causes

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
| 124 | detr0ittJ cs_headshots_m12 under 11.5 | 13 | 0.6101 (Medium) | lean | model 61%, hist 59% | variance | **untagged** | root leg of a 13-leg script loss: #124, #125, #126, #127, #128, #129, #131, #137, #139, #148, #155, #377, #485 |
| 125 | gbb cs_kills_m12 under 31.5 | 42 | 0.6031 (Medium) | lean | model 60%, hist 63% | correlated | **untagged** | same game script as #124 (variance); own read: variance |
| 126 | PKL cs_headshots_m12 under 13.0 | 14 | 0.6057 (Medium) | lean | model 60%, hist 60% | correlated | **untagged** | same game script as #124 (variance); own read: variance |
| 127 | detr0ittJ cs_kills_m12 under 29.0 | 33 | 0.598 (Medium) | lean | model 60%, hist 60% | correlated | **untagged** | same game script as #124 (variance); own read: variance |
| 128 | PKL cs_kills_m12 under 24.5 | 25 | 0.5966 (Medium) | lean | model 60%, hist 59% | correlated | **untagged** | same game script as #124 (variance); own read: variance; closest possible loss (missed by the minimum) |
| 129 | gbb cs_headshots_m12 under 16.5 | 27 | 0.6032 (Low) | pass | model 62%, hist 48% (against) | correlated | **untagged** | same game script as #124 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 131 | drg cs_headshots_m12 under 16.5 | 20 | 0.5869 (Medium) | lean | model 59%, hist 50% (against) | correlated | **untagged** | same game script as #124 (variance); own read: variance |
| 134 | sirah cs_headshots_m12 under 17.5 | 18 | 0.5827 (Medium) | lean | model 57%, hist 56% | variance | variance | root leg of a 9-leg script loss: #134, #141, #142, #144, #147, #149, #150, #151, #153; closest possible loss (missed by the minimum) |
| 137 | destiny cs_headshots_m12 under 14.5 | 27 | 0.5683 (Low) | pass | model 57%, hist 48% (against) | correlated | **untagged** | same game script as #124 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 138 | ju1ces cs_headshots_m12 under 14.5 | 21 | 0.5756 (Low) | pass | model 54%, hist 65% | correlated | correlated | same game script as #112 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 139 | destiny cs_kills_m12 under 30.0 | 52 | 0.5675 (Low) | pass | model 59%, hist 38% (against) | correlated | **untagged** | same game script as #124 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 141 | sinnopsyy cs_headshots_m12 over 14.5 | 7 | 0.5692 (Low) | pass | model 54%, hist 59% | correlated | correlated | same game script as #134 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 142 | 0SAMAS cs_kills_m12 over 27.5 | 24 | 0.5622 (Low) | pass | model 52%, hist 68% | correlated | correlated | same game script as #134 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 144 | CacaNito cs_kills_m12 over 30.5 | 22 | 0.5574 (Low) | pass | model 50%, hist 73% | correlated | correlated | same game script as #134 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 147 | 0SAMAS cs_headshots_m12 over 15.5 | 9 | 0.5496 (Low) | pass | model 50%, hist 68% | correlated | correlated | same game script as #134 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 148 | drg cs_kills_m12 under 28.5 | 31 | 0.5294 (Low) | pass | model 53%, hist 50% (against) | correlated | **untagged** | same game script as #124 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 149 | Gizmy cs_kills_m12 over 26.5 | 17 | 0.5391 (Low) | pass | model 51%, hist 55% | correlated | correlated | same game script as #134 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 150 | m1N1 cs_kills_m12 over 30.5 | 15 | 0.5384 (Low) | pass | model 48% (against), hist 73% | correlated | correlated | same game script as #134 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 151 | sinnopsyy cs_kills_m12 over 26.5 | 16 | 0.5347 (Low) | pass | model 50% (against), hist 59% | correlated | correlated | same game script as #134 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 152 | MIstR cs_headshots_m12 over 14.5 | 11 | 0.5336 (Low) | pass | model 50% (against), hist 61% | correlated | correlated | same game script as #101 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 153 | Gizmy cs_headshots_m12 over 14.0 | 8 | 0.5334 (Low) | pass | model 53%, hist 41% (against) | correlated | correlated | same game script as #134 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 155 | ckzao cs_kills_m12 under 31.5 | 32 | 0.5177 (Low) | pass | model 53%, hist 25% (against) | correlated | **untagged** | same game script as #124 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 156 | device cs_headshots_m12 over 9.5 | 9 | 0.5262 (Low) | pass | model 52%, hist 44% (against) | correlated | correlated | same game script as #134 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 157 | leakz cs_kills_m12 under 30.5 | 37 | 0.5227 (Low) | pass | model 51%, hist 47% (against) | correlated | correlated | same game script as #101 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 158 | EliGe cs_headshots_m12 over 19.5 | 17 | 0.4817 (Low) | pass | model 44% (against), hist 54% | correlated | correlated | same game script as #101 (variance); own read: variance; we priced this side at 48%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 159 | device cs_kills_m12 over 32.0 | 30 | 0.4503 (Low) | pass | model 43% (against), hist 38% (against) | correlated | correlated | same game script as #134 (variance); own read: variance; we priced this side at 45%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 165 | Freddy Peralta pitcher_hits_allowed under 3.5 | 4 | 0.529 (Low) | pass | market 52% | correlated | **untagged** | same game script as #177 (opportunity); own read: variance; logged as a PASS: no money on it; reviewed for calibration; line: 18 outs, 25 BF, 99 pitches, 4 H, 2 BB, 6 K, 0 ER; closest possible loss (missed by the minimum) |
| 166 | Parker Messick pitcher_earned_runs over 1.5 | 0 | 0.5083 (Low) | pass | market 50% | correlated | **untagged** | same game script as #177 (opportunity); own read: variance; logged as a PASS: no money on it; reviewed for calibration; line: 15 outs, 22 BF, 82 pitches, 6 H, 2 BB, 3 K, 0 ER |
| 167 | Junior Caminero batter_hrr over 1.5 | 1 | 0.5092 (Low) | pass | market 50% | correlated | **untagged** | same game script as #177 (opportunity); own read: variance; logged as a PASS: no money on it; reviewed for calibration; 4 PA from the 3 slot; opposing starter Parker Messick went 15 outs / 0 ER; 1 of 1 H+R+RBI came off the starter, 0 off the bullpen; closest possible loss (missed by the minimum) |
| 168 | Yandy Díaz batter_hrr over 1.5 | 0 |  (Low) | pass | none logged | correlated | **untagged** | same game script as #177 (opportunity); own read: variance; logged as a PASS: no money on it; reviewed for calibration; 4 PA from the 1 slot; opposing starter Parker Messick went 15 outs / 0 ER |
| 177 | Patrick Bailey batter_total_bases over 0.5 | 0 |  (Low) | pass | none logged | opportunity | **untagged** | root leg of a 13-leg script loss: #165, #166, #167, #168, #177, #178, #181, #182, #386, #388, #396, #399, #401; logged as a PASS: no money on it; reviewed for calibration; only 2 plate appearances; 2 PA from the 8 slot; opposing starter Freddy Peralta went 18 outs / 0 ER |
| 178 | Patrick Bailey batter_hits over 0.5 | 0 | 0.5171 (Low) | pass | market 51% | correlated | **untagged** | same game script as #177 (opportunity); own read: opportunity; logged as a PASS: no money on it; reviewed for calibration; only 2 plate appearances; 2 PA from the 8 slot; opposing starter Freddy Peralta went 18 outs / 0 ER |
| 181 | Brayan Rocchio batter_total_bases over 0.5 | 0 |  (Low) | pass | none logged | correlated | **untagged** | same game script as #177 (opportunity); own read: variance; logged as a PASS: no money on it; reviewed for calibration; 4 PA from the 9 slot; opposing starter Freddy Peralta went 18 outs / 0 ER; closest possible loss (missed by the minimum) |
| 182 | Brayan Rocchio batter_hits over 0.5 | 0 | 0.529 (Low) | pass | market 52% | correlated | **untagged** | same game script as #177 (opportunity); own read: variance; logged as a PASS: no money on it; reviewed for calibration; 4 PA from the 9 slot; opposing starter Freddy Peralta went 18 outs / 0 ER; closest possible loss (missed by the minimum) |
| 191 | Roman Gagliano pass_yds under 208.5 | 291.0 | 0.5389 (Low) | pass | hist 60% | variance | **untagged** | root leg of a 5-leg script loss: #191, #192, #193, #195, #196; logged as a PASS: no money on it; reviewed for calibration |
| 192 | Antonio Martin rush_yds over 74.5 | 48.0 | 0.5389 (Low) | pass | hist 60% | correlated | **untagged** | same game script as #191 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 193 | Cam'Ron Lacy rec_yds over 64.5 | 34.0 | 0.5389 (Low) | pass | hist 60% | correlated | **untagged** | same game script as #191 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 195 | Da'Wain Lofton rec_yds over 43.5 | 40.0 | 0.576 (Low) | pass | hist 75% | correlated | **untagged** | same game script as #191 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 196 | Da'Wain Lofton receptions over 3.5 | 3.0 | 0.5063 (Low) | pass | hist 50% (against) | correlated | **untagged** | same game script as #191 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 198 | Caden Creel pass_yds over 218.5 | 214.0 | 0.5673 (Low) | pass | hist 67% | variance | **untagged** | root leg of a 2-leg script loss: #198, #204; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 204 | Devonte Lyons rush_yds under 38.5 | 73.0 | 0.5389 (Low) | pass | hist 60% | correlated | **untagged** | same game script as #198 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 208 | OMON kills_m123 over 15.5 | 13 | 0.4619 (Low) | pass | model 45% (against), hist 48% (against) | variance | **untagged** | we priced this side at 46%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; 13 kills vs 19.4 expected for the actual game results; games had 34/29/34 total kills |
| 226 | Jakub Markovic passes_att over 37.5 | 34.0 | 0.8267 (Low) | pass | model 87%, hist 33% (against) | variance | **untagged** | root leg of a 2-leg script loss: #226, #265; logged as a PASS: no money on it; reviewed for calibration |
| 229 | Gabriel Jesus shots over 2.5 | 1.0 | 0.7007 (Medium) | pass | market 74%, hist 0% (against) | variance | **untagged** | root leg of a 9-leg script loss: #229, #269, #281, #315, #335, #337, #361, #363, #365; logged as a PASS: no money on it; reviewed for calibration |
| 231 | Julián Alvarez passes_att over 29.5 | 28.0 | 0.6307 (Low) | pass | model 65%, hist 43% (against) | variance | **untagged** | root leg of a 8-leg script loss: #231, #236, #246, #248, #267, #289, #308, #353; logged as a PASS: no money on it; reviewed for calibration |
| 236 | Matheus Cunha shots over 2.0 | 1.0 | 0.6107 (Medium) | lean | market 59%, hist 86% | correlated | **untagged** | same game script as #231 (variance); own read: variance |
| 237 | Willi Orbán passes_att over 73.5 | 40.0 | 0.5309 (Low) | pass | model 53%, hist 50% (against) | variance | **untagged** | root leg of a 6-leg script loss: #237, #270, #277, #352, #354, #359; logged as a PASS: no money on it; reviewed for calibration |
| 241 | Ismael Saibari shots over 4.5 | 2.0 | 0.6001 (Low) | pass | market 62%, hist 17% (against) | variance | **untagged** | root leg of a 6-leg script loss: #241, #258, #274, #316, #470, #472; logged as a PASS: no money on it; reviewed for calibration |
| 242 | Marcus Thuram shots over 3.5 | 2.0 | 0.599 (Medium) | lean | market 61%, hist 43% (against) | variance | **untagged** | root leg of a 7-leg script loss: #242, #253, #329, #334, #347, #351, #357 |
| 245 | Bukayo Saka shots over 3.0 | 1.0 | 0.5966 (Medium) | lean | market 60%, hist 43% (against) | variance | **untagged** | root leg of a 9-leg script loss: #245, #247, #283, #290, #302, #322, #341, #344, #346 |
| 246 | Matheus Cunha passes_att over 24.5 | 14.0 | 0.5489 (Low) | pass | model 51%, hist 81% | correlated | **untagged** | same game script as #231 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 247 | Kai Havertz shots over 3.0 | 0.0 | 0.5899 (Low) | pass | market 62%, hist 0% (against) | correlated | **untagged** | same game script as #245 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 248 | Marcus Rashford shots over 2.0 | 1.0 | 0.5865 (Medium) | lean | market 59%, hist 50% (against) | correlated | **untagged** | same game script as #231 (variance); own read: variance |
| 253 | Brandon Mechele passes_att over 58.5 | 54.0 | 0.5942 (Medium) | lean | model 58%, hist 80% | correlated | **untagged** | same game script as #242 (variance); own read: variance |
| 254 | Gonçalo Inácio passes_att over 70.5 | 67.0 | 0.5697 (Low) | pass | model 56%, hist 67% | variance | **untagged** | root leg of a 5-leg script loss: #254, #319, #321, #330, #342; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 258 | Michael Olise shots over 4.5 | 3.0 | 0.5643 (Low) | pass | market 57%, hist 40% (against) | correlated | **untagged** | same game script as #241 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 265 | Joy-Lance Mickels shots over 2.5 | 1.0 | 0.5507 (Low) | pass | hist 100% | correlated | **untagged** | same game script as #226 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 267 | Julián Alvarez shots over 3.0 | 2.0 | 0.5409 (Low) | pass | market 55%, hist 0% (against) | correlated | **untagged** | same game script as #231 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 269 | Rafael Leão shots over 2.0 | 0.0 | 0.5389 (Low) | pass | hist 60% | correlated | **untagged** | same game script as #229 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 270 | Christopher Nkunku shots over 3.0 | 1.0 | 0.5379 (Low) | pass | market 53%, hist 50% (against) | correlated | **untagged** | same game script as #237 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 274 | Harry Kane shots over 5.5 | 5.0 | 0.5271 (Low) | pass | market 54%, hist 30% (against) | correlated | **untagged** | same game script as #241 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 277 | Kodai Sano passes_att under 46.5 | 52.0 | 0.5161 (Low) | pass | model 53%, hist 29% (against) | correlated | **untagged** | same game script as #237 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 279 | Kevin De Bruyne shots over 2.0 | 1.0 | 0.5226 (Low) | pass | market 55%, hist 12% (against) | variance | **untagged** | root leg of a 3-leg script loss: #279, #473, #477; logged as a PASS: no money on it; reviewed for calibration |
| 281 | Victor Osimhen shots over 3.0 | 1.0 | 0.5201 (Low) | pass | market 48% (against), hist 100% | correlated | **untagged** | same game script as #229 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 283 | Olivier Giroud shots over 1.5 | 0.0 | 0.5146 (Low) | pass | market 53%, hist 22% (against) | correlated | **untagged** | same game script as #245 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 289 | Bruno Fernandes passes_att over 43.5 | 32.0 | 0.7161 (Medium) | lean | model 69%, hist 96% | correlated | **untagged** | same game script as #231 (variance); own read: variance |
| 290 | David Raya passes_att over 29.5 | 21.0 | 0.513 (Low) | pass | model 51%, hist 46% (against) | correlated | **untagged** | same game script as #245 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 302 | Ayase Ueda shots over 1.5 | 1.0 | 0.4728 (Low) | pass | market 46% (against), hist 60% | correlated | **untagged** | same game script as #245 (variance); own read: variance; we priced this side at 47%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 308 | Senne Lammens gk_saves over 3.5 | 3.0 | 0.4558 (Low) | pass | market 46% (against), hist 30% (against) | correlated | **untagged** | same game script as #231 (variance); own read: variance; we priced this side at 46%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 315 | Lamine Yamal sot over 2.0 | 0.0 | 0.437 (Low) | pass | market 43% (against), hist 40% (against) | correlated | **untagged** | same game script as #229 (variance); own read: variance; we priced this side at 44%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 316 | Michael Olise sot over 2.0 | 1.0 | 0.4346 (Low) | pass | market 43% (against), hist 38% (against) | correlated | **untagged** | same game script as #241 (variance); own read: variance; we priced this side at 43%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 319 | Luis Suárez shots over 3.0 | 2.0 | 0.4198 (Low) | pass | hist 29% (against) | correlated | **untagged** | same game script as #254 (variance); own read: variance; we priced this side at 42%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 321 | Luís Guilherme passes_att over 29.5 | 15.0 | 0.4173 (Low) | pass | model 39% (against), hist 50% (against) | correlated | **untagged** | same game script as #254 (variance); own read: variance; we priced this side at 42%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 322 | David Raya gk_saves over 2.0 | 0.0 | 0.4169 (Low) | pass | market 40% (against), hist 57% | correlated | **untagged** | same game script as #245 (variance); own read: variance; we priced this side at 42%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 329 | Francesco Pio Esposito shots over 3.5 | 1.0 | 0.3973 (Low) | pass | hist 25% (against) | correlated | **untagged** | same game script as #242 (variance); own read: variance; we priced this side at 40%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 330 | Junior Kadile shots over 2.5 | 2.0 | 0.3931 (Low) | pass | hist 0% (against) | correlated | **untagged** | same game script as #254 (variance); own read: variance; we priced this side at 39%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 334 | Josep Martínez passes_att under 36.5 | 37.0 | 0.6614 (Medium) | lean | model 68%, hist 60% | correlated | **untagged** | same game script as #242 (variance); own read: variance; closest possible loss (missed by the minimum) |
| 335 | Fermín López shots over 3.0 | 2.0 | 0.3618 (Low) | pass | hist 14% (against) | correlated | **untagged** | same game script as #229 (variance); own read: variance; we priced this side at 36%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 337 | Joan García gk_saves over 3.0 | 2.0 | 0.3474 (Low) | pass | market 35% (against), hist 14% (against) | correlated | **untagged** | same game script as #229 (variance); own read: variance; we priced this side at 35%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 341 | Declan Rice passes_att over 79.5 | 77.0 | 0.3442 (Low) | pass | model 36% (against), hist 12% (against) | correlated | **untagged** | same game script as #245 (variance); own read: variance; we priced this side at 34%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 342 | Kyllian Antonio passes_att over 58.5 | 56.0 | 0.3398 (Low) | pass | model 31% (against), hist 40% (against) | correlated | **untagged** | same game script as #254 (variance); own read: variance; we priced this side at 34%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 344 | Viktor Gyökeres shots over 3.0 | 0.0 | 0.3035 (Low) | pass | hist 0% (against) | correlated | **untagged** | same game script as #245 (variance); own read: variance; we priced this side at 30%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 346 | Berke Özer passes_att under 36.5 | 39.0 | 0.743 (Medium) | lean | model 77%, hist 58% | correlated | **untagged** | same game script as #245 (variance); own read: variance |
| 347 | Alessandro Bastoni passes_att under 71.5 | 79.0 | 0.5826 (Low) | pass | model 60%, hist 41% (against) | correlated | **untagged** | same game script as #242 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 351 | Hans Vanaken passes_att under 50.5 | 69.0 | 0.5198 (Low) | pass | model 55%, hist 11% (against) | correlated | **untagged** | same game script as #242 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 352 | Antonio Nusa passes_att under 26.5 | 28.0 | 0.6747 (Medium) | lean | model 70%, hist 55% | correlated | **untagged** | same game script as #237 (variance); own read: variance |
| 353 | Jan Oblak passes_att under 34.5 | 36.0 | 0.7967 (Medium) | lean | model 82%, hist 80% | correlated | **untagged** | same game script as #231 (variance); own read: variance; closest possible loss (missed by the minimum) |
| 354 | Maarten Vandevoordt passes_att under 37.5 | 43.0 | 0.7956 (Medium) | lean | model 82%, hist 71% | correlated | **untagged** | same game script as #237 (variance); own read: variance |
| 357 | Yann Sommer passes_att under 34.5 | 46.0 | 0.747 (Low) | pass | model 79%, hist 44% (against) | correlated | **untagged** | same game script as #242 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 359 | Matej Kovár passes_att under 37.5 | 43.0 | 0.847 (Medium) | lean | model 88%, hist 50% (against) | correlated | **untagged** | same game script as #237 (variance); own read: variance |
| 361 | Lamine Yamal passes_att under 45.5 | 50.0 | 0.6336 (Low) | pass | model 66%, hist 47% (against) | correlated | **untagged** | same game script as #229 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 363 | Rodri passes_att under 86.5 | 116.0 | 0.7328 (Medium) | lean | model 76%, hist 67% | correlated | **untagged** | same game script as #229 (variance); own read: variance |
| 365 | Ugurcan Çakir passes_att under 35.5 | 46.0 | 0.9166 (Low) | pass | model 95%, hist 36% (against) | correlated | **untagged** | same game script as #229 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 370 | JASON cs_headshots_m12 under 15.0 | 16 | 0.5804 (Medium) | lean | model 57%, hist 62% | variance | **untagged** | root leg of a 8-leg script loss: #370, #376, #378, #379, #380, #381, #382, #384 |
| 376 | POSEIDONN cs_headshots_m12 over 12.0 | 6 | 0.5492 (Low) | pass | model 55%, hist 67% | correlated | **untagged** | same game script as #370 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 377 | drg cs_kills_m12 under 28.0 | 31 | 0.5374 (Low) | pass | model 55%, hist 33% (against) | correlated | **untagged** | same game script as #124 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 378 | TWIGS cs_headshots_m12 over 11.5 | 7 | 0.5332 (Low) | pass | model 52%, hist 67% | correlated | **untagged** | same game script as #370 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 379 | UMAR cs_headshots_m12 under 11.5 | 17 | 0.5324 (Low) | pass | model 51%, hist 67% | correlated | **untagged** | same game script as #370 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 380 | CAJUN cs_headshots_m12 under 13.5 | 17 | 0.532 (Low) | pass | model 53%, hist 50% (against) | correlated | **untagged** | same game script as #370 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 381 | INTRA cs_headshots_m12 over 18.0 | 17 | 0.5296 (Low) | pass | model 53%, hist 50% (against) | correlated | **untagged** | same game script as #370 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 382 | POSEIDONN cs_kills_m12 over 33.5 | 21 | 0.5202 (Low) | pass | model 49% (against), hist 100% | correlated | **untagged** | same game script as #370 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 384 | UMAR cs_kills_m12 under 30.0 | 43 | 0.5099 (Low) | pass | model 49% (against), hist 60% | correlated | **untagged** | same game script as #370 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 386 | Steven Kwan batter_total_bases under 1.5 | 2 | 0.6453 (Medium) | lean | model 62%, market 66%, hist 66% | correlated | **untagged** | same game script as #177 (opportunity); own read: variance; 5 PA from the 1 slot; opposing starter Freddy Peralta went 18 outs / 0 ER; closest possible loss (missed by the minimum) |
| 388 | Junior Caminero batter_total_bases under 1.5 | 2 | 0.5793 (Low) | pass | model 59%, market 57%, hist 53% | correlated | **untagged** | same game script as #177 (opportunity); own read: variance; logged as a PASS: no money on it; reviewed for calibration; 4 PA from the 3 slot; opposing starter Parker Messick went 15 outs / 0 ER; closest possible loss (missed by the minimum) |
| 396 | Brayan Rocchio batter_hrr over 0.5 | 0 | 0.5885 (Medium) | lean | market 57%, hist 67% | correlated | **untagged** | same game script as #177 (opportunity); own read: variance; 4 PA from the 9 slot; opposing starter Freddy Peralta went 18 outs / 0 ER; closest possible loss (missed by the minimum) |
| 399 | Angel Martinez batter_hits over 0.5 | 0 | 0.5328 (Low) | pass | hist 53% | correlated | **untagged** | same game script as #177 (opportunity); own read: opportunity; logged as a PASS: no money on it; reviewed for calibration; only 1 plate appearances; 1 PA from the 7 slot; opposing starter Freddy Peralta went 18 outs / 0 ER |
| 401 | Ben Williamson batter_hits over 0.5 | 0 | 0.5466 (Low) | pass | market 55%, hist 49% (against) | correlated | **untagged** | same game script as #177 (opportunity); own read: opportunity; logged as a PASS: no money on it; reviewed for calibration; only 2 plate appearances; 2 PA from the 7 slot; opposing starter Parker Messick went 15 outs / 0 ER |
| 404 | Dylan Larkin skater_points over 0.5 | 0 | 0.6217 (Low) | pass | market 62% | variance | **untagged** | root leg of a 15-leg script loss: #404, #407, #409, #410, #412, #415, #416, #421, #425, #426, #427, #430, #438, #439, #440; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 407 | Jack Hughes skater_points under 1.5 | 3 | 0.6676 (Low) | pass | market 66% | correlated | **untagged** | same game script as #404 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 409 | Jack Hughes skater_sog under 3.5 | 8 | 0.5742 (Low) | pass | market 57% | correlated | **untagged** | same game script as #404 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 410 | Timo Meier skater_points over 0.5 | 0 | 0.5111 (Low) | pass | market 50% | correlated | **untagged** | same game script as #404 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 412 | Timo Meier skater_sog over 2.5 | 2 | 0.5439 (Low) | pass | market 54% | correlated | **untagged** | same game script as #404 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 415 | Dougie Hamilton skater_sog under 2.5 | 5 | 0.5904 (Low) | pass | market 59% | correlated | **untagged** | same game script as #404 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 416 | Lucas Raymond skater_points over 0.5 | 0 | 0.6127 (Low) | pass | market 61% | correlated | **untagged** | same game script as #404 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 421 | Nico Hischier skater_sog under 2.5 | 3 | 0.6078 (Low) | pass | market 60% | correlated | **untagged** | same game script as #404 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 425 | Luke Hughes skater_sog over 1.5 | 1 | 0.5904 (Low) | pass | market 59% | correlated | **untagged** | same game script as #404 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 426 | Moritz Seider skater_points under 0.5 | 1 | 0.5303 (Low) | pass | market 52% | correlated | **untagged** | same game script as #404 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 427 | Moritz Seider skater_assists under 0.5 | 1 | 0.5981 (Low) | pass | market 59% | correlated | **untagged** | same game script as #404 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 430 | Jesper Bratt skater_assists under 0.5 | 2 | 0.5625 (Low) | pass | market 56% | correlated | **untagged** | same game script as #404 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 438 | Michael Brandsegg-Nygard skater_points under 0.5 | 2 | 0.6078 (Low) | pass | market 60% | correlated | **untagged** | same game script as #404 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 439 | Michael Brandsegg-Nygard skater_assists under 0.5 | 1 | 0.7087 (Low) | pass | market 71% | correlated | **untagged** | same game script as #404 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 440 | Viktor Arvidsson skater_points over 0.5 | 0 | 0.5625 (Low) | pass | market 56% | correlated | **untagged** | same game script as #404 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 442 | Akira Schmid goalie_saves under 23.5 | 24 | 0.5111 (Low) | pass | market 50% | variance | **untagged** | root leg of a 11-leg script loss: #442, #444, #446, #449, #452, #453, #454, #455, #456, #459, #463; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 444 | Brady Tkachuk skater_assists under 0.5 | 1 | 0.6149 (Low) | pass | market 61% | correlated | **untagged** | same game script as #442 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 446 | Adam Fantilli skater_points over 0.5 | 0 | 0.5742 (Low) | pass | market 57% | correlated | **untagged** | same game script as #442 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 449 | Sam Bennett skater_points over 0.5 | 0 | 0.5162 (Low) | pass | market 51% | correlated | **untagged** | same game script as #442 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 452 | Charlie Coyle skater_points under 0.5 | 1 | 0.5402 (Low) | pass | market 54% | correlated | **untagged** | same game script as #442 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 453 | Charlie Coyle skater_assists under 0.5 | 1 | 0.6799 (Low) | pass | market 68% | correlated | **untagged** | same game script as #442 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 454 | Charlie Coyle skater_sog over 1.5 | 1 | 0.5499 (Low) | pass | market 55% | correlated | **untagged** | same game script as #442 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 455 | Valeri Nichushkin skater_points under 0.5 | 1 | 0.5625 (Low) | pass | market 56% | correlated | **untagged** | same game script as #442 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 456 | Valeri Nichushkin skater_assists under 0.5 | 1 | 0.6988 (Low) | pass | market 70% | correlated | **untagged** | same game script as #442 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 459 | Zach Werenski skater_assists over 0.5 | 0 | 0.5981 (Low) | pass | market 59% | correlated | **untagged** | same game script as #442 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 463 | Sean Monahan skater_sog under 1.5 | 3 | 0.5592 (Low) | pass | market 55% | correlated | **untagged** | same game script as #442 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 470 | Gianni Stensness passes_att under 39.5 | 40.0 | 0.557 (Low) | pass | model 60%, hist 17% (against) | correlated | **untagged** | same game script as #241 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 472 | Peter Christiansen passes_att under 10.5 | 16.0 | 0.5261 (Low) | pass | model 56%, hist 15% (against) | correlated | **untagged** | same game script as #241 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 473 | Renato Veiga passes_att over 72.5 | 57.0 | 0.5236 (Low) | pass | model 53%, hist 45% (against) | correlated | **untagged** | same game script as #279 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 477 | Rasmus Højlund passes_att under 13.5 | 18.0 | 0.8346 (Medium) | lean | model 87%, hist 50% (against) | correlated | **untagged** | same game script as #279 (variance); own read: variance |
| 480 | Mikko Rantanen skater_sog over 1.5 | 0 | 0.6385 (Medium) | pass | market 64%, hist 61% | variance | **untagged** | logged as a PASS: no money on it; reviewed for calibration |
| 485 | ckzao cs_kills_m12 under 31.5 | 32 | 0.574 (Low) | user_entry | model 60%, hist 75% | correlated | **untagged** | same game script as #124 (variance); own read: variance; closest possible loss (missed by the minimum) |
| 489 | Macklin Celebrini skater_sog under 3.5 | 5 | 0.5411 (Low) | pass | market 54%, hist 54% | variance | **untagged** | logged as a PASS: no money on it; reviewed for calibration |
| 511 | Tom Wilson skater_toi over 19.5 | 19.2 | 0.56 (Low) | user_entry | hist 56% | variance | **untagged** | closest possible loss (missed by the minimum) |
| 512 | Zemgus Girgensons skater_hits over 2.5 | 2 | 0.52 (Low) | user_entry | hist 52% | variance | **untagged** | closest possible loss (missed by the minimum) |
| 513 | Tim Stützle skater_toi under 21.5 | 22.05 | 0.55 (Low) | user_entry | hist 55% | variance | **untagged** |  |

Lessons:
- #86: Tout pick, we priced 49% and passed; Liquid lost Nuke (5 HS) and won Mirage (12 HS).
- #88: Near miss (9 vs 9.5): AWPer, 9 HS on 30 kills; 100T won 2-0 in only 36 rounds, which also capped #92 (kills 30 vs 31.5).
- #89: Correct pass (priced over at 49%); he had 26.
- #92: User entry we priced at 41% (Low): 2-0 in 36 rounds capped volume, 30 kills at .83 KPR. Root on #88. Don't enter Lows.
- #94: Both maps went long (Nuke 22, Mirage 21 rounds) and favored Liquid dropped Nuke; kills scale with rounds. Liquid unders #95 #98 #104 rode the same script (all passes).
- #101: Missed by the minimum (26 vs 26.5) on 43 rounds; inputs held.
- #112: Rooster stomped Fruju (16- and 19-round maps) and SkulL had 32 kills in 35 rounds (0.91 per round) against a projected median of 27. Same stomp effect as divine #14 (L21), on a roster that changed the day before.
- #117: Same Rooster stomp as #112: ju1ces 35 kills.
- #134: Missed by the minimum (18 vs 17.5): 18 HS on 29 kills (62%) in a 36-round 2-0; HS% spike, not volume.
- #138: Same Rooster stomp as #112; was a pass.

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
- #226 Jakub Markovic: minutes=90.0, passes=34.0, team_passes=403, possession=55.2, saves=4.0, score=SAB 2 - SLP 0
- #229 Gabriel Jesus: minutes=32.0, passes=15.0, team_passes=689, possession=71, saves=0.0, score=GAL 1 - BAR 4
- #231 Julián Alvarez: minutes=71.0, passes=28.0, team_passes=652, possession=57.8, saves=0.0, score=ATM 2 - MAN 0
- #236 Matheus Cunha: minutes=10.0, passes=14.0, team_passes=466, possession=42.2, saves=0.0, score=ATM 2 - MAN 0
- #237 Willi Orbán: minutes=90.0, passes=40.0, team_passes=350, possession=43, saves=0.0, score=RBL 1 - PSV 0
- #241 Ismael Saibari: minutes=38.0, passes=6.0, team_passes=566, possession=65.5, saves=0.0, score=VIK 3 - MUN 3
- #242 Marcus Thuram: minutes=67.0, passes=27.0, team_passes=533, possession=53.3, saves=0.0, score=INT 3 - BRU 4
- #245 Bukayo Saka: minutes=25.0, passes=10.0, team_passes=543, possession=58, saves=0.0, score=ARS 3 - LILL 0
- #246 Matheus Cunha: minutes=10.0, passes=14.0, team_passes=466, possession=42.2, saves=0.0, score=ATM 2 - MAN 0
- #247 Kai Havertz: minutes=25.0, passes=11.0, team_passes=543, possession=58, saves=0.0, score=ARS 3 - LILL 0
- #248 Marcus Rashford: minutes=66.0, passes=11.0, team_passes=466, possession=42.2, saves=0.0, score=ATM 2 - MAN 0
- #253 Brandon Mechele: minutes=90.0, passes=54.0, team_passes=475, possession=46.7, saves=0.0, score=INT 3 - BRU 4
- #254 Gonçalo Inácio: minutes=90.0, passes=67.0, team_passes=435, possession=44.1, saves=0.0, score=RCL 0 - SCP 2
- #258 Michael Olise: minutes=73.0, passes=55.0, team_passes=566, possession=65.5, saves=0.0, score=VIK 3 - MUN 3
- #265 Joy-Lance Mickels: minutes=90.0, passes=18.0, team_passes=341, possession=44.8, saves=0.0, score=SAB 2 - SLP 0
- #267 Julián Alvarez: minutes=71.0, passes=28.0, team_passes=652, possession=57.8, saves=0.0, score=ATM 2 - MAN 0
- #269 Rafael Leão: minutes=90.0, passes=27.0, team_passes=273, possession=29, saves=0.0, score=GAL 1 - BAR 4
- #270 Christopher Nkunku: minutes=90.0, passes=19.0, team_passes=350, possession=43, saves=0.0, score=RBL 1 - PSV 0
- #274 Harry Kane: minutes=90.0, passes=20.0, team_passes=566, possession=65.5, saves=0.0, score=VIK 3 - MUN 3
- #277 Kodai Sano: minutes=90.0, passes=52.0, team_passes=466, possession=57, saves=0.0, score=RBL 1 - PSV 0
- #279 Kevin De Bruyne: minutes=90.0, passes=52.0, team_passes=443, possession=48, saves=0.0, score=VIL 3 - NAP 1
- #281 Victor Osimhen: minutes=90.0, passes=3.0, team_passes=273, possession=29, saves=0.0, score=GAL 1 - BAR 4
- #283 Olivier Giroud: minutes=12.0, passes=4.0, team_passes=405, possession=42, saves=0.0, score=ARS 3 - LILL 0
- #289 Bruno Fernandes: minutes=80.0, passes=32.0, team_passes=466, possession=42.2, saves=0.0, score=ATM 2 - MAN 0
- #290 David Raya: minutes=90.0, passes=21.0, team_passes=543, possession=58, saves=0.0, score=ARS 3 - LILL 0
- #302 Ayase Ueda: minutes=78.0, passes=12.0, team_passes=405, possession=42, saves=0.0, score=ARS 3 - LILL 0
- #308 Senne Lammens: minutes=90.0, passes=24.0, team_passes=466, possession=42.2, saves=3.0, score=ATM 2 - MAN 0
- #315 Lamine Yamal: minutes=90.0, passes=50.0, team_passes=689, possession=71, saves=0.0, score=GAL 1 - BAR 4
- #316 Michael Olise: minutes=73.0, passes=55.0, team_passes=566, possession=65.5, saves=0.0, score=VIK 3 - MUN 3
- #319 Luis Suárez: minutes=85.0, passes=18.0, team_passes=435, possession=44.1, saves=0.0, score=RCL 0 - SCP 2
- #321 Luís Guilherme: minutes=24.0, passes=15.0, team_passes=435, possession=44.1, saves=0.0, score=RCL 0 - SCP 2
- #322 David Raya: minutes=90.0, passes=21.0, team_passes=543, possession=58, saves=0.0, score=ARS 3 - LILL 0
- #329 Francesco Pio Esposito: minutes=23.0, passes=10.0, team_passes=533, possession=53.3, saves=0.0, score=INT 3 - BRU 4
- #330 Junior Kadile: minutes=68.0, passes=21.0, team_passes=545, possession=55.9, saves=0.0, score=RCL 0 - SCP 2
- #334 Josep Martínez: minutes=90.0, passes=37.0, team_passes=533, possession=53.3, saves=4.0, score=INT 3 - BRU 4
- #335 Fermín López: minutes=82.0, passes=46.0, team_passes=689, possession=71, saves=0.0, score=GAL 1 - BAR 4
- #337 Joan García: minutes=90.0, passes=21.0, team_passes=689, possession=71, saves=2.0, score=GAL 1 - BAR 4
- #341 Declan Rice: minutes=90.0, passes=77.0, team_passes=543, possession=58, saves=0.0, score=ARS 3 - LILL 0
- #342 Kyllian Antonio: minutes=90.0, passes=56.0, team_passes=545, possession=55.9, saves=0.0, score=RCL 0 - SCP 2
- #344 Viktor Gyökeres: minutes=65.0, passes=8.0, team_passes=543, possession=58, saves=0.0, score=ARS 3 - LILL 0
- #346 Berke Özer: minutes=90.0, passes=39.0, team_passes=405, possession=42, saves=5.0, score=ARS 3 - LILL 0
- #347 Alessandro Bastoni: minutes=90.0, passes=79.0, team_passes=533, possession=53.3, saves=0.0, score=INT 3 - BRU 4
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
- #511 Tom Wilson: toi=19.2, sog=0, shifts=22, pp_goals=0, score=2-4
- #512 Zemgus Girgensons: toi=15.0, sog=2, shifts=19, pp_goals=0, score=1-4
- #513 Tim Stützle: toi=22.1, sog=1, shifts=25, pp_goals=0, score=7-2

## 2026-10-12: 38 losses from 20 independent causes

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
| 48 | Harpoon kills_m123 under 18.5 | 24 | 0.6947 (Low) | lean | model 73%, hist 48% (against) | variance | **untagged** | root leg of a 4-leg script loss: #48, #59, #61, #84; 24 kills vs 20.2 expected for the actual game results; games had 34/29/34 total kills |
| 52 | Quad kills_m123 under 8 | 16 | 0.6634 (Medium) | lean | model 68%, hist 57% | variance | variance | root leg of a 4-leg script loss: #52, #62, #64, #76; 16 kills vs 6.8 expected for the actual game results; games had 33/37/43 total kills |
| 55 | Cube kills_m123 under 7.5 | 15 | 0.6204 (Medium) | bet | model 60%, hist 74% | variance | correlated | root leg of a 3-leg script loss: #55, #56, #81; 15 kills vs 7.0 expected for the actual game results; games had 33/37/43 total kills |
| 56 | About kills_m123 under 14.5 | 16 | 0.6077 (Medium) | lean | model 59%, hist 74% | correlated | correlated | same game script as #55 (variance); own read: variance; 16 kills vs 13.8 expected for the actual game results; games had 33/37/43 total kills |
| 57 | 13 kills_m123 over 12.5 | 12 | 0.5683 (Low) | pass | model 55%, hist 75% | variance | **untagged** | logged as a PASS: no money on it; reviewed for calibration; 12 kills vs 9.6 expected for the actual game results; games had 34/29/34 total kills; closest possible loss (missed by the minimum) |
| 59 | Thayger kills_m123 under 14 | 18 | 0.6324 (Medium) | pass | model 63%, hist 71% | correlated | **untagged** | same game script as #48 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; 18 kills vs 17.3 expected for the actual game results; games had 34/29/34 total kills |
| 61 | Carlsen kills_m123 over 10 | 9 | 0.5647 (Low) | lean | model 56%, hist 60% | correlated | **untagged** | same game script as #48 (variance); own read: variance; 9 kills vs 13.5 expected for the actual game results; games had 34/29/34 total kills |
| 62 | Gakgos kills_m123 under 6.5 | 8 | 0.5865 (Medium) | lean | model 60%, hist 50% (against) | correlated | correlated | same game script as #52 (variance); own read: variance; 8 kills vs 5.9 expected for the actual game results; games had 33/37/43 total kills |
| 64 | Cryogen kills_m123 over 1.5 | 1 | 0.5596 (Low) | pass | model 55%, hist 61% | correlated | correlated | same game script as #52 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; 1 kills vs 2.1 expected for the actual game results; games had 33/37/43 total kills; closest possible loss (missed by the minimum) |
| 65 | Gideon kills_m123 under 10 | 12 | 0.5597 (Low) | pass | model 56%, hist 56% | variance | variance | root leg of a 4-leg script loss: #65, #66, #75, #80; logged as a PASS: no money on it; reviewed for calibration; 12 kills vs 11.0 expected for the actual game results; games had 23/34/20 total kills |
| 66 | Roamer kills_m123 under 9.5 | 10 | 0.5533 (Low) | pass | model 55%, hist 55% | correlated | correlated | same game script as #65 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; 10 kills vs 10.9 expected for the actual game results; games had 23/34/20 total kills; closest possible loss (missed by the minimum) |
| 73 | Burdol kills_m123 over 7.5 | 6 | 0.5345 (Low) | pass | model 53%, hist 54% | correlated | correlated | same game script as #47 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; 6 kills vs 7.3 expected for the actual game results; games had 23/34/20 total kills |
| 75 | Casting kills_m123 over 7.5 | 4 | 0.5208 (Low) | pass | model 52%, hist 51% | correlated | correlated | same game script as #65 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; 4 kills vs 8.5 expected for the actual game results; games had 23/34/20 total kills |
| 76 | Gryffinn kills_m123 under 9.5 | 14 | 0.5238 (Low) | pass | model 53%, hist 46% (against) | correlated | correlated | same game script as #52 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; 14 kills vs 9.6 expected for the actual game results; games had 33/37/43 total kills |
| 80 | Teddy kills_m123 under 12.5 | 14 | 0.5084 (Low) | pass | model 50%, hist 50% | correlated | correlated | same game script as #65 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; 14 kills vs 14.9 expected for the actual game results; games had 23/34/20 total kills |
| 81 | Monki kills_m123 under 10.5 | 21 | 0.4972 (Low) | pass | model 47% (against), hist 64% | correlated | correlated | same game script as #55 (variance); own read: variance; we priced this side at 50%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; 21 kills vs 11.5 expected for the actual game results; games had 33/37/43 total kills |
| 84 | Omon kills_m123 over 14.5 | 13 | 0.5239 (Low) | pass | model 50% (against), hist 62% | correlated | **untagged** | same game script as #48 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; 13 kills vs 19.4 expected for the actual game results; games had 34/29/34 total kills |

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
- #52: Tail game script: WE-FQ games ran 33/37/43 combined kills; Quad 16 vs 6.8 expected for the actual results (W,L,L). Spread re-checked on 967 past series (var z 0.92, mean -0.02, Demacia Cup -0.02): calibrated, no model change. Every leg on this series lost together: one leg per LoL series, never stack unders on one match.
- #55: Same WE-FQ series as #52: WE won games 2-3 with 25 and 27 kills; Cube 15 vs 7.0 expected. Root cause on #52.
- #73: Same LGD script as #47: LGD scored 16/15/5 kills in G1-3; Burdol 6 vs 7.3 expected.

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
- #52 Quad: G1 W: 7 K (expected 3.6); Team WE 9 - FlyQuest 24, 33 total; G2 L: 4 K (expected 1.6); FlyQuest 12 - Team WE 25, 37 total; G3 L: 5 K (expected 1.6); Team WE 27 - FlyQuest 16, 43 total
- #55 Cube: G1 L: 2 K (expected 1.0); Team WE 9 - FlyQuest 24, 33 total; G2 W: 6 K (expected 3.0); FlyQuest 12 - Team WE 25, 37 total; G3 W: 7 K (expected 3.0); Team WE 27 - FlyQuest 16, 43 total
- #56 About: G1 L: 4 K (expected 2.1); Team WE 9 - FlyQuest 24, 33 total; G2 W: 5 K (expected 5.8); FlyQuest 12 - Team WE 25, 37 total; G3 W: 7 K (expected 5.8); Team WE 27 - FlyQuest 16, 43 total
- #57 13: G1 L: 4 K (expected 3.2); Movistar KOI Fenix 7 - Galions 27, 34 total; G2 L: 3 K (expected 3.2); Galions 19 - Movistar KOI Fenix 10, 29 total; G3 L: 5 K (expected 3.2); Galions 24 - Movistar KOI Fenix 10, 34 total
- #59 Thayger: G1 W: 5 K (expected 5.8); Movistar KOI Fenix 7 - Galions 27, 34 total; G2 W: 6 K (expected 5.8); Galions 19 - Movistar KOI Fenix 10, 29 total; G3 W: 7 K (expected 5.8); Galions 24 - Movistar KOI Fenix 10, 34 total
- #61 Carlsen: G1 W: 5 K (expected 4.5); Movistar KOI Fenix 7 - Galions 27, 34 total; G2 W: 1 K (expected 4.5); Galions 19 - Movistar KOI Fenix 10, 29 total; G3 W: 3 K (expected 4.5); Galions 24 - Movistar KOI Fenix 10, 34 total
- #62 Gakgos: G1 W: 3 K (expected 3.3); Team WE 9 - FlyQuest 24, 33 total; G2 L: 0 K (expected 1.3); FlyQuest 12 - Team WE 25, 37 total; G3 L: 5 K (expected 1.3); Team WE 27 - FlyQuest 16, 43 total
- #64 Cryogen: G1 W: 0 K (expected 1.1); Team WE 9 - FlyQuest 24, 33 total; G2 L: 1 K (expected 0.5); FlyQuest 12 - Team WE 25, 37 total; G3 L: 0 K (expected 0.5); Team WE 27 - FlyQuest 16, 43 total
- #65 Gideon: G1 L: 2 K (expected 2.4); HANJIN BRION 7 - LGD Gaming 16, 23 total; G2 W: 6 K (expected 4.3); LGD Gaming 15 - HANJIN BRION 19, 34 total; G3 W: 4 K (expected 4.3); HANJIN BRION 15 - LGD Gaming 5, 20 total
- #66 Roamer: G1 L: 3 K (expected 1.8); HANJIN BRION 7 - LGD Gaming 16, 23 total; G2 W: 4 K (expected 4.5); LGD Gaming 15 - HANJIN BRION 19, 34 total; G3 W: 3 K (expected 4.5); HANJIN BRION 15 - LGD Gaming 5, 20 total
- #73 Burdol: G1 W: 3 K (expected 3.3); HANJIN BRION 7 - LGD Gaming 16, 23 total; G2 L: 3 K (expected 2.0); LGD Gaming 15 - HANJIN BRION 19, 34 total; G3 L: 0 K (expected 2.0); HANJIN BRION 15 - LGD Gaming 5, 20 total
- #75 Casting: G1 L: 1 K (expected 2.0); HANJIN BRION 7 - LGD Gaming 16, 23 total; G2 W: 2 K (expected 3.3); LGD Gaming 15 - HANJIN BRION 19, 34 total; G3 W: 1 K (expected 3.3); HANJIN BRION 15 - LGD Gaming 5, 20 total
- #76 Gryffinn: G1 W: 8 K (expected 4.5); Team WE 9 - FlyQuest 24, 33 total; G2 L: 4 K (expected 2.6); FlyQuest 12 - Team WE 25, 37 total; G3 L: 2 K (expected 2.6); Team WE 27 - FlyQuest 16, 43 total
- #80 Teddy: G1 L: 1 K (expected 2.5); HANJIN BRION 7 - LGD Gaming 16, 23 total; G2 W: 6 K (expected 6.2); LGD Gaming 15 - HANJIN BRION 19, 34 total; G3 W: 7 K (expected 6.2); HANJIN BRION 15 - LGD Gaming 5, 20 total
- #81 Monki: G1 L: 2 K (expected 1.5); Team WE 9 - FlyQuest 24, 33 total; G2 W: 8 K (expected 5.0); FlyQuest 12 - Team WE 25, 37 total; G3 W: 11 K (expected 5.0); Team WE 27 - FlyQuest 16, 43 total
- #84 Omon: G1 W: 3 K (expected 6.5); Movistar KOI Fenix 7 - Galions 27, 34 total; G2 W: 5 K (expected 6.5); Galions 19 - Movistar KOI Fenix 10, 29 total; G3 W: 5 K (expected 6.5); Galions 24 - Movistar KOI Fenix 10, 34 total

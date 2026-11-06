# Post-mortems

Every graded loss is examined here, including passes and Low-confidence legs. `python -m edge review` writes the diagnosis; `python -m edge tag ID "tag" --lesson "..."` confirms the cause. Tags: `variance`, `opportunity`, `correlated`, `role/lineup`, `model bias`, `market info`, `stale line`, `data error`, `format misread`.

## 2026-11-05: 22 losses from 5 independent causes

| # | Leg | Result | Our p | Action | Sources | Auto tag | Confirmed | Evidence |
|---|---|---|---|---|---|---|---|---|
| 519 | Jase Richardson pr under 11.5 | 12.0 | 0.494 (Low) | pass | model 47% (against) | variance | **untagged** | root leg of a 7-leg script loss: #519, #577, #580, #584, #601, #602, #606; we priced this side at 49%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 521 | Yaxel Lendeborg pra under 30.5 | 31.0 | 0.5225 (Low) | pass | model 63%, market 50% (against) | model bias | **untagged** | root leg of a 10-leg script loss: #521, #522, #592, #595, #596, #597, #598, #599, #600, #611; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 522 | Brandin Podziemski pa over 19.5 | 12.0 | 0.511 (Low) | pass | model 56% | correlated | **untagged** | same game script as #521 (model bias); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 546 | Zay Flowers rec_yds over 47.5 | 6.0 | 0.5331 (Low) | pass | model 52%, market 50% (against), hist 86% | variance | **untagged** | root leg of a 3-leg script loss: #546, #565, #575; logged as a PASS: no money on it; reviewed for calibration |
| 555 | Mitch Marner nhl_assists over 0.5 | 0.0 | 0.4978 (Low) | pass | model 48% (against), market 50% | variance | **untagged** | we priced this side at 50%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 562 | Vincent Trocheck nhl_sog over 1.5 | 1.0 | 0.5364 (Low) | pass | model 56%, market 53% | variance | **untagged** | logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 565 | Joe Fagnano pass_td over 0.5 | 0.0 | 0.5384 (Low) | pass | model 57%, market 50% (against), hist 0% (against) | correlated | **untagged** | same game script as #546 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 575 | Zay Flowers rec_yds over 48.5 | 6.0 | 0.5325 (Low) | pass | model 52%, market 50% (against), hist 86% | correlated | **untagged** | same game script as #546 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 577 | Jalen Green pra over 22.5 | 9.0 | 0.5651 (Medium) | pass | model 62%, market 55% | correlated | **untagged** | same game script as #519 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 580 | Jalen Green pr over 19.5 | 6.0 | 0.5161 (Low) | pass | model 58% | correlated | **untagged** | same game script as #519 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 584 | Collin Gillespie ast over 3.5 | 2.0 | 0.566 (Medium) | lean | model 74%, market 52% | correlated | **untagged** | same game script as #519 (variance); own read: variance |
| 592 | Draymond Green pa under 12.5 | 13.0 | 0.5366 (Low) | pass | model 59%, market 52% | correlated | **untagged** | same game script as #521 (model bias); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 595 | Stephen Curry pra over 35.5 | 34.0 | 0.5178 (Low) | pass | model 49% (against), market 52% | correlated | **untagged** | same game script as #521 (model bias); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 596 | Stephen Curry ast over 4.5 | 4.0 | 0.5121 (Low) | pass | model 40% (against), market 54% | correlated | **untagged** | same game script as #521 (model bias); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 597 | Stephen Curry reb over 3.5 | 1.0 | 0.5106 (Low) | pass | model 50%, market 51% | correlated | **untagged** | same game script as #521 (model bias); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 598 | Stephen Curry pa under 32.5 | 33.0 | 0.5069 (Low) | pass | model 53%, market 50% (against) | correlated | **untagged** | same game script as #521 (model bias); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 599 | Stephen Curry pr over 31.0 | 30.0 | 0.5063 (Low) | pass | model 49% (against), market 51% | correlated | **untagged** | same game script as #521 (model bias); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 600 | Stephen Curry pts under 27.5 | 29.0 | 0.501 (Low) | pass | model 51%, market 50% (against) | correlated | **untagged** | same game script as #521 (model bias); own read: model bias; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 601 | Devin Booker pts under 25.5 | 30.0 | 0.5179 (Low) | pass | model 50% (against), market 52% | correlated | **untagged** | same game script as #519 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 602 | Jalen Green pra over 23.0 | 9.0 | 0.5402 (Medium) | pass | model 61%, market 52% | correlated | **untagged** | same game script as #519 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 606 | Oso Ighodaro ast over 2.5 | 1.0 | 0.5729 (Low) | pass | model 74%, market 52% | correlated | **untagged** | same game script as #519 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 611 | Draymond Green pa under 11.5 | 13.0 | 0.4813 (Low) | pass | model 52%, market 47% (against) | correlated | **untagged** | same game script as #521 (model bias); own read: model bias; we priced this side at 48%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |

Detail from the feeds:
- #555 Mitch Marner: error=HTTPError
- #562 Vincent Trocheck: error=HTTPError

## 2026-11-04: 163 losses from 14 independent causes

| # | Leg | Result | Our p | Action | Sources | Auto tag | Confirmed | Evidence |
|---|---|---|---|---|---|---|---|---|
| 206 | Nickeil Alexander-Walker pr under 25.5 | 30.0 | 0.5975 (Medium) | pass | model 68%, market 51%, hist 50% (against) | variance | model bias | root leg of a 8-leg script loss: #206, #207, #324, #325, #422, #461, #466, #499; logged as a PASS: no money on it; reviewed for calibration |
| 207 | Luguentz Dort pra over 13.5 | 12.0 | 0.5995 (Medium) | pass | model 60%, hist 62% | correlated | variance | same game script as #206 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 208 | Joel Embiid pr under 27.5 | 41.0 | 0.593 (Medium) | pass | model 65%, market 53%, hist 50% (against) | variance | model bias | root leg of a 18-leg script loss: #208, #209, #212, #213, #214, #215, #216, #322, #328, #329, #330, #331, #334, #421, #423, #460, #507, #516; logged as a PASS: no money on it; reviewed for calibration |
| 209 | Joel Embiid pts under 19.5 | 26.0 | 0.5995 (Medium) | pass | model 65%, market 55%, hist 50% (against) | correlated | model bias | same game script as #208 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 212 | Daniss Jenkins pa over 13.5 | 9.0 | 0.6195 (Medium) | pass | model 69%, market 55%, hist 43% (against) | correlated | model bias | same game script as #208 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 213 | Anfernee Simons pra over 12.5 | 1.0 | 0.7047 (Medium) | pass | model 74%, hist 50% (against) | correlated | role/lineup | same game script as #208 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 214 | Anfernee Simons pr over 10.5 | 1.0 | 0.6824 (Medium) | pass | model 71%, hist 50% (against) | correlated | role/lineup | same game script as #208 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 215 | Anfernee Simons pts over 8.5 | 0.0 | 0.6047 (Medium) | pass | model 69%, market 51%, hist 50% (against) | correlated | role/lineup | same game script as #208 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 216 | Daniss Jenkins reb over 2.5 | 1.0 | 0.6059 (Medium) | pass | model 68%, market 52%, hist 57% | correlated | model bias | same game script as #208 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 218 | Paul George pr under 25.5 | 28.0 | 0.4048 (Low) | pass | model 36% (against), hist 67% | variance | model bias | root leg of a 29-leg script loss: #218, #219, #220, #221, #222, #223, #224, #225, #229, #230, #233, #336, #337, #338, #341, #343, #425, #426, #427, #428, #430, #431, #432, #467, #468, #469, #470, #500, #501; we priced this side at 40%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 219 | Tyler Herro pa under 25.5 | 28.0 | 0.6254 (Medium) | pass | model 64%, hist 57% | correlated | model bias | same game script as #218 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 220 | Derrick White pra under 23.5 | 35.0 | 0.4642 (Low) | pass | model 44% (against), market 44% (against), hist 71% | correlated | model bias | same game script as #218 (variance); own read: variance; we priced this side at 46%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 221 | Paul George pts under 20.5 | 25.0 | 0.4727 (Low) | pass | model 40% (against), market 49% (against), hist 83% | correlated | model bias | same game script as #218 (variance); own read: variance; we priced this side at 47%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 222 | Derrick White pa under 19.5 | 31.0 | 0.459 (Low) | pass | model 42% (against), hist 71% | correlated | model bias | same game script as #218 (variance); own read: variance; we priced this side at 46%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 223 | Derrick White pr under 19.5 | 28.0 | 0.6091 (Medium) | pass | model 60%, hist 86% | correlated | model bias | same game script as #218 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 224 | Kyle Kuzma pra over 16.5 | 15.0 | 0.5552 (Low) | pass | model 60%, market 49% (against), hist 57% | correlated | variance | same game script as #218 (variance); own read: model bias; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 225 | Derrick White pts under 16.5 | 24.0 | 0.5905 (Medium) | lean | model 63%, market 52%, hist 86% | correlated | model bias | same game script as #218 (variance); own read: variance |
| 229 | Kel'el Ware pts over 9.5 | 2.0 | 0.6015 (Medium) | pass | model 68%, market 51%, hist 57% | correlated | model bias | same game script as #218 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 230 | Kel'el Ware reb over 7.5 | 5.0 | 0.5959 (Low) | pass | model 68%, market 49% (against), hist 71% | correlated | model bias | same game script as #218 (variance); own read: model bias; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 233 | AJ Green pts over 6.5 | 5.0 | 0.5353 (Low) | pass | model 58%, market 47% (against), hist 57% | correlated | variance | same game script as #218 (variance); own read: model bias; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 236 | Dennis Schröder pa over 11.5 | 9.0 | 0.6578 (Medium) | pass | model 78%, market 51%, hist 62% | variance | model bias | root leg of a 10-leg script loss: #236, #238, #345, #346, #347, #471, #472, #473, #479, #502; logged as a PASS: no money on it; reviewed for calibration |
| 238 | Noah Clowney pr over 9.5 | 8.0 | 0.6092 (Medium) | pass | model 68%, market 52%, hist 57% | correlated | model bias | same game script as #236 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 246 | Jarrett Allen pr over 20.5 | 1.0 | 0.5971 (Medium) | pass | model 68%, market 50% (against), hist 57% | variance | role/lineup | root leg of a 10-leg script loss: #246, #356, #358, #359, #360, #361, #363, #436, #481, #482; logged as a PASS: no money on it; reviewed for calibration |
| 249 | Lauri Markkanen pr under 28.5 | 31.0 | 0.6157 (Medium) | pass | model 70%, market 51%, hist 67% | variance | model bias | root leg of a 16-leg script loss: #249, #250, #253, #254, #257, #259, #364, #366, #368, #370, #372, #379, #441, #483, #486, #511; logged as a PASS: no money on it; reviewed for calibration |
| 250 | Lauri Markkanen pa under 23.5 | 25.0 | 0.6323 (Medium) | pass | model 64%, hist 67% | correlated | model bias | same game script as #249 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 253 | Karlo Matković pra over 14.5 | 11.0 | 0.7699 (Medium) | pass | model 81%, hist 50% (against) | correlated | variance | same game script as #249 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 254 | Isaiah Collier pra over 13.5 | 1.0 | 0.8016 (Medium) | lean | model 84%, hist 57% | correlated | role/lineup | same game script as #249 (variance); own read: variance |
| 257 | Ace Bailey ra over 7.5 | 6.0 | 0.6789 (Medium) | pass | model 68%, hist 86% | correlated | variance | same game script as #249 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 259 | Isaiah Collier ast over 4.5 | 0.0 | 0.715 (Medium) | pass | model 74%, hist 57% | correlated | role/lineup | same game script as #249 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 261 | Cedric Coward pr under 20.5 | 32.0 | 0.5679 (Low) | pass | model 62%, market 50%, hist 50% (against) | variance | model bias | root leg of a 4-leg script loss: #261, #264, #270, #375; logged as a PASS: no money on it; reviewed for calibration |
| 264 | Cedric Coward pts under 13.5 | 23.0 | 0.5816 (Medium) | pass | model 63%, market 52%, hist 50% (against) | correlated | model bias | same game script as #261 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 270 | Cam Spencer pts over 7.5 | 7.0 | 0.5875 (Medium) | pass | model 64%, market 51%, hist 86% | correlated | variance | same game script as #261 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 279 | Joan Beringer pr over 12.5 | 11.0 | 0.7491 (Medium) | pass | model 79%, hist 50% (against) | variance | role/lineup | root leg of a 12-leg script loss: #279, #282, #283, #381, #382, #385, #387, #388, #446, #448, #449, #504; logged as a PASS: no money on it; reviewed for calibration |
| 282 | Amen Thompson reb under 6.5 | 8.0 | 0.599 (Medium) | pass | model 66%, market 52%, hist 62% | correlated | model bias | same game script as #279 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 283 | Joan Beringer pts over 6.5 | 4.0 | 0.7212 (Medium) | pass | model 75%, hist 50% (against) | correlated | role/lineup | same game script as #279 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 286 | Collin Gillespie pa over 12.5 | 4.0 | 0.6097 (Low) | pass | model 70%, market 52%, hist 40% (against) | variance | variance | root leg of a 8-leg script loss: #286, #287, #295, #323, #391, #394, #450, #452; logged as a PASS: no money on it; reviewed for calibration |
| 287 | Donovan Clingan ast over 1.5 | 1.0 | 0.5787 (Low) | pass | model 64%, market 51%, hist 50% (against) | correlated | variance | same game script as #286 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 288 | Nikola Jokić pr under 36.5 | 42.0 | 0.635 (Medium) | pass | model 73%, market 51%, hist 83% | variance | variance | root leg of a 9-leg script loss: #288, #289, #291, #296, #297, #395, #398, #402, #506; logged as a PASS: no money on it; reviewed for calibration |
| 289 | Nikola Jokić pa under 34.5 | 43.0 | 0.6233 (Low) | pass | model 73%, market 49% (against), hist 83% | correlated | variance | same game script as #288 (variance); own read: model bias; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 291 | Ja'Kobe Walter pra over 16.5 | 11.0 | 0.6605 (Medium) | pass | model 67%, hist 71% | correlated | variance | same game script as #288 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 295 | Damian Lillard pts under 21.5 | 25.0 | 0.5835 (Medium) | pass | model 64%, market 51%, hist 67% | correlated | model bias | same game script as #286 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 296 | Nikola Jokić pra under 46.5 | 53.0 | 0.6593 (Medium) | pass | model 78%, market 50%, hist 83% | correlated | variance | same game script as #288 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 297 | Nikola Jokić pts under 25.5 | 32.0 | 0.6137 (Medium) | pass | model 70%, market 51%, hist 67% | correlated | variance | same game script as #288 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 298 | Daniel Gafford pra over 17.5 | 7.0 | 0.684 (Medium) | pass | model 70%, hist 71% | variance | model bias | root leg of a 16-leg script loss: #298, #299, #300, #301, #302, #303, #304, #306, #403, #404, #405, #406, #407, #455, #462, #493; logged as a PASS: no money on it; reviewed for calibration |
| 299 | Keldon Johnson pra over 15.5 | 11.0 | 0.7716 (Medium) | lean | model 81%, hist 57% | correlated | model bias | same game script as #298 (variance); own read: variance |
| 300 | Zaccharie Risacher pra over 12.5 | 5.0 | 0.6478 (Medium) | pass | model 76%, market 50%, hist 71% | correlated | model bias | same game script as #298 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 301 | Keldon Johnson pr over 12.5 | 9.0 | 0.7073 (Medium) | pass | model 84%, market 52%, hist 86% | correlated | model bias | same game script as #298 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 302 | Keldon Johnson pts over 8.5 | 4.0 | 0.651 (Medium) | pass | model 77%, market 52%, hist 57% | correlated | model bias | same game script as #298 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 303 | Daniel Gafford ra over 8.5 | 5.0 | 0.6743 (Medium) | pass | model 70%, hist 57% | correlated | model bias | same game script as #298 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 304 | Zaccharie Risacher pts over 7.5 | 2.0 | 0.5841 (Medium) | pass | model 65%, market 50%, hist 57% | correlated | model bias | same game script as #298 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 306 | Zaccharie Risacher reb over 3.5 | 1.0 | 0.7203 (Medium) | pass | model 73%, hist 100% | correlated | model bias | same game script as #298 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 309 | Matisse Thybulle pts over 6.5 | 3.0 | 0.6015 (Medium) | pass | model 67%, market 53%, hist 50% (against) | variance | variance | root leg of a 6-leg script loss: #309, #310, #410, #412, #413, #513; logged as a PASS: no money on it; reviewed for calibration |
| 310 | Quentin Grimes ra over 5.5 | 2.0 | 0.6273 (Medium) | pass | model 64%, hist 50% (against) | correlated | variance | same game script as #309 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 311 | Rui Hachimura pra under 22.5 | 37.0 | 0.595 (Medium) | pass | model 60%, hist 60% | variance | model bias | root leg of a 13-leg script loss: #311, #312, #314, #316, #317, #320, #419, #458, #495, #496, #497, #514, #515; logged as a PASS: no money on it; reviewed for calibration |
| 312 | Keaton Wagler pra over 19.5 | 14.0 | 0.6186 (Medium) | pass | model 63%, hist 57% | correlated | model bias | same game script as #311 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 314 | Bobby Portis Jr. pr over 14.5 | 14.0 | 0.6853 (Medium) | pass | model 71%, hist 57% | correlated | model bias | same game script as #311 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 316 | Isaiah Jackson pts over 8.5 | 2.0 | 0.574 (Low) | pass | model 63%, market 50% (against), hist 57% | correlated | role/lineup | same game script as #311 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 317 | Bobby Portis Jr. pts over 8.5 | 4.0 | 0.6276 (Medium) | pass | model 68%, market 57%, hist 57% | correlated | model bias | same game script as #311 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 320 | Keaton Wagler ast over 3.5 | 1.0 | 0.5225 (Low) | pass | model 59%, market 43% (against), hist 57% | correlated | model bias | same game script as #311 (variance); own read: model bias; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 322 | Tyrese Maxey pa over 27.5 | 26.0 | 0.5008 (Low) | pass | model 41% (against), market 53%, hist 100% | correlated | variance | same game script as #208 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 323 | Toumani Camara tpm over 2.5 | 1.0 | 0.5399 (Low) | pass | model 54%, market 49% (against), hist 100% | correlated | variance | same game script as #286 (variance); own read: model bias; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 324 | Anthony Davis pa under 26.5 | 29.0 | 0.5825 (Medium) | pass | model 63%, market 52%, hist 57% | correlated | variance | same game script as #206 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 325 | Nickeil Alexander-Walker pts under 21.5 | 26.0 | 0.5924 (Medium) | pass | model 67%, market 50%, hist 50% (against) | correlated | model bias | same game script as #206 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 328 | Cade Cunningham ra under 14.0 | 18.0 | 0.7301 (Medium) | pass | model 75%, hist 71% | correlated | model bias | same game script as #208 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 329 | Daniss Jenkins pr over 12.5 | 6.0 | 0.6122 (Medium) | pass | model 62%, hist 57% | correlated | model bias | same game script as #208 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 330 | Anfernee Simons pra over 11.5 | 1.0 | 0.739 (Medium) | pass | model 77%, hist 50% (against) | correlated | role/lineup | same game script as #208 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 331 | Kevin Huerter pra over 11.5 | 9.0 | 0.7356 (Medium) | pass | model 77%, hist 57% | correlated | variance | same game script as #208 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 334 | John Collins ra over 7.0 | 1.0 | 0.5833 (Medium) | pass | model 58%, hist 57% | correlated | variance | same game script as #208 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 336 | Derrick White pts under 17.5 | 24.0 | 0.619 (Medium) | pass | model 68%, market 52%, hist 100% | correlated | model bias | same game script as #218 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 337 | Kel'el Ware pra over 16.5 | 8.0 | 0.7835 (Low) | pass | model 83%, hist 43% (against) | correlated | model bias | same game script as #218 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 338 | Baylor Scheierman pr under 13.5 | 20.0 | 0.6002 (Medium) | pass | model 59%, hist 86% | correlated | model bias | same game script as #218 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 341 | Kel'el Ware ra over 8.5 | 6.0 | 0.5843 (Medium) | pass | model 59%, hist 57% | correlated | model bias | same game script as #218 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 343 | Jaime Jaquez Jr. reb over 5.0 | 2.0 | 0.5854 (Medium) | pass | model 59%, market 55%, hist 86% | correlated | variance | same game script as #218 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 345 | Moussa Diabaté ra over 10.5 | 8.0 | 0.5846 (Medium) | pass | model 57%, hist 75% | correlated | variance | same game script as #236 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 346 | Noah Clowney pr over 10.0 | 8.0 | 0.6355 (Medium) | pass | model 65%, hist 57% | correlated | model bias | same game script as #236 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 347 | Dennis Schröder pts over 7.5 | 5.0 | 0.6221 (Medium) | pass | model 72%, market 50%, hist 62% | correlated | model bias | same game script as #236 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 349 | Karl-Anthony Towns ra over 16.5 | 13.0 | 0.6361 (Medium) | pass | model 65%, hist 57% | variance | role/lineup | root leg of a 4-leg script loss: #349, #434, #435, #476; logged as a PASS: no money on it; reviewed for calibration |
| 356 | Shai Gilgeous-Alexander pa under 38.5 | 50.0 | 0.5591 (Low) | pass | model 55%, hist 71% | correlated | model bias | same game script as #246 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 358 | Donovan Mitchell ra over 10.0 | 9.0 | 0.5854 (Medium) | pass | model 59%, hist 57% | correlated | variance | same game script as #246 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 359 | Shai Gilgeous-Alexander ra under 10.0 | 12.0 | 0.6625 (Medium) | lean | model 68%, hist 67% | correlated | model bias | same game script as #246 (variance); own read: variance |
| 360 | Jarrett Allen reb over 8.0 | 1.0 | 0.5989 (Medium) | pass | model 68%, market 50%, hist 60% | correlated | role/lineup | same game script as #246 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 361 | Jared McCain ra over 5.0 | 1.0 | 0.6792 (Medium) | pass | model 70%, hist 57% | correlated | variance | same game script as #246 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 363 | Jared McCain reb over 3.0 | 1.0 | 0.6172 (Medium) | pass | model 72%, market 51%, hist 50% (against) | correlated | variance | same game script as #246 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 364 | Lauri Markkanen pr under 27.5 | 31.0 | 0.5813 (Low) | pass | model 66%, market 48% (against), hist 67% | correlated | model bias | same game script as #249 (variance); own read: model bias; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 366 | Karlo Matković pra over 15.5 | 11.0 | 0.7414 (Medium) | pass | model 78%, hist 50% (against) | correlated | variance | same game script as #249 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 368 | Brice Sensabaugh pts over 7.5 | 6.0 | 0.6803 (Medium) | pass | model 70%, hist 57% | correlated | model bias | same game script as #249 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 370 | Isaiah Collier pts over 6.5 | 0.0 | 0.7172 (Medium) | pass | model 73%, hist 86% | correlated | role/lineup | same game script as #249 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 372 | Brice Sensabaugh reb over 2.5 | 2.0 | 0.5868 (Medium) | pass | model 59%, hist 57% | correlated | model bias | same game script as #249 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 375 | Jerami Grant pra over 14.5 | 14.0 | 0.5857 (Medium) | pass | model 59%, hist 57% | correlated | variance | same game script as #261 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 379 | Keyonte George ast under 6.0 | 9.0 | 0.5708 (Low) | pass | model 64%, market 48% (against), hist 67% | correlated | model bias | same game script as #249 (variance); own read: model bias; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 381 | Marcus Smart pra over 11.5 | 6.0 | 0.6078 (Medium) | pass | model 68%, market 51%, hist 80% | correlated | model bias | same game script as #279 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 382 | Joan Beringer pra over 11.5 | 11.0 | 0.8435 (Medium) | lean | model 88%, hist 62% | correlated | opportunity | same game script as #279 (variance); own read: variance; closest possible loss (missed by the minimum) |
| 385 | Marcus Smart ra over 4.5 | 2.0 | 0.6523 (Medium) | pass | model 67%, hist 60% | correlated | model bias | same game script as #279 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 387 | Fred VanVleet tpm under 2.5 | 4.0 | 0.6039 (Medium) | pass | model 66%, market 55%, hist 50% (against) | correlated | model bias | same game script as #279 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 388 | Alperen Şengün reb under 9.0 | 12.0 | 0.5776 (Low) | pass | model 63%, market 52%, hist 50% (against) | correlated | model bias | same game script as #279 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 391 | Khaman Maluach pra over 14.5 | 14.0 | 0.6081 (Medium) | pass | model 62%, hist 60% | correlated | model bias | same game script as #286 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 394 | Jalen Green ra over 6.0 | 4.0 | 0.6689 (Low) | pass | model 70%, hist 40% (against) | correlated | variance | same game script as #286 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 395 | Nikola Jokić pr under 37.5 | 42.0 | 0.6618 (Medium) | pass | model 76%, market 54%, hist 83% | correlated | variance | same game script as #288 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 398 | Jamal Murray ast under 6.0 | 7.0 | 0.6123 (Medium) | pass | model 68%, market 53%, hist 67% | correlated | variance | same game script as #288 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 402 | Trevon Brazile tpm over 0.5 | 0.0 | 0.6695 (Medium) | pass | model 68%, hist 67% | correlated | variance | same game script as #288 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 403 | Kyrie Irving pts under 20.5 | 29.0 | 0.5857 (Medium) | pass | model 62%, market 54%, hist 60% | correlated | model bias | same game script as #298 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 404 | Stephon Castle pts under 16.5 | 17.0 | 0.587 (Medium) | pass | model 62%, market 53%, hist 71% | correlated | model bias | same game script as #298 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 405 | Keldon Johnson pra over 14.5 | 11.0 | 0.8095 (Medium) | lean | model 84%, hist 86% | correlated | model bias | same game script as #298 (variance); own read: variance |
| 406 | Victor Wembanyama reb under 11.5 | 24.0 | 0.5871 (Medium) | pass | model 65%, market 51%, hist 57% | correlated | model bias | same game script as #298 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 407 | Keldon Johnson pts over 9.0 | 4.0 | 0.6349 (Medium) | pass | model 74%, market 52%, hist 50% (against) | correlated | model bias | same game script as #298 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 410 | Quentin Grimes pr over 10.5 | 7.0 | 0.5857 (Medium) | pass | model 65%, market 51%, hist 50% (against) | correlated | variance | same game script as #309 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 412 | Matisse Thybulle pra over 10.5 | 6.0 | 0.6852 (Medium) | pass | model 70%, hist 62% | correlated | variance | same game script as #309 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 413 | Matisse Thybulle pr over 9.5 | 4.0 | 0.5712 (Low) | pass | model 64%, market 49% (against), hist 50% (against) | correlated | variance | same game script as #309 (variance); own read: model bias; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 419 | Isaiah Jackson pr over 15.5 | 6.0 | 0.6194 (Medium) | pass | model 63%, hist 57% | correlated | role/lineup | same game script as #311 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 421 | Tyrese Maxey pa over 28.5 | 26.0 | 0.4735 (Low) | pass | model 36% (against), market 52%, hist 100% | correlated | role/lineup | same game script as #208 (variance); own read: variance; we priced this side at 47%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 422 | CJ McCollum ast under 4.0 | 5.0 | 0.5837 (Medium) | pass | model 59%, market 55%, hist 75% | correlated | variance | same game script as #206 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 423 | Javonte Green pra over 9.5 | 5.0 | 0.7368 (Low) | pass | model 78%, hist 43% (against) | correlated | model bias | same game script as #208 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 425 | Derrick White pra under 27.5 | 35.0 | 0.5874 (Medium) | pass | model 64%, market 50%, hist 86% | correlated | model bias | same game script as #218 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 426 | Derrick White pr under 21.5 | 28.0 | 0.6258 (Medium) | pass | model 69%, market 52%, hist 100% | correlated | model bias | same game script as #218 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 427 | Kel'el Ware pra over 17.5 | 8.0 | 0.7419 (Low) | pass | model 78%, hist 43% (against) | correlated | model bias | same game script as #218 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 428 | Baylor Scheierman pra under 16.5 | 21.0 | 0.5913 (Medium) | pass | model 58%, hist 86% | correlated | model bias | same game script as #218 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 430 | Jaime Jaquez Jr. ra over 8.5 | 4.0 | 0.5852 (Medium) | pass | model 58%, hist 71% | correlated | variance | same game script as #218 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 431 | Mitchell Robinson pts over 5.5 | 3.0 | 0.6394 (Medium) | pass | model 74%, market 53%, hist 50% (against) | correlated | variance | same game script as #218 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 432 | Paul George reb over 5.0 | 3.0 | 0.5889 (Medium) | pass | model 65%, market 50%, hist 100% | correlated | variance | same game script as #218 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 434 | OG Anunoby pra over 25.5 | 25.0 | 0.6138 (Medium) | pass | model 69%, market 54%, hist 43% (against) | correlated | role/lineup | same game script as #349 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 435 | Karl-Anthony Towns reb over 13.0 | 12.0 | 0.6326 (Medium) | pass | model 74%, market 52%, hist 50% (against) | correlated | role/lineup | same game script as #349 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 436 | Jarrett Allen pr over 21.5 | 1.0 | 0.5641 (Low) | pass | model 63%, market 49% (against), hist 43% (against) | correlated | role/lineup | same game script as #246 (variance); own read: model bias; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 441 | Karlo Matković pra over 16.5 | 11.0 | 0.6998 (Medium) | pass | model 73%, hist 50% (against) | correlated | variance | same game script as #249 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 446 | Tari Eason pra over 16.5 | 16.0 | 0.601 (Medium) | pass | model 60%, hist 62% | correlated | variance | same game script as #279 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 448 | Joan Beringer pr over 11.5 | 11.0 | 0.7878 (Medium) | pass | model 82%, hist 62% | correlated | role/lineup | same game script as #279 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 449 | Fred VanVleet ra over 8.5 | 6.0 | 0.6111 (Medium) | pass | model 60%, hist 83% | correlated | variance | same game script as #279 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 450 | Damian Lillard pa under 26.5 | 30.0 | 0.5833 (Medium) | pass | model 64%, market 50%, hist 83% | correlated | model bias | same game script as #286 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 452 | Khaman Maluach pr over 12.5 | 12.0 | 0.6177 (Medium) | pass | model 63%, hist 60% | correlated | model bias | same game script as #286 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 455 | Cooper Flagg ra under 12.0 | 15.0 | 0.6806 (Medium) | pass | model 71%, hist 50% (against) | correlated | model bias | same game script as #298 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 458 | Klay Thompson reb under 2.5 | 5.0 | 0.6376 (Medium) | pass | model 66%, market 60%, hist 86% | correlated | model bias | same game script as #311 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 460 | Tyrese Maxey pa over 29.5 | 26.0 | 0.4423 (Low) | pass | model 32% (against), market 49% (against), hist 100% | correlated | variance | same game script as #208 (variance); own read: variance; we priced this side at 44%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 461 | AJ Dybantsa reb under 5.5 | 6.0 | 0.5496 (Low) | pass | model 57%, market 51%, hist 67% | correlated | model bias | same game script as #206 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 462 | Kyrie Irving pa under 24.5 | 34.0 | 0.5476 (Low) | pass | model 57%, market 51%, hist 60% | correlated | model bias | same game script as #298 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 466 | Dyson Daniels ra under 11.0 | 24.0 | 0.6149 (Medium) | pass | model 62%, hist 60% | correlated | model bias | same game script as #206 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 467 | Derrick White pa under 23.5 | 31.0 | 0.5914 (Medium) | pass | model 62%, market 53%, hist 86% | correlated | model bias | same game script as #218 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 468 | Neemias Queta ra under 9.5 | 15.0 | 0.6784 (Medium) | pass | model 68%, hist 100% | correlated | model bias | same game script as #218 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 469 | Derrick White ra under 9.5 | 11.0 | 0.5858 (Medium) | pass | model 59%, hist 57% | correlated | model bias | same game script as #218 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 470 | Baylor Scheierman ra under 7.5 | 12.0 | 0.6729 (Medium) | pass | model 68%, hist 86% | correlated | model bias | same game script as #218 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 471 | Naz Reid ra under 9.5 | 11.0 | 0.6483 (Medium) | pass | model 66%, hist 62% | correlated | model bias | same game script as #236 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 472 | Day'Ron Sharpe ra under 9.5 | 13.0 | 0.5894 (Medium) | pass | model 58%, hist 71% | correlated | model bias | same game script as #236 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 473 | Michael Porter Jr. ra under 8.5 | 10.0 | 0.6162 (Medium) | pass | model 62%, hist 57% | correlated | model bias | same game script as #236 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 476 | Matas Buzelis ra under 6.5 | 8.0 | 0.6486 (Medium) | pass | model 66%, hist 57% | correlated | variance | same game script as #349 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 479 | Coby White ra under 6.0 | 7.0 | 0.7217 (Low) | pass | model 75%, hist 100% | correlated | variance | same game script as #236 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 481 | Evan Mobley ra under 12.5 | 13.0 | 0.5885 (Medium) | pass | model 59%, hist 57% | correlated | variance | same game script as #246 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 482 | Isaiah Hartenstein pts over 9.5 | 3.0 | 0.5863 (Medium) | pass | model 61%, market 55%, hist 57% | correlated | variance | same game script as #246 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 483 | Keyonte George ra under 9.5 | 11.0 | 0.5877 (Medium) | pass | model 66%, market 50% (against), hist 71% | correlated | model bias | same game script as #249 (variance); own read: model bias; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 486 | Darryn Peterson ra under 8.0 | 9.0 | 0.6272 (Medium) | pass | model 64%, hist 60% | correlated | variance | same game script as #249 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 493 | Kyrie Irving ra under 8.0 | 12.0 | 0.5931 (Medium) | pass | model 60%, hist 60% | correlated | model bias | same game script as #298 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 495 | Darius Garland pr under 24.5 | 27.0 | 0.6177 (Medium) | pass | model 63%, hist 57% | correlated | model bias | same game script as #311 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 496 | Rui Hachimura pr under 20.5 | 30.0 | 0.5854 (Medium) | pass | model 59%, hist 60% | correlated | model bias | same game script as #311 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 497 | Bam Adebayo ra under 12.5 | 14.0 | 0.6169 (Medium) | pass | model 61%, hist 86% | correlated | model bias | same game script as #311 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 499 | Nickeil Alexander-Walker pra under 28.5 | 32.0 | 0.5812 (Medium) | pass | model 65%, market 50% (against), hist 62% | correlated | model bias | same game script as #206 (variance); own read: model bias; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 500 | Kel'el Ware ra over 7.5 | 6.0 | 0.6679 (Medium) | pass | model 68%, hist 71% | correlated | model bias | same game script as #218 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 501 | Brayden Burries ast under 2.5 | 3.0 | 0.5922 (Medium) | pass | model 61%, market 54%, hist 86% | correlated | variance | same game script as #218 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 502 | Mikel Brown Jr. pr under 15.5 | 20.0 | 0.5851 (Medium) | pass | model 58%, hist 80% | correlated | variance | same game script as #236 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 504 | Marcus Smart pa over 9.5 | 5.0 | 0.5782 (Low) | pass | model 64%, market 49% (against), hist 80% | correlated | model bias | same game script as #279 (variance); own read: model bias; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 506 | Nikola Jokić pra under 47.0 | 53.0 | 0.6821 (Medium) | pass | model 81%, market 52%, hist 83% | correlated | variance | same game script as #288 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 507 | Tyrese Maxey pr over 28.5 | 20.0 | 0.3816 (Low) | pass | model 31% (against), hist 100% | correlated | variance | same game script as #208 (variance); own read: variance; we priced this side at 38%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 511 | Brice Sensabaugh pra over 11.5 | 8.0 | 0.7345 (Medium) | pass | model 76%, hist 71% | correlated | model bias | same game script as #249 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 513 | Quentin Grimes pa over 9.5 | 7.0 | 0.6423 (Medium) | pass | model 75%, market 52%, hist 62% | correlated | variance | same game script as #309 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 514 | Darius Garland pra under 32.5 | 34.0 | 0.6105 (Medium) | pass | model 65%, market 54%, hist 86% | correlated | model bias | same game script as #311 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 515 | Brook Lopez tpm under 1.5 | 2.0 | 0.5849 (Medium) | pass | model 59%, market 56%, hist 71% | correlated | model bias | same game script as #311 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 516 | Cade Cunningham pr under 29.5 | 33.0 | 0.5802 (Medium) | pass | model 58%, hist 57% | correlated | model bias | same game script as #208 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |

Lessons:
- #206: 32 min vs 27 projected on an under (starter): v1 starter minutes squeeze (exponent 0.8), fixed by v2
- #207: minutes as projected (31 vs 26): rate variance or the game script
- #208: 33 min vs 27 projected on an under (starter): v1 starter minutes squeeze (exponent 0.8), fixed by v2
- #209: 33 min vs 27 projected on an under (starter): v1 starter minutes squeeze (exponent 0.8), fixed by v2
- #212: 21 min vs 25 projected on an over (starter): v1 minutes allocation (exponent 0.8), fixed by v2
- #213: 10 min vs 24 projected: out of his usual role tonight
- #214: 10 min vs 24 projected: out of his usual role tonight
- #215: 10 min vs 24 projected: out of his usual role tonight
- #216: 21 min vs 25 projected on an over (starter): v1 minutes allocation (exponent 0.8), fixed by v2
- #218: 35 min vs 26 projected on an under (starter): v1 starter minutes squeeze (exponent 0.8), fixed by v2
- #219: 33 min vs 27 projected on an under (starter): v1 starter minutes squeeze (exponent 0.8), fixed by v2
- #220: 36 min vs 25 projected on an under (starter): v1 starter minutes squeeze (exponent 0.8), fixed by v2
- #221: 35 min vs 26 projected on an under (starter): v1 starter minutes squeeze (exponent 0.8), fixed by v2
- #222: 36 min vs 25 projected on an under (starter): v1 starter minutes squeeze (exponent 0.8), fixed by v2
- #223: 36 min vs 25 projected on an under (starter): v1 starter minutes squeeze (exponent 0.8), fixed by v2
- #224: minutes as projected (27 vs 23): rate variance or the game script
- #225: 36 min vs 25 projected; with Tatum out Boston leaned on its starters (White 36, George 35). v1 starter squeeze (exponent 0.8); fixed by v2.
- #229: 16 min vs 22 projected on an over (bench): v1 minutes allocation (exponent 0.8), fixed by v2
- #230: 16 min vs 22 projected on an over (bench): v1 minutes allocation (exponent 0.8), fixed by v2
- #233: minutes as projected (20 vs 23): rate variance or the game script
- #236: 20 min vs 27 projected on an over (starter): v1 minutes allocation (exponent 0.8), fixed by v2
- #238: 17 min vs 22 projected on an over (bench): v1 minutes allocation (exponent 0.8), fixed by v2
- #246: 7 min vs 30 projected: out of his usual role tonight
- #249: 39 min vs 24 projected on an under (starter): v1 starter minutes squeeze (exponent 0.8), fixed by v2
- #250: 39 min vs 24 projected on an under (starter): v1 starter minutes squeeze (exponent 0.8), fixed by v2
- #253: minutes as projected (21 vs 23): rate variance or the game script
- #254: 3 min vs 19 projected: dropped from the rotation (Keyonte George 44 min). PrizePicks pulled his line before tip and verify withdrew it: a pulled line is a role signal.
- #257: minutes as projected (35 vs 29): rate variance or the game script
- #259: 3 min vs 19 projected: out of his usual role tonight
- #261: 33 min vs 24 projected on an under (starter): v1 starter minutes squeeze (exponent 0.8), fixed by v2
- #264: 33 min vs 24 projected on an under (starter): v1 starter minutes squeeze (exponent 0.8), fixed by v2
- #270: minutes as projected (24 vs 20): rate variance or the game script
- #279: 13 min vs 22 projected: out of his usual role tonight
- #282: 32 min vs 26 projected on an under (starter): v1 starter minutes squeeze (exponent 0.8), fixed by v2
- #283: 13 min vs 22 projected: out of his usual role tonight
- #286: minutes as projected (23 vs 24): rate variance or the game script
- #287: minutes as projected (29 vs 24): rate variance or the game script
- #288: minutes as projected (30 vs 30): rate variance or the game script
- #289: minutes as projected (30 vs 30): rate variance or the game script
- #291: minutes as projected (27 vs 29): rate variance or the game script
- #295: 33 min vs 28 projected on an under (starter): v1 starter minutes squeeze (exponent 0.8), fixed by v2
- #296: minutes as projected (30 vs 30): rate variance or the game script
- #297: minutes as projected (30 vs 30): rate variance or the game script
- #298: 18 min vs 25 projected on an over (starter): v1 minutes allocation (exponent 0.8), fixed by v2
- #299: Same leg as #405 at 15.5: 19 min vs 25.2 projected, v1 bench-minutes inflation (exponent 0.8). Fixed by v2.
- #300: 18 min vs 26 projected on an over (starter): v1 minutes allocation (exponent 0.8), fixed by v2
- #301: 19 min vs 25 projected on an over (bench): v1 minutes allocation (exponent 0.8), fixed by v2
- #302: 19 min vs 25 projected on an over (bench): v1 minutes allocation (exponent 0.8), fixed by v2
- #303: 18 min vs 25 projected on an over (starter): v1 minutes allocation (exponent 0.8), fixed by v2
- #304: 18 min vs 26 projected on an over (starter): v1 minutes allocation (exponent 0.8), fixed by v2
- #306: 18 min vs 26 projected on an over (starter): v1 minutes allocation (exponent 0.8), fixed by v2
- #311: 37 min vs 25 projected on an under: v1 starter minutes squeeze (exponent 0.8), fixed by v2
- #312: 16 min vs 22 projected on an over: v1 minutes allocation (exponent 0.8), fixed by v2
- #314: 18 min vs 23 projected on an over: v1 minutes allocation (exponent 0.8), fixed by v2
- #316: 13 min vs 21 projected: out of his usual role
- #317: 18 min vs 23 projected on an over: v1 minutes allocation (exponent 0.8), fixed by v2
- #320: 16 min vs 22 projected on an over: v1 minutes allocation (exponent 0.8), fixed by v2
- #322: minutes as projected (34 vs 29): rate variance or the game script
- #323: Minutes as projected (32 vs 26.5); 1 three on 9 FGA. 3-pointers made is the noisiest stat; DraftKings had the over at 49%.
- #324: minutes as projected (30 vs 30): rate variance or the game script
- #325: 32 min vs 27 projected on an under (starter): v1 starter minutes squeeze (exponent 0.8), fixed by v2
- #328: 40 min vs 30 projected on an under (starter): v1 starter minutes squeeze (exponent 0.8), fixed by v2
- #329: 21 min vs 25 projected on an over (starter): v1 minutes allocation (exponent 0.8), fixed by v2
- #330: 10 min vs 24 projected: out of his usual role tonight
- #331: minutes as projected (20 vs 23): rate variance or the game script
- #334: minutes as projected (26 vs 25): rate variance or the game script
- #336: 36 min vs 29 projected on an under (starter): v1 starter minutes squeeze (exponent 0.8), fixed by v2
- #337: 16 min vs 22 projected on an over (bench): v1 minutes allocation (exponent 0.8), fixed by v2
- #338: 29 min vs 23 projected on an under (starter): v1 starter minutes squeeze (exponent 0.8), fixed by v2
- #341: 16 min vs 22 projected on an over (bench): v1 minutes allocation (exponent 0.8), fixed by v2
- #343: minutes as projected (31 vs 24): rate variance or the game script
- #345: minutes as projected (29 vs 26): rate variance or the game script
- #346: 17 min vs 22 projected on an over (bench): v1 minutes allocation (exponent 0.8), fixed by v2
- #347: 20 min vs 27 projected on an over (starter): v1 minutes allocation (exponent 0.8), fixed by v2
- #349: 25 min vs 33 projected: out of his usual role tonight
- #356: 35 min vs 32 projected on an under (starter): v1 starter minutes squeeze (exponent 0.8), fixed by v2
- #358: minutes as projected (33 vs 33): rate variance or the game script
- #359: 35 min vs 31.5 projected (v1 starter squeeze, exponent 0.8); with Caruso, Holmgren and J. Williams out he ran the offense (8 ast). Starter unders lose when starter minutes are under-projected.
- #360: 7 min vs 30 projected: out of his usual role tonight
- #361: minutes as projected (25 vs 27): rate variance or the game script
- #363: minutes as projected (25 vs 27): rate variance or the game script
- #364: 39 min vs 24 projected on an under (starter): v1 starter minutes squeeze (exponent 0.8), fixed by v2
- #366: minutes as projected (21 vs 23): rate variance or the game script
- #368: 12 min vs 17 projected on an over (bench): v1 minutes allocation (exponent 0.8), fixed by v2
- #370: 3 min vs 19 projected: out of his usual role tonight
- #372: 12 min vs 17 projected on an over (bench): v1 minutes allocation (exponent 0.8), fixed by v2
- #375: minutes as projected (24 vs 21): rate variance or the game script
- #379: 44 min vs 27 projected on an under (starter): v1 starter minutes squeeze (exponent 0.8), fixed by v2
- #381: 18 min vs 23 projected on an over (bench): v1 minutes allocation (exponent 0.8), fixed by v2
- #382: 13 min vs 24.6 projected: Edwards' minutes went to wings (Dosunmu 34, Clark 25), not to a backup center behind Gobert (33). Minutes freed by an absence should go to the absent player's position, and v1's minutes exponent 0.8 inflated bench minutes.
- #385: 18 min vs 23 projected on an over (bench): v1 minutes allocation (exponent 0.8), fixed by v2
- #387: 30 min vs 25 projected on an under (starter): v1 starter minutes squeeze (exponent 0.8), fixed by v2
- #388: 39 min vs 28 projected on an under (starter): v1 starter minutes squeeze (exponent 0.8), fixed by v2
- #391: 16 min vs 21 projected on an over (bench): v1 minutes allocation (exponent 0.8), fixed by v2
- #394: minutes as projected (32 vs 27): rate variance or the game script
- #395: minutes as projected (30 vs 30): rate variance or the game script
- #398: minutes as projected (28 vs 31): rate variance or the game script
- #402: minutes as projected (23 vs 21): rate variance or the game script
- #403: 36 min vs 28 projected on an under (starter): v1 starter minutes squeeze (exponent 0.8), fixed by v2
- #404: 35 min vs 26 projected on an under (starter): v1 starter minutes squeeze (exponent 0.8), fixed by v2
- #405: 19 min vs 25.2 projected; San Antonio's top five played 33-36. v1's minutes exponent 0.8 moved minutes from starters to the bench (tonight bench +2.1 min too high, starters 2.8 too low). Fixed by v2 (exponent 1.0), promoted Nov 5.
- #406: 34 min vs 28 projected on an under (starter): v1 starter minutes squeeze (exponent 0.8), fixed by v2
- #407: 19 min vs 25 projected on an over (bench): v1 minutes allocation (exponent 0.8), fixed by v2
- #419: 13 min vs 21 projected: out of his usual role
- #421: History-only pick (8/8 over at the line) ignored that Embiid and James are back: 34 min vs 38 this season, 19 pts. The model priced the over at 36%; the history count was the wrong input.
- #422: minutes as projected (25 vs 25): rate variance or the game script
- #423: 15 min vs 22 projected on an over (bench): v1 minutes allocation (exponent 0.8), fixed by v2
- #425: 36 min vs 29 projected on an under (starter): v1 starter minutes squeeze (exponent 0.8), fixed by v2
- #426: Same game as #225: 36 min vs 28.6 projected, 18 FGA. v1 starter squeeze; the line was also over-only on PrizePicks by tip and was withdrawn.
- #427: 16 min vs 22 projected on an over (bench): v1 minutes allocation (exponent 0.8), fixed by v2
- #428: 29 min vs 23 projected on an under (starter): v1 starter minutes squeeze (exponent 0.8), fixed by v2
- #430: minutes as projected (31 vs 24): rate variance or the game script
- #431: minutes as projected (20 vs 22): rate variance or the game script
- #432: minutes as projected (35 vs 30): rate variance or the game script
- #434: 24 min vs 35 projected: out of his usual role tonight
- #435: 25 min vs 33 projected: out of his usual role tonight
- #436: 7 min vs 30 projected: out of his usual role tonight
- #441: minutes as projected (21 vs 23): rate variance or the game script
- #446: minutes as projected (24 vs 25): rate variance or the game script
- #448: 13 min vs 25 projected: out of his usual role tonight
- #449: minutes as projected (30 vs 26): rate variance or the game script
- #450: 33 min vs 28 projected on an under (starter): v1 starter minutes squeeze (exponent 0.8), fixed by v2
- #452: 16 min vs 21 projected on an over (bench): v1 minutes allocation (exponent 0.8), fixed by v2
- #455: 40 min vs 32 projected on an under (starter): v1 starter minutes squeeze (exponent 0.8), fixed by v2
- #458: 35 min vs 24 projected on an under: v1 starter minutes squeeze (exponent 0.8), fixed by v2
- #460: minutes as projected (34 vs 29): rate variance or the game script
- #461: 32 min vs 28 projected on an under (starter): v1 starter minutes squeeze (exponent 0.8), fixed by v2
- #462: 36 min vs 28 projected on an under (starter): v1 starter minutes squeeze (exponent 0.8), fixed by v2
- #466: 34 min vs 27 projected on an under (starter): v1 starter minutes squeeze (exponent 0.8), fixed by v2
- #467: 36 min vs 29 projected on an under (starter): v1 starter minutes squeeze (exponent 0.8), fixed by v2
- #468: 29 min vs 23 projected on an under (starter): v1 starter minutes squeeze (exponent 0.8), fixed by v2
- #469: 36 min vs 29 projected on an under (starter): v1 starter minutes squeeze (exponent 0.8), fixed by v2
- #470: 29 min vs 23 projected on an under (starter): v1 starter minutes squeeze (exponent 0.8), fixed by v2
- #471: 36 min vs 25 projected on an under (starter): v1 starter minutes squeeze (exponent 0.8), fixed by v2
- #472: 27 min vs 22 projected on an under (bench): v1 starter minutes squeeze (exponent 0.8), fixed by v2
- #473: 38 min vs 28 projected on an under (starter): v1 starter minutes squeeze (exponent 0.8), fixed by v2
- #476: minutes as projected (26 vs 23): rate variance or the game script
- #479: minutes as projected (18 vs 17): rate variance or the game script
- #481: minutes as projected (33 vs 33): rate variance or the game script
- #482: minutes as projected (26 vs 26): rate variance or the game script
- #483: 44 min vs 27 projected on an under (starter): v1 starter minutes squeeze (exponent 0.8), fixed by v2
- #486: minutes as projected (30 vs 28): rate variance or the game script
- #493: 36 min vs 28 projected on an under (starter): v1 starter minutes squeeze (exponent 0.8), fixed by v2
- #495: 39 min vs 27 projected on an under: v1 starter minutes squeeze (exponent 0.8), fixed by v2
- #496: 37 min vs 25 projected on an under: v1 starter minutes squeeze (exponent 0.8), fixed by v2
- #497: 41 min vs 30 projected on an under: v1 starter minutes squeeze (exponent 0.8), fixed by v2
- #499: 32 min vs 27 projected on an under (starter): v1 starter minutes squeeze (exponent 0.8), fixed by v2
- #500: 16 min vs 22 projected on an over (bench): v1 minutes allocation (exponent 0.8), fixed by v2
- #501: minutes as projected (22 vs 22): rate variance or the game script
- #502: minutes as projected (20 vs 22): rate variance or the game script
- #504: 18 min vs 23 projected on an over (bench): v1 minutes allocation (exponent 0.8), fixed by v2
- #506: minutes as projected (30 vs 30): rate variance or the game script
- #507: minutes as projected (34 vs 29): rate variance or the game script
- #511: 12 min vs 17 projected; Utah's starters played 44/39/35. v1 bench-minutes inflation (exponent 0.8); fixed by v2.
- #514: 39 min vs 27 projected on an under: v1 starter minutes squeeze (exponent 0.8), fixed by v2
- #515: 35 min vs 20 projected on an under: v1 starter minutes squeeze (exponent 0.8), fixed by v2
- #516: 40 min vs 30 projected on an under (starter): v1 starter minutes squeeze (exponent 0.8), fixed by v2

## 2026-10-13: 53 losses from 11 independent causes

| # | Leg | Result | Our p | Action | Sources | Auto tag | Confirmed | Evidence |
|---|---|---|---|---|---|---|---|---|
| 86 | EliGE cs_headshots_m12 over 18.5 | 17 | 0.492 (Low) | pass | model 45% (against), hist 69% | variance | variance | we priced this side at 49%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 88 | dev1ce cs_headshots_m12 over 9.5 | 9 | 0.466 (Low) | pass | model 44% (against), hist 41% (against) | variance | variance | root leg of a 2-leg script loss: #88, #92; we priced this side at 47%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 89 | foggers cs_kills_m12 over 30.5 | 26 | 0.489 (Low) | pass | model 51%, hist 24% (against) | variance | variance | we priced this side at 49%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 92 | dev1ce cs_kills_m12 over 31.5 | 30 | 0.413 (Low) | user_entry | model 38% (against), hist 41% (against) | correlated | variance | same game script as #88 (variance); own read: variance; we priced this side at 41%: losing was the more likely outcome; closest possible loss (missed by the minimum) |
| 94 | Jorko cs_kills_m12 under 30.5 | 35 | 0.6129 (Low) | pass | model 62%, hist 46% (against) | variance | model bias | root leg of a 4-leg script loss: #94, #95, #98, #104; logged as a PASS: no money on it; reviewed for calibration |
| 95 | malbsMd cs_kills_m12 under 32 | 40 | 0.6809 (Medium) | pass | model 67%, hist 75% | correlated | correlated | same game script as #94 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 98 | JT cs_kills_m12 under 25.5 | 28 | 0.5934 (Low) | pass | model 60%, hist 46% (against) | correlated | correlated | same game script as #94 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 101 | NickyB cs_kills_m12 over 26.5 | 26 | 0.5499 (Low) | pass | model 52%, hist 60% | variance | variance | root leg of a 7-leg script loss: #101, #102, #108, #109, #152, #157, #158; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 102 | MIstR cs_kills_m12 over 25.5 | 23 | 0.5545 (Low) | pass | model 51%, hist 65% | correlated | correlated | same game script as #101 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 104 | malbsMd cs_headshots_m12 under 20 | 23 | 0.5638 (Low) | pass | model 54%, hist 64% | correlated | correlated | same game script as #94 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 108 | salazar cs_headshots_m12 over 9.5 | 8 | 0.5460 (Low) | pass | model 52%, hist 53% | correlated | correlated | same game script as #101 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 109 | NickyB cs_headshots_m12 over 13.5 | 13 | 0.5977 (Medium) | lean | model 57%, hist 67% | correlated | correlated | same game script as #101 (variance); own read: variance; closest possible loss (missed by the minimum) |
| 112 | SkulL cs_kills_m12 under 30.5 | 32 | 0.7284 (High) | lean | model 72%, hist 80% | variance | model bias | root leg of a 3-leg script loss: #112, #117, #138; closest possible loss (missed by the minimum) |
| 117 | ju1ces cs_kills_m12 under 30.5 | 35 | 0.6748 (High) | lean | model 66%, hist 75% | correlated | correlated | same game script as #112 (variance); own read: variance |
| 124 | detr0ittJ cs_headshots_m12 under 11.5 | 13 | 0.6101 (Medium) | lean | model 61%, hist 59% | variance | variance | root leg of a 11-leg script loss: #124, #125, #126, #127, #128, #129, #131, #137, #139, #148, #155 |
| 125 | gbb cs_kills_m12 under 31.5 | 42 | 0.5802 (Medium) | lean | model 60%, hist 63% | correlated | correlated | same game script as #124 (variance); own read: variance |
| 126 | PKL cs_headshots_m12 under 13.0 | 14 | 0.6057 (Medium) | lean | model 60%, hist 60% | correlated | correlated | same game script as #124 (variance); own read: variance |
| 127 | detr0ittJ cs_kills_m12 under 29.0 | 33 | 0.5749 (Low) | lean | model 60%, hist 60% | correlated | correlated | same game script as #124 (variance); own read: variance |
| 128 | PKL cs_kills_m12 under 24.5 | 25 | 0.5735 (Low) | lean | model 60%, hist 59% | correlated | correlated | same game script as #124 (variance); own read: variance; closest possible loss (missed by the minimum) |
| 129 | gbb cs_headshots_m12 under 16.5 | 27 | 0.6032 (Low) | pass | model 62%, hist 48% (against) | correlated | correlated | same game script as #124 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 131 | drg cs_headshots_m12 under 16.5 | 20 | 0.5869 (Medium) | lean | model 59%, hist 50% (against) | correlated | correlated | same game script as #124 (variance); own read: variance |
| 134 | sirah cs_headshots_m12 under 17.5 | 18 | 0.5827 (Medium) | lean | model 57%, hist 56% | variance | variance | root leg of a 9-leg script loss: #134, #141, #142, #144, #147, #149, #150, #151, #153; closest possible loss (missed by the minimum) |
| 137 | destiny cs_headshots_m12 under 14.5 | 27 | 0.5683 (Low) | pass | model 57%, hist 48% (against) | correlated | correlated | same game script as #124 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 138 | ju1ces cs_headshots_m12 under 14.5 | 21 | 0.5756 (Low) | pass | model 54%, hist 65% | correlated | correlated | same game script as #112 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 139 | destiny cs_kills_m12 under 30.0 | 52 | 0.5441 (Low) | pass | model 59%, hist 38% (against) | correlated | correlated | same game script as #124 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 141 | sinnopsyy cs_headshots_m12 over 14.5 | 7 | 0.5692 (Low) | pass | model 54%, hist 59% | correlated | correlated | same game script as #134 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 142 | 0SAMAS cs_kills_m12 over 27.5 | 24 | 0.5622 (Low) | pass | model 52%, hist 68% | correlated | correlated | same game script as #134 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 144 | CacaNito cs_kills_m12 over 30.5 | 22 | 0.5574 (Low) | pass | model 50%, hist 73% | correlated | correlated | same game script as #134 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 147 | 0SAMAS cs_headshots_m12 over 15.5 | 9 | 0.5496 (Low) | pass | model 50%, hist 68% | correlated | correlated | same game script as #134 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 148 | drg cs_kills_m12 under 28.5 | 31 | 0.5057 (Low) | pass | model 53%, hist 50% (against) | correlated | correlated | same game script as #124 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 149 | Gizmy cs_kills_m12 over 26.5 | 17 | 0.5391 (Low) | pass | model 51%, hist 55% | correlated | correlated | same game script as #134 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 150 | m1N1 cs_kills_m12 over 30.5 | 15 | 0.5384 (Low) | pass | model 48% (against), hist 73% | correlated | correlated | same game script as #134 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 151 | sinnopsyy cs_kills_m12 over 26.5 | 16 | 0.5347 (Low) | pass | model 50% (against), hist 59% | correlated | correlated | same game script as #134 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 152 | MIstR cs_headshots_m12 over 14.5 | 11 | 0.5336 (Low) | pass | model 50% (against), hist 61% | correlated | correlated | same game script as #101 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 153 | Gizmy cs_headshots_m12 over 14.0 | 8 | 0.5334 (Low) | pass | model 53%, hist 41% (against) | correlated | correlated | same game script as #134 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 155 | ckzao cs_kills_m12 under 31.5 | 32 | 0.494 (Low) | pass | model 53%, hist 25% (against) | correlated | correlated | same game script as #124 (variance); own read: variance; we priced this side at 49%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 157 | leakz cs_kills_m12 under 30.5 | 37 | 0.5227 (Low) | pass | model 51%, hist 47% (against) | correlated | correlated | same game script as #101 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 158 | EliGe cs_headshots_m12 over 19.5 | 17 | 0.4817 (Low) | pass | model 44% (against), hist 54% | correlated | correlated | same game script as #101 (variance); own read: variance; we priced this side at 48%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 165 | Freddy Peralta pitcher_hits_allowed under 3.5 | 4 | 0.529 (Low) | pass | market 52% | correlated | variance | same game script as #177 (opportunity); own read: variance; logged as a PASS: no money on it; reviewed for calibration; line: 18 outs, 25 BF, 99 pitches, 4 H, 2 BB, 6 K, 0 ER; closest possible loss (missed by the minimum) |
| 166 | Parker Messick pitcher_earned_runs over 1.5 | 0 | 0.5083 (Low) | pass | market 50% | correlated | correlated | same game script as #177 (opportunity); own read: variance; logged as a PASS: no money on it; reviewed for calibration; line: 15 outs, 22 BF, 82 pitches, 6 H, 2 BB, 3 K, 0 ER |
| 167 | Junior Caminero batter_hrr over 1.5 | 1 | 0.5092 (Low) | pass | market 50% | correlated | correlated | same game script as #177 (opportunity); own read: variance; logged as a PASS: no money on it; reviewed for calibration; 4 PA from the 3 slot; opposing starter Parker Messick went 15 outs / 0 ER; 1 of 1 H+R+RBI came off the starter, 0 off the bullpen; closest possible loss (missed by the minimum) |
| 168 | Yandy Díaz batter_hrr over 1.5 | 0 |  (Low) | pass | none logged | correlated | correlated | same game script as #177 (opportunity); own read: variance; logged as a PASS: no money on it; reviewed for calibration; 4 PA from the 1 slot; opposing starter Parker Messick went 15 outs / 0 ER |
| 177 | Patrick Bailey batter_total_bases over 0.5 | 0 |  (Low) | pass | none logged | opportunity | role/lineup | root leg of a 8-leg script loss: #165, #166, #167, #168, #177, #178, #181, #182; logged as a PASS: no money on it; reviewed for calibration; only 2 plate appearances; 2 PA from the 8 slot; opposing starter Freddy Peralta went 18 outs / 0 ER |
| 178 | Patrick Bailey batter_hits over 0.5 | 0 | 0.5171 (Low) | pass | market 51% | correlated | role/lineup | same game script as #177 (opportunity); own read: opportunity; logged as a PASS: no money on it; reviewed for calibration; only 2 plate appearances; 2 PA from the 8 slot; opposing starter Freddy Peralta went 18 outs / 0 ER |
| 181 | Brayan Rocchio batter_total_bases over 0.5 | 0 |  (Low) | pass | none logged | correlated | correlated | same game script as #177 (opportunity); own read: variance; logged as a PASS: no money on it; reviewed for calibration; 4 PA from the 9 slot; opposing starter Freddy Peralta went 18 outs / 0 ER; closest possible loss (missed by the minimum) |
| 182 | Brayan Rocchio batter_hits over 0.5 | 0 | 0.529 (Low) | pass | market 52% | correlated | correlated | same game script as #177 (opportunity); own read: variance; logged as a PASS: no money on it; reviewed for calibration; 4 PA from the 9 slot; opposing starter Freddy Peralta went 18 outs / 0 ER; closest possible loss (missed by the minimum) |
| 191 | Roman Gagliano pass_yds under 208.5 | 291.0 | 0.5389 (Low) | pass | hist 60% | variance | variance | root leg of a 5-leg script loss: #191, #192, #193, #195, #196; logged as a PASS: no money on it; reviewed for calibration |
| 192 | Antonio Martin rush_yds over 74.5 | 48.0 | 0.5389 (Low) | pass | hist 60% | correlated | correlated | same game script as #191 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 193 | Cam'Ron Lacy rec_yds over 64.5 | 34.0 | 0.5389 (Low) | pass | hist 60% | correlated | correlated | same game script as #191 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 195 | Da'Wain Lofton rec_yds over 43.5 | 40.0 | 0.576 (Low) | pass | hist 75% | correlated | correlated | same game script as #191 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 196 | Da'Wain Lofton receptions over 3.5 | 3.0 | 0.5063 (Low) | pass | hist 50% (against) | correlated | correlated | same game script as #191 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 198 | Caden Creel pass_yds over 218.5 | 214.0 | 0.5673 (Low) | pass | hist 67% | variance | variance | root leg of a 2-leg script loss: #198, #204; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 204 | Devonte Lyons rush_yds under 38.5 | 73.0 | 0.5389 (Low) | pass | hist 60% | correlated | correlated | same game script as #198 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |

Lessons:
- #86: Priced the over at 49%: correct pass; HS 17 vs 18.5
- #88: Priced the over at 47%: correct pass; missed by one HS
- #89: Correct pass (priced over at 49%); he had 26.
- #92: User entry leg we priced at 41% (Low): L20, never put a leg under break-even in an entry
- #94: CS2 kill unders now 7 of 20 vs 59% predicted (z<-2): segment auto-added to AVOID; no kill unders until the model is refit
- #95: Same Nuke/Mirage match as #94
- #98: Same Nuke/Mirage match as #94
- #101: Coin-flip pass (55%); 26 vs 26.5
- #102: Same Nuke/Mirage match as #101
- #104: Same Nuke/Mirage match as #94
- #108: Same Nuke/Mirage match as #101
- #109: Same Nuke/Mirage match as #101
- #112: Rooster stomped Fruju (16- and 19-round maps) and SkulL had 32 kills in 35 rounds (0.91 per round) against a projected median of 27. Same stomp effect as divine #14 (L21), on a roster that changed the day before.
- #117: Same Rooster stomp as #112: ju1ces 35 kills.
- #124: Ancient went to overtime (30 rounds): 6+ extra rounds sank every kill/HS under in the match
- #125: Same overtime match as #124 (Ancient 30 rounds)
- #126: Same overtime match as #124 (Ancient 30 rounds)
- #127: Same overtime match as #124 (Ancient 30 rounds)
- #128: Same overtime match as #124 (Ancient 30 rounds)
- #129: Same overtime match as #124 (Ancient 30 rounds)
- #131: Same overtime match as #124 (Ancient 30 rounds)
- #134: HS under missed by one (18 vs 17.5)
- #137: Same overtime match as #124 (Ancient 30 rounds)
- #138: Same Rooster stomp as #112; was a pass.
- #139: Same overtime match as #124 (Ancient 30 rounds)
- #141: Same Cache/Dust2 match as #134: underdog players' overs died in a 13-3 Dust2 stomp (map-winner effect, L9)
- #142: Same Cache/Dust2 match as #134: underdog players' overs died in a 13-3 Dust2 stomp (map-winner effect, L9)
- #144: Same Cache/Dust2 match as #134: underdog players' overs died in a 13-3 Dust2 stomp (map-winner effect, L9)
- #147: Same Cache/Dust2 match as #134: underdog players' overs died in a 13-3 Dust2 stomp (map-winner effect, L9)
- #148: Same overtime match as #124 (Ancient 30 rounds)
- #149: Same Cache/Dust2 match as #134: underdog players' overs died in a 13-3 Dust2 stomp (map-winner effect, L9)
- #150: Same Cache/Dust2 match as #134: underdog players' overs died in a 13-3 Dust2 stomp (map-winner effect, L9)
- #151: Same Cache/Dust2 match as #134: underdog players' overs died in a 13-3 Dust2 stomp (map-winner effect, L9)
- #152: Same Nuke/Mirage match as #101
- #153: Same Cache/Dust2 match as #134: underdog players' overs died in a 13-3 Dust2 stomp (map-winner effect, L9)
- #155: Same overtime match as #124 (Ancient 30 rounds)
- #157: Same Nuke/Mirage match as #101
- #158: Same Nuke/Mirage match as #101
- #165: Both starters dominated (Peralta 18 outs 0 ER, Messick 15 outs 0 ER); hits U3.5 missed by one
- #166: Same low-scoring ALCS script as #165 (both starters 0 ER)
- #167: Same low-scoring ALCS script as #165 (both starters 0 ER)
- #168: Same low-scoring ALCS script as #165 (both starters 0 ER)
- #177: Bailey did not start (entered in the 7th, 2 PA): log hitter props only after the lineup is posted (L5)
- #178: Same as #177: not in the starting lineup
- #181: Same low-scoring ALCS script as #165 (both starters 0 ER)
- #182: Same low-scoring ALCS script as #165 (both starters 0 ER)
- #191: History-only single source (Low): correct pass; QB threw for 291
- #192: Same CFB game script as #191
- #193: Same CFB game script as #191
- #195: Same CFB game script as #191
- #196: Same CFB game script as #191
- #198: History-only single source (Low): pass yds 214 vs 218.5
- #204: Same CFB game as #198

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

## 2026-10-12: 20 losses from 14 independent causes

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

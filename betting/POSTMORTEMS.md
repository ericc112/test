# Post-mortems

Every graded loss is examined here, including passes and Low-confidence legs. `python -m edge review` writes the diagnosis; `python -m edge tag ID "tag" --lesson "..."` confirms the cause. Tags: `variance`, `opportunity`, `correlated`, `role/lineup`, `model bias`, `market info`, `stale line`, `data error`, `format misread`.

## 2026-11-25: 50 losses from 18 independent causes

| # | Leg | Result | Our p | Action | Sources | Auto tag | Confirmed | Evidence |
|---|---|---|---|---|---|---|---|---|
| 3484 | LeBron James pra under 32.5 | 47.0 | 0.59 (Medium) | pass | model 63%, market 55% | variance | role/lineup | root leg of a 8-leg script loss: #3484, #3485, #3486, #3488, #3490, #3491, #3493, #3494; logged as a PASS: no money on it; reviewed for calibration |
| 3485 | LeBron James pr under 25.5 | 35.0 | 0.5444 (Medium) | pass | model 63%, market 54% | correlated | **untagged** | same game script as #3484 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 3486 | VJ Edgecombe pra under 24.5 | 29.0 | 0.5785 (Medium) | pass | model 51%, market 56% | correlated | **untagged** | same game script as #3484 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 3488 | VJ Edgecombe pr under 20.5 | 24.0 | 0.5411 (Medium) | pass | model 54%, market 54% | correlated | **untagged** | same game script as #3484 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 3490 | LeBron James pts under 18.5 | 25.0 | 0.557 (Medium) | pass | model 59%, market 53% | correlated | **untagged** | same game script as #3484 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 3491 | LeBron James ast under 7.0 | 12.0 | 0.6118 (Medium) | lean | model 61%, market 57% | correlated | role/lineup | same game script as #3484 (variance); own read: variance |
| 3493 | Jabari Walker reb over 5.0 | 2.0 | 0.5459 (Medium) | pass | model 50%, market 57% | correlated | **untagged** | same game script as #3484 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 3494 | VJ Edgecombe ast under 4.0 | 5.0 | 0.634 (Low) | pass | model 47% (against), market 63% | correlated | **untagged** | same game script as #3484 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 3499 | LaMelo Ball pra under 29.5 | 34.0 | 0.5454 (Medium) | pass | model 51%, market 52% | variance | **untagged** | root leg of a 5-leg script loss: #3499, #3500, #3505, #3506, #3537; logged as a PASS: no money on it; reviewed for calibration |
| 3500 | Rudy Gobert pts under 8.5 | 9.0 | 0.5445 (Medium) | pass | model 59%, market 52% | correlated | **untagged** | same game script as #3499 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 3504 | Jalen Brunson tpm over 2.5 | 2.0 | 0.5612 (Low) | pass | model 52%, market 53% | variance | **untagged** | root leg of a 4-leg script loss: #3504, #3528, #3530, #3534; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 3505 | LaMelo Ball ast under 6.0 | 8.0 | 0.5787 (Medium) | lean | model 56%, market 54% | correlated | variance | same game script as #3499 (variance); own read: variance |
| 3506 | Isaiah Hartenstein ast under 4.0 | 6.0 | 0.5765 (Medium) | pass | model 60%, market 53% | correlated | **untagged** | same game script as #3499 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 3507 | Julius Randle pra under 33.5 | 40.0 | 0.5517 (Medium) | pass | model 55%, market 52% | variance | **untagged** | root leg of a 4-leg script loss: #3507, #3508, #3509, #3513; logged as a PASS: no money on it; reviewed for calibration |
| 3508 | Day'Ron Sharpe pra under 22.5 | 30.0 | 0.5514 (Medium) | pass | model 52%, market 52% | correlated | **untagged** | same game script as #3507 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 3509 | Jaime Jaquez Jr. pra under 19.5 | 30.0 | 0.5702 (Medium) | pass | model 60%, market 53% | correlated | **untagged** | same game script as #3507 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 3513 | Tyler Herro reb over 4.0 | 2.0 | 0.5928 (Low) | pass | model 39% (against), market 65% | correlated | **untagged** | same game script as #3507 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 3514 | Rui Hachimura pra under 19.5 | 31.0 | 0.5462 (Medium) | pass | model 55%, market 51% | variance | **untagged** | root leg of a 6-leg script loss: #3514, #3516, #3517, #3518, #3519, #3544; logged as a PASS: no money on it; reviewed for calibration |
| 3516 | Kris Murray pra under 10.5 | 15.0 | 0.5459 (Medium) | pass | model 79%, market 55% | correlated | role/lineup | same game script as #3514 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 3517 | Keaton Wagler pts under 9.5 | 12.0 | 0.5541 (Medium) | pass | model 57%, market 54% | correlated | **untagged** | same game script as #3514 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 3518 | Javon Small ast over 3.5 | 1.0 | 0.5421 (Medium) | pass | model 75%, market 54% | correlated | variance | same game script as #3514 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 3519 | Kris Dunn tpm over 0.5 | 0.0 | 0.5854 (Medium) | lean | model 50% (against), market 58% | correlated | variance | same game script as #3514 (variance); own read: variance; closest possible loss (missed by the minimum) |
| 3521 | Jalen Green pra under 20.5 | 25.0 | 0.5525 (Medium) | pass | model 54%, market 52% | variance | **untagged** | root leg of a 2-leg script loss: #3521, #3522; logged as a PASS: no money on it; reviewed for calibration |
| 3522 | Khaman Maluach pts under 6.5 | 12.0 | 0.5518 (Medium) | pass | model 57%, market 53% | correlated | **untagged** | same game script as #3521 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 3523 | Devin Vassell pts under 13.5 | 18.0 | 0.5519 (Medium) | pass | model 59%, market 53% | variance | **untagged** | root leg of a 3-leg script loss: #3523, #3524, #3538; logged as a PASS: no money on it; reviewed for calibration |
| 3524 | Deni Avdija ast under 6.0 | 7.0 | 0.5545 (Medium) | lean | model 56%, market 51% | correlated | role/lineup | same game script as #3523 (variance); own read: variance |
| 3526 | De'Anthony Melton pr under 16.5 | 28.0 | 0.5441 (Medium) | pass | model 69%, market 54% | variance | **untagged** | logged as a PASS: no money on it; reviewed for calibration |
| 3528 | Meleek Thomas pts over 8.5 | 8.0 | 0.4542 (Low) | pass | model 58%, market 47% (against) | correlated | variance | same game script as #3504 (variance); own read: model bias; we priced this side at 45%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 3530 | Mikal Bridges pra under 19.5 | 29.0 | 0.5162 (Low) | pass | model 65%, market 52% | correlated | role/lineup | same game script as #3504 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 3534 | Josh Hart pa under 15.5 | 26.0 | 0.4851 (Low) | pass | model 63%, market 50% (against) | correlated | role/lineup | same game script as #3504 (variance); own read: variance; we priced this side at 49%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 3537 | Isaiah Hartenstein pa under 13.5 | 14.0 | 0.479 (Low) | pass | model 56%, market 51% | correlated | variance | same game script as #3499 (variance); own read: variance; we priced this side at 48%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 3538 | Stephon Castle pra under 32.5 | 35.0 | 0.4939 (Low) | pass | model 64%, market 49% (against) | correlated | variance | same game script as #3523 (variance); own read: model bias; we priced this side at 49%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 3540 | Brandon Miller tpm under 3.5 | 4.0 | 0.5114 (Low) | pass | model 69%, market 52% | variance | variance | logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 3544 | Max Strus pts over 7.5 | 0.0 | 0.5027 (Low) | pass | model 63%, market 52% | correlated | variance | same game script as #3514 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 3548 | Dylan Cozens nhl_sog under 2.0 | 6.0 | 0.5934 (Medium) | pass | model 57%, market 59% | variance | **untagged** | root leg of a 2-leg script loss: #3548, #3586; logged as a PASS: no money on it; reviewed for calibration |
| 3553 | Joel Hanley nhl_hits over 0.5 | 0.0 | 0.5319 (Low) | pass | model 61% | variance | **untagged** | logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 3554 | Taylor Hall nhl_sog over 1.5 | 0.0 | 0.4943 (Low) | pass | model 52%, market 54% | variance | **untagged** | root leg of a 4-leg script loss: #3554, #3563, #3564, #3570; we priced this side at 49%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 3555 | Clayton Keller nhl_assists over 0.5 | 0.0 | 0.5467 (Low) | pass | model 50%, market 53% | variance | **untagged** | logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 3563 | Logan Stankoven nhl_sog over 2.0 | 0.0 | 0.5122 (Low) | pass | model 58%, market 54% | correlated | **untagged** | same game script as #3554 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 3564 | Jalen Chatfield nhl_blocks under 1.5 | 2.0 | 0.5082 (Low) | pass | model 70%, market 55% | correlated | **untagged** | same game script as #3554 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 3565 | Filip Chytil nhl_blocks over 0.5 | 0.0 | 0.4078 (Low) | pass | model 53% | variance | **untagged** | root leg of a 2-leg script loss: #3565, #3578; we priced this side at 41%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 3566 | Martin Necas nhl_toi under 20.0 | 20.07 | 0.5807 (Low) | pass | model 75% | variance | **untagged** | root leg of a 2-leg script loss: #3566, #3581; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 3570 | Jaccob Slavin nhl_toi under 21.5 | 24.8 | 0.5468 (Low) | pass | model 60% | correlated | **untagged** | same game script as #3554 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 3574 | Josh Doan nhl_hits over 0.5 | 0.0 | 0.5312 (Low) | pass | model 61% | variance | **untagged** | logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 3577 | Cutter Gauthier nhl_sog over 4.0 | 2.0 | 0.5217 (Low) | pass | model 66%, market 53% | variance | **untagged** | root leg of a 2-leg script loss: #3577, #3585; logged as a PASS: no money on it; reviewed for calibration |
| 3578 | Andrew Copp nhl_hits over 0.5 | 0.0 | 0.5184 (Low) | pass | model 55% | correlated | **untagged** | same game script as #3565 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 3581 | Brent Burns nhl_sog under 1.5 | 2.0 | 0.5094 (Low) | pass | model 52%, market 49% (against) | correlated | **untagged** | same game script as #3566 (variance); own read: model bias; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 3582 | Timo Meier nhl_sog over 3.0 | 2.0 | 0.4934 (Low) | pass | model 66%, market 50% (against) | variance | **untagged** | we priced this side at 49%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 3585 | Alexander Wennberg nhl_blocks over 0.5 | 0.0 | 0.4156 (Low) | pass | model 57% | correlated | **untagged** | same game script as #3577 (variance); own read: variance; we priced this side at 42%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 3586 | Tim Stutzle nhl_blocks over 0.5 | 0.0 | 0.4066 (Low) | pass | model 53% | correlated | **untagged** | same game script as #3548 (variance); own read: variance; we priced this side at 41%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |

Lessons:
- #3484: LeBron 35 min vs 28 projected (L28 minutes warning fired): 25-10-12
- #3491: LeBron 35 min vs 28 projected (warning fired): 12 ast
- #3505: 8 ast in 29 min (as projected)
- #3516: Kris Murray 32 min vs 14 projected
- #3518: 1 ast in 17 min (fewer than projected)
- #3519: 0-1 from three in 22 min
- #3524: Avdija 36 min vs 30 projected; 7 ast
- #3528: 8 vs 8.5 in 16 min; priced 45%
- #3530: Mikal Bridges 37 min vs 30 projected
- #3534: Hart 36 min vs 30 projected; 11 ast
- #3537: 14 vs 13.5 in 31 min (vs 25 projected)
- #3538: 35 vs 32.5 in 34 min
- #3540: 4-9 from three in 34 min
- #3544: 0 pts on 0-5 in 21 min

Detail from the feeds:
- #3548 Dylan Cozens: error=HTTPError
- #3553 Joel Hanley: error=HTTPError
- #3554 Taylor Hall: error=HTTPError
- #3555 Clayton Keller: error=HTTPError
- #3563 Logan Stankoven: error=HTTPError
- #3564 Jalen Chatfield: error=HTTPError
- #3565 Filip Chytil: error=HTTPError
- #3566 Martin Necas: error=HTTPError
- #3570 Jaccob Slavin: error=HTTPError
- #3574 Josh Doan: error=HTTPError
- #3577 Cutter Gauthier: error=HTTPError
- #3578 Andrew Copp: error=HTTPError
- #3581 Brent Burns: error=HTTPError
- #3582 Timo Meier: error=HTTPError
- #3585 Alexander Wennberg: error=HTTPError
- #3586 Tim Stutzle: error=HTTPError

## 2026-11-24: 23 losses from 12 independent causes

| # | Leg | Result | Our p | Action | Sources | Auto tag | Confirmed | Evidence |
|---|---|---|---|---|---|---|---|---|
| 3428 | Desmond Bane pra under 24.5 | 27.0 | 0.5543 (Medium) | pass | model 53%, market 52% | variance | **untagged** | root leg of a 3-leg script loss: #3428, #3446, #3455; logged as a PASS: no money on it; reviewed for calibration |
| 3434 | Paul George pra under 28.5 | 41.0 | 0.5749 (Medium) | lean | model 60%, market 53% | variance | role/lineup | root leg of a 4-leg script loss: #3434, #3435, #3436, #3438 |
| 3435 | Trae Young pra under 25.5 | 29.0 | 0.5689 (Medium) | pass | model 57%, market 53% | correlated | **untagged** | same game script as #3434 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 3436 | Trae Young ast under 7.5 | 12.0 | 0.5466 (Medium) | pass | model 56%, market 50% (against) | correlated | **untagged** | same game script as #3434 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 3438 | Jayson Tatum ast under 6.5 | 8.0 | 0.5412 (Medium) | pass | model 53%, market 50% (against) | correlated | **untagged** | same game script as #3434 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 3440 | Christian Braun pra under 20.5 | 21.0 | 0.5518 (Medium) | lean | model 54%, market 51% | variance | variance | root leg of a 6-leg script loss: #3440, #3441, #3442, #3451, #3453, #3454; closest possible loss (missed by the minimum) |
| 3441 | Daniel Gafford pts under 9.5 | 13.0 | 0.5429 (Medium) | pass | model 60%, market 52% | correlated | **untagged** | same game script as #3440 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 3442 | Nikola Jokić ast over 9.5 | 5.0 | 0.5441 (Medium) | pass | model 57%, market 55% | correlated | **untagged** | same game script as #3440 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 3446 | Isaiah Joe reb under 2.5 | 4.0 | 0.4692 (Low) | pass | model 68% | correlated | role/lineup | same game script as #3428 (variance); own read: variance; we priced this side at 47%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 3451 | Daniel Gafford ra under 8.5 | 9.0 | 0.5343 (Low) | pass | model 63%, market 55% | correlated | variance | same game script as #3440 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 3453 | Cameron Johnson pa under 15.5 | 20.0 | 0.501 (Low) | pass | model 52%, market 55% | correlated | role/lineup | same game script as #3440 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 3454 | Jamal Murray pts over 22.5 | 20.0 | 0.5139 (Low) | pass | model 63%, market 52% | correlated | variance | same game script as #3440 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 3455 | Isaiah Joe pra under 15.5 | 25.0 | 0.5 (Low) | pass | model 63%, market 50% (against) | correlated | role/lineup | same game script as #3428 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 3456 | Nikita Kucherov nhl_sog under 2.5 | 3.0 | 0.5233 (Low) | pass | model 59% | variance | **untagged** | logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 3458 | Filip Forsberg nhl_sog under 2.5 | 3.0 | 0.5155 (Low) | pass | model 55% | variance | **untagged** | logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 3470 | Tage Thompson nhl_sog over 3.5 | 2.0 | 0.4695 (Low) | pass | model 54% | variance | **untagged** | root leg of a 2-leg script loss: #3470, #3474; we priced this side at 47%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 3472 | Dylan Guenther nhl_sog under 2.5 | 3.0 | 0.5115 (Low) | pass | model 53% | variance | **untagged** | logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 3473 | Bobby McMann nhl_sog under 2.5 | 3.0 | 0.5071 (Low) | pass | model 51% | variance | **untagged** | logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 3474 | Rasmus Dahlin nhl_sog over 2.5 | 2.0 | 0.4564 (Low) | pass | model 48% (against) | correlated | **untagged** | same game script as #3470 (variance); own read: variance; we priced this side at 46%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 3477 | Fraser Minten nhl_sog under 1.5 | 2.0 | 0.508 (Low) | pass | model 51% | variance | **untagged** | logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 3478 | Jakob Chychrun nhl_sog over 2.5 | 2.0 | 0.4693 (Low) | pass | model 54% | variance | **untagged** | we priced this side at 47%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 3479 | Anton Shepp tennis_games under 22.5 | 23.0 | 0.5818 (Low) | pass | model 58% | variance | **untagged** | logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 3481 | Matthew Dellavedova tennis_games under 21.5 | 29.0 | 0.5479 (Low) | pass | model 54% | variance | **untagged** | logged as a PASS: no money on it; reviewed for calibration |

Lessons:
- #3434: Paul George 33 min vs 27 projected; 28 pts on 6-9 from three, 9 ast
- #3440: 21 vs 20.5 in 29 min
- #3446: Isaiah Joe 30 min vs 17 projected
- #3451: 27 min vs 22 projected; 9 vs 8.5
- #3453: Cameron Johnson 34 min vs 28 projected
- #3454: 6-17 FG in 36 min (as projected)
- #3455: Isaiah Joe 30 min vs 17 projected; 21 pts

Detail from the feeds:
- #3456 Nikita Kucherov: error=HTTPError
- #3458 Filip Forsberg: error=HTTPError
- #3470 Tage Thompson: error=HTTPError
- #3472 Dylan Guenther: error=HTTPError
- #3473 Bobby McMann: error=HTTPError
- #3474 Rasmus Dahlin: error=HTTPError
- #3477 Fraser Minten: error=HTTPError
- #3478 Jakob Chychrun: error=HTTPError

## 2026-11-23: 60 losses from 20 independent causes

| # | Leg | Result | Our p | Action | Sources | Auto tag | Confirmed | Evidence |
|---|---|---|---|---|---|---|---|---|
| 3306 | Coby White pra under 24.5 | 26.0 | 0.5511 (Medium) | pass | model 50% (against), market 51% | variance | **untagged** | root leg of a 2-leg script loss: #3306, #3309; logged as a PASS: no money on it; reviewed for calibration |
| 3309 | Naz Reid reb over 8.0 | 6.0 | 0.5462 (Medium) | pass | model 55%, market 55% | correlated | **untagged** | same game script as #3306 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 3313 | Donovan Clingan pra under 24.5 | 38.0 | 0.5568 (Medium) | pass | model 53%, market 51% | variance | **untagged** | root leg of a 6-leg script loss: #3313, #3314, #3315, #3320, #3321, #3387; logged as a PASS: no money on it; reviewed for calibration |
| 3314 | VJ Edgecombe pra under 22.5 | 26.0 | 0.5759 (Medium) | lean | model 58%, market 52% | correlated | role/lineup | same game script as #3313 (variance); own read: variance |
| 3315 | Jrue Holiday pra under 21.5 | 25.0 | 0.5431 (Medium) | pass | model 48% (against), market 50% | correlated | **untagged** | same game script as #3313 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 3320 | Donovan Clingan pts under 11.5 | 15.0 | 0.5487 (Medium) | pass | model 52%, market 54% | correlated | **untagged** | same game script as #3313 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 3321 | Deni Avdija ast under 6.0 | 7.0 | 0.5535 (Medium) | pass | model 51%, market 50% (against) | correlated | **untagged** | same game script as #3313 (variance); own read: model bias; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 3325 | Danny Wolf pra under 16.5 | 20.0 | 0.556 (Medium) | pass | model 49% (against), market 52% | variance | **untagged** | root leg of a 5-leg script loss: #3325, #3326, #3328, #3329, #3381; logged as a PASS: no money on it; reviewed for calibration |
| 3326 | Jaden McDaniels ra under 9.0 | 16.0 | 0.554 (Medium) | pass | model 51%, market 60% | correlated | **untagged** | same game script as #3325 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 3328 | Ayo Dosunmu ast under 4.0 | 5.0 | 0.6086 (Medium) | lean | model 59%, market 55% | correlated | variance | same game script as #3325 (variance); own read: variance |
| 3329 | Day'Ron Sharpe ast under 3.5 | 7.0 | 0.5722 (Medium) | pass | model 50% (against), market 53% | correlated | **untagged** | same game script as #3325 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 3330 | Ivica Zubac pra under 22.5 | 30.0 | 0.5596 (Medium) | pass | model 54%, market 51% | variance | **untagged** | root leg of a 4-leg script loss: #3330, #3331, #3332, #3372; logged as a PASS: no money on it; reviewed for calibration |
| 3331 | Kelly Oubre Jr. pra under 18.5 | 26.0 | 0.5548 (Medium) | pass | model 56%, market 50% (against) | correlated | **untagged** | same game script as #3330 (variance); own read: model bias; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 3332 | Ivica Zubac pts under 11.5 | 14.0 | 0.5436 (Medium) | pass | model 57%, market 52% | correlated | **untagged** | same game script as #3330 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 3333 | Jakob Poeltl pra under 20.5 | 28.0 | 0.5564 (Medium) | pass | model 56%, market 50% | variance | **untagged** | root leg of a 10-leg script loss: #3333, #3334, #3337, #3338, #3339, #3340, #3342, #3343, #3344, #3345; logged as a PASS: no money on it; reviewed for calibration |
| 3334 | Brayden Burries pra under 19.5 | 28.0 | 0.5652 (Medium) | pass | model 58%, market 51% | correlated | **untagged** | same game script as #3333 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 3337 | Myles Turner pra under 14.5 | 39.0 | 0.5549 (Medium) | pass | model 56%, market 50% (against) | correlated | **untagged** | same game script as #3333 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 3338 | Kyle Kuzma pts under 11.5 | 18.0 | 0.5492 (Medium) | pass | model 56%, market 53% | correlated | **untagged** | same game script as #3333 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 3339 | Jamal Shead pts under 8.5 | 11.0 | 0.5488 (Medium) | pass | model 58%, market 53% | correlated | **untagged** | same game script as #3333 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 3340 | Scottie Barnes reb over 7.0 | 5.0 | 0.5448 (Medium) | pass | model 58%, market 54% | correlated | **untagged** | same game script as #3333 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 3342 | Scottie Barnes ast under 5.5 | 8.0 | 0.5405 (Medium) | pass | model 49% (against), market 49% (against) | correlated | variance | same game script as #3333 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 3343 | Tyler Herro ast under 4.0 | 8.0 | 0.5596 (Medium) | pass | model 57%, market 49% (against) | correlated | **untagged** | same game script as #3333 (variance); own read: model bias; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 3344 | Immanuel Quickley reb over 3.5 | 3.0 | 0.5407 (Medium) | pass | model 57%, market 54% | correlated | **untagged** | same game script as #3333 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 3345 | Brayden Burries ast under 2.5 | 4.0 | 0.5627 (Medium) | pass | model 54%, market 50% | correlated | **untagged** | same game script as #3333 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 3346 | Miles Bridges pra under 23.5 | 30.0 | 0.5515 (Medium) | pass | model 53%, market 50% | variance | **untagged** | root leg of a 6-leg script loss: #3346, #3348, #3349, #3350, #3354, #3355; logged as a PASS: no money on it; reviewed for calibration |
| 3348 | Jalen Green pra under 21.5 | 28.0 | 0.5631 (Medium) | pass | model 55%, market 51% | correlated | **untagged** | same game script as #3346 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 3349 | Dillon Brooks pra under 21.5 | 28.0 | 0.586 (Medium) | pass | model 55%, market 54% | correlated | **untagged** | same game script as #3346 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 3350 | Dillon Brooks pr under 19.5 | 21.0 | 0.5464 (Medium) | pass | model 57%, market 55% | correlated | **untagged** | same game script as #3346 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 3354 | Devin Booker ast under 6.0 | 8.0 | 0.5726 (Medium) | pass | model 57%, market 51% | correlated | **untagged** | same game script as #3346 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 3355 | Jordan Goodwin reb over 4.5 | 2.0 | 0.5505 (Medium) | pass | model 61%, market 54% | correlated | **untagged** | same game script as #3346 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 3357 | Buddy Hield pra under 19.5 | 22.0 | 0.5703 (Medium) | lean | model 55%, market 52% | variance | variance | root leg of a 3-leg script loss: #3357, #3358, #3374 |
| 3358 | Meleek Thomas tpm over 1.5 | 1.0 | 0.54 (Medium) | pass | model 58%, market 52% | correlated | **untagged** | same game script as #3357 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 3359 | Darius Garland pra under 27.5 | 35.0 | 0.5594 (Medium) | pass | model 51%, market 52% | variance | **untagged** | root leg of a 3-leg script loss: #3359, #3368, #3385; logged as a PASS: no money on it; reviewed for calibration |
| 3361 | De'Andre Hunter pts under 14.5 | 15.0 | 0.5436 (Medium) | pass | model 51%, market 54% | variance | **untagged** | root leg of a 2-leg script loss: #3361, #3379; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 3366 | Jake LaRavia pra under 11.5 | 26.0 | 0.5499 (Medium) | pass | model 49% (against), market 51% | variance | **untagged** | root leg of a 3-leg script loss: #3366, #3367, #3376; logged as a PASS: no money on it; reviewed for calibration |
| 3367 | Collin Sexton ast under 2.5 | 4.0 | 0.5681 (Low) | pass | model 46% (against), market 53% | correlated | **untagged** | same game script as #3366 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 3368 | Keaton Wagler pra over 13.5 | 5.0 | 0.422 (Low) | pass | model 63%, market 48% (against) | correlated | variance | same game script as #3359 (variance); own read: model bias; we priced this side at 42%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 3372 | Isaiah Hartenstein pa under 13.5 | 21.0 | 0.4847 (Low) | pass | model 55%, market 51% | correlated | variance | same game script as #3330 (variance); own read: variance; we priced this side at 48%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 3374 | Jarrett Allen pts under 14.5 | 16.0 | 0.4989 (Low) | pass | model 54%, market 48% (against) | correlated | variance | same game script as #3357 (variance); own read: model bias; we priced this side at 50%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 3376 | Darryn Peterson ra under 9.5 | 11.0 | 0.5314 (Low) | pass | model 74%, market 53% | correlated | variance | same game script as #3366 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 3379 | Darius Acuff Jr. ra over 9.5 | 5.0 | 0.4473 (Low) | pass | model 52%, market 49% (against) | correlated | variance | same game script as #3361 (variance); own read: model bias; we priced this side at 45%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 3381 | Mikel Brown Jr. pts under 13.5 | 17.0 | 0.5125 (Low) | pass | model 61%, market 51% | correlated | role/lineup | same game script as #3325 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 3385 | Kevin Durant pra under 30.5 | 45.0 | 0.5092 (Low) | pass | model 65%, market 51% | correlated | variance | same game script as #3359 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 3387 | Sidy Cissoko pts over 6.0 | 5.0 | 0.5057 (Low) | pass | model 61%, market 53% | correlated | variance | same game script as #3313 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 3390 | Chandler Stephenson nhl_points over 0.5 | 0.0 | 0.5788 (Low) | pass | model 45% (against), market 54% | variance | **untagged** | root leg of a 2-leg script loss: #3390, #3401; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 3393 | Matt Boldy nhl_pm under 0.5 | 3.0 | 0.6126 (Low) | pass | model 63% | variance | **untagged** | logged as a PASS: no money on it; reviewed for calibration |
| 3395 | Nic Dowd nhl_hits under 3.0 | 6.0 | 0.5809 (Low) | pass | model 72% | variance | **untagged** | root leg of a 3-leg script loss: #3395, #3396, #3422; logged as a PASS: no money on it; reviewed for calibration |
| 3396 | Colton Dach nhl_hits under 2.5 | 4.0 | 0.5423 (Low) | pass | model 62% | correlated | **untagged** | same game script as #3395 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 3398 | Kent Johnson nhl_points over 0.5 | 0.0 | 0.5626 (Low) | pass | model 48% (against), market 51% | variance | **untagged** | root leg of a 2-leg script loss: #3398, #3404; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 3399 | Matias Maccelli nhl_points over 0.5 | 0.0 | 0.555 (Low) | pass | model 48% (against), market 50% | variance | **untagged** | logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 3400 | Yegor Sharangovich nhl_sog under 1.5 | 2.0 | 0.4819 (Low) | pass | model 55%, market 48% (against) | model bias | **untagged** | root leg of a 2-leg script loss: #3400, #3418; we priced this side at 48%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 3401 | Bobby McMann nhl_points under 0.5 | 1.0 | 0.523 (Low) | pass | model 62%, market 48% (against) | correlated | **untagged** | same game script as #3390 (variance); own read: model bias; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 3403 | Jack McBain nhl_blocks under 0.5 | 1.0 | 0.4507 (Low) | pass | model 56% | variance | **untagged** | root leg of a 2-leg script loss: #3403, #3409; we priced this side at 45%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 3404 | Adam Fantilli nhl_fow over 8.5 | 8.0 | 0.498 (Low) | pass | model 53% | correlated | **untagged** | same game script as #3398 (variance); own read: variance; we priced this side at 50%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 3408 | Brandt Clarke nhl_sog under 1.5 | 2.0 | 0.484 (Low) | pass | model 46% (against) | variance | **untagged** | we priced this side at 48%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 3409 | Dawson Mercer nhl_sog over 1.5 | 0.0 | 0.4753 (Low) | pass | model 48% (against), market 52% | correlated | **untagged** | same game script as #3403 (variance); own read: variance; we priced this side at 48%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 3418 | Tim Stutzle nhl_blocks over 0.5 | 0.0 | 0.4067 (Low) | pass | model 52% | correlated | **untagged** | same game script as #3400 (model bias); own read: variance; we priced this side at 41%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 3422 | Mark Stone nhl_hits over 0.5 | 0.0 | 0.5236 (Low) | pass | model 66% | correlated | **untagged** | same game script as #3395 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 3425 | Dane Sweeny tennis_games over 22.0 | 19.0 | 0.4464 (Low) | pass | model 44% (against) | variance | **untagged** | we priced this side at 45%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 3426 | Laura Samson tennis_games over 18.5 | 18.0 | 0.6052 (Low) | pass | model 60% | variance | **untagged** | logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |

Lessons:
- #3314: Edgecombe 35 min vs 29 projected (L28 minutes warning fired)
- #3328: 5 ast in 30 min (as projected)
- #3342: 38 min vs 34 projected; 8 ast
- #3357: 27 min vs 24 projected; 22 vs 19.5
- #3368: 17 min, 2 pts; priced 42%
- #3372: 30 min vs 26 projected; 18 pts on 7-12
- #3374: 6-7 FG for 16
- #3376: 29 min vs 26 projected; 11 vs 9.5
- #3379: 1 reb in 33 min; priced 45%
- #3381: Mikel Brown Jr. 29 min vs 24 projected; 4-6 from three
- #3385: Durant 32-9-4 in 33 min (vs 28 projected); 11-19 FG
- #3387: 1-3 FG in 24 min

Detail from the feeds:
- #3390 Chandler Stephenson: error=HTTPError
- #3393 Matt Boldy: error=HTTPError
- #3395 Nic Dowd: error=HTTPError
- #3396 Colton Dach: error=HTTPError
- #3398 Kent Johnson: error=HTTPError
- #3399 Matias Maccelli: error=HTTPError
- #3400 Yegor Sharangovich: error=HTTPError
- #3401 Bobby McMann: error=HTTPError
- #3403 Jack McBain: error=HTTPError
- #3404 Adam Fantilli: error=HTTPError
- #3408 Brandt Clarke: error=HTTPError
- #3409 Dawson Mercer: error=HTTPError
- #3418 Tim Stutzle: error=HTTPError
- #3422 Mark Stone: error=HTTPError

## 2026-11-22: 40 losses from 12 independent causes

| # | Leg | Result | Our p | Action | Sources | Auto tag | Confirmed | Evidence |
|---|---|---|---|---|---|---|---|---|
| 3216 | Jared McCain pra under 24.5 | 25.0 | 0.5775 (Medium) | lean | model 60%, market 52% | variance | variance | root leg of a 6-leg script loss: #3216, #3218, #3260, #3267, #3270, #3271; closest possible loss (missed by the minimum) |
| 3218 | Isaiah Hartenstein reb over 10.5 | 8.0 | 0.5444 (Medium) | pass | model 58%, market 52% | correlated | **untagged** | same game script as #3216 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 3224 | Kyrie Irving ast under 4.5 | 8.0 | 0.5747 (Medium) | pass | model 56%, market 51% | variance | variance | root leg of a 5-leg script loss: #3224, #3225, #3226, #3239, #3272; logged as a PASS: no money on it; reviewed for calibration |
| 3225 | Brice Sensabaugh reb over 3.5 | 3.0 | 0.5492 (Medium) | pass | model 58%, market 52% | correlated | **untagged** | same game script as #3224 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 3226 | Naji Marshall ast under 3.5 | 4.0 | 0.6035 (Medium) | lean | model 60%, market 54% | correlated | variance | same game script as #3224 (variance); own read: variance; closest possible loss (missed by the minimum) |
| 3227 | Matas Buzelis pra under 25.5 | 29.0 | 0.577 (Medium) | lean | model 58%, market 52% | variance | role/lineup | root leg of a 6-leg script loss: #3227, #3228, #3229, #3230, #3231, #3262 |
| 3228 | Aaron Gordon pra under 21.5 | 31.0 | 0.5646 (Medium) | pass | model 52%, market 52% | correlated | **untagged** | same game script as #3227 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 3229 | Christian Braun pra under 20.5 | 32.0 | 0.5441 (Medium) | pass | model 52%, market 50% (against) | correlated | **untagged** | same game script as #3227 (variance); own read: model bias; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 3230 | Buddy Hield pra under 17.5 | 46.0 | 0.5522 (Medium) | pass | model 53%, market 51% | correlated | **untagged** | same game script as #3227 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 3231 | Jamal Murray ast under 6.0 | 7.0 | 0.546 (Medium) | pass | model 50% (against), market 49% (against) | correlated | **untagged** | same game script as #3227 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 3236 | Goga Bitadze reb over 4.5 | 4.0 | 0.582 (Medium) | lean | model 62%, market 55% | variance | variance | root leg of a 3-leg script loss: #3236, #3237, #3242; closest possible loss (missed by the minimum) |
| 3237 | Bilal Coulibaly reb over 3.5 | 3.0 | 0.5425 (Medium) | pass | model 55%, market 52% | correlated | **untagged** | same game script as #3236 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 3239 | Darryn Peterson ast under 4.5 | 5.0 | 0.6035 (Medium) | pass | model 59%, market 54% | correlated | **untagged** | same game script as #3224 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 3242 | Kyshawn George reb over 4.0 | 3.0 | 0.5632 (Medium) | pass | model 52%, market 56% | correlated | **untagged** | same game script as #3236 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 3249 | Andrew Nembhard ast under 7.0 | 8.0 | 0.5614 (Medium) | pass | model 52%, market 50% | variance | **untagged** | root leg of a 2-leg script loss: #3249, #3254; logged as a PASS: no money on it; reviewed for calibration |
| 3251 | Gui Santos pra under 14.5 | 21.0 | 0.5796 (Medium) | lean | model 58%, market 53% | variance | variance | root leg of a 4-leg script loss: #3251, #3252, #3253, #3273 |
| 3252 | Draymond Green pts under 5.0 | 9.0 | 0.552 (Medium) | pass | model 69%, market 55% | correlated | role/lineup | same game script as #3251 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 3253 | Gui Santos ra under 6.0 | 8.0 | 0.5521 (Medium) | pass | model 58%, market 58% | correlated | **untagged** | same game script as #3251 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 3254 | Josh Hart reb under 8.5 | 11.0 | 0.4632 (Low) | pass | model 75%, market 49% (against) | correlated | role/lineup | same game script as #3249 (variance); own read: model bias; we priced this side at 46%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 3260 | Davion Mitchell pts over 14.5 | 14.0 | 0.4573 (Low) | pass | model 50% (against), market 49% (against) | correlated | variance | same game script as #3216 (variance); own read: variance; we priced this side at 46%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 3262 | Josh Giddey pr under 18.5 | 37.0 | 0.4805 (Low) | pass | model 47% (against), market 49% (against) | correlated | role/lineup | same game script as #3227 (variance); own read: variance; we priced this side at 48%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 3267 | Bam Adebayo pr under 29.5 | 39.0 | 0.5312 (Low) | pass | model 74%, market 53% | correlated | **untagged** | same game script as #3216 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 3270 | Pelle Larsson pr under 14.5 | 24.0 | 0.5163 (Low) | pass | model 64%, market 52% | correlated | variance | same game script as #3216 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 3271 | Bobby Portis Jr. pr under 13.5 | 18.0 | 0.5127 (Low) | pass | model 48% (against), market 52% | correlated | variance | same game script as #3216 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 3272 | Ace Bailey pts under 14.5 | 16.0 | 0.5104 (Low) | pass | model 65%, market 51% | correlated | role/lineup | same game script as #3224 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 3273 | Brandin Podziemski ra under 8.5 | 9.0 | 0.5018 (Low) | pass | model 61%, market 51% | correlated | role/lineup | same game script as #3251 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 3282 | Mikko Rantanen nhl_pm under 0.5 | 1.0 | 0.5734 (Low) | pass | model 60% | variance | **untagged** | root leg of a 5-leg script loss: #3282, #3291, #3298, #3299, #3301; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 3287 | Rasmus Dahlin nhl_toi over 25.0 | 21.95 | 0.4753 (Low) | pass | model 60% | variance | **untagged** | root leg of a 2-leg script loss: #3287, #3289; we priced this side at 48%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 3289 | John Carlson nhl_assists under 0.5 | 1.0 | 0.4229 (Low) | pass | model 60%, market 49% (against) | correlated | **untagged** | same game script as #3287 (variance); own read: model bias; we priced this side at 42%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 3290 | Tyler Bertuzzi nhl_sog under 1.5 | 4.0 | 0.4682 (Low) | pass | model 51%, market 51% | variance | **untagged** | root leg of a 2-leg script loss: #3290, #3296; we priced this side at 47%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 3291 | Rutger McGroarty nhl_blocks over 0.5 | 0.0 | 0.3724 (Low) | pass | model 35% (against) | correlated | **untagged** | same game script as #3282 (variance); own read: variance; we priced this side at 37%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 3294 | Leon Draisaitl nhl_fow under 9.5 | 14.0 | 0.5048 (Low) | pass | model 58% | variance | **untagged** | root leg of a 2-leg script loss: #3294, #3297; logged as a PASS: no money on it; reviewed for calibration |
| 3296 | Frank Nazar nhl_hits over 0.5 | 0.0 | 0.5251 (Low) | pass | model 64% | correlated | **untagged** | same game script as #3290 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 3297 | Leon Draisaitl nhl_sog over 3.0 | 2.0 | 0.5162 (Low) | pass | model 64%, market 56% | correlated | **untagged** | same game script as #3294 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 3298 | Sidney Crosby nhl_toi over 19.5 | 17.97 | 0.5076 (Low) | pass | model 74% | correlated | **untagged** | same game script as #3282 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 3299 | Kaedan Korczak nhl_blocks under 1.5 | 2.0 | 0.4846 (Low) | pass | model 63%, market 55% | correlated | **untagged** | same game script as #3282 (variance); own read: variance; we priced this side at 48%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 3301 | Trevor van Riemsdyk nhl_blocks under 1.5 | 2.0 | 0.4546 (Low) | pass | model 56%, market 52% | correlated | **untagged** | same game script as #3282 (variance); own read: variance; we priced this side at 45%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 3303 | Matt Boldy nhl_sog under 3.5 | 5.0 | 0.4388 (Low) | pass | model 41% (against) | variance | **untagged** | root leg of a 2-leg script loss: #3303, #3304; we priced this side at 44%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 3304 | Will Smith nhl_sog over 2.5 | 1.0 | 0.4112 (Low) | pass | model 38% (against) | correlated | **untagged** | same game script as #3303 (variance); own read: variance; we priced this side at 41%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 3305 | Rebeka Masarova tennis_first_set under 9.5 | 10.0 | 0.5849 (Low) | pass | model 58% | variance | **untagged** | logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |

Lessons:
- #3216: 25 vs 24.5 at projected minutes
- #3224: 8 ast in 27 min (fewer than projected)
- #3226: 4 vs 3.5 in 25 min
- #3227: Buzelis 38 min vs 29 projected in a 151-145 game
- #3236: 4 reb in 15 min
- #3251: 23 min vs 19 projected; 3-5 from three
- #3252: Draymond 27 min vs 21 projected; 3-6 from three
- #3254: Hart 39 min vs 30 projected
- #3260: 14 vs 14.5; priced 46%
- #3262: Giddey 41 min vs 30 projected in a 151-145 game; 23 pts, 14 reb, 22 ast
- #3270: 30 min vs 26 projected; 9-14 FG
- #3271: 21 min vs 19 projected; 8 reb
- #3272: Bailey 33 min vs 25 projected
- #3273: Podziemski 38 min vs 28 projected; 9 vs 8.5

Detail from the feeds:
- #3282 Mikko Rantanen: error=HTTPError
- #3287 Rasmus Dahlin: error=HTTPError
- #3289 John Carlson: error=HTTPError
- #3290 Tyler Bertuzzi: error=HTTPError
- #3291 Rutger McGroarty: error=HTTPError
- #3294 Leon Draisaitl: error=HTTPError
- #3296 Frank Nazar: error=HTTPError
- #3297 Leon Draisaitl: error=HTTPError
- #3298 Sidney Crosby: error=HTTPError
- #3299 Kaedan Korczak: error=HTTPError
- #3301 Trevor van Riemsdyk: error=HTTPError
- #3303 Matt Boldy: error=HTTPError
- #3304 Will Smith: error=HTTPError

## 2026-11-21: 33 losses from 14 independent causes

| # | Leg | Result | Our p | Action | Sources | Auto tag | Confirmed | Evidence |
|---|---|---|---|---|---|---|---|---|
| 3135 | Jrue Holiday pra under 21.5 | 29.0 | 0.5446 (Medium) | pass | model 54%, market 50% | variance | **untagged** | root leg of a 3-leg script loss: #3135, #3163, #3165; logged as a PASS: no money on it; reviewed for calibration |
| 3140 | Joan Beringer reb over 5.5 | 4.0 | 0.5595 (Medium) | lean | model 56%, market 55% | variance | variance |  |
| 3147 | Daniel Gafford ra under 8.5 | 13.0 | 0.5683 (Medium) | pass | model 70%, market 57% | variance | **untagged** | root leg of a 5-leg script loss: #3147, #3148, #3150, #3164, #3172; logged as a PASS: no money on it; reviewed for calibration |
| 3148 | Cooper Flagg ast under 6.0 | 8.0 | 0.5582 (Medium) | pass | model 56%, market 50% (against) | correlated | **untagged** | same game script as #3147 (variance); own read: model bias; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 3150 | Kyrie Irving reb under 4.0 | 6.0 | 0.5933 (Medium) | lean | model 60%, market 68% | correlated | variance | same game script as #3147 (variance); own read: variance |
| 3154 | Domantas Sabonis pra under 29.5 | 36.0 | 0.5436 (Medium) | pass | model 68%, market 54% | variance | **untagged** | root leg of a 4-leg script loss: #3154, #3155, #3169, #3171; logged as a PASS: no money on it; reviewed for calibration |
| 3155 | De'Andre Hunter pts under 13.5 | 20.0 | 0.5563 (Medium) | pass | model 52%, market 56% | correlated | **untagged** | same game script as #3154 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 3163 | Deni Avdija pa over 27.5 | 25.0 | 0.457 (Low) | pass | model 32% (against), market 52% | correlated | variance | same game script as #3135 (variance); own read: variance; we priced this side at 46%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 3164 | Derrick Jones Jr. pa over 10.5 | 5.0 | 0.4774 (Low) | pass | model 50% (against), market 50% | correlated | variance | same game script as #3147 (variance); own read: variance; we priced this side at 48%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 3165 | Josh Hart ra under 11.0 | 14.0 | 0.47 (Low) | pass | model 70%, market 47% (against) | correlated | role/lineup | same game script as #3135 (variance); own read: model bias; we priced this side at 47%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 3169 | Darius Acuff Jr. pa over 29.5 | 29.0 | 0.4506 (Low) | pass | model 38% (against), market 50% (against) | correlated | variance | same game script as #3154 (variance); own read: variance; we priced this side at 45%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 3171 | Zach LaVine ra over 5.5 | 3.0 | 0.4898 (Low) | pass | model 50% (against), market 56% | correlated | variance | same game script as #3154 (variance); own read: variance; we priced this side at 49%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 3172 | Daniel Gafford pra under 17.5 | 23.0 | 0.5312 (Low) | pass | model 65%, market 53% | correlated | role/lineup | same game script as #3147 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 3173 | Keldon Johnson reb over 5.0 | 4.0 | 0.5148 (Low) | pass | model 70%, market 52% | variance | opportunity | logged as a PASS: no money on it; reviewed for calibration |
| 3174 | Zach Werenski nhl_toi under 27.5 | 31.97 | 0.5818 (Low) | pass | model 83% | variance | **untagged** | logged as a PASS: no money on it; reviewed for calibration |
| 3175 | Quinton Byfield nhl_fow under 9.5 | 10.0 | 0.5707 (Low) | pass | model 71% | variance | **untagged** | root leg of a 4-leg script loss: #3175, #3180, #3181, #3205; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 3176 | Matt Kiersted nhl_pm under 0.5 | 1.0 | 0.5767 (Low) | pass | model 62% | variance | **untagged** | logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 3178 | Dylan Strome nhl_fow under 8.0 | 10.0 | 0.5678 (Low) | pass | model 69% | variance | **untagged** | root leg of a 2-leg script loss: #3178, #3206; logged as a PASS: no money on it; reviewed for calibration |
| 3179 | Victor Olofsson nhl_points over 0.5 | 0.0 | 0.5181 (Low) | pass | model 47% (against), market 50% | variance | **untagged** | logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 3180 | Quinton Byfield nhl_points under 0.5 | 1.0 | 0.539 (Low) | pass | model 66%, market 49% (against) | correlated | **untagged** | same game script as #3175 (variance); own read: model bias; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 3181 | Artem Zub nhl_blocks under 1.5 | 2.0 | 0.4923 (Low) | pass | model 59%, market 54% | correlated | **untagged** | same game script as #3175 (variance); own read: variance; we priced this side at 49%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 3183 | Nico Hischier nhl_fow under 11.5 | 12.0 | 0.5301 (Low) | pass | model 52% | variance | **untagged** | root leg of a 2-leg script loss: #3183, #3184; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 3184 | Philip Broberg nhl_blocks under 1.5 | 3.0 | 0.4456 (Low) | pass | model 54%, market 49% (against) | correlated | **untagged** | same game script as #3183 (variance); own read: model bias; we priced this side at 45%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 3188 | Nick Seeler nhl_blocks over 1.5 | 1.0 | 0.4196 (Low) | pass | model 58% | variance | **untagged** | root leg of a 2-leg script loss: #3188, #3203; we priced this side at 42%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 3191 | Kevin Stenlund nhl_fow under 9.0 | 10.0 | 0.5536 (Low) | pass | model 63% | variance | **untagged** | root leg of a 4-leg script loss: #3191, #3192, #3193, #3211; logged as a PASS: no money on it; reviewed for calibration |
| 3192 | Andrew Peeke nhl_blocks under 1.5 | 3.0 | 0.4664 (Low) | pass | model 62% | correlated | **untagged** | same game script as #3191 (variance); own read: variance; we priced this side at 47%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 3193 | Jackson LaCombe nhl_assists over 0.5 | 0.0 | 0.4727 (Low) | pass | model 40% (against), market 51% | correlated | **untagged** | same game script as #3191 (variance); own read: variance; we priced this side at 47%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 3203 | Travis Konecny nhl_sog over 1.5 | 1.0 | 0.4694 (Low) | pass | model 60%, market 52% | correlated | **untagged** | same game script as #3188 (variance); own read: variance; we priced this side at 47%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 3205 | Tim Stutzle nhl_toi over 21.75 | 19.42 | 0.4609 (Low) | pass | model 64% | correlated | **untagged** | same game script as #3175 (variance); own read: variance; we priced this side at 46%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 3206 | Elias Lindholm nhl_blocks under 0.5 | 1.0 | 0.4596 (Low) | pass | model 59% | correlated | **untagged** | same game script as #3178 (variance); own read: variance; we priced this side at 46%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 3208 | Viktor Arvidsson nhl_sog over 2.5 | 2.0 | 0.4417 (Low) | pass | model 55%, market 50% (against) | model bias | **untagged** | root leg of a 2-leg script loss: #3208, #3210; we priced this side at 44%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 3210 | Victor Eklund nhl_blocks over 0.5 | 0.0 | 0.4109 (Low) | pass | model 54% | correlated | **untagged** | same game script as #3208 (model bias); own read: variance; we priced this side at 41%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 3211 | Vincent Trocheck nhl_blocks over 0.5 | 0.0 | 0.4076 (Low) | pass | model 52% | correlated | **untagged** | same game script as #3191 (variance); own read: variance; we priced this side at 41%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |

Lessons:
- #3140: 4 reb in 16 min
- #3150: 6 reb in 35 min (vs 30 projected)
- #3163: 25 vs 27.5 in 36 min; priced 46%
- #3164: 1-7 FG; priced 48%
- #3165: Hart 35 min vs 27 projected; 8 reb, 6 ast
- #3169: 29 vs 29.5 (7-23 FG); priced 45%
- #3171: 3 reb + ast in 30 min
- #3172: Gafford 31 min vs 20 projected; 10 reb
- #3173: Keldon Johnson 23 min vs 29 projected in a 23-point win

Detail from the feeds:
- #3174 Zach Werenski: error=HTTPError
- #3175 Quinton Byfield: error=HTTPError
- #3176 Matt Kiersted: error=HTTPError
- #3178 Dylan Strome: error=HTTPError
- #3179 Victor Olofsson: error=HTTPError
- #3180 Quinton Byfield: error=HTTPError
- #3181 Artem Zub: error=HTTPError
- #3183 Nico Hischier: error=HTTPError
- #3184 Philip Broberg: error=HTTPError
- #3188 Nick Seeler: error=HTTPError
- #3191 Kevin Stenlund: error=HTTPError
- #3192 Andrew Peeke: error=HTTPError
- #3193 Jackson LaCombe: error=HTTPError
- #3203 Travis Konecny: error=HTTPError
- #3205 Tim Stutzle: error=HTTPError
- #3206 Elias Lindholm: error=HTTPError
- #3208 Viktor Arvidsson: error=HTTPError
- #3210 Victor Eklund: error=HTTPError
- #3211 Vincent Trocheck: error=HTTPError

## 2026-11-20: 42 losses from 18 independent causes

| # | Leg | Result | Our p | Action | Sources | Auto tag | Confirmed | Evidence |
|---|---|---|---|---|---|---|---|---|
| 3039 | Dyson Daniels pra under 24.0 | 29.0 | 0.5557 (Medium) | pass | model 52%, market 53% | variance | **untagged** | root leg of a 4-leg script loss: #3039, #3041, #3043, #3045; logged as a PASS: no money on it; reviewed for calibration |
| 3041 | Aaron Wiggins pra under 19.5 | 24.0 | 0.5461 (Medium) | pass | model 56%, market 51% | correlated | **untagged** | same game script as #3039 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 3043 | Dyson Daniels ast under 5.5 | 10.0 | 0.5492 (Medium) | pass | model 47% (against), market 50% | correlated | **untagged** | same game script as #3039 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 3045 | Luguentz Dort tpm over 1.5 | 0.0 | 0.5418 (Medium) | pass | model 54%, market 52% | correlated | **untagged** | same game script as #3039 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 3051 | Desmond Bane pts under 19.5 | 21.0 | 0.5516 (Medium) | pass | model 59%, market 53% | variance | **untagged** | logged as a PASS: no money on it; reviewed for calibration |
| 3060 | Kelly Oubre Jr. pts under 12.5 | 17.0 | 0.5517 (Medium) | pass | model 60%, market 53% | variance | **untagged** | root leg of a 3-leg script loss: #3060, #3093, #3096; logged as a PASS: no money on it; reviewed for calibration |
| 3061 | Shai Gilgeous-Alexander pts under 32.5 | 40.0 | 0.5407 (Medium) | pass | model 59%, market 52% | variance | **untagged** | root leg of a 5-leg script loss: #3061, #3062, #3065, #3066, #3068; logged as a PASS: no money on it; reviewed for calibration |
| 3062 | Jeremiah Fears pra under 27.5 | 33.0 | 0.5592 (Medium) | pass | model 59%, market 52% | correlated | **untagged** | same game script as #3061 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 3065 | Herbert Jones pr under 11.5 | 16.0 | 0.5443 (Medium) | pass | model 54%, market 54% | correlated | **untagged** | same game script as #3061 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 3066 | Herbert Jones pts under 8.5 | 14.0 | 0.5456 (Medium) | pass | model 53%, market 54% | correlated | **untagged** | same game script as #3061 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 3068 | Kenrich Williams ast under 1.5 | 4.0 | 0.564 (Medium) | pass | model 50%, market 52% | correlated | **untagged** | same game script as #3061 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 3071 | Nic Claxton pr under 16.5 | 18.0 | 0.6078 (Medium) | lean | model 71%, market 61% | variance | role/lineup | root leg of a 4-leg script loss: #3071, #3073, #3074, #3076 |
| 3073 | Isaac Okoro pra under 15.5 | 17.0 | 0.5451 (Medium) | pass | model 54%, market 52% | correlated | **untagged** | same game script as #3071 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 3074 | Kyshawn George ast under 4.5 | 5.0 | 0.5839 (Medium) | pass | model 50%, market 54% | correlated | **untagged** | same game script as #3071 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 3076 | AJ Dybantsa ast under 2.5 | 6.0 | 0.5723 (Medium) | pass | model 51%, market 52% | correlated | **untagged** | same game script as #3071 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 3081 | Khaman Maluach pra under 13.5 | 16.0 | 0.5435 (Medium) | pass | model 55%, market 51% | variance | **untagged** | root leg of a 4-leg script loss: #3081, #3095, #3102, #3103; logged as a PASS: no money on it; reviewed for calibration |
| 3085 | Keegan Murray ast under 1.5 | 4.0 | 0.5668 (Low) | pass | model 58% | variance | **untagged** | root leg of a 3-leg script loss: #3085, #3101, #3104; logged as a PASS: no money on it; reviewed for calibration |
| 3086 | Jamal Murray ast under 5.5 | 7.0 | 0.574 (Low) | pass | model 49% (against), market 53% | variance | **untagged** | root leg of a 2-leg script loss: #3086, #3088; logged as a PASS: no money on it; reviewed for calibration |
| 3088 | Jamal Murray tpm over 2.5 | 1.0 | 0.5419 (Medium) | pass | model 57%, market 51% | correlated | **untagged** | same game script as #3086 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 3091 | Kevin Huerter pra under 19.5 | 26.0 | 0.4939 (Low) | pass | model 59%, market 49% (against) | model bias | role/lineup | root leg of a 2-leg script loss: #3091, #3099; we priced this side at 49%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 3093 | Kelly Oubre Jr. ra under 5.5 | 6.0 | 0.5333 (Low) | pass | model 67%, market 54% | correlated | variance | same game script as #3060 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 3095 | Svi Mykhailiuk pts under 7.5 | 11.0 | 0.4965 (Low) | pass | model 43% (against), market 50% (against) | correlated | variance | same game script as #3081 (variance); own read: variance; we priced this side at 50%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 3096 | Sam Merrill pra over 10.5 | 8.0 | 0.4459 (Low) | pass | model 64%, market 51% | correlated | variance | same game script as #3060 (variance); own read: variance; we priced this side at 45%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 3099 | Javonte Green pr under 10.5 | 13.0 | 0.5217 (Low) | pass | model 57%, market 50% | correlated | role/lineup | same game script as #3091 (model bias); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 3101 | Luka Dončić tpm over 4.5 | 2.0 | 0.4667 (Low) | pass | model 47% (against), market 44% (against) | correlated | variance | same game script as #3085 (variance); own read: variance; we priced this side at 47%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 3102 | Collin Gillespie ra under 6.5 | 9.0 | 0.5215 (Low) | pass | model 50% (against), market 56% | correlated | variance | same game script as #3081 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 3103 | Jordan Goodwin pts over 7.5 | 5.0 | 0.5139 (Low) | pass | model 55%, market 55% | correlated | variance | same game script as #3081 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 3104 | Keegan Murray pts under 11.5 | 13.0 | 0.5134 (Low) | pass | model 67%, market 51% | correlated | role/lineup | same game script as #3085 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 3105 | Matthew Tkachuk nhl_assists over 0.5 | 0.0 | 0.4935 (Low) | pass | model 56% | variance | **untagged** | we priced this side at 49%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 3106 | Zayne Parekh nhl_points under 0.5 | 1.0 | 0.5941 (Medium) | lean | model 68%, market 55% | variance | **untagged** | root leg of a 3-leg script loss: #3106, #3107, #3116; closest possible loss (missed by the minimum) |
| 3107 | Roman Kantserov nhl_points under 0.5 | 2.0 | 0.5902 (Medium) | pass | model 61%, market 57% | correlated | **untagged** | same game script as #3106 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 3108 | Logan Stankoven nhl_points under 0.5 | 2.0 | 0.5254 (Low) | pass | model 55%, market 50% (against) | model bias | **untagged** | root leg of a 2-leg script loss: #3108, #3122; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 3112 | Charlie McAvoy nhl_assists under 0.5 | 3.0 | 0.4683 (Low) | pass | model 62% | variance | **untagged** | we priced this side at 47%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 3113 | Sidney Crosby nhl_assists under 0.5 | 1.0 | 0.5272 (Low) | pass | model 63%, market 57% | variance | **untagged** | root leg of a 2-leg script loss: #3113, #3119; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 3114 | Cam York nhl_blocks over 1.5 | 1.0 | 0.3933 (Low) | pass | model 45% (against) | variance | **untagged** | we priced this side at 39%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 3116 | Mikael Backlund nhl_points under 0.5 | 1.0 | 0.575 (Low) | pass | model 62%, market 55% | correlated | **untagged** | same game script as #3106 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 3118 | Bo Horvat nhl_sog over 2.5 | 2.0 | 0.4421 (Low) | pass | model 54% | variance | **untagged** | we priced this side at 44%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 3119 | Erik Karlsson nhl_points over 0.5 | 0.0 | 0.5763 (Low) | pass | model 55%, market 56% | correlated | **untagged** | same game script as #3113 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 3122 | Shayne Gostisbehere nhl_sog over 1.5 | 0.0 | 0.4414 (Low) | pass | model 54%, market 50% (against) | correlated | **untagged** | same game script as #3108 (model bias); own read: model bias; we priced this side at 44%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 3126 | Laura Samson tennis_games over 21.5 | 17.0 | 0.5047 (Low) | pass | model 44% (against), market 50% (against) | variance | **untagged** | logged as a PASS: no money on it; reviewed for calibration |
| 3133 | Ben Shelton tennis_games_won under 10.5 | 15.0 | 0.5542 (Low) | pass | model 52% | variance | **untagged** | root leg of a 2-leg script loss: #3133, #3134; logged as a PASS: no money on it; reviewed for calibration |
| 3134 | Carlos Alcaraz tennis_tiebreaks under 0.5 | 1.0 | 0.5876 (Low) | pass | model 59% | correlated | **untagged** | same game script as #3133 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |

Lessons:
- #3071: Claxton 29 min vs 18.5 projected
- #3091: Huerter 36 min vs 28 projected (L28 minutes warning fired)
- #3093: 6 vs 5.5 at projected minutes (warning fired)
- #3095: 28 min vs 24 projected; 3-4 from three
- #3096: 2-7 FG; priced 45%
- #3099: Javonte Green 23 min vs 19 projected; 3-4 from three
- #3101: 2-9 from three
- #3102: 27 min vs 24.5 projected; 5 ast
- #3103: 2-8 FG in 28 min (more than projected)
- #3104: Murray 40 min vs 24 projected

Detail from the feeds:
- #3105 Matthew Tkachuk: error=HTTPError
- #3106 Zayne Parekh: error=HTTPError
- #3107 Roman Kantserov: error=HTTPError
- #3108 Logan Stankoven: error=HTTPError
- #3112 Charlie McAvoy: error=HTTPError
- #3113 Sidney Crosby: error=HTTPError
- #3114 Cam York: error=HTTPError
- #3116 Mikael Backlund: error=HTTPError
- #3118 Bo Horvat: error=HTTPError
- #3119 Erik Karlsson: error=HTTPError
- #3122 Shayne Gostisbehere: error=HTTPError

## 2026-11-18: 60 losses from 19 independent causes

| # | Leg | Result | Our p | Action | Sources | Auto tag | Confirmed | Evidence |
|---|---|---|---|---|---|---|---|---|
| 2915 | Ivica Zubac ast under 1.5 | 4.0 | 0.5463 (Medium) | pass | model 51%, market 49% (against) | model bias | **untagged** | root leg of a 2-leg script loss: #2915, #3007; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 2917 | Brayden Burries pts under 12.5 | 20.0 | 0.5512 (Medium) | pass | model 57%, market 53% | variance | **untagged** | root leg of a 3-leg script loss: #2917, #2919, #2920; logged as a PASS: no money on it; reviewed for calibration |
| 2919 | Bam Adebayo reb over 8.0 | 4.0 | 0.5532 (Medium) | pass | model 50%, market 55% | correlated | **untagged** | same game script as #2917 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2920 | Myles Turner tpm over 1.5 | 0.0 | 0.5557 (Medium) | pass | model 56%, market 53% | correlated | **untagged** | same game script as #2917 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2922 | Wendell Carter Jr. pts under 11.5 | 15.0 | 0.5511 (Medium) | pass | model 59%, market 53% | variance | **untagged** | root leg of a 6-leg script loss: #2922, #2923, #2924, #2925, #2932, #2999; logged as a PASS: no money on it; reviewed for calibration |
| 2923 | Joel Embiid reb over 7.5 | 6.0 | 0.5492 (Medium) | pass | model 55%, market 53% | correlated | **untagged** | same game script as #2922 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2924 | Franz Wagner ast under 6.5 | 11.0 | 0.5414 (Medium) | pass | model 50%, market 49% (against) | correlated | **untagged** | same game script as #2922 (variance); own read: model bias; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 2925 | Anfernee Simons ast under 1.5 | 2.0 | 0.5688 (Medium) | pass | model 52%, market 52% | correlated | **untagged** | same game script as #2922 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2926 | Donovan Mitchell pra under 35.5 | 41.0 | 0.5441 (Medium) | pass | model 53%, market 52% | variance | **untagged** | root leg of a 7-leg script loss: #2926, #2929, #2930, #2931, #2990, #2991, #3003; logged as a PASS: no money on it; reviewed for calibration |
| 2929 | James Harden ast under 6.5 | 9.0 | 0.5604 (Medium) | pass | model 52%, market 51% | correlated | variance | same game script as #2926 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2930 | Donovan Mitchell tpm over 2.5 | 2.0 | 0.5484 (Medium) | pass | model 55%, market 52% | correlated | **untagged** | same game script as #2926 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2931 | Jaylen Wells ast under 1.5 | 2.0 | 0.5738 (Medium) | pass | model 54%, market 52% | correlated | **untagged** | same game script as #2926 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2932 | LeBron James reb over 6.5 | 3.0 | 0.5575 (Medium) | pass | model 50%, market 56% | correlated | **untagged** | same game script as #2922 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2935 | Kyshawn George pra under 23.5 | 26.0 | 0.5422 (Medium) | pass | model 52%, market 52% | variance | **untagged** | root leg of a 2-leg script loss: #2935, #2936; logged as a PASS: no money on it; reviewed for calibration |
| 2936 | Bilal Coulibaly pra under 11.5 | 13.0 | 0.5445 (Medium) | pass | model 53%, market 52% | correlated | **untagged** | same game script as #2935 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2940 | Matas Buzelis pra under 23.5 | 34.0 | 0.54 (Medium) | pass | model 55%, market 51% | variance | **untagged** | root leg of a 6-leg script loss: #2940, #2941, #2943, #2944, #2946, #2997; logged as a PASS: no money on it; reviewed for calibration |
| 2941 | Mikel Brown Jr. pra under 16.5 | 20.0 | 0.5495 (Medium) | pass | model 53%, market 52% | correlated | **untagged** | same game script as #2940 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2943 | Josh Giddey pts under 12.5 | 18.0 | 0.5449 (Medium) | pass | model 58%, market 52% | correlated | **untagged** | same game script as #2940 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2944 | Josh Giddey ast under 8.5 | 9.0 | 0.5741 (Medium) | pass | model 56%, market 51% | correlated | **untagged** | same game script as #2940 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2946 | Tre Jones ast under 4.0 | 6.0 | 0.5995 (Medium) | lean | model 57%, market 54% | correlated | variance | same game script as #2940 (variance); own read: variance |
| 2950 | Herbert Jones pts under 8.5 | 9.0 | 0.5561 (Medium) | pass | model 58%, market 54% | variance | **untagged** | root leg of a 3-leg script loss: #2950, #2953, #2994; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2953 | Kevin Huerter ast under 4.0 | 7.0 | 0.5665 (Medium) | pass | model 69%, market 57% | correlated | **untagged** | same game script as #2950 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2954 | Kenrich Williams pts under 8.5 | 10.0 | 0.5454 (Medium) | pass | model 53%, market 53% | variance | **untagged** | logged as a PASS: no money on it; reviewed for calibration |
| 2956 | P.J. Washington pr under 19.5 | 26.0 | 0.5451 (Medium) | pass | model 70%, market 55% | variance | **untagged** | root leg of a 4-leg script loss: #2956, #2957, #2960, #2962; logged as a PASS: no money on it; reviewed for calibration |
| 2957 | Gui Santos pra under 14.5 | 18.0 | 0.5622 (Medium) | pass | model 57%, market 53% | correlated | **untagged** | same game script as #2956 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2960 | Morez Johnson Jr. reb over 4.5 | 1.0 | 0.5585 (Medium) | pass | model 54%, market 55% | correlated | **untagged** | same game script as #2956 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2962 | Gui Santos ast under 1.5 | 6.0 | 0.5472 (Medium) | pass | model 48% (against), market 50% (against) | correlated | **untagged** | same game script as #2956 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2968 | DeMar DeRozan pra under 13.5 | 22.0 | 0.547 (Medium) | pass | model 53%, market 52% | variance | **untagged** | root leg of a 4-leg script loss: #2968, #2969, #2970, #3006; logged as a PASS: no money on it; reviewed for calibration |
| 2969 | Christian Braun pts under 11.5 | 15.0 | 0.5483 (Medium) | pass | model 56%, market 53% | correlated | **untagged** | same game script as #2968 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2970 | Christian Braun ra under 6.5 | 8.0 | 0.5426 (Medium) | pass | model 57%, market 57% | correlated | **untagged** | same game script as #2968 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2978 | Dillon Brooks pts under 14.5 | 29.0 | 0.544 (Medium) | pass | model 57%, market 52% | variance | **untagged** | root leg of a 3-leg script loss: #2978, #2981, #2983; logged as a PASS: no money on it; reviewed for calibration |
| 2981 | Oso Ighodaro reb over 5.0 | 4.0 | 0.5536 (Medium) | pass | model 60%, market 53% | correlated | variance | same game script as #2978 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2983 | Dillon Brooks ast under 1.5 | 5.0 | 0.5469 (Medium) | pass | model 44% (against), market 51% | correlated | **untagged** | same game script as #2978 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2985 | Keyonte George ast under 7.0 | 10.0 | 0.5522 (Medium) | pass | model 53%, market 49% (against) | model bias | **untagged** | root leg of a 3-leg script loss: #2985, #2986, #2995; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 2986 | Jake LaRavia tpm over 0.5 | 0.0 | 0.5409 (Medium) | pass | model 51%, market 52% | correlated | **untagged** | same game script as #2985 (model bias); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2990 | Cam Spencer pa under 21.5 | 33.0 | 0.4422 (Low) | pass | model 58%, market 48% (against) | correlated | variance | same game script as #2926 (variance); own read: model bias; we priced this side at 44%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 2991 | Javon Small ra under 8.5 | 9.0 | 0.4988 (Low) | pass | model 55%, market 52% | correlated | variance | same game script as #2926 (variance); own read: variance; we priced this side at 50%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2994 | Daniss Jenkins ra under 11.5 | 13.0 | 0.5086 (Low) | pass | model 62%, market 52% | correlated | variance | same game script as #2950 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2995 | Luka Dončić tpm over 4.5 | 2.0 | 0.4913 (Low) | pass | model 39% (against), market 49% (against) | correlated | variance | same game script as #2985 (model bias); own read: variance; we priced this side at 49%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 2997 | Josh Giddey pr under 18.5 | 32.0 | 0.4929 (Low) | pass | model 61%, market 49% (against) | correlated | variance | same game script as #2940 (variance); own read: model bias; we priced this side at 49%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 2999 | Tristan da Silva pra over 16.0 | 14.0 | 0.4222 (Low) | pass | model 55%, market 50% | correlated | variance | same game script as #2922 (variance); own read: variance; we priced this side at 42%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 3003 | Jarrett Allen pra under 24.5 | 32.0 | 0.5338 (Low) | pass | model 56%, market 50% (against) | correlated | variance | same game script as #2926 (variance); own read: model bias; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 3006 | Derrick White pra under 21.5 | 23.0 | 0.5232 (Low) | pass | model 64%, market 52% | correlated | role/lineup | same game script as #2968 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 3007 | Kelly Oubre Jr. pts under 12.5 | 17.0 | 0.5062 (Low) | pass | model 65%, market 51% | correlated | variance | same game script as #2915 (model bias); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 3011 | Kevin Stenlund nhl_fow under 9.0 | 15.0 | 0.578 (Low) | pass | model 74% | variance | **untagged** | root leg of a 4-leg script loss: #3011, #3019, #3026, #3033; logged as a PASS: no money on it; reviewed for calibration |
| 3013 | Evan Bouchard nhl_sog under 2.5 | 4.0 | 0.4597 (Low) | pass | model 64% | variance | **untagged** | we priced this side at 46%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 3019 | Lawson Crouse nhl_hits under 2.5 | 4.0 | 0.4778 (Low) | pass | model 46% (against) | correlated | **untagged** | same game script as #3011 (variance); own read: variance; we priced this side at 48%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 3021 | Lane Hutson nhl_sog over 1.5 | 0.0 | 0.4609 (Low) | pass | model 56%, market 52% | variance | **untagged** | root leg of a 3-leg script loss: #3021, #3024, #3029; we priced this side at 46%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 3022 | Elias Lindholm nhl_points over 0.5 | 0.0 | 0.5221 (Low) | pass | model 46% (against), market 51% | variance | **untagged** | root leg of a 5-leg script loss: #3022, #3023, #3027, #3030, #3031; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 3023 | Pavel Zacha nhl_sog under 1.5 | 3.0 | 0.4231 (Low) | pass | model 51%, market 49% (against) | correlated | **untagged** | same game script as #3022 (variance); own read: model bias; we priced this side at 42%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 3024 | Arseny Gritsyuk nhl_points over 0.5 | 0.0 | 0.5135 (Low) | pass | model 45% (against), market 50% | correlated | **untagged** | same game script as #3021 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 3026 | Nazem Kadri nhl_hits under 0.5 | 1.0 | 0.5164 (Low) | pass | model 64% | correlated | **untagged** | same game script as #3011 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 3027 | Connor Clifton nhl_hits over 2.5 | 1.0 | 0.5135 (Low) | pass | model 65% | correlated | **untagged** | same game script as #3022 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 3029 | Jack Hughes nhl_assists over 0.5 | 0.0 | 0.5038 (Low) | pass | model 52%, market 52% | correlated | **untagged** | same game script as #3021 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 3030 | Elias Lindholm nhl_hits over 0.5 | 0.0 | 0.4867 (Low) | pass | model 52% | correlated | **untagged** | same game script as #3022 (variance); own read: variance; we priced this side at 49%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 3031 | Alex DeBrincat nhl_blocks under 0.5 | 2.0 | 0.469 (Low) | pass | model 63% | correlated | **untagged** | same game script as #3022 (variance); own read: variance; we priced this side at 47%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 3033 | Brock Nelson nhl_blocks over 0.5 | 0.0 | 0.4093 (Low) | pass | model 53% | correlated | **untagged** | same game script as #3011 (variance); own read: variance; we priced this side at 41%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 3034 | Rickard Rakell nhl_sog under 2.5 | 7.0 | 0.432 (Low) | pass | model 51% | variance | **untagged** | we priced this side at 43%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 3035 | William Nylander nhl_sog over 2.5 | 1.0 | 0.4161 (Low) | pass | model 41% (against) | variance | **untagged** | we priced this side at 42%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 3038 | Pierre-Hugues Herbert tennis_games under 23.5 | 33.0 | 0.5774 (Low) | pass | model 61% | variance | **untagged** | logged as a PASS: no money on it; reviewed for calibration |

Lessons:
- #2929: 36 min vs 32 projected; 9 ast
- #2946: 6 ast in 16 min (fewer minutes than projected)
- #2981: 4 reb in 21 min
- #2990: 26 pts on 9-11; priced 44%
- #2991: 9 vs 8.5 in 21 min
- #2994: 36 min as projected; 9 ast
- #2995: 2-12 from three
- #2997: 28 min as projected; 14 reb, 9 ast
- #2999: 14 vs 16; priced 42%
- #3003: 30 min vs 27 projected; 19 pts
- #3006: Derrick White 35 min vs 26 projected
- #3007: 23 min as projected; 7-10 FG

Detail from the feeds:
- #3011 Kevin Stenlund: error=HTTPError
- #3013 Evan Bouchard: error=HTTPError
- #3019 Lawson Crouse: error=HTTPError
- #3021 Lane Hutson: error=HTTPError
- #3022 Elias Lindholm: error=HTTPError
- #3023 Pavel Zacha: error=HTTPError
- #3024 Arseny Gritsyuk: error=HTTPError
- #3026 Nazem Kadri: error=HTTPError
- #3027 Connor Clifton: error=HTTPError
- #3029 Jack Hughes: error=HTTPError
- #3030 Elias Lindholm: error=HTTPError
- #3031 Alex DeBrincat: error=HTTPError
- #3033 Brock Nelson: error=HTTPError
- #3034 Rickard Rakell: error=HTTPError
- #3035 William Nylander: error=HTTPError

## 2026-11-17: 35 losses from 15 independent causes

| # | Leg | Result | Our p | Action | Sources | Auto tag | Confirmed | Evidence |
|---|---|---|---|---|---|---|---|---|
| 2834 | Ja'Kobe Walter pts under 11.0 | 25.0 | 0.5512 (Medium) | pass | model 57%, market 53% | variance | **untagged** | root leg of a 4-leg script loss: #2834, #2835, #2862, #2867; logged as a PASS: no money on it; reviewed for calibration |
| 2835 | Immanuel Quickley ast under 5.0 | 7.0 | 0.5818 (Medium) | lean | model 59%, market 51% | correlated | role/lineup | same game script as #2834 (variance); own read: variance |
| 2839 | Dylan Harper pr under 21.5 | 24.0 | 0.5537 (Medium) | pass | model 57%, market 54% | variance | **untagged** | root leg of a 7-leg script loss: #2839, #2841, #2842, #2843, #2855, #2864, #2870; logged as a PASS: no money on it; reviewed for calibration |
| 2841 | Dylan Harper pts under 16.5 | 20.0 | 0.5476 (Medium) | pass | model 56%, market 53% | correlated | **untagged** | same game script as #2839 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2842 | Keldon Johnson pts over 8.5 | 4.0 | 0.559 (Medium) | pass | model 66%, market 56% | correlated | **untagged** | same game script as #2839 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2843 | Stephon Castle ast under 5.5 | 7.0 | 0.5759 (Medium) | lean | model 53%, market 52% | correlated | role/lineup | same game script as #2839 (variance); own read: variance |
| 2846 | Keyonte George pts under 22.5 | 30.0 | 0.5469 (Medium) | lean | model 52%, market 54% | variance | variance | root leg of a 3-leg script loss: #2846, #2854, #2858 |
| 2848 | Naz Reid pts under 17.5 | 23.0 | 0.5443 (Medium) | pass | model 57%, market 52% | variance | **untagged** | root leg of a 3-leg script loss: #2848, #2850, #2861; logged as a PASS: no money on it; reviewed for calibration |
| 2850 | Quentin Grimes pts under 13.5 | 47.0 | 0.5544 (Medium) | pass | model 60%, market 53% | correlated | variance | same game script as #2848 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2854 | Mo Bamba ra under 11.5 | 13.0 | 0.4963 (Low) | pass | model 77%, market 50% (against) | correlated | role/lineup | same game script as #2846 (variance); own read: model bias; we priced this side at 50%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 2855 | Javonte Green pr under 10.5 | 12.0 | 0.494 (Low) | pass | model 44% (against) | correlated | variance | same game script as #2839 (variance); own read: variance; we priced this side at 49%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 2857 | Jaden McDaniels reb over 5.5 | 5.0 | 0.5081 (Low) | pass | model 52%, market 49% (against) | model bias | variance | logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 2858 | Brice Sensabaugh pra under 20.5 | 56.0 | 0.5272 (Low) | pass | model 55%, market 50% (against) | correlated | role/lineup | same game script as #2846 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2861 | Ziaire Williams pa over 10.5 | 1.0 | 0.4807 (Low) | pass | model 60%, market 49% (against) | correlated | variance | same game script as #2848 (variance); own read: model bias; we priced this side at 48%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 2862 | Scottie Barnes pts over 21.5 | 20.0 | 0.4268 (Low) | pass | model 36% (against), market 46% (against) | correlated | variance | same game script as #2834 (variance); own read: variance; we priced this side at 43%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 2864 | Paul Reed pra under 20.5 | 21.0 | 0.4906 (Low) | pass | model 30% (against), market 52% | correlated | variance | same game script as #2839 (variance); own read: variance; we priced this side at 49%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2867 | Karl-Anthony Towns pts over 20.5 | 16.0 | 0.4884 (Low) | pass | model 48% (against), market 51% | correlated | variance | same game script as #2834 (variance); own read: variance; we priced this side at 49%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 2870 | Keldon Johnson reb over 5.0 | 2.0 | 0.5093 (Low) | pass | model 60%, market 51% | correlated | role/lineup | same game script as #2839 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2872 | Mikhail Sergachev nhl_sog over 2.5 | 2.0 | 0.4525 (Low) | pass | model 49% (against) | variance | **untagged** | we priced this side at 45%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2877 | Joel Eriksson Ek nhl_pm under 0.5 | 3.0 | 0.5844 (Low) | pass | model 63% | variance | **untagged** | root leg of a 2-leg script loss: #2877, #2897; logged as a PASS: no money on it; reviewed for calibration |
| 2879 | Victor Olofsson nhl_points over 0.5 | 0.0 | 0.5125 (Low) | pass | model 41% (against), market 52% | variance | **untagged** | root leg of a 2-leg script loss: #2879, #2880; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2880 | Mitch Marner nhl_assists over 0.5 | 0.0 | 0.52 (Low) | pass | model 49% (against), market 52% | correlated | **untagged** | same game script as #2879 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2886 | Connor Bedard nhl_assists over 0.5 | 0.0 | 0.5059 (Low) | pass | model 49% (against), market 50% | variance | **untagged** | root leg of a 3-leg script loss: #2886, #2891, #2893; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2887 | Josh Morrissey nhl_toi under 24.25 | 25.92 | 0.4934 (Low) | pass | model 51% | variance | **untagged** | root leg of a 2-leg script loss: #2887, #2902; we priced this side at 49%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 2891 | Darren Raddysh nhl_sog under 2.5 | 3.0 | 0.4487 (Low) | pass | model 50%, market 54% | correlated | **untagged** | same game script as #2886 (variance); own read: variance; we priced this side at 45%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2892 | Michael Misa nhl_sog under 1.5 | 3.0 | 0.3915 (Low) | pass | model 49% (against), market 48% (against) | variance | **untagged** | we priced this side at 39%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 2893 | Artyom Levshunov nhl_hits under 1.5 | 2.0 | 0.4725 (Low) | pass | model 50% | correlated | **untagged** | same game script as #2886 (variance); own read: variance; we priced this side at 47%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2894 | David Pastrnak nhl_assists over 0.5 | 0.0 | 0.5443 (Low) | pass | model 53%, market 54% | variance | **untagged** | root leg of a 2-leg script loss: #2894, #2899; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2896 | Rasmus Dahlin nhl_assists under 0.5 | 1.0 | 0.5338 (Low) | pass | model 60%, market 52% | variance | **untagged** | logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2897 | Matt Boldy nhl_assists under 0.5 | 1.0 | 0.5274 (Low) | pass | model 61%, market 51% | correlated | **untagged** | same game script as #2877 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2899 | Michael Eyssimont nhl_sog over 1.5 | 1.0 | 0.4823 (Low) | pass | model 54%, market 52% | correlated | **untagged** | same game script as #2894 (variance); own read: variance; we priced this side at 48%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2900 | Bo Horvat nhl_toi over 20.75 | 17.82 | 0.4712 (Low) | pass | model 62% | variance | **untagged** | root leg of a 2-leg script loss: #2900, #2901; we priced this side at 47%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 2901 | Mathieu Olivier nhl_sog over 1.5 | 0.0 | 0.4542 (Low) | pass | model 55%, market 49% (against) | correlated | **untagged** | same game script as #2900 (variance); own read: model bias; we priced this side at 45%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 2902 | Tim Stutzle nhl_toi over 21.5 | 21.08 | 0.4542 (Low) | pass | model 54% | correlated | **untagged** | same game script as #2887 (variance); own read: variance; we priced this side at 45%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2904 | Ryan Shea nhl_blocks over 1.5 | 0.0 | 0.4274 (Low) | pass | model 50%, market 52% | variance | **untagged** | we priced this side at 43%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |

Lessons:
- #2835: Quickley 34 min vs 27 projected (L28 minutes warning fired)
- #2843: Castle 31 min vs 26 projected
- #2846: 35 min as projected; 30 pts
- #2850: Grimes 47 pts on 10-14 from three in 42 min (vs 32 projected): a career night
- #2854: Bamba 31 min vs 24 projected
- #2855: 23 min as projected; 12 vs 10.5
- #2857: 37 min (the over got its minutes); 5 reb
- #2858: Sensabaugh 35 min vs 23 projected; 40 pts on 16-21
- #2861: 0 pts in 24 min
- #2862: 20 vs 21.5; priced 43%
- #2864: 21 vs 20.5 in 25 min (fewer than projected)
- #2867: 7-9 FG for 16; 16 reb
- #2870: Keldon Johnson 15 min vs 25 projected

Detail from the feeds:
- #2872 Mikhail Sergachev: error=HTTPError
- #2877 Joel Eriksson Ek: error=HTTPError
- #2879 Victor Olofsson: error=HTTPError
- #2880 Mitch Marner: error=HTTPError
- #2886 Connor Bedard: error=HTTPError
- #2887 Josh Morrissey: error=HTTPError
- #2891 Darren Raddysh: error=HTTPError
- #2892 Michael Misa: error=HTTPError
- #2893 Artyom Levshunov: error=HTTPError
- #2894 David Pastrnak: error=HTTPError
- #2896 Rasmus Dahlin: error=HTTPError
- #2897 Matt Boldy: error=HTTPError
- #2899 Michael Eyssimont: error=HTTPError
- #2900 Bo Horvat: error=HTTPError
- #2901 Mathieu Olivier: error=HTTPError
- #2902 Tim Stutzle: error=HTTPError
- #2904 Ryan Shea: error=HTTPError

## 2026-11-16: 49 losses from 16 independent causes

| # | Leg | Result | Our p | Action | Sources | Auto tag | Confirmed | Evidence |
|---|---|---|---|---|---|---|---|---|
| 2720 | Cedric Coward pra under 27.5 | 32.0 | 0.5498 (Medium) | pass | model 50% (against), market 52% | variance | **untagged** | root leg of a 5-leg script loss: #2720, #2721, #2724, #2725, #2774; logged as a PASS: no money on it; reviewed for calibration |
| 2721 | Cam Spencer pra under 24.5 | 27.0 | 0.5453 (Medium) | pass | model 56%, market 50% (against) | correlated | role/lineup | same game script as #2720 (variance); own read: model bias; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 2724 | Trae Young ast under 8.5 | 12.0 | 0.5702 (Medium) | pass | model 54%, market 50% | correlated | **untagged** | same game script as #2720 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2725 | Cam Spencer ast under 7.5 | 9.0 | 0.59 (Medium) | lean | model 59%, market 51% | correlated | role/lineup | same game script as #2720 (variance); own read: variance |
| 2726 | Paul George pra under 26.5 | 33.0 | 0.5817 (Medium) | pass | model 60%, market 53% | variance | **untagged** | root leg of a 6-leg script loss: #2726, #2727, #2728, #2731, #2737, #2798; logged as a PASS: no money on it; reviewed for calibration |
| 2727 | Payton Pritchard pra under 21.5 | 30.0 | 0.5437 (Medium) | pass | model 64%, market 54% | correlated | **untagged** | same game script as #2726 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2728 | Payton Pritchard pts under 13.5 | 21.0 | 0.5504 (Medium) | pass | model 59%, market 52% | correlated | role/lineup | same game script as #2726 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2731 | Desmond Bane ast under 3.0 | 5.0 | 0.5738 (Medium) | pass | model 73%, market 57% | correlated | **untagged** | same game script as #2726 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2733 | Tre Jones pra under 17.5 | 24.0 | 0.5554 (Medium) | pass | model 53%, market 52% | variance | **untagged** | root leg of a 2-leg script loss: #2733, #2734; logged as a PASS: no money on it; reviewed for calibration |
| 2734 | Isaac Okoro pts under 8.5 | 13.0 | 0.5439 (Medium) | pass | model 51%, market 54% | correlated | **untagged** | same game script as #2733 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2737 | Anthony Black ast under 4.0 | 7.0 | 0.5407 (Medium) | pass | model 48% (against), market 48% (against) | correlated | **untagged** | same game script as #2726 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2738 | Jaylen Brown pra under 33.5 | 48.0 | 0.5455 (Medium) | pass | model 54%, market 50% | variance | **untagged** | root leg of a 7-leg script loss: #2738, #2742, #2743, #2744, #2779, #2786, #2795; logged as a PASS: no money on it; reviewed for calibration |
| 2742 | Tyrese Maxey ast under 6.0 | 9.0 | 0.601 (Medium) | lean | model 50%, market 55% | correlated | variance | same game script as #2738 (variance); own read: variance |
| 2743 | Day'Ron Sharpe ast under 3.5 | 5.0 | 0.5572 (Medium) | pass | model 52%, market 49% (against) | correlated | **untagged** | same game script as #2738 (variance); own read: model bias; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 2744 | Mikel Brown Jr. ast under 3.5 | 5.0 | 0.5523 (Medium) | pass | model 64%, market 55% | correlated | **untagged** | same game script as #2738 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2747 | Bobby Portis Jr. pra under 13.5 | 22.0 | 0.5499 (Medium) | pass | model 54%, market 51% | variance | **untagged** | root leg of a 4-leg script loss: #2747, #2749, #2777, #2789; logged as a PASS: no money on it; reviewed for calibration |
| 2749 | Giannis Antetokounmpo ast under 5.0 | 6.0 | 0.5632 (Medium) | pass | model 53%, market 50% (against) | correlated | **untagged** | same game script as #2747 (variance); own read: model bias; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 2751 | Deni Avdija pra under 36.5 | 39.0 | 0.5531 (Medium) | pass | model 56%, market 51% | variance | **untagged** | root leg of a 3-leg script loss: #2751, #2753, #2788; logged as a PASS: no money on it; reviewed for calibration |
| 2753 | Rudy Gobert pra under 21.5 | 36.0 | 0.5593 (Medium) | pass | model 52%, market 52% | correlated | **untagged** | same game script as #2751 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2757 | Saddiq Bey pra under 26.0 | 32.0 | 0.5432 (Medium) | pass | model 51%, market 51% | variance | **untagged** | root leg of a 6-leg script loss: #2757, #2758, #2759, #2760, #2787, #2794; logged as a PASS: no money on it; reviewed for calibration |
| 2758 | Derik Queen pra under 19.5 | 27.0 | 0.563 (Medium) | pass | model 52%, market 53% | correlated | **untagged** | same game script as #2757 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2759 | Will Richard pra under 11.5 | 15.0 | 0.5423 (Medium) | pass | model 55%, market 50% (against) | correlated | **untagged** | same game script as #2757 (variance); own read: model bias; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 2760 | Jeremiah Fears ra under 11.0 | 20.0 | 0.5793 (Medium) | pass | model 61%, market 60% | correlated | **untagged** | same game script as #2757 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2763 | Nikola Jokić pra under 47.5 | 50.0 | 0.5664 (Medium) | pass | model 56%, market 52% | variance | **untagged** | root leg of a 4-leg script loss: #2763, #2764, #2767, #2773; logged as a PASS: no money on it; reviewed for calibration |
| 2764 | Devin Booker pra under 31.5 | 32.0 | 0.5656 (Medium) | pass | model 59%, market 52% | correlated | **untagged** | same game script as #2763 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2767 | Jalen Green pra under 17.5 | 24.0 | 0.5618 (Medium) | pass | model 52%, market 53% | correlated | **untagged** | same game script as #2763 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2773 | Cameron Johnson reb over 3.5 | 0.0 | 0.5404 (Medium) | pass | model 55%, market 53% | correlated | **untagged** | same game script as #2763 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2774 | Javon Small ra under 8.5 | 17.0 | 0.5325 (Low) | pass | model 56%, market 56% | correlated | variance | same game script as #2720 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2777 | Giannis Antetokounmpo pr over 39.5 | 33.0 | 0.4559 (Low) | pass | model 37% (against), market 50% | correlated | variance | same game script as #2747 (variance); own read: variance; we priced this side at 46%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 2779 | Egor Dëmin ast under 2.5 | 4.0 | 0.4899 (Low) | pass | model 58%, market 49% (against) | correlated | role/lineup | same game script as #2738 (variance); own read: model bias; we priced this side at 49%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 2786 | Joel Embiid pa under 25.5 | 38.0 | 0.4329 (Low) | pass | model 51%, market 49% (against) | correlated | variance | same game script as #2738 (variance); own read: model bias; we priced this side at 43%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 2787 | Saddiq Bey pr under 23.5 | 29.0 | 0.5092 (Low) | pass | model 54%, market 52% | correlated | variance | same game script as #2757 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2788 | Ayo Dosunmu pa over 20.5 | 10.0 | 0.5338 (Low) | pass | model 57%, market 56% | correlated | variance | same game script as #2751 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2789 | Andrew Wiggins pts under 9.5 | 17.0 | 0.528 (Low) | pass | model 51%, market 52% | correlated | role/lineup | same game script as #2747 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2794 | Al Horford reb under 4.5 | 5.0 | 0.5166 (Low) | pass | model 72%, market 55% | correlated | variance | same game script as #2757 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2795 | Jaylen Brown ra under 10.5 | 17.0 | 0.5145 (Low) | pass | model 54%, market 54% | correlated | variance | same game script as #2738 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2798 | Jayson Tatum ra under 13.5 | 16.0 | 0.5067 (Low) | pass | model 65% | correlated | role/lineup | same game script as #2726 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2800 | Brayden Schenn nhl_sog over 1.5 | 1.0 | 0.4682 (Low) | pass | model 50% (against) | variance | **untagged** | we priced this side at 47%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2801 | Mika Zibanejad nhl_toi under 20.5 | 20.67 | 0.55 (Low) | pass | model 64% | variance | **untagged** | root leg of a 4-leg script loss: #2801, #2802, #2811, #2816; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2802 | Nick Suzuki nhl_toi under 20.25 | 21.42 | 0.5521 (Low) | pass | model 65% | correlated | **untagged** | same game script as #2801 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2803 | Matt Boldy nhl_sog over 3.5 | 3.0 | 0.4802 (Low) | pass | model 56% | variance | **untagged** | we priced this side at 48%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2804 | Thomas Chabot nhl_sog over 1.5 | 1.0 | 0.4734 (Low) | pass | model 52% | variance | **untagged** | we priced this side at 47%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2808 | Dmitri Simashev nhl_pm under 0.5 | 1.0 | 0.5626 (Low) | pass | model 55% | variance | **untagged** | root leg of a 2-leg script loss: #2808, #2810; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2809 | Dylan Strome nhl_sog over 1.5 | 1.0 | 0.4802 (Low) | pass | model 56% | variance | **untagged** | we priced this side at 48%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2810 | MacKenzie Weegar nhl_pm under 0.5 | 1.0 | 0.5538 (Low) | pass | model 51% | correlated | **untagged** | same game script as #2808 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2811 | Nick Suzuki nhl_fow over 9.5 | 7.0 | 0.4741 (Low) | pass | model 39% (against) | correlated | **untagged** | same game script as #2801 (variance); own read: variance; we priced this side at 47%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 2816 | Lane Hutson nhl_blocks under 1.5 | 4.0 | 0.4945 (Low) | pass | model 62%, market 53% | correlated | **untagged** | same game script as #2801 (variance); own read: variance; we priced this side at 49%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 2822 | Varvara Lepchenko tennis_games_won over 11.5 | 8.0 | 0.6316 (Low) | pass | model 61% | variance | **untagged** | logged as a PASS: no money on it; reviewed for calibration |
| 2824 | Alicia Herrero Linana tennis_games_won over 11.5 | 4.0 | 0.7393 (Low) | pass | model 72% | variance | **untagged** | logged as a PASS: no money on it; reviewed for calibration |

Lessons:
- #2721: Spencer 32 min vs 27 projected
- #2725: Spencer 32 min vs 27 projected; 9 ast
- #2728: Pritchard 32 min vs 24 projected
- #2742: 9 ast at projected minutes (35)
- #2774: 29 min vs 26 projected; 12 ast
- #2777: 33 in 29 min; priced 46%
- #2779: Demin 26 min vs 20 projected: the L35 minutes-outlier warning fired
- #2786: 37 pts; priced 43%
- #2787: 33 min as projected; 5-8 from three
- #2788: 3-11 FG in 30 min
- #2789: Wiggins 34 min vs 25 projected
- #2794: 5 vs 4.5 in 14 min
- #2795: 13 reb at projected minutes (33)
- #2798: Tatum 36 min vs 29 projected; 12 reb

Detail from the feeds:
- #2800 Brayden Schenn: error=HTTPError
- #2801 Mika Zibanejad: error=HTTPError
- #2802 Nick Suzuki: error=HTTPError
- #2803 Matt Boldy: error=HTTPError
- #2804 Thomas Chabot: error=HTTPError
- #2808 Dmitri Simashev: error=HTTPError
- #2809 Dylan Strome: error=HTTPError
- #2810 MacKenzie Weegar: error=HTTPError
- #2811 Nick Suzuki: error=HTTPError
- #2816 Lane Hutson: error=HTTPError

## 2026-11-15: 66 losses from 17 independent causes

| # | Leg | Result | Our p | Action | Sources | Auto tag | Confirmed | Evidence |
|---|---|---|---|---|---|---|---|---|
| 2577 | Quentin Grimes pra under 18.5 | 29.0 | 0.5998 (Medium) | pass | model 68%, market 60% | variance | **untagged** | root leg of a 11-leg script loss: #2577, #2579, #2580, #2581, #2582, #2583, #2586, #2587, #2588, #2589, #2658; logged as a PASS: no money on it; reviewed for calibration |
| 2579 | Khaman Maluach reb over 5.5 | 4.0 | 0.5545 (Medium) | pass | model 58%, market 51% | correlated | **untagged** | same game script as #2577 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2580 | Sandro Mamukelashvili reb over 4.5 | 2.0 | 0.5544 (Medium) | pass | model 54%, market 52% | correlated | **untagged** | same game script as #2577 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2581 | Collin Gillespie ast under 3.5 | 4.0 | 0.5642 (Medium) | pass | model 45% (against), market 49% (against) | correlated | **untagged** | same game script as #2577 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2582 | Miles Bridges ast under 2.5 | 3.0 | 0.5929 (Medium) | pass | model 50%, market 52% | correlated | **untagged** | same game script as #2577 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2583 | Collin Sexton ast under 2.5 | 3.0 | 0.582 (Medium) | pass | model 49% (against), market 51% | correlated | **untagged** | same game script as #2577 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2586 | Jake LaRavia ast under 2.5 | 3.0 | 0.6019 (Low) | pass | model 61% | correlated | **untagged** | same game script as #2577 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2587 | Oso Ighodaro reb over 5.0 | 2.0 | 0.5563 (Medium) | pass | model 55%, market 52% | correlated | **untagged** | same game script as #2577 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2588 | Devin Booker ast under 5.0 | 7.0 | 0.5659 (Medium) | pass | model 46% (against), market 49% (against) | correlated | **untagged** | same game script as #2577 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2589 | Jake LaRavia reb over 4.0 | 3.0 | 0.5463 (Medium) | pass | model 55%, market 50% | correlated | **untagged** | same game script as #2577 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2590 | Sion James pra under 13.5 | 15.0 | 0.5452 (Medium) | pass | model 57%, market 50% (against) | model bias | **untagged** | root leg of a 7-leg script loss: #2590, #2591, #2594, #2595, #2596, #2665, #2675; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 2591 | Moussa Diabaté ra under 11.5 | 14.0 | 0.543 (Medium) | pass | model 64%, market 55% | correlated | **untagged** | same game script as #2590 (model bias); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2594 | Kris Dunn pts under 6.5 | 7.0 | 0.5434 (Medium) | pass | model 56%, market 52% | correlated | **untagged** | same game script as #2590 (model bias); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2595 | Max Strus reb over 3.5 | 3.0 | 0.5577 (Medium) | pass | model 58%, market 51% | correlated | **untagged** | same game script as #2590 (model bias); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2596 | Keaton Wagler ast under 2.5 | 5.0 | 0.6085 (Medium) | lean | model 49% (against), market 54% | correlated | role/lineup | same game script as #2590 (model bias); own read: variance |
| 2598 | Dylan Harper pra under 29.5 | 44.0 | 0.6688 (High) | pass | model 76%, market 67% | variance | **untagged** | root leg of a 8-leg script loss: #2598, #2599, #2600, #2601, #2602, #2603, #2605, #2670; logged as a PASS: no money on it; reviewed for calibration |
| 2599 | Stephon Castle pra under 28.5 | 33.0 | 0.5796 (Medium) | pass | model 71%, market 58% | correlated | **untagged** | same game script as #2598 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2600 | Dylan Harper pa under 23.5 | 35.0 | 0.6187 (Medium) | pass | model 72%, market 66% | correlated | **untagged** | same game script as #2598 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2601 | Stephon Castle pr under 22.5 | 24.0 | 0.5969 (Medium) | pass | model 71%, market 60% | correlated | role/lineup | same game script as #2598 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2602 | Dylan Harper pts under 18.5 | 31.0 | 0.6426 (Medium) | pass | model 73%, market 64% | correlated | **untagged** | same game script as #2598 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2603 | Stephon Castle pts under 16.5 | 20.0 | 0.5651 (Medium) | pass | model 67%, market 56% | correlated | **untagged** | same game script as #2598 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2605 | Mo Bamba pts under 7.5 | 26.0 | 0.5503 (Medium) | pass | model 54%, market 53% | correlated | **untagged** | same game script as #2598 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2607 | Karl-Anthony Towns pra under 36.5 | 48.0 | 0.5523 (Medium) | pass | model 58%, market 50% | variance | **untagged** | root leg of a 4-leg script loss: #2607, #2609, #2611, #2673; logged as a PASS: no money on it; reviewed for calibration |
| 2609 | Immanuel Quickley ast under 5.0 | 6.0 | 0.5968 (Low) | pass | model 48% (against), market 52% | correlated | **untagged** | same game script as #2607 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2611 | Ja'Kobe Walter reb over 3.5 | 2.0 | 0.5579 (Medium) | pass | model 56%, market 52% | correlated | **untagged** | same game script as #2607 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2616 | Zaccharie Risacher pra under 11.5 | 23.0 | 0.5525 (Medium) | pass | model 53%, market 52% | variance | **untagged** | root leg of a 3-leg script loss: #2616, #2617, #2621; logged as a PASS: no money on it; reviewed for calibration |
| 2617 | Zaccharie Risacher pts under 7.5 | 18.0 | 0.5527 (Medium) | pass | model 60%, market 52% | correlated | **untagged** | same game script as #2616 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2621 | Payton Pritchard ast under 4.0 | 6.0 | 0.6082 (Medium) | pass | model 54%, market 52% | correlated | **untagged** | same game script as #2616 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2623 | Amen Thompson pra under 29.5 | 40.0 | 0.5676 (Medium) | pass | model 58%, market 52% | variance | **untagged** | root leg of a 9-leg script loss: #2623, #2625, #2629, #2630, #2631, #2633, #2635, #2636, #2637; logged as a PASS: no money on it; reviewed for calibration |
| 2625 | AJ Dybantsa pra under 23.5 | 24.0 | 0.558 (Medium) | pass | model 56%, market 52% | correlated | **untagged** | same game script as #2623 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2629 | Amen Thompson pts under 17.5 | 26.0 | 0.5591 (Medium) | pass | model 58%, market 53% | correlated | **untagged** | same game script as #2623 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2630 | AJ Dybantsa pts under 15.5 | 16.0 | 0.5486 (Medium) | pass | model 58%, market 52% | correlated | **untagged** | same game script as #2623 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2631 | Alperen Şengün reb over 9.0 | 8.0 | 0.5529 (Medium) | pass | model 52%, market 52% | correlated | **untagged** | same game script as #2623 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2633 | Amen Thompson ast under 4.5 | 7.0 | 0.6049 (Medium) | pass | model 58%, market 51% | correlated | opportunity | same game script as #2623 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2635 | Alex Sarr ast under 1.5 | 2.0 | 0.5488 (Medium) | pass | model 42% (against), market 48% (against) | correlated | **untagged** | same game script as #2623 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2636 | Kevin Durant reb over 5.0 | 4.0 | 0.5616 (Medium) | pass | model 52%, market 53% | correlated | variance | same game script as #2623 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2637 | Reed Sheppard ast under 4.0 | 6.0 | 0.5665 (Medium) | pass | model 74%, market 57% | correlated | **untagged** | same game script as #2623 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2642 | Brayden Burries pra under 20.5 | 25.0 | 0.555 (Medium) | pass | model 57%, market 51% | variance | role/lineup | root leg of a 4-leg script loss: #2642, #2648, #2649, #2664; logged as a PASS: no money on it; reviewed for calibration |
| 2648 | Jaime Jaquez Jr. ast under 3.5 | 4.0 | 0.5962 (Medium) | pass | model 53%, market 51% | correlated | **untagged** | same game script as #2642 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2649 | Nickeil Alexander-Walker tpm over 3.5 | 2.0 | 0.5457 (Medium) | pass | model 59%, market 53% | correlated | **untagged** | same game script as #2642 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2653 | Darius Acuff Jr. pts under 23.5 | 26.0 | 0.5506 (Medium) | pass | model 60%, market 52% | variance | **untagged** | root leg of a 2-leg script loss: #2653, #2662; logged as a PASS: no money on it; reviewed for calibration |
| 2658 | Ziaire Williams pra over 12.5 | 11.0 | 0.4223 (Low) | pass | model 59%, market 48% (against) | correlated | variance | same game script as #2577 (variance); own read: model bias; we priced this side at 42%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 2662 | Domantas Sabonis pra over 30.5 | 27.0 | 0.3866 (Low) | pass | model 29% (against), market 51% | correlated | variance | same game script as #2653 (variance); own read: variance; we priced this side at 39%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 2664 | Jalen Johnson reb under 9.5 | 11.0 | 0.4257 (Low) | pass | model 56%, market 48% (against) | correlated | variance | same game script as #2642 (variance); own read: model bias; we priced this side at 43%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 2665 | Coby White pr under 16.5 | 21.0 | 0.4587 (Low) | pass | model 64%, market 46% (against) | correlated | variance | same game script as #2590 (model bias); own read: model bias; we priced this side at 46%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 2670 | Mo Bamba ra under 8.5 | 9.0 | 0.536 (Low) | pass | model 72%, market 54% | correlated | role/lineup | same game script as #2598 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2673 | OG Anunoby pr under 22.5 | 30.0 | 0.5142 (Low) | pass | model 65%, market 51% | correlated | role/lineup | same game script as #2607 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2675 | Moussa Diabaté pr under 18.5 | 24.0 | 0.5037 (Low) | pass | model 62%, market 50% | correlated | variance | same game script as #2590 (model bias); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2676 | Leo Carlsson nhl_assists over 0.5 | 0.0 | 0.5494 (Low) | pass | model 48% (against), market 53% | variance | **untagged** | root leg of a 2-leg script loss: #2676, #2697; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2677 | Leon Draisaitl nhl_pm under 0.5 | 3.0 | 0.5829 (Low) | pass | model 64% | variance | **untagged** | root leg of a 3-leg script loss: #2677, #2686, #2687; logged as a PASS: no money on it; reviewed for calibration |
| 2680 | Noah Dobson nhl_sog over 1.5 | 1.0 | 0.4726 (Low) | pass | model 57% | variance | **untagged** | root leg of a 4-leg script loss: #2680, #2681, #2703, #2704; we priced this side at 47%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2681 | Lane Hutson nhl_sog over 1.5 | 1.0 | 0.4887 (Low) | pass | model 57%, market 51% | correlated | **untagged** | same game script as #2680 (variance); own read: variance; we priced this side at 49%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2686 | Cam York nhl_blocks over 1.5 | 0.0 | 0.4179 (Low) | pass | model 42% (against), market 51% | correlated | **untagged** | same game script as #2677 (variance); own read: variance; we priced this side at 42%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 2687 | Nick Seeler nhl_blocks over 1.5 | 1.0 | 0.4662 (Low) | pass | model 62%, market 52% | correlated | **untagged** | same game script as #2677 (variance); own read: variance; we priced this side at 47%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2689 | Michael Misa nhl_sog under 1.5 | 2.0 | 0.4328 (Low) | pass | model 48% (against), market 49% (against) | variance | **untagged** | root leg of a 2-leg script loss: #2689, #2694; we priced this side at 43%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2690 | Parker Wotherspoon nhl_pm under 0.5 | 1.0 | 0.5632 (Low) | pass | model 54% | variance | **untagged** | logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2691 | Matthew Tkachuk nhl_assists over 0.5 | 0.0 | 0.54 (Low) | pass | model 47% (against), market 52% | variance | **untagged** | root leg of a 3-leg script loss: #2691, #2696, #2702; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2694 | Jacob Trouba nhl_sog under 1.5 | 2.0 | 0.4771 (Low) | pass | model 47% (against), market 55% | correlated | **untagged** | same game script as #2689 (variance); own read: variance; we priced this side at 48%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2696 | Sandis Vilmanis nhl_hits over 2.5 | 1.0 | 0.4776 (Low) | pass | model 41% (against) | correlated | **untagged** | same game script as #2691 (variance); own read: variance; we priced this side at 48%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 2697 | Alex Killorn nhl_sog under 1.5 | 3.0 | 0.4662 (Low) | pass | model 50% (against), market 53% | correlated | **untagged** | same game script as #2676 (variance); own read: variance; we priced this side at 47%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 2702 | Mikko Rantanen nhl_sog under 2.0 | 3.0 | 0.4771 (Low) | pass | model 68%, market 50% (against) | correlated | **untagged** | same game script as #2691 (variance); own read: model bias; we priced this side at 48%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 2703 | Gabe Perreault nhl_sog over 1.5 | 0.0 | 0.4669 (Low) | pass | model 55% | correlated | **untagged** | same game script as #2680 (variance); own read: variance; we priced this side at 47%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 2704 | Adam Fox nhl_sog over 1.5 | 1.0 | 0.4616 (Low) | pass | model 52% | correlated | **untagged** | same game script as #2680 (variance); own read: variance; we priced this side at 46%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2713 | Shintaro Mochizuki tennis_games under 21.5 | 32.0 | 0.5628 (Low) | pass | model 56% | variance | **untagged** | logged as a PASS: no money on it; reviewed for calibration |
| 2714 | Andrea Guerrieri tennis_games under 22.0 | 23.0 | 0.5412 (Low) | pass | model 54% | variance | **untagged** | logged as a PASS: no money on it; reviewed for calibration |
| 2717 | Nuria Brancaccio tennis_games over 19.5 | 18.0 | 0.5079 (Low) | pass | model 54%, market 50% (against) | variance | **untagged** | logged as a PASS: no money on it; reviewed for calibration |

Lessons:
- #2596: Wagler 28 min vs 19 projected
- #2601: Castle 35 min vs 24.5 projected
- #2633: Thompson 29 min vs 35 projected in a 28-point win, still 7 ast
- #2636: 4 reb in 30 min of a 28-point win
- #2642: Burries 29 min vs 24 projected
- #2658: 19 min vs 24.5 projected; priced 42%
- #2662: 27 vs 30.5; priced 39% (minutes warning fired)
- #2664: 11 reb at projected minutes; priced 43%
- #2665: 21 pts in 20 min (as projected); priced 46%
- #2670: Bamba 36 min vs 19 projected; 9 vs 8.5
- #2673: Anunoby 44 min vs 28.5 projected
- #2675: 26 min as projected; 12 reb

Detail from the feeds:
- #2676 Leo Carlsson: error=HTTPError
- #2677 Leon Draisaitl: error=HTTPError
- #2680 Noah Dobson: error=HTTPError
- #2681 Lane Hutson: error=HTTPError
- #2686 Cam York: error=HTTPError
- #2687 Nick Seeler: error=HTTPError
- #2689 Michael Misa: error=HTTPError
- #2690 Parker Wotherspoon: error=HTTPError
- #2691 Matthew Tkachuk: error=HTTPError
- #2694 Jacob Trouba: error=HTTPError
- #2696 Sandis Vilmanis: error=HTTPError
- #2697 Alex Killorn: error=HTTPError
- #2702 Mikko Rantanen: error=HTTPError
- #2703 Gabe Perreault: error=HTTPError
- #2704 Adam Fox: error=HTTPError

## 2026-11-14: 32 losses from 15 independent causes

| # | Leg | Result | Our p | Action | Sources | Auto tag | Confirmed | Evidence |
|---|---|---|---|---|---|---|---|---|
| 2493 | Christian Braun pr under 16.5 | 24.0 | 0.5413 (Medium) | pass | model 57%, market 53% | variance | **untagged** | root leg of a 3-leg script loss: #2493, #2494, #2532; logged as a PASS: no money on it; reviewed for calibration |
| 2494 | Cameron Johnson ra under 5.5 | 7.0 | 0.5419 (Medium) | pass | model 51%, market 57% | correlated | **untagged** | same game script as #2493 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2498 | Kyrie Irving ast under 4.0 | 5.0 | 0.5664 (Medium) | lean | model 49% (against), market 48% (against) | variance | role/lineup | root leg of a 2-leg script loss: #2498, #2530 |
| 2507 | Julius Randle ast under 4.5 | 5.0 | 0.5863 (Medium) | lean | model 53%, market 50% (against) | model bias | variance | root leg of a 4-leg script loss: #2507, #2508, #2519, #2534; model was on our side, the market was against it, and the market was right |
| 2508 | Day'Ron Sharpe ast under 4.0 | 5.0 | 0.5425 (Medium) | pass | model 64%, market 54% | correlated | **untagged** | same game script as #2507 (model bias); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2513 | LaMelo Ball ra under 11.5 | 14.0 | 0.5464 (Medium) | pass | model 59%, market 55% | variance | variance | root leg of a 3-leg script loss: #2513, #2515, #2518; logged as a PASS: no money on it; reviewed for calibration |
| 2515 | Matas Buzelis ra under 7.5 | 11.0 | 0.547 (Medium) | pass | model 66%, market 55% | correlated | **untagged** | same game script as #2513 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2518 | Jonathan Kuminga ast under 2.5 | 3.0 | 0.5581 (Medium) | pass | model 45% (against), market 48% (against) | correlated | **untagged** | same game script as #2513 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2519 | Cam Spencer pra under 24.5 | 26.0 | 0.5061 (Low) | pass | model 76%, market 51% | correlated | role/lineup | same game script as #2507 (model bias); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2523 | Kevin Huerter reb under 3.5 | 4.0 | 0.4627 (Low) | pass | model 55%, market 52% | variance | role/lineup | we priced this side at 46%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2530 | Kyrie Irving ra under 8.0 | 11.0 | 0.491 (Low) | pass | model 53%, market 50% (against) | correlated | role/lineup | same game script as #2498 (variance); own read: model bias; we priced this side at 49%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 2532 | Jordan Poole pts under 10.5 | 14.0 | 0.5286 (Low) | pass | model 57% | correlated | variance | same game script as #2493 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2534 | Day'Ron Sharpe pr under 16.5 | 27.0 | 0.5162 (Low) | pass | model 60%, market 52% | correlated | role/lineup | same game script as #2507 (model bias); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2536 | Zach Benson nhl_points over 0.5 | 0.0 | 0.5834 (Low) | pass | model 46% (against), market 54% | variance | **untagged** | logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2538 | Jack Roslovic nhl_points over 0.5 | 0.0 | 0.582 (Medium) | lean | model 49% (against), market 53% | variance | **untagged** | root leg of a 2-leg script loss: #2538, #2555; closest possible loss (missed by the minimum) |
| 2539 | Jordan Kyrou nhl_points over 0.5 | 0.0 | 0.5927 (Low) | pass | model 44% (against), market 56% | variance | **untagged** | logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2540 | Evgeni Malkin nhl_points over 0.5 | 0.0 | 0.5947 (Medium) | lean | model 56%, market 53% | variance | **untagged** | root leg of a 4-leg script loss: #2540, #2541, #2566, #2571; closest possible loss (missed by the minimum) |
| 2541 | Jake Sanderson nhl_points over 0.5 | 0.0 | 0.5915 (Medium) | pass | model 50%, market 54% | correlated | **untagged** | same game script as #2540 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2544 | Jackson LaCombe nhl_assists over 0.5 | 0.0 | 0.5431 (Low) | pass | model 49% (against), market 53% | variance | **untagged** | logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2547 | Andrew Peeke nhl_blocks under 1.5 | 2.0 | 0.4656 (Low) | pass | model 57%, market 50% | variance | **untagged** | root leg of a 2-leg script loss: #2547, #2569; we priced this side at 47%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2549 | Ross Johnston nhl_hits over 3.5 | 1.0 | 0.4574 (Low) | pass | model 30% (against) | variance | **untagged** | we priced this side at 46%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 2550 | Elias Lindholm nhl_points over 0.5 | 0.0 | 0.5543 (Low) | pass | model 47% (against), market 50% | variance | **untagged** | root leg of a 2-leg script loss: #2550, #2563; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2551 | Adam Fantilli nhl_points under 0.5 | 1.0 | 0.4999 (Low) | pass | model 62%, market 46% (against) | model bias | **untagged** | root leg of a 4-leg script loss: #2551, #2553, #2560, #2567; we priced this side at 50%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 2553 | Zach Werenski nhl_toi over 27.75 | 24.55 | 0.3982 (Low) | pass | model 24% (against) | correlated | **untagged** | same game script as #2551 (model bias); own read: variance; we priced this side at 40%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 2555 | Colton Dach nhl_sog over 1.5 | 0.0 | 0.5301 (Low) | pass | model 55%, market 52% | correlated | **untagged** | same game script as #2538 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2560 | Tyson Foerster nhl_sog over 1.5 | 1.0 | 0.5189 (Low) | pass | model 59%, market 50% (against) | correlated | **untagged** | same game script as #2551 (model bias); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2562 | Alex DeBrincat nhl_hits over 0.5 | 0.0 | 0.515 (Low) | pass | model 57% | variance | **untagged** | logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2563 | Matt Boldy nhl_sog over 3.5 | 3.0 | 0.5138 (Low) | pass | model 56%, market 50% | correlated | **untagged** | same game script as #2550 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2566 | Tim Stutzle nhl_toi over 21.5 | 19.72 | 0.504 (Low) | pass | model 73% | correlated | **untagged** | same game script as #2540 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2567 | Owen Tippett nhl_blocks under 0.5 | 1.0 | 0.4757 (Low) | pass | model 64% | correlated | **untagged** | same game script as #2551 (model bias); own read: variance; we priced this side at 48%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2569 | Macklin Celebrini nhl_blocks over 0.5 | 0.0 | 0.441 (Low) | pass | model 59% | correlated | **untagged** | same game script as #2547 (variance); own read: variance; we priced this side at 44%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2571 | Thomas Chabot nhl_blocks over 1.5 | 0.0 | 0.4396 (Low) | pass | model 62%, market 49% (against) | correlated | **untagged** | same game script as #2540 (variance); own read: model bias; we priced this side at 44%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |

Lessons:
- #2498: Irving 37 min vs 30 projected; 5 vs 4
- #2507: minutes warning fired (28 vs 32 last 5); 31 min, 5 vs 4.5
- #2513: 30 min as projected; 8 reb
- #2519: Spencer 34 min vs 23 projected
- #2523: Huerter 38 min vs 28 projected; 4 vs 3.5
- #2530: Irving 37 min vs 30 projected
- #2532: 24 min vs 20 projected; 14 on 3-7 FG
- #2534: Sharpe 28 min vs 20 projected; 11 reb

Detail from the feeds:
- #2536 Zach Benson: error=HTTPError
- #2538 Jack Roslovic: error=HTTPError
- #2539 Jordan Kyrou: error=HTTPError
- #2540 Evgeni Malkin: error=HTTPError
- #2541 Jake Sanderson: error=HTTPError
- #2544 Jackson LaCombe: error=HTTPError
- #2547 Andrew Peeke: error=HTTPError
- #2549 Ross Johnston: error=HTTPError
- #2550 Elias Lindholm: error=HTTPError
- #2551 Adam Fantilli: error=HTTPError
- #2553 Zach Werenski: error=HTTPError
- #2555 Colton Dach: error=HTTPError
- #2560 Tyson Foerster: error=HTTPError
- #2562 Alex DeBrincat: error=HTTPError
- #2563 Matt Boldy: error=HTTPError
- #2566 Tim Stutzle: error=HTTPError
- #2567 Owen Tippett: error=HTTPError
- #2569 Macklin Celebrini: error=HTTPError
- #2571 Thomas Chabot: error=HTTPError

## 2026-11-13: 62 losses from 20 independent causes

| # | Leg | Result | Our p | Action | Sources | Auto tag | Confirmed | Evidence |
|---|---|---|---|---|---|---|---|---|
| 2367 | Ivica Zubac reb under 10.0 | 13.0 | 0.5479 (Medium) | pass | model 84%, market 55% | variance | **untagged** | root leg of a 5-leg script loss: #2367, #2369, #2433, #2438, #2442; logged as a PASS: no money on it; reviewed for calibration |
| 2369 | Kelly Oubre Jr. reb under 4.0 | 5.0 | 0.5957 (Medium) | pass | model 89%, market 60% | correlated | **untagged** | same game script as #2367 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2372 | Franz Wagner pra under 38.5 | 56.0 | 0.5405 (Medium) | pass | model 50%, market 52% | variance | **untagged** | root leg of a 6-leg script loss: #2372, #2374, #2375, #2376, #2379, #2440; logged as a PASS: no money on it; reviewed for calibration |
| 2374 | Jaime Jaquez Jr. pra under 21.5 | 32.0 | 0.5518 (Medium) | pass | model 52%, market 53% | correlated | **untagged** | same game script as #2372 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2375 | Kyle Kuzma pra under 18.5 | 20.0 | 0.5474 (Medium) | pass | model 56%, market 51% | correlated | **untagged** | same game script as #2372 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2376 | Myles Turner pts under 9.5 | 14.0 | 0.551 (Medium) | pass | model 59%, market 52% | correlated | **untagged** | same game script as #2372 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2379 | Anthony Black tpm over 1.5 | 1.0 | 0.5402 (Medium) | pass | model 55%, market 53% | correlated | **untagged** | same game script as #2372 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2381 | Jerami Grant pts under 11.5 | 22.0 | 0.5446 (Medium) | pass | model 55%, market 52% | variance | **untagged** | root leg of a 2-leg script loss: #2381, #2426; logged as a PASS: no money on it; reviewed for calibration |
| 2385 | Josh Giddey pra under 28.5 | 39.0 | 0.5696 (Medium) | pass | model 60%, market 53% | variance | **untagged** | root leg of a 7-leg script loss: #2385, #2387, #2388, #2389, #2392, #2431, #2432; logged as a PASS: no money on it; reviewed for calibration |
| 2387 | Jalen Johnson ra under 16.5 | 21.0 | 0.5413 (Medium) | pass | model 60%, market 53% | correlated | **untagged** | same game script as #2385 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2388 | Josh Giddey pts under 13.5 | 15.0 | 0.5524 (Medium) | pass | model 58%, market 52% | correlated | **untagged** | same game script as #2385 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2389 | Josh Giddey ast under 8.5 | 14.0 | 0.6252 (Medium) | lean | model 54%, market 54% | correlated | role/lineup | same game script as #2385 (variance); own read: variance |
| 2392 | Aaron Wiggins ast under 2.5 | 3.0 | 0.612 (Medium) | pass | model 58%, market 51% | correlated | **untagged** | same game script as #2385 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2393 | James Harden pra under 28.5 | 34.0 | 0.544 (Medium) | pass | model 54%, market 51% | variance | **untagged** | root leg of a 5-leg script loss: #2393, #2395, #2425, #2439, #2441; logged as a PASS: no money on it; reviewed for calibration |
| 2395 | Donovan Mitchell ast under 5.5 | 7.0 | 0.6019 (Low) | pass | model 48% (against), market 52% | correlated | **untagged** | same game script as #2393 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2399 | Keyonte George ast under 5.5 | 7.0 | 0.5525 (Medium) | pass | model 41% (against), market 48% (against) | variance | **untagged** | root leg of a 5-leg script loss: #2399, #2400, #2403, #2404, #2436; logged as a PASS: no money on it; reviewed for calibration |
| 2400 | Ace Bailey reb over 5.0 | 3.0 | 0.5734 (Medium) | pass | model 61%, market 54% | correlated | **untagged** | same game script as #2399 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2403 | Isaiah Collier ast under 3.5 | 5.0 | 0.5607 (Medium) | pass | model 44% (against), market 48% (against) | correlated | **untagged** | same game script as #2399 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2404 | Reed Sheppard ast under 2.5 | 3.0 | 0.6173 (Medium) | lean | model 57%, market 52% | correlated | variance | same game script as #2399 (variance); own read: variance; closest possible loss (missed by the minimum) |
| 2406 | Stephon Castle pts under 16.5 | 32.0 | 0.5551 (Medium) | pass | model 68%, market 56% | variance | **untagged** | root leg of a 3-leg script loss: #2406, #2409, #2430; logged as a PASS: no money on it; reviewed for calibration |
| 2409 | Stephon Castle ast under 5.5 | 6.0 | 0.5959 (Medium) | pass | model 57%, market 50% (against) | correlated | variance | same game script as #2406 (variance); own read: model bias; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 2411 | Deni Avdija pra under 37.5 | 44.0 | 0.5417 (Medium) | pass | model 52%, market 52% | variance | **untagged** | root leg of a 4-leg script loss: #2411, #2416, #2445, #2446; logged as a PASS: no money on it; reviewed for calibration |
| 2416 | De'Andre Hunter ast under 1.5 | 2.0 | 0.6032 (Medium) | lean | model 54%, market 51% | correlated | role/lineup | same game script as #2411 (variance); own read: variance; closest possible loss (missed by the minimum) |
| 2417 | Jared McCain pr under 18.5 | 27.0 | 0.5624 (Medium) | pass | model 61%, market 55% | variance | **untagged** | root leg of a 8-leg script loss: #2417, #2418, #2419, #2420, #2421, #2424, #2435, #2447; logged as a PASS: no money on it; reviewed for calibration |
| 2418 | Jared McCain pts under 14.5 | 23.0 | 0.5439 (Medium) | pass | model 58%, market 51% | correlated | **untagged** | same game script as #2417 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2419 | Brook Lopez pts under 11.5 | 26.0 | 0.5555 (Medium) | pass | model 54%, market 53% | correlated | **untagged** | same game script as #2417 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2420 | Keaton Wagler pts under 10.5 | 14.0 | 0.5542 (Medium) | pass | model 56%, market 53% | correlated | **untagged** | same game script as #2417 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2421 | Derrick Jones Jr. pts under 10.5 | 14.0 | 0.5539 (Medium) | pass | model 59%, market 52% | correlated | **untagged** | same game script as #2417 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2424 | Alex Caruso ast under 2.5 | 4.0 | 0.6014 (Medium) | pass | model 51%, market 52% | correlated | **untagged** | same game script as #2417 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2425 | Jaylon Tyson pr under 16.5 | 19.0 | 0.5212 (Low) | pass | model 67%, market 52% | correlated | role/lineup | same game script as #2393 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2426 | Saddiq Bey ra under 7.5 | 10.0 | 0.453 (Low) | pass | model 61%, market 45% (against) | correlated | variance | same game script as #2381 (variance); own read: model bias; we priced this side at 45%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 2430 | Draymond Green ast over 5.5 | 3.0 | 0.5077 (Low) | pass | model 56%, market 54% | correlated | opportunity | same game script as #2406 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2431 | Josh Giddey pr under 19.5 | 25.0 | 0.5122 (Low) | pass | model 60%, market 51% | correlated | role/lineup | same game script as #2385 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2432 | Jalen Johnson reb under 9.5 | 11.0 | 0.5162 (Low) | pass | model 68%, market 52% | correlated | role/lineup | same game script as #2385 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2433 | Obi Toppin pra over 15.5 | 13.0 | 0.3908 (Low) | pass | model 37% (against) | correlated | variance | same game script as #2367 (variance); own read: variance; we priced this side at 39%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 2435 | Isaiah Hartenstein pa under 13.5 | 27.0 | 0.4614 (Low) | pass | model 59% | correlated | role/lineup | same game script as #2417 (variance); own read: variance; we priced this side at 46%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 2436 | Isaiah Collier pr over 8.5 | 5.0 | 0.4963 (Low) | pass | model 57%, market 50% (against) | correlated | variance | same game script as #2399 (variance); own read: model bias; we priced this side at 50%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 2438 | Jalen Brunson ra under 9.5 | 12.0 | 0.495 (Low) | pass | model 65%, market 50% (against) | correlated | role/lineup | same game script as #2367 (variance); own read: model bias; we priced this side at 50%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 2439 | Bam Adebayo ra under 12.5 | 17.0 | 0.4883 (Low) | pass | model 47% (against) | correlated | variance | same game script as #2393 (variance); own read: variance; we priced this side at 49%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 2440 | Anthony Black reb over 5.0 | 2.0 | 0.537 (Low) | pass | model 58%, market 50% | correlated | variance | same game script as #2372 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2441 | Mario Hezonja reb over 4.5 | 4.0 | 0.5362 (Low) | pass | model 55%, market 51% | correlated | role/lineup | same game script as #2393 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2442 | Mikal Bridges pts under 8.5 | 18.0 | 0.526 (Low) | pass | model 63%, market 53% | correlated | role/lineup | same game script as #2367 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2445 | Robert Williams III ra under 7.5 | 8.0 | 0.5205 (Low) | pass | model 52%, market 53% | correlated | variance | same game script as #2411 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2446 | Keegan Murray pa under 12.5 | 20.0 | 0.5192 (Low) | pass | model 68%, market 55% | correlated | role/lineup | same game script as #2411 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2447 | Darius Garland reb under 2.5 | 4.0 | 0.5162 (Low) | pass | model 70%, market 52% | correlated | role/lineup | same game script as #2417 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2452 | Brandt Clarke nhl_sog over 1.5 | 1.0 | 0.501 (Low) | pass | model 58% | variance | **untagged** | logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2454 | Jack Hughes nhl_sog over 3.5 | 2.0 | 0.4981 (Low) | pass | model 56% | variance | **untagged** | root leg of a 2-leg script loss: #2454, #2480; we priced this side at 50%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 2456 | Trevor Connelly nhl_sog under 2.0 | 4.0 | 0.5627 (Low) | pass | model 68%, market 62% | variance | **untagged** | root leg of a 2-leg script loss: #2456, #2466; logged as a PASS: no money on it; reviewed for calibration |
| 2458 | Tye Kartye nhl_points over 0.5 | 0.0 | 0.5341 (Low) | pass | model 53%, market 48% (against) | model bias | **untagged** | logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 2461 | Josh Morrissey nhl_assists under 0.5 | 1.0 | 0.5202 (Low) | pass | model 60% | variance | **untagged** | root leg of a 3-leg script loss: #2461, #2470, #2472; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2466 | Nick Perbix nhl_blocks over 1.5 | 0.0 | 0.4739 (Low) | pass | model 51%, market 46% (against) | correlated | **untagged** | same game script as #2456 (variance); own read: model bias; we priced this side at 47%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 2470 | Kyle Connor nhl_assists under 0.5 | 1.0 | 0.5188 (Low) | pass | model 59% | correlated | **untagged** | same game script as #2461 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2472 | Frank Nazar nhl_sog over 1.5 | 1.0 | 0.5024 (Low) | pass | model 58% | correlated | **untagged** | same game script as #2461 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2474 | Viktor Arvidsson nhl_sog over 2.5 | 1.0 | 0.4789 (Low) | pass | model 47% (against) | variance | **untagged** | root leg of a 2-leg script loss: #2474, #2475; we priced this side at 48%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 2475 | Jake Guentzel nhl_sog under 2.5 | 3.0 | 0.4344 (Low) | pass | model 52% | correlated | **untagged** | same game script as #2474 (variance); own read: variance; we priced this side at 43%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2476 | William Nylander nhl_sog over 2.5 | 1.0 | 0.4759 (Low) | pass | model 45% (against) | variance | **untagged** | we priced this side at 48%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 2480 | Jakob Chychrun nhl_sog over 2.5 | 2.0 | 0.4884 (Low) | pass | model 51% | correlated | **untagged** | same game script as #2454 (variance); own read: variance; we priced this side at 49%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2484 | Aryna Sabalenka tennis_games_won over 12.5 | 10.0 | 0.4071 (Low) | pass | model 41% (against) | variance | **untagged** | we priced this side at 41%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 2485 | Taylor Fritz tennis_games under 22.5 | 31.0 | 0.5215 (Low) | pass | model 61%, market 50% (against) | variance | **untagged** | root leg of a 2-leg script loss: #2485, #2486; logged as a PASS: no money on it; reviewed for calibration |
| 2486 | Thiago Agustin Tirante tennis_games_won under 9.5 | 14.0 | 0.547 (Low) | pass | model 55% | correlated | **untagged** | same game script as #2485 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2488 | Mirra Andreeva tennis_games over 22.0 | 19.0 | 0.4828 (Low) | pass | model 42% (against), market 50% (against) | variance | **untagged** | we priced this side at 48%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 2490 | Ben Shelton tennis_games under 25.5 | 26.0 | 0.6056 (Low) | pass | model 61% | variance | **untagged** | logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |

Lessons:
- #2389: Giddey 39 min vs 28 projected; 14 ast
- #2404: 3 vs 2.5 in 19 min (as projected)
- #2409: 6 vs 5.5 in 25 min of a 38-point win
- #2416: Hunter 42 min vs 28 projected (L28 minutes warning fired); 2 ast
- #2425: Tyson 30 min vs 22 projected (Mobley out)
- #2426: 35 min, 10 reb; priced 45%
- #2430: Draymond 16 min vs 25 projected in a 38-point loss
- #2431: Giddey 39 min vs 28 projected; 14 ast
- #2432: Jalen Johnson 40 min vs 32 projected
- #2433: 13 in 16 min; priced 39%
- #2435: Hartenstein 30 min vs 23 projected; 16 reb
- #2436: 1-4 FG in 16 min (as projected)
- #2438: Brunson 36 min vs 30 projected; 11 ast
- #2439: 38 min vs 34 projected; 14 reb
- #2440: 2 reb in 37 min
- #2441: Hezonja 9 min vs 19 projected
- #2442: Mikal Bridges 29 min vs 20 projected
- #2445: 8 vs 7.5 at projected minutes
- #2446: Murray 40 min vs 21 projected (L28 minutes warning fired)
- #2447: Garland 37 min vs 29 projected; 4 reb

Detail from the feeds:
- #2452 Brandt Clarke: error=HTTPError
- #2454 Jack Hughes: error=HTTPError
- #2456 Trevor Connelly: error=HTTPError
- #2458 Tye Kartye: error=HTTPError
- #2461 Josh Morrissey: error=HTTPError
- #2466 Nick Perbix: error=HTTPError
- #2470 Kyle Connor: error=HTTPError
- #2472 Frank Nazar: error=HTTPError
- #2474 Viktor Arvidsson: error=HTTPError
- #2475 Jake Guentzel: error=HTTPError
- #2476 William Nylander: error=HTTPError
- #2480 Jakob Chychrun: error=HTTPError

## 2026-11-12: 42 losses from 12 independent causes

| # | Leg | Result | Our p | Action | Sources | Auto tag | Confirmed | Evidence |
|---|---|---|---|---|---|---|---|---|
| 2285 | VJ Edgecombe pr under 20.5 | 23.0 | 0.5494 (Medium) | pass | model 55%, market 54% | variance | **untagged** | root leg of a 4-leg script loss: #2285, #2287, #2289, #2318; logged as a PASS: no money on it; reviewed for calibration |
| 2287 | Collin Murray-Boyles pts under 12.5 | 14.0 | 0.5454 (Medium) | pass | model 54%, market 51% | correlated | **untagged** | same game script as #2285 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2289 | Tyrese Maxey ast under 6.0 | 8.0 | 0.6247 (Medium) | lean | model 52%, market 53% | correlated | variance | same game script as #2285 (variance); own read: variance |
| 2290 | Anthony Davis pra under 34.5 | 49.0 | 0.5766 (Medium) | pass | model 61%, market 54% | variance | **untagged** | root leg of a 9-leg script loss: #2290, #2291, #2292, #2293, #2294, #2295, #2297, #2298, #2331; logged as a PASS: no money on it; reviewed for calibration |
| 2291 | Anthony Davis pts under 21.5 | 30.0 | 0.5607 (Medium) | pass | model 58%, market 52% | correlated | **untagged** | same game script as #2290 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2292 | Daniss Jenkins pts under 14.5 | 21.0 | 0.5572 (Medium) | pass | model 57%, market 52% | correlated | **untagged** | same game script as #2290 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2293 | Trae Young ra under 10.5 | 16.0 | 0.5552 (Medium) | pass | model 58%, market 53% | correlated | **untagged** | same game script as #2290 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2294 | Tre Johnson pts under 9.5 | 13.0 | 0.5486 (Medium) | pass | model 50%, market 52% | correlated | **untagged** | same game script as #2290 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2295 | Cade Cunningham ast under 8.5 | 11.0 | 0.6051 (Medium) | lean | model 53%, market 50% | correlated | opportunity | same game script as #2290 (variance); own read: variance |
| 2297 | Kyshawn George ast under 4.0 | 5.0 | 0.6127 (Low) | pass | model 48% (against), market 52% | correlated | **untagged** | same game script as #2290 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2298 | Ausar Thompson ast under 4.0 | 11.0 | 0.569 (Medium) | pass | model 44% (against), market 48% (against) | correlated | **untagged** | same game script as #2290 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2300 | LaMelo Ball ra under 10.5 | 12.0 | 0.5497 (Medium) | pass | model 60%, market 52% | variance | variance | root leg of a 9-leg script loss: #2300, #2301, #2303, #2304, #2305, #2306, #2309, #2310, #2326; logged as a PASS: no money on it; reviewed for calibration |
| 2301 | Naji Marshall pts under 9.5 | 13.0 | 0.5493 (Medium) | pass | model 50%, market 52% | correlated | **untagged** | same game script as #2300 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2303 | Trey Lyles pr over 9.5 | 2.0 | 0.5848 (Medium) | pass | model 68%, market 58% | correlated | **untagged** | same game script as #2300 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2304 | Jaden McDaniels ra under 9.0 | 12.0 | 0.6031 (Medium) | pass | model 56%, market 60% | correlated | **untagged** | same game script as #2300 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2305 | Caleb Martin pra under 7.5 | 14.0 | 0.5425 (Medium) | pass | model 54%, market 52% | correlated | **untagged** | same game script as #2300 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2306 | LaMelo Ball ast under 6.5 | 9.0 | 0.6073 (Medium) | pass | model 54%, market 50% | correlated | **untagged** | same game script as #2300 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2309 | Caleb Martin pts under 3.5 | 7.0 | 0.5523 (Medium) | pass | model 55%, market 52% | correlated | **untagged** | same game script as #2300 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2310 | Ayo Dosunmu reb over 4.0 | 2.0 | 0.5788 (Medium) | pass | model 56%, market 57% | correlated | **untagged** | same game script as #2300 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2311 | Jordan Goodwin pr under 10.5 | 11.0 | 0.5561 (Medium) | pass | model 58%, market 54% | variance | **untagged** | root leg of a 8-leg script loss: #2311, #2314, #2315, #2316, #2317, #2319, #2329, #2330; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2314 | Sion James reb under 4.0 | 8.0 | 0.5809 (Medium) | pass | model 69%, market 59% | correlated | **untagged** | same game script as #2311 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2315 | Miles Bridges ast under 2.5 | 3.0 | 0.573 (Medium) | pass | model 50% (against), market 47% (against) | correlated | **untagged** | same game script as #2311 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2316 | Naz Reid ast under 2.5 | 3.0 | 0.586 (Medium) | pass | model 46% (against), market 49% (against) | correlated | variance | same game script as #2311 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2317 | Christian Anderson Jr. pra under 13.5 | 15.0 | 0.5249 (Low) | pass | model 73%, market 52% | correlated | variance | same game script as #2311 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2318 | Tyrese Maxey ra under 9.5 | 10.0 | 0.471 (Low) | pass | model 50% (against), market 45% (against) | correlated | variance | same game script as #2285 (variance); own read: variance; we priced this side at 47%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2319 | Grayson Allen ra under 7.5 | 10.0 | 0.4888 (Low) | pass | model 65%, market 49% (against) | correlated | role/lineup | same game script as #2311 (variance); own read: model bias; we priced this side at 49%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 2326 | Trey Lyles pts over 5.5 | 2.0 | 0.5358 (Low) | pass | model 67%, market 54% | correlated | role/lineup | same game script as #2300 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2329 | Collin Gillespie pts under 8.0 | 13.0 | 0.5165 (Low) | pass | model 50% (against), market 48% (against) | correlated | role/lineup | same game script as #2311 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2330 | Ryan Kalkbrenner pra over 10.5 | 9.0 | 0.5135 (Low) | pass | model 81%, market 52% | correlated | role/lineup | same game script as #2311 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2331 | Duncan Robinson pr over 18.5 | 16.0 | 0.5032 (Low) | pass | model 54%, market 49% (against) | correlated | variance | same game script as #2290 (variance); own read: model bias; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 2332 | Jake Sanderson nhl_points over 0.5 | 0.0 | 0.5743 (Low) | pass | model 50% (against), market 53% | variance | **untagged** | root leg of a 2-leg script loss: #2332, #2351; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2336 | Dylan Holloway nhl_points over 0.5 | 0.0 | 0.5786 (Low) | pass | model 44% (against), market 55% | variance | **untagged** | logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2338 | Nick Suzuki nhl_fow over 9.5 | 8.0 | 0.4691 (Low) | pass | model 35% (against) | variance | **untagged** | root leg of a 2-leg script loss: #2338, #2347; we priced this side at 47%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 2339 | Matthew Schaefer nhl_blocks under 1.5 | 3.0 | 0.5027 (Low) | pass | model 72%, market 49% (against) | model bias | **untagged** | logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 2340 | Zach Werenski nhl_toi over 28.0 | 26.28 | 0.3816 (Low) | pass | model 25% (against) | variance | **untagged** | root leg of a 3-leg script loss: #2340, #2348, #2354; we priced this side at 38%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 2344 | Jack Roslovic nhl_points over 0.5 | 0.0 | 0.5276 (Low) | pass | model 46% (against), market 48% (against) | variance | **untagged** | logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2347 | Pavel Zacha nhl_sog under 2.0 | 3.0 | 0.5307 (Low) | pass | model 60%, market 59% | correlated | **untagged** | same game script as #2338 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2348 | Matthew Knies nhl_points under 0.5 | 1.0 | 0.4756 (Low) | pass | model 57%, market 48% (against) | correlated | **untagged** | same game script as #2340 (variance); own read: model bias; we priced this side at 48%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 2350 | Jack Hughes nhl_assists over 0.5 | 0.0 | 0.5393 (Low) | pass | model 59%, market 51% | variance | **untagged** | logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2351 | Artturi Lehkonen nhl_sog over 1.5 | 1.0 | 0.514 (Low) | pass | model 61%, market 52% | correlated | **untagged** | same game script as #2332 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2354 | Matthew Knies nhl_sog under 1.5 | 3.0 | 0.47 (Low) | pass | model 60%, market 51% | correlated | **untagged** | same game script as #2340 (variance); own read: variance; we priced this side at 47%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 2362 | Aryna Sabalenka tennis_games under 22.5 | 25.0 | 0.5232 (Low) | pass | model 61%, market 50% (against) | variance | **untagged** | logged as a PASS: no money on it; reviewed for calibration |

Lessons:
- #2289: 8 assists in 35 min (as projected)
- #2295: Cunningham 48 min vs 32 projected in a 144-140 game: 52 pts, 11 ast
- #2300: 25 min in a 39-point win; 9 assists
- #2316: 3 assists in 34 min (as projected)
- #2317: 18 min vs 15 projected; 13 pts (box name Christian Anderson)
- #2318: 10 vs 9.5 at projected minutes
- #2319: Grayson Allen 34 min vs 27.5 projected
- #2326: Lyles 15 min vs 22 projected, 1 shot, in a 39-point win
- #2329: Gillespie 27 min vs 22 projected; 3-9 from three
- #2330: Kalkbrenner 16 min vs 25 projected: the L28 minutes warning (over needs minutes) fired and was right
- #2331: 41 min (more than projected) in a 144-140 game; 5-14 FG

Detail from the feeds:
- #2332 Jake Sanderson: error=HTTPError
- #2336 Dylan Holloway: error=HTTPError
- #2338 Nick Suzuki: error=HTTPError
- #2339 Matthew Schaefer: error=HTTPError
- #2340 Zach Werenski: error=HTTPError
- #2344 Jack Roslovic: error=HTTPError
- #2347 Pavel Zacha: error=HTTPError
- #2348 Matthew Knies: error=HTTPError
- #2350 Jack Hughes: error=HTTPError
- #2351 Artturi Lehkonen: error=HTTPError
- #2354 Matthew Knies: error=HTTPError

## 2026-11-11: 70 losses from 24 independent causes

| # | Leg | Result | Our p | Action | Sources | Auto tag | Confirmed | Evidence |
|---|---|---|---|---|---|---|---|---|
| 2128 | Ja'Kobe Walter pra under 19.5 | 21.0 | 0.5537 (Medium) | pass | model 56%, market 52% | variance | **untagged** | root leg of a 2-leg script loss: #2128, #2130; logged as a PASS: no money on it; reviewed for calibration |
| 2130 | Derrick White ast under 4.5 | 7.0 | 0.5488 (Medium) | pass | model 44% (against), market 45% (against) | correlated | **untagged** | same game script as #2128 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2133 | Pascal Siakam ra under 10.5 | 13.0 | 0.5719 (Medium) | pass | model 60%, market 55% | variance | **untagged** | root leg of a 7-leg script loss: #2133, #2134, #2142, #2210, #2211, #2212, #2220; logged as a PASS: no money on it; reviewed for calibration |
| 2134 | Kelly Oubre Jr. pts under 9.5 | 14.0 | 0.5539 (Medium) | pass | model 75%, market 55% | correlated | **untagged** | same game script as #2133 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2142 | Andrew Nembhard ast under 7.0 | 10.0 | 0.5855 (Medium) | pass | model 50%, market 48% (against) | correlated | **untagged** | same game script as #2133 (variance); own read: model bias; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 2143 | Nikola Jokić pts under 25.5 | 27.0 | 0.5619 (Medium) | pass | model 59%, market 52% | variance | **untagged** | root leg of a 6-leg script loss: #2143, #2144, #2146, #2148, #2151, #2152; logged as a PASS: no money on it; reviewed for calibration |
| 2144 | Jaylen Wells pra under 14.5 | 25.0 | 0.565 (Medium) | pass | model 60%, market 53% | correlated | **untagged** | same game script as #2143 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2146 | Christian Braun pts under 11.5 | 12.0 | 0.5404 (Medium) | pass | model 56%, market 50% (against) | correlated | **untagged** | same game script as #2143 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2148 | Cedric Coward ra under 9.5 | 15.0 | 0.5646 (Medium) | pass | model 59%, market 54% | correlated | **untagged** | same game script as #2143 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2151 | Cedric Coward ast under 2.5 | 4.0 | 0.6043 (Medium) | pass | model 54%, market 50% (against) | correlated | **untagged** | same game script as #2143 (variance); own read: model bias; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 2152 | Ty Jerome tpm over 2.5 | 1.0 | 0.5413 (Medium) | pass | model 56%, market 53% | correlated | **untagged** | same game script as #2143 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2153 | Zion Williamson pts under 21.5 | 29.0 | 0.542 (Medium) | pass | model 55%, market 50% | variance | **untagged** | logged as a PASS: no money on it; reviewed for calibration |
| 2161 | Nic Claxton pra under 16.5 | 24.0 | 0.7 (Low) | pass | model 70%, market 68% | variance | **untagged** | root leg of a 3-leg script loss: #2161, #2162, #2203; logged as a PASS: no money on it; reviewed for calibration |
| 2162 | Julian Champagnie pts under 10.5 | 12.0 | 0.5645 (Medium) | pass | model 58%, market 52% | correlated | **untagged** | same game script as #2161 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2164 | Jaime Jaquez Jr. pra under 23.5 | 33.0 | 0.5509 (Medium) | pass | model 57%, market 52% | variance | **untagged** | root leg of a 5-leg script loss: #2164, #2169, #2170, #2172, #2214; logged as a PASS: no money on it; reviewed for calibration |
| 2169 | Austin Reaves reb over 3.5 | 3.0 | 0.5587 (Medium) | pass | model 53%, market 55% | correlated | **untagged** | same game script as #2164 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2170 | Collin Sexton ast under 2.5 | 3.0 | 0.5773 (Medium) | pass | model 42% (against), market 49% (against) | correlated | **untagged** | same game script as #2164 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2172 | Ziaire Williams reb over 2.5 | 1.0 | 0.5552 (Medium) | pass | model 57%, market 54% | correlated | **untagged** | same game script as #2164 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2173 | Franz Wagner pra under 38.5 | 47.0 | 0.54 (Medium) | pass | model 56%, market 51% | variance | **untagged** | root leg of a 7-leg script loss: #2173, #2174, #2175, #2176, #2177, #2179, #2233; logged as a PASS: no money on it; reviewed for calibration |
| 2174 | Franz Wagner pts under 24.0 | 38.0 | 0.5443 (Medium) | pass | model 58%, market 50% (against) | correlated | **untagged** | same game script as #2173 (variance); own read: model bias; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 2175 | Ace Bailey pra under 23.5 | 27.0 | 0.5833 (Medium) | pass | model 55%, market 56% | correlated | **untagged** | same game script as #2173 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2176 | Wendell Carter Jr. reb over 8.5 | 7.0 | 0.5458 (Medium) | pass | model 51%, market 54% | correlated | **untagged** | same game script as #2173 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2177 | Jaxson Hayes ra under 7.5 | 8.0 | 0.5417 (Medium) | pass | model 55%, market 52% | correlated | **untagged** | same game script as #2173 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2179 | Wendell Carter Jr. ast under 1.5 | 3.0 | 0.6062 (Low) | pass | model 54% | correlated | **untagged** | same game script as #2173 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2180 | Brandin Podziemski pra under 23.5 | 32.0 | 0.5553 (Medium) | pass | model 57%, market 52% | variance | **untagged** | root leg of a 13-leg script loss: #2180, #2183, #2184, #2185, #2186, #2187, #2188, #2190, #2191, #2192, #2193, #2194, #2196; logged as a PASS: no money on it; reviewed for calibration |
| 2183 | Yaxel Lendeborg pts under 18.5 | 25.0 | 0.5569 (Medium) | pass | model 57%, market 52% | correlated | **untagged** | same game script as #2180 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2184 | Draymond Green pra under 16.5 | 19.0 | 0.5491 (Medium) | pass | model 64%, market 55% | correlated | **untagged** | same game script as #2180 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2185 | Amen Thompson pts under 15.5 | 19.0 | 0.568 (Medium) | pass | model 59%, market 53% | correlated | variance | same game script as #2180 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2186 | Brandin Podziemski pts under 15.5 | 22.0 | 0.5783 (Medium) | pass | model 60%, market 54% | correlated | **untagged** | same game script as #2180 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2187 | De'Anthony Melton pra under 14.5 | 19.0 | 0.5515 (Medium) | pass | model 51%, market 53% | correlated | **untagged** | same game script as #2180 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2188 | Draymond Green ra under 11.5 | 12.0 | 0.5457 (Medium) | pass | model 66%, market 55% | correlated | **untagged** | same game script as #2180 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2190 | Reed Sheppard pts under 8.5 | 13.0 | 0.556 (Medium) | pass | model 50%, market 53% | correlated | **untagged** | same game script as #2180 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2191 | Alperen Şengün ast under 6.5 | 9.0 | 0.5943 (Medium) | pass | model 45% (against), market 51% | correlated | **untagged** | same game script as #2180 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2192 | Draymond Green ast under 6.0 | 7.0 | 0.6169 (Medium) | pass | model 55%, market 51% | correlated | **untagged** | same game script as #2180 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2193 | Fred VanVleet ast under 5.0 | 6.0 | 0.6352 (Medium) | lean | model 59%, market 53% | correlated | variance | same game script as #2180 (variance); own read: variance |
| 2194 | Draymond Green pts under 4.5 | 7.0 | 0.5512 (Medium) | pass | model 55%, market 52% | correlated | variance | same game script as #2180 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2196 | Kevin Durant ast under 3.5 | 5.0 | 0.6313 (Medium) | pass | model 53%, market 54% | correlated | **untagged** | same game script as #2180 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2197 | Jared McCain pra under 18.5 | 19.0 | 0.5417 (Medium) | pass | model 52%, market 52% | variance | **untagged** | root leg of a 4-leg script loss: #2197, #2198, #2201, #2228; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2198 | Sidy Cissoko pra under 13.5 | 21.0 | 0.5459 (Medium) | pass | model 58%, market 51% | correlated | **untagged** | same game script as #2197 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2201 | Isaiah Hartenstein pa under 13.5 | 26.0 | 0.501 (Low) | pass | model 69%, market 52% | correlated | role/lineup | same game script as #2197 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2203 | Luke Kornet pra under 12.5 | 13.0 | 0.5323 (Low) | pass | model 64%, market 53% | correlated | variance | same game script as #2161 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2210 | Obi Toppin pr over 15.5 | 11.0 | 0.4765 (Low) | pass | model 30% (against), market 52% | correlated | variance | same game script as #2133 (variance); own read: variance; we priced this side at 48%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 2211 | Ivica Zubac pr under 23.5 | 32.0 | 0.5092 (Low) | pass | model 83%, market 51% | correlated | role/lineup | same game script as #2133 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2212 | Jarace Walker reb over 4.5 | 1.0 | 0.4571 (Low) | pass | model 40% (against), market 46% (against) | correlated | opportunity | same game script as #2133 (variance); own read: variance; we priced this side at 46%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 2214 | Kyle Kuzma ast over 2.5 | 1.0 | 0.4863 (Low) | pass | model 55%, market 52% | correlated | variance | same game script as #2164 (variance); own read: variance; we priced this side at 49%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 2215 | Jarrett Allen ra under 9.0 | 17.0 | 0.5665 (Low) | pass | model 74% | variance | role/lineup | root leg of a 2-leg script loss: #2215, #2226; logged as a PASS: no money on it; reviewed for calibration |
| 2220 | Ivica Zubac pa under 15.5 | 21.0 | 0.5224 (Low) | pass | model 79%, market 52% | correlated | role/lineup | same game script as #2133 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2226 | James Harden pr under 20.5 | 34.0 | 0.5142 (Low) | pass | model 62%, market 51% | correlated | variance | same game script as #2215 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2228 | Isaiah Hartenstein pra under 23.5 | 37.0 | 0.5112 (Low) | pass | model 68%, market 51% | correlated | role/lineup | same game script as #2197 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2233 | Desmond Bane pts under 19.5 | 25.0 | 0.5 (Low) | pass | model 60%, market 50% (against) | correlated | variance | same game script as #2173 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2234 | Sebastian Aho nhl_sog over 2.5 | 2.0 | 0.4777 (Low) | pass | model 53% | variance | **untagged** | root leg of a 2-leg script loss: #2234, #2271; we priced this side at 48%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2235 | Cale Makar nhl_sog over 2.5 | 2.0 | 0.4683 (Low) | pass | model 48% (against) | variance | **untagged** | we priced this side at 47%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2236 | Viktor Arvidsson nhl_sog over 2.5 | 1.0 | 0.4731 (Low) | pass | model 50% | variance | **untagged** | we priced this side at 47%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 2238 | David Pastrnak nhl_sog over 3.5 | 3.0 | 0.4722 (Low) | pass | model 50% | variance | **untagged** | we priced this side at 47%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2240 | Trevor Zegras nhl_points over 0.5 | 0.0 | 0.5583 (Low) | pass | model 45% (against), market 52% | variance | **untagged** | root leg of a 2-leg script loss: #2240, #2261; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2244 | Jackson LaCombe nhl_sog under 1.5 | 2.0 | 0.4474 (Low) | pass | model 63%, market 48% (against) | model bias | **untagged** | we priced this side at 45%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 2250 | Tyson Kozak nhl_blocks under 0.5 | 1.0 | 0.4584 (Low) | pass | model 48% (against) | variance | **untagged** | we priced this side at 46%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2254 | Vincent Trocheck nhl_toi under 18.75 | 20.23 | 0.4476 (Low) | pass | model 41% (against) | variance | **untagged** | we priced this side at 45%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 2261 | Zach Hyman nhl_points under 0.5 | 2.0 | 0.5224 (Low) | pass | model 60%, market 53% | correlated | **untagged** | same game script as #2240 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2267 | Justin Brazeau nhl_blocks under 0.5 | 1.0 | 0.4762 (Low) | pass | model 57% | variance | **untagged** | we priced this side at 48%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2269 | William Nylander nhl_sog over 2.5 | 1.0 | 0.4542 (Low) | pass | model 41% (against) | variance | **untagged** | we priced this side at 45%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 2271 | Jordan Eberle nhl_sog over 1.5 | 0.0 | 0.4757 (Low) | pass | model 52% | correlated | **untagged** | same game script as #2234 (variance); own read: variance; we priced this side at 48%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 2274 | Wyatt Johnston nhl_sog under 2.5 | 4.0 | 0.445 (Low) | pass | model 52% | variance | **untagged** | we priced this side at 44%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 2275 | Aryna Sabalenka tennis_games over 22.5 | 16.0 | 0.4801 (Low) | pass | model 40% (against), market 50% (against) | variance | **untagged** | we priced this side at 48%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 2278 | Coco Gauff tennis_games_won under 12.5 | 13.0 | 0.6102 (Low) | pass | model 61% | variance | **untagged** | root leg of a 3-leg script loss: #2278, #2282, #2283; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2279 | Jessica Pegula tennis_games under 22.5 | 35.0 | 0.592 (Low) | pass | model 59% | variance | **untagged** | root leg of a 3-leg script loss: #2279, #2280, #2281; logged as a PASS: no money on it; reviewed for calibration |
| 2280 | Linda Noskova tennis_games_won under 12.5 | 17.0 | 0.6305 (Low) | pass | model 63% | correlated | **untagged** | same game script as #2279 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2281 | Jessica Pegula tennis_games_won under 12.5 | 18.0 | 0.5731 (Low) | pass | model 57% | correlated | **untagged** | same game script as #2279 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2282 | Marta Kostyuk tennis_games_won over 11.5 | 9.0 | 0.5193 (Low) | pass | model 52% | correlated | **untagged** | same game script as #2278 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2283 | Coco Gauff tennis_games under 21.5 | 22.0 | 0.5145 (Low) | pass | model 57%, market 50% (against) | correlated | **untagged** | same game script as #2278 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |

Lessons:
- #2185: 29 min as projected; 8-11 FG for 19
- #2193: 6 ast in 30 min (as projected)
- #2194: 7 pts on 3-5 in 27 min (as projected)
- #2201: Hartenstein 34 min vs 22 projected with Holmgren out
- #2203: 13 vs 12.5, 14 min as projected
- #2210: 11 in 16 min; priced 48%
- #2211: Zubac 31 min vs 17.5 projected (L35)
- #2212: Walker 7 min vs 17 projected: dropped from the rotation; priced 46%
- #2214: 1 assist in 24 min; priced 49%
- #2215: Allen 32 min vs 20 projected: a 7-minute game in his last 5 pulled the projection down (L35)
- #2220: Zubac 31 min vs 17.5 projected: a 7-minute game in his last 5 pulled the projection down (L35)
- #2226: 33 min vs 29 projected; 32 pts on 5-7 from three
- #2228: Hartenstein 34 min vs 22 projected with Chet Holmgren out: freed frontcourt minutes (L28 open work)
- #2233: minutes WARN fired (33 vs 37 last 5); 34 min, 7-11 from three

Detail from the feeds:
- #2234 Sebastian Aho: error=HTTPError
- #2235 Cale Makar: error=HTTPError
- #2236 Viktor Arvidsson: error=HTTPError
- #2238 David Pastrnak: error=HTTPError
- #2240 Trevor Zegras: error=HTTPError
- #2244 Jackson LaCombe: error=HTTPError
- #2250 Tyson Kozak: error=HTTPError
- #2254 Vincent Trocheck: error=HTTPError
- #2261 Zach Hyman: error=HTTPError
- #2267 Justin Brazeau: error=HTTPError
- #2269 William Nylander: error=HTTPError
- #2271 Jordan Eberle: error=HTTPError
- #2274 Wyatt Johnston: error=HTTPError

## 2026-11-10: 43 losses from 15 independent causes

| # | Leg | Result | Our p | Action | Sources | Auto tag | Confirmed | Evidence |
|---|---|---|---|---|---|---|---|---|
| 1998 | Andre Drummond ra under 8.5 | 17.0 | 0.5509 (Medium) | pass | model 51%, market 54% | variance | **untagged** | logged as a PASS: no money on it; reviewed for calibration |
| 2002 | Payton Pritchard pra under 19.5 | 29.0 | 0.5481 (Medium) | pass | model 57%, market 52% | variance | **untagged** | root leg of a 7-leg script loss: #2002, #2003, #2004, #2006, #2010, #2041, #2120; logged as a PASS: no money on it; reviewed for calibration |
| 2003 | Payton Pritchard pr under 15.5 | 24.0 | 0.5405 (Medium) | pass | model 58%, market 54% | correlated | **untagged** | same game script as #2002 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2004 | Payton Pritchard pts under 12.5 | 18.0 | 0.5503 (Medium) | pass | model 57%, market 52% | correlated | **untagged** | same game script as #2002 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2006 | Payton Pritchard ra under 6.5 | 11.0 | 0.5815 (Medium) | pass | model 54%, market 57% | correlated | **untagged** | same game script as #2002 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2010 | Payton Pritchard ast under 3.5 | 5.0 | 0.5964 (Medium) | pass | model 50%, market 51% | correlated | **untagged** | same game script as #2002 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2013 | Collin Gillespie pra under 16.5 | 22.0 | 0.5406 (Medium) | pass | model 56%, market 51% | variance | variance | root leg of a 2-leg script loss: #2013, #2035; logged as a PASS: no money on it; reviewed for calibration |
| 2016 | Pelle Larsson ra under 7.5 | 9.0 | 0.6134 (Medium) | lean | model 66%, market 58% | variance | role/lineup | root leg of a 5-leg script loss: #2016, #2031, #2032, #2098, #2114 |
| 2018 | Anthony Black ra under 10.0 | 12.0 | 0.5543 (Medium) | pass | model 50% (against), market 55% | variance | **untagged** | root leg of a 5-leg script loss: #2018, #2102, #2103, #2104, #2107; logged as a PASS: no money on it; reviewed for calibration |
| 2027 | Sidy Cissoko pts under 5.5 | 17.0 | 0.5723 (Medium) | pass | model 56%, market 55% | variance | **untagged** | root leg of a 8-leg script loss: #2027, #2028, #2030, #2034, #2036, #2039, #2045, #2118; logged as a PASS: no money on it; reviewed for calibration |
| 2028 | Deni Avdija ast under 6.0 | 8.0 | 0.5973 (Low) | pass | model 45% (against), market 53% | correlated | **untagged** | same game script as #2027 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2030 | Isaiah Hartenstein ast under 4.0 | 5.0 | 0.5514 (Medium) | pass | model 68%, market 55% | correlated | **untagged** | same game script as #2027 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2031 | Isaiah Collier pts under 9.5 | 17.0 | 0.5083 (Low) | pass | model 64%, market 51% | correlated | role/lineup | same game script as #2016 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2032 | Darryn Peterson pra under 29.5 | 33.0 | 0.5209 (Low) | pass | model 61%, market 52% | correlated | variance | same game script as #2016 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2034 | Scoot Henderson tpm under 1.5 | 3.0 | 0.4975 (Low) | pass | model 53%, market 52% | correlated | variance | same game script as #2027 (variance); own read: variance; we priced this side at 50%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 2035 | Keaton Wagler ra over 5.0 | 4.0 | 0.4566 (Low) | pass | model 63% | correlated | variance | same game script as #2013 (variance); own read: variance; we priced this side at 46%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 2036 | Alex Caruso pra over 12.0 | 8.0 | 0.4422 (Low) | pass | model 45% (against), market 52% | correlated | variance | same game script as #2027 (variance); own read: variance; we priced this side at 44%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 2039 | Donovan Clingan ra under 13.0 | 16.0 | 0.4962 (Low) | pass | model 67%, market 50% (against) | correlated | **untagged** | same game script as #2027 (variance); own read: model bias; we priced this side at 50%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 2041 | Jayson Tatum ast over 6.5 | 4.0 | 0.4893 (Low) | pass | model 48% (against), market 54% | correlated | **untagged** | same game script as #2002 (variance); own read: variance; we priced this side at 49%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 2045 | Donovan Clingan reb under 11.0 | 13.0 | 0.516 (Low) | pass | model 68%, market 52% | correlated | variance | same game script as #2027 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2048 | Viktor Arvidsson nhl_points over 0.5 | 0.0 | 0.5844 (Low) | pass | model 48% (against), market 52% | variance | **untagged** | logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2050 | Quinton Byfield nhl_points over 0.5 | 0.0 | 0.5742 (Low) | pass | model 43% (against), market 52% | variance | **untagged** | root leg of a 2-leg script loss: #2050, #2065; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2051 | Alex Tuch nhl_sog over 2.0 | 0.0 | 0.5819 (Medium) | lean | model 65%, market 60% | variance | **untagged** | root leg of a 3-leg script loss: #2051, #2053, #2054 |
| 2052 | Kent Johnson nhl_points over 0.5 | 0.0 | 0.5818 (Low) | pass | model 43% (against), market 53% | variance | **untagged** | logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2053 | Tom Wilson nhl_points under 0.5 | 1.0 | 0.5334 (Low) | pass | model 69%, market 53% | correlated | **untagged** | same game script as #2051 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2054 | Jake Sanderson nhl_blocks under 1.5 | 2.0 | 0.4472 (Low) | pass | model 53% | correlated | **untagged** | same game script as #2051 (variance); own read: variance; we priced this side at 45%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2059 | Phillip Danault nhl_blocks under 0.5 | 3.0 | 0.4583 (Low) | pass | model 59% | variance | **untagged** | root leg of a 3-leg script loss: #2059, #2063, #2069; we priced this side at 46%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 2062 | Gabriel Landeskog nhl_sog under 1.5 | 4.0 | 0.4352 (Low) | pass | model 53%, market 48% (against) | model bias | **untagged** | root leg of a 2-leg script loss: #2062, #2070; we priced this side at 44%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 2063 | Nick Suzuki nhl_toi over 20.5 | 18.27 | 0.409 (Low) | pass | model 40% (against) | correlated | **untagged** | same game script as #2059 (variance); own read: variance; we priced this side at 41%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 2065 | Drew Doughty nhl_toi under 22.25 | 22.37 | 0.4817 (Low) | pass | model 52% | correlated | **untagged** | same game script as #2050 (variance); own read: variance; we priced this side at 48%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2069 | Juraj Slafkovský nhl_blocks over 0.5 | 0.0 | 0.5125 (Low) | pass | model 56% | correlated | **untagged** | same game script as #2059 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2070 | Nick Paul nhl_blocks over 0.5 | 0.0 | 0.5097 (Low) | pass | model 55% | correlated | **untagged** | same game script as #2062 (model bias); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2075 | Jessica Pegula tennis_games_won under 12.5 | 13.0 | 0.6004 (Low) | pass | model 60% | variance | **untagged** | logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2086 | Karolina Muchova tennis_games under 21.5 | 25.0 | 0.508 (Low) | pass | model 54%, market 50% (against) | variance | **untagged** | logged as a PASS: no money on it; reviewed for calibration |
| 2098 | Davion Mitchell ra under 10.5 | 13.0 | 0.549 (Medium) | pass | model 52%, market 53% | correlated | **untagged** | same game script as #2016 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2102 | Anthony Black pra under 26.5 | 38.0 | 0.5448 (Medium) | pass | model 56%, market 52% | correlated | **untagged** | same game script as #2018 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2103 | Franz Wagner pts under 24.5 | 33.0 | 0.5459 (Medium) | pass | model 56%, market 52% | correlated | **untagged** | same game script as #2018 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2104 | De'Andre Hunter pra under 19.5 | 21.0 | 0.5812 (Medium) | pass | model 56%, market 56% | correlated | **untagged** | same game script as #2018 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2107 | De'Andre Hunter pts under 13.5 | 15.0 | 0.5413 (Medium) | pass | model 56%, market 51% | correlated | **untagged** | same game script as #2018 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2114 | Isaiah Collier tpm under 0.5 | 4.0 | 0.5081 (Low) | pass | model 67%, market 51% | correlated | variance | same game script as #2016 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 2118 | Scoot Henderson ra under 4.5 | 5.0 | 0.503 (Low) | pass | model 47% (against), market 49% (against) | correlated | variance | same game script as #2027 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 2120 | Tyrese Maxey pra over 32.5 | 29.0 | 0.4429 (Low) | pass | model 42% (against), market 53% | correlated | variance | same game script as #2002 (variance); own read: variance; we priced this side at 44%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 2123 | Lucia Bronzetti tennis_games under 21.5 | 22.0 | 0.5736 (Low) | pass | model 57% | variance | **untagged** | logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |

Lessons:
- #2013: 4-9 from three in 22 min (as projected); withdrawn in the afternoon (More-only)
- #2016: Larsson 31 min vs 26.2 projected; 7 reb + 2 ast = 9
- #2031: Collier 24 min vs 16 projected; 4-4 from three
- #2032: 31 min as projected; 10-19 FG
- #2034: 3-5 from three in 23 min
- #2035: 0 rebounds in 23 min (more minutes than projected); priced 46%
- #2036: 1-5 FG in 19 min; priced 44%
- #2045: 13 reb at 26 min (as projected)
- #2114: 4-4 from three in 24 min; an under 0.5 threes line needs a zero
- #2118: 5 vs 4.5 (by the minimum) in 23 min
- #2120: 24 pts, 1 reb in 34 min (as projected) in a 22-point loss; priced 44%

Detail from the feeds:
- #2048 Viktor Arvidsson: error=HTTPError
- #2050 Quinton Byfield: error=HTTPError
- #2051 Alex Tuch: error=HTTPError
- #2052 Kent Johnson: error=HTTPError
- #2053 Tom Wilson: error=HTTPError
- #2054 Jake Sanderson: error=HTTPError
- #2059 Phillip Danault: error=HTTPError
- #2062 Gabriel Landeskog: error=HTTPError
- #2063 Nick Suzuki: error=HTTPError
- #2065 Drew Doughty: error=HTTPError
- #2069 Juraj Slafkovský: error=HTTPError
- #2070 Nick Paul: error=HTTPError

## 2026-11-09: 103 losses from 14 independent causes

| # | Leg | Result | Our p | Action | Sources | Auto tag | Confirmed | Evidence |
|---|---|---|---|---|---|---|---|---|
| 1777 | AJ Dybantsa pr under 23.5 | 29.0 | 0.5891 (Low) | pass | model 74% | variance | **untagged** | root leg of a 12-leg script loss: #1777, #1778, #1780, #1781, #1825, #1871, #1873, #1874, #1875, #1876, #1928, #1993; logged as a PASS: no money on it; reviewed for calibration |
| 1778 | Duncan Robinson pr under 18.5 | 25.0 | 0.5484 (Medium) | pass | model 52%, market 51% | correlated | **untagged** | same game script as #1777 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1780 | John Collins pts under 11.5 | 24.0 | 0.5447 (Medium) | pass | model 49% (against), market 49% (against) | correlated | variance | same game script as #1777 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1781 | Paul Reed ra under 10.5 | 12.0 | 0.5408 (Medium) | pass | model 51%, market 52% | correlated | **untagged** | same game script as #1777 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1783 | Jakob Poeltl pts under 10.5 | 18.0 | 0.5481 (Medium) | pass | model 70%, market 55% | variance | **untagged** | root leg of a 13-leg script loss: #1783, #1784, #1785, #1787, #1827, #1842, #1888, #1889, #1916, #1926, #1927, #1962, #1992; logged as a PASS: no money on it; reviewed for calibration |
| 1784 | Jakob Poeltl ra under 9.5 | 10.0 | 0.5371 (Low) | pass | model 71%, market 54% | correlated | role/lineup | same game script as #1783 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1785 | Jakob Poeltl reb under 7.5 | 8.0 | 0.5481 (Medium) | pass | model 68%, market 55% | correlated | **untagged** | same game script as #1783 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1787 | Jaylen Wells tpm under 1.5 | 4.0 | 0.5405 (Medium) | pass | model 55%, market 50% | correlated | **untagged** | same game script as #1783 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1790 | Kevin Durant pts under 20.5 | 23.0 | 0.5656 (Medium) | pass | model 55%, market 50% | variance | **untagged** | root leg of a 13-leg script loss: #1790, #1793, #1794, #1795, #1796, #1797, #1900, #1901, #1919, #1930, #1971, #1972, #1973; logged as a PASS: no money on it; reviewed for calibration |
| 1793 | Tari Eason pr under 15.5 | 17.0 | 0.5561 (Medium) | pass | model 52%, market 52% | correlated | **untagged** | same game script as #1790 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1794 | Kevin Durant ra under 9.5 | 20.0 | 0.5964 (Medium) | pass | model 60%, market 56% | correlated | **untagged** | same game script as #1790 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1795 | Jabari Smith Jr. ra under 8.5 | 10.0 | 0.5438 (Medium) | pass | model 49% (against), market 52% | correlated | **untagged** | same game script as #1790 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1796 | Kevin Durant reb under 5.5 | 12.0 | 0.5561 (Medium) | pass | model 56%, market 56% | correlated | **untagged** | same game script as #1790 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1797 | Fred VanVleet tpm under 2.5 | 3.0 | 0.5511 (Medium) | pass | model 51%, market 53% | correlated | **untagged** | same game script as #1790 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1798 | Devin Booker pts under 24.5 | 32.0 | 0.5586 (Medium) | pass | model 54%, market 50% (against) | model bias | **untagged** | root leg of a 13-leg script loss: #1798, #1800, #1801, #1805, #1808, #1810, #1812, #1813, #1819, #1870, #1975, #1977, #1988; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 1800 | Dylan Harper pts under 16.5 | 17.0 | 0.5575 (Medium) | pass | model 52%, market 50% | correlated | **untagged** | same game script as #1798 (model bias); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1801 | De'Aaron Fox pr under 16.5 | 24.0 | 0.5411 (Medium) | pass | model 52%, market 50% (against) | correlated | **untagged** | same game script as #1798 (model bias); own read: model bias; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 1805 | De'Aaron Fox pts under 13.5 | 15.0 | 0.5715 (Medium) | pass | model 54%, market 51% | correlated | **untagged** | same game script as #1798 (model bias); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1808 | Julian Champagnie pts under 9.5 | 11.0 | 0.579 (Medium) | pass | model 55%, market 52% | correlated | **untagged** | same game script as #1798 (model bias); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1810 | Stephon Castle ast under 5.5 | 7.0 | 0.5528 (Medium) | pass | model 53%, market 50% (against) | correlated | **untagged** | same game script as #1798 (model bias); own read: model bias; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 1812 | Stephon Castle tpm over 1.5 | 0.0 | 0.5523 (Medium) | pass | model 66%, market 55% | correlated | **untagged** | same game script as #1798 (model bias); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1813 | Keldon Johnson tpm over 0.5 | 0.0 | 0.5479 (Medium) | pass | model 59%, market 52% | correlated | **untagged** | same game script as #1798 (model bias); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1819 | Miles Bridges pra over 24.5 | 12.0 | 0.4836 (Low) | pass | model 62%, market 50% | correlated | opportunity | same game script as #1798 (model bias); own read: variance; we priced this side at 48%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 1820 | Tyrese Maxey pra over 33.5 | 29.0 | 0.4117 (Low) | pass | model 39% (against), market 50% (against) | variance | **untagged** | root leg of a 2-leg script loss: #1820, #1823; we priced this side at 41%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 1823 | Jaylen Brown ast over 3.5 | 2.0 | 0.4999 (Low) | pass | model 56%, market 53% | correlated | opportunity | same game script as #1820 (variance); own read: variance; we priced this side at 50%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 1825 | John Collins pr under 17.5 | 34.0 | 0.5305 (Low) | pass | model 49% (against), market 49% (against) | correlated | **untagged** | same game script as #1777 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1827 | Ja'Kobe Walter pts under 11.5 | 12.0 | 0.4812 (Low) | pass | model 56%, market 48% (against) | correlated | **untagged** | same game script as #1783 (variance); own read: model bias; we priced this side at 48%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 1842 | Cameron Boozer pts under 17.5 | 22.0 | 0.5031 (Low) | pass | model 66%, market 50% | correlated | **untagged** | same game script as #1783 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1844 | Jacob Trouba nhl_toi under 21.5 | 23.37 | 0.537 (Low) | pass | model 62% | variance | **untagged** | root leg of a 5-leg script loss: #1844, #1851, #1855, #1860, #1943; logged as a PASS: no money on it; reviewed for calibration |
| 1847 | Max Jones nhl_hits under 2.0 | 3.0 | 0.5618 (Low) | pass | model 83% | variance | **untagged** | root leg of a 5-leg script loss: #1847, #1850, #1853, #1854, #1940; logged as a PASS: no money on it; reviewed for calibration |
| 1850 | Adam Fox nhl_assists over 0.5 | 0.0 | 0.5549 (Low) | pass | model 54%, market 54% | correlated | **untagged** | same game script as #1847 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1851 | Michael Misa nhl_sog under 1.5 | 5.0 | 0.4594 (Low) | pass | model 55%, market 49% (against) | correlated | **untagged** | same game script as #1844 (variance); own read: model bias; we priced this side at 46%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 1853 | Mattias Ekholm nhl_sog under 1.5 | 2.0 | 0.5095 (Low) | pass | model 64%, market 52% | correlated | **untagged** | same game script as #1847 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1854 | Eeli Tolvanen nhl_hits under 1.5 | 2.0 | 0.4899 (Low) | pass | model 53% | correlated | **untagged** | same game script as #1847 (variance); own read: variance; we priced this side at 49%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1855 | Macklin Celebrini nhl_toi under 23.25 | 25.67 | 0.4727 (Low) | pass | model 31% (against) | correlated | **untagged** | same game script as #1844 (variance); own read: variance; we priced this side at 47%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 1856 | Travis Sanheim nhl_blocks over 1.5 | 0.0 | 0.5021 (Low) | pass | model 48% (against), market 51% | variance | **untagged** | root leg of a 3-leg script loss: #1856, #1941, #1945; logged as a PASS: no money on it; reviewed for calibration |
| 1860 | Matthew Schaefer nhl_hits over 0.5 | 0.0 | 0.5042 (Low) | pass | model 52% | correlated | **untagged** | same game script as #1844 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1869 | Mirra Andreeva tennis_games over 22.0 | 16.0 | 0.4807 (Low) | pass | model 40% (against), market 50% (against) | variance | **untagged** | we priced this side at 48%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 1870 | Miles Bridges pr over 14.5 | 12.0 | 0.7 (Medium) | lean | model 86%, market 78% | correlated | opportunity | same game script as #1798 (model bias); own read: variance |
| 1871 | Duncan Robinson pts under 15.5 | 22.0 | 0.5449 (Medium) | pass | model 45% (against), market 50% | correlated | **untagged** | same game script as #1777 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1873 | Anthony Davis ra under 12.0 | 14.0 | 0.5914 (Low) | pass | model 60%, market 56% | correlated | **untagged** | same game script as #1777 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1874 | Daniss Jenkins pts under 10.5 | 22.0 | 0.5463 (Medium) | pass | model 46% (against), market 50% | correlated | **untagged** | same game script as #1777 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1875 | Ausar Thompson reb over 7.0 | 5.0 | 0.5074 (Low) | pass | model 59%, market 51% | correlated | variance | same game script as #1777 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1876 | AJ Dybantsa reb under 5.5 | 8.0 | 0.5446 (Medium) | pass | model 57%, market 54% | correlated | **untagged** | same game script as #1777 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1878 | Naz Reid ra under 11.0 | 17.0 | 0.5504 (Medium) | pass | model 54%, market 52% | variance | **untagged** | root leg of a 9-leg script loss: #1878, #1879, #1917, #1920, #1931, #1952, #1954, #1955, #1985; logged as a PASS: no money on it; reviewed for calibration |
| 1879 | Sion James tpm under 1.5 | 3.0 | 0.5795 (Medium) | lean | model 60%, market 54% | correlated | **untagged** | same game script as #1878 (variance); own read: variance |
| 1880 | Onyeka Okongwu pr under 21.5 | 25.0 | 0.5455 (Medium) | pass | model 55%, market 50% (against) | model bias | **untagged** | root leg of a 9-leg script loss: #1880, #1882, #1883, #1886, #1918, #1923, #1957, #1958, #1959; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 1882 | Walker Kessler pts under 13.5 | 21.0 | 0.5707 (Medium) | pass | model 52%, market 52% | correlated | **untagged** | same game script as #1880 (model bias); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1883 | Aaron Wiggins pts under 13.0 | 15.0 | 0.5523 (Medium) | pass | model 53%, market 49% (against) | correlated | **untagged** | same game script as #1880 (model bias); own read: model bias; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 1886 | Onyeka Okongwu tpm under 1.5 | 2.0 | 0.5405 (Medium) | pass | model 52%, market 51% | correlated | **untagged** | same game script as #1880 (model bias); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1888 | Jerami Grant pts under 10.5 | 17.0 | 0.5657 (Medium) | pass | model 52%, market 51% | correlated | **untagged** | same game script as #1783 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1889 | Jaylen Wells pts under 10.0 | 14.0 | 0.5733 (Medium) | pass | model 58%, market 51% | correlated | **untagged** | same game script as #1783 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1894 | P.J. Washington pr under 21.5 | 22.0 | 0.5696 (Medium) | pass | model 56%, market 52% | variance | **untagged** | root leg of a 7-leg script loss: #1894, #1897, #1922, #1965, #1966, #1990, #1996; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1897 | P.J. Washington ra under 8.5 | 10.0 | 0.5434 (Medium) | pass | model 55%, market 51% | correlated | **untagged** | same game script as #1894 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1900 | Nikola Jokić reb under 11.0 | 16.0 | 0.5387 (Low) | pass | model 79%, market 54% | correlated | model bias | same game script as #1790 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1901 | Tari Eason pts under 9.5 | 12.0 | 0.5645 (Medium) | pass | model 53%, market 51% | correlated | **untagged** | same game script as #1790 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1906 | Brandin Podziemski pts under 15.5 | 25.0 | 0.5607 (Medium) | pass | model 56%, market 50% (against) | model bias | **untagged** | root leg of a 9-leg script loss: #1906, #1907, #1909, #1910, #1912, #1929, #1982, #1983, #1984; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 1907 | Derik Queen pr under 15.5 | 20.0 | 0.5629 (Medium) | pass | model 55%, market 52% | correlated | **untagged** | same game script as #1906 (model bias); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1909 | De'Anthony Melton pts under 9.5 | 16.0 | 0.5722 (Medium) | pass | model 55%, market 51% | correlated | **untagged** | same game script as #1906 (model bias); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1910 | Derik Queen pts under 9.5 | 16.0 | 0.5767 (Medium) | pass | model 56%, market 52% | correlated | **untagged** | same game script as #1906 (model bias); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1912 | Georges Niang pts under 8.0 | 9.0 | 0.543 (Medium) | pass | model 48% (against), market 49% (against) | correlated | **untagged** | same game script as #1906 (model bias); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1916 | Cedric Coward reb over 6.5 | 6.0 | 0.5022 (Low) | pass | model 50%, market 50% | correlated | variance | same game script as #1783 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1917 | Royce O'Neale pts under 8.5 | 10.0 | 0.4719 (Low) | pass | model 60%, market 47% (against) | correlated | **untagged** | same game script as #1878 (variance); own read: model bias; we priced this side at 47%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 1918 | Luka Dončić tpm over 4.5 | 3.0 | 0.5216 (Low) | pass | model 46% (against), market 52% | correlated | variance | same game script as #1880 (model bias); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1919 | Fred VanVleet pa over 16.5 | 14.0 | 0.5013 (Low) | pass | model 60%, market 52% | correlated | **untagged** | same game script as #1790 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1920 | Peyton Watson ra over 6.5 | 3.0 | 0.4232 (Low) | pass | model 43% (against), market 51% | correlated | variance | same game script as #1878 (variance); own read: variance; we priced this side at 42%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 1922 | Obi Toppin pra over 17.5 | 16.0 | 0.4009 (Low) | pass | model 19% (against), market 52% | correlated | variance | same game script as #1894 (variance); own read: variance; we priced this side at 40%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 1923 | Luguentz Dort pra over 11.5 | 9.0 | 0.5109 (Low) | pass | model 69%, market 52% | correlated | role/lineup | same game script as #1880 (model bias); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1926 | Cameron Boozer pr under 26.5 | 29.0 | 0.527 (Low) | pass | model 67%, market 53% | correlated | **untagged** | same game script as #1783 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1927 | Jerami Grant pr under 12.5 | 20.0 | 0.5264 (Low) | pass | model 51%, market 48% (against) | correlated | **untagged** | same game script as #1783 (variance); own read: model bias; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 1928 | AJ Dybantsa pts under 17.5 | 21.0 | 0.5239 (Low) | pass | model 74%, market 52% | correlated | **untagged** | same game script as #1777 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1929 | Gui Santos pra under 13.5 | 14.0 | 0.5224 (Low) | pass | model 69%, market 52% | correlated | **untagged** | same game script as #1906 (model bias); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1930 | Amen Thompson reb under 7.0 | 9.0 | 0.5192 (Low) | pass | model 62%, market 52% | correlated | **untagged** | same game script as #1790 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1931 | Peyton Watson pts under 12.5 | 13.0 | 0.5125 (Low) | pass | model 64%, market 51% | correlated | **untagged** | same game script as #1878 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1934 | Aaron Jones Sr. rush_rec_yds over 45.5 | 21.0 | 0.6023 (Medium) | lean | model 55%, market 50% (against), hist 57% | variance | **untagged** | root leg of a 2-leg script loss: #1934, #1936 |
| 1936 | Dawson Knox rec_yds under 8.5 | 37.0 | 0.4947 (Low) | pass | model 52%, market 50% (against), hist 86% | correlated | **untagged** | same game script as #1934 (variance); own read: variance; we priced this side at 49%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 1940 | Vasily Podkolzin nhl_pm under 0.5 | 2.0 | 0.5614 (Low) | pass | model 66% | correlated | **untagged** | same game script as #1847 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1941 | Travis Sanheim nhl_toi under 24.0 | 25.07 | 0.5493 (Low) | pass | model 68% | correlated | **untagged** | same game script as #1856 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1943 | Anthony Duclair nhl_sog under 1.5 | 2.0 | 0.4868 (Low) | pass | model 63% | correlated | **untagged** | same game script as #1844 (variance); own read: variance; we priced this side at 49%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1945 | Owen Tippett nhl_blocks under 0.5 | 1.0 | 0.5381 (Low) | pass | model 68% | correlated | **untagged** | same game script as #1856 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1952 | Naz Reid pr under 28.5 | 38.0 | 0.5548 (Medium) | pass | model 51%, market 52% | correlated | **untagged** | same game script as #1878 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1954 | Sion James pts under 7.5 | 11.0 | 0.5848 (Medium) | pass | model 58%, market 52% | correlated | **untagged** | same game script as #1878 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1955 | Ryan Kalkbrenner pts under 7.5 | 8.0 | 0.557 (Medium) | pass | model 53%, market 50% (against) | correlated | **untagged** | same game script as #1878 (variance); own read: model bias; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 1957 | Walker Kessler pr under 25.5 | 31.0 | 0.5523 (Medium) | pass | model 51%, market 52% | correlated | **untagged** | same game script as #1880 (model bias); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1958 | Onyeka Okongwu pts under 13.5 | 16.0 | 0.5776 (Medium) | pass | model 54%, market 52% | correlated | **untagged** | same game script as #1880 (model bias); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1959 | CJ McCollum pts under 12.5 | 21.0 | 0.5523 (Medium) | pass | model 48% (against), market 50% | correlated | **untagged** | same game script as #1880 (model bias); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1962 | Jaylen Wells pr under 13.5 | 18.0 | 0.6096 (Medium) | lean | model 62%, market 56% | correlated | variance | same game script as #1783 (variance); own read: variance |
| 1965 | Kyrie Irving pts under 21.5 | 35.0 | 0.5845 (Medium) | pass | model 59%, market 52% | correlated | **untagged** | same game script as #1894 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1966 | P.J. Washington pr under 21.0 | 22.0 | 0.5719 (Medium) | pass | model 55%, market 53% | correlated | **untagged** | same game script as #1894 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1971 | Alperen Şengün pr under 29.5 | 32.0 | 0.5536 (Medium) | pass | model 55%, market 51% | correlated | **untagged** | same game script as #1790 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1972 | Kevin Durant pr under 26.5 | 35.0 | 0.5966 (Medium) | lean | model 55%, market 56% | correlated | variance | same game script as #1790 (variance); own read: variance |
| 1973 | Kevin Durant pts under 21.0 | 23.0 | 0.5574 (Medium) | pass | model 54%, market 50% (against) | correlated | **untagged** | same game script as #1790 (variance); own read: model bias; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 1975 | Victor Wembanyama pts under 26.5 | 40.0 | 0.5436 (Medium) | pass | model 48% (against), market 49% (against) | correlated | **untagged** | same game script as #1798 (model bias); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1977 | De'Aaron Fox pts under 14.5 | 15.0 | 0.5697 (Medium) | pass | model 52%, market 52% | correlated | **untagged** | same game script as #1798 (model bias); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1982 | Derik Queen pts under 9.0 | 16.0 | 0.5706 (Medium) | pass | model 53%, market 52% | correlated | **untagged** | same game script as #1906 (model bias); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1983 | Jeremiah Fears reb over 4.0 | 3.0 | 0.5532 (Medium) | pass | model 54%, market 56% | correlated | **untagged** | same game script as #1906 (model bias); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1984 | De'Anthony Melton tpm under 1.5 | 4.0 | 0.5638 (Medium) | pass | model 58%, market 52% | correlated | **untagged** | same game script as #1906 (model bias); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1985 | Ryan Kalkbrenner pra under 15.0 | 26.0 | 0.5149 (Low) | pass | model 58% | correlated | role/lineup | same game script as #1878 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1988 | Khaman Maluach reb over 5.5 | 5.0 | 0.4939 (Low) | pass | model 61%, market 49% (against) | correlated | variance | same game script as #1798 (model bias); own read: model bias; we priced this side at 49%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 1990 | Ivica Zubac pts under 11.5 | 16.0 | 0.5 (Low) | pass | model 88%, market 50% (against) | correlated | role/lineup | same game script as #1894 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1992 | Jaylen Wells ra under 4.5 | 5.0 | 0.5523 (Low) | pass | model 63% | correlated | variance | same game script as #1783 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1993 | AJ Dybantsa pr under 22.5 | 29.0 | 0.5284 (Low) | pass | model 70%, market 53% | correlated | role/lineup | same game script as #1777 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1996 | Aaron Nesmith pr under 15.5 | 20.0 | 0.5101 (Low) | pass | model 61%, market 51% | correlated | role/lineup | same game script as #1894 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |

Lessons:
- #1780: 28 min as projected; 9-13 FG for 24
- #1784: Poeltl 31 min vs 20.6 projected; under rested on the minutes projection
- #1819: Same PHX blowout (96-122): 26 min vs 32.3 projected
- #1823: Brown 26 min vs 34.4 projected in a 22-point win: blowout minutes
- #1870: PHX lost by 26: Bridges played 26 min vs 32.3 projected, 3-9 FG. A More-only line on the likely loser of a lopsided game carries blowout-minutes risk the sim's minutes don't widen for
- #1875: 28 min as projected; 5 reb
- #1900: Sim projected Jokic for 8 reb (79% under) vs market 54%: the sim was far under his rebounding; got 16
- #1916: Missed by the minimum (6 vs 6.5)
- #1918: 3 threes vs 4.5
- #1920: 21 min, 2 reb
- #1922: 16 vs 17.5 despite 19 min (7 above projection)
- #1923: Dort 18 min vs 25.7 projected, 1-6 FG
- #1962: 26 min vs 24.2 projected; 4-5 from three
- #1972: 36 min vs 33.4 projected; 12 reb, 8 ast
- #1985: Kalkbrenner 35 min vs 21.5 projected, 15 reb
- #1988: 5 reb vs 5.5; market was against the model and was right
- #1990: Zubac 28 min vs 11.4 projected: the minutes projection was far off his role
- #1992: Missed by the minimum (5 vs 4.5) at projected minutes
- #1993: Dybantsa 37 min vs 29.2 projected
- #1996: Nesmith 34 min vs 22.3 projected

Detail from the feeds:
- #1844 Jacob Trouba: error=HTTPError
- #1847 Max Jones: error=HTTPError
- #1850 Adam Fox: error=HTTPError
- #1851 Michael Misa: error=HTTPError
- #1853 Mattias Ekholm: error=HTTPError
- #1854 Eeli Tolvanen: error=HTTPError
- #1855 Macklin Celebrini: error=HTTPError
- #1856 Travis Sanheim: error=HTTPError
- #1860 Matthew Schaefer: error=HTTPError
- #1940 Vasily Podkolzin: error=HTTPError
- #1941 Travis Sanheim: error=HTTPError
- #1943 Anthony Duclair: error=HTTPError
- #1945 Owen Tippett: error=HTTPError

## 2026-11-08: 100 losses from 11 independent causes

| # | Leg | Result | Our p | Action | Sources | Auto tag | Confirmed | Evidence |
|---|---|---|---|---|---|---|---|---|
| 1526 | Patrick Mahomes pass_yds under 229.5 | 242.0 | 0.4882 (Low) | pass | none logged | variance | **untagged** | we priced this side at 49%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 1528 | Tee Higgins rec_yds over 76.5 | 32.0 | 0.5145 (Low) | pass | none logged | variance | **untagged** | root leg of a 23-leg script loss: #1528, #1529, #1531, #1545, #1547, #1548, #1549, #1551, #1552, #1554, #1556, #1557, #1566, #1568, #1569, #1570, #1576, #1577, #1579, #1583, #1585, #1589, #1599; logged as a PASS: no money on it; reviewed for calibration |
| 1529 | Ja'Marr Chase rec_yds under 76.5 | 155.0 | 0.5261 (Low) | pass | none logged | correlated | **untagged** | same game script as #1528 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1531 | Michael Penix Jr. pass_yds over 222.5 | 162.0 | 0.5183 (Low) | pass | none logged | correlated | **untagged** | same game script as #1528 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1533 | Jared Goff pass_yds over 261.5 | 170.0 | 0.5104 (Low) | pass | none logged | variance | **untagged** | logged as a PASS: no money on it; reviewed for calibration |
| 1541 | Malik Nabers rec_yds over 74.5 | 43.0 | 0.4979 (Low) | pass | none logged | variance | **untagged** | we priced this side at 50%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 1545 | Chase Brown rush_yds under 49.5 | 57.0 | 0.5071 (Low) | pass | none logged | correlated | **untagged** | same game script as #1528 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1547 | Joe Burrow rush_yds over 14.5 | 7.0 | 0.4134 (Low) | pass | none logged | correlated | **untagged** | same game script as #1528 (variance); own read: variance; we priced this side at 41%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 1548 | Khalil Herbert rush_yds over 7.5 | 7.0 | 0.5319 (Low) | pass | none logged | correlated | **untagged** | same game script as #1528 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1549 | Michael Penix Jr. rush_yds under 4.5 | 50.0 | 0.5143 (Low) | pass | none logged | correlated | **untagged** | same game script as #1528 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1551 | Ja'Marr Chase rec_yds under 76.5 | 155.0 | 0.5261 (Low) | pass | none logged | correlated | **untagged** | same game script as #1528 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1552 | Tee Higgins rec_yds over 76.5 | 32.0 | 0.5145 (Low) | pass | none logged | correlated | **untagged** | same game script as #1528 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1554 | Jahan Dotson rec_yds over 29.5 | 16.0 | 0.5124 (Low) | pass | none logged | correlated | **untagged** | same game script as #1528 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1556 | Bijan Robinson rec_yds under 24.5 | 47.0 | 0.5113 (Low) | pass | none logged | correlated | **untagged** | same game script as #1528 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1557 | Chase Brown rec_yds over 24.5 | 18.0 | 0.493 (Low) | pass | none logged | correlated | **untagged** | same game script as #1528 (variance); own read: variance; we priced this side at 49%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 1566 | Michael Penix Jr. pass_td over 1.5 | 1.0 | 0.5047 (Low) | pass | none logged | correlated | **untagged** | same game script as #1528 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1568 | Michael Penix Jr. completions over 20.5 | 20.0 | 0.4891 (Low) | pass | none logged | correlated | **untagged** | same game script as #1528 (variance); own read: variance; we priced this side at 49%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1569 | Ja'Marr Chase receptions under 6.5 | 10.0 | 0.5299 (Low) | pass | none logged | correlated | **untagged** | same game script as #1528 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1570 | Tee Higgins receptions over 5.5 | 5.0 | 0.5032 (Low) | pass | none logged | correlated | **untagged** | same game script as #1528 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1576 | Jahan Dotson receptions under 1.5 | 2.0 | 0.4959 (Low) | pass | none logged | correlated | **untagged** | same game script as #1528 (variance); own read: variance; we priced this side at 50%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1577 | Olamide Zaccheaus receptions over 1.5 | 1.0 | 0.4691 (Low) | pass | none logged | correlated | **untagged** | same game script as #1528 (variance); own read: variance; we priced this side at 47%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1579 | Dohnte Meyers receptions under 1.5 | 2.0 | 0.5102 (Low) | pass | none logged | correlated | **untagged** | same game script as #1528 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1583 | Charlie Woerner receptions under 0.5 | 1.0 | 0.5141 (Low) | pass | none logged | correlated | **untagged** | same game script as #1528 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1585 | Chase Brown rush_rec_yds under 69.5 | 75.0 | 0.4587 (Low) | pass | none logged | correlated | **untagged** | same game script as #1528 (variance); own read: variance; we priced this side at 46%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 1589 | Michael Penix Jr. pass_yds over 222.5 | 162.0 | 0.5183 (Low) | pass | none logged | correlated | **untagged** | same game script as #1528 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1599 | Samaje Perine rush_rec_yds under 39.5 | 43.0 | 0.6377 (Medium) | lean | model 57%, market 69%, hist 71% | correlated | variance | same game script as #1528 (variance); own read: variance |
| 1603 | Tyrese Maxey pts under 24.5 | 27.0 | 0.5703 (Medium) | pass | model 50% (against), market 48% (against) | variance | **untagged** | root leg of a 10-leg script loss: #1603, #1605, #1606, #1608, #1609, #1610, #1614, #1707, #1708, #1710; logged as a PASS: no money on it; reviewed for calibration |
| 1605 | Josh Giddey pr under 18.5 | 26.0 | 0.5778 (Medium) | pass | model 60%, market 55% | correlated | **untagged** | same game script as #1603 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1606 | Matas Buzelis pr under 18.5 | 24.0 | 0.6159 (Medium) | lean | model 60%, market 59% | correlated | **untagged** | same game script as #1603 (variance); own read: variance |
| 1608 | LeBron James pts under 17.5 | 22.0 | 0.6028 (Medium) | pass | model 55%, market 51% | correlated | **untagged** | same game script as #1603 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1609 | VJ Edgecombe pts under 12.5 | 13.0 | 0.5552 (Medium) | pass | model 44% (against), market 48% (against) | correlated | **untagged** | same game script as #1603 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1610 | Josh Giddey pts under 11.5 | 19.0 | 0.5943 (Medium) | pass | model 53%, market 51% | correlated | **untagged** | same game script as #1603 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1614 | Tyrese Maxey ast under 5.5 | 7.0 | 0.5413 (Medium) | pass | model 53%, market 50% (against) | correlated | **untagged** | same game script as #1603 (variance); own read: model bias; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 1617 | Daniss Jenkins pra under 17.5 | 40.0 | 0.5492 (Medium) | pass | model 50% (against), market 54% | variance | **untagged** | root leg of a 9-leg script loss: #1617, #1622, #1625, #1628, #1629, #1703, #1739, #1742, #1745; logged as a PASS: no money on it; reviewed for calibration |
| 1622 | Daniss Jenkins pts under 9.5 | 31.0 | 0.5694 (Medium) | pass | model 48% (against), market 49% (against) | correlated | **untagged** | same game script as #1617 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1625 | Kevin Huerter pts under 7.5 | 24.0 | 0.5738 (Medium) | pass | model 46% (against), market 50% (against) | correlated | **untagged** | same game script as #1617 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1628 | Jake LaRavia reb over 3.5 | 1.0 | 0.5577 (Medium) | pass | model 50%, market 53% | correlated | **untagged** | same game script as #1617 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1629 | Cade Cunningham reb over 5.0 | 4.0 | 0.5715 (Medium) | pass | model 55%, market 54% | correlated | **untagged** | same game script as #1617 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1630 | Rudy Gobert pra under 23.5 | 27.0 | 0.5911 (Medium) | pass | model 62%, market 56% | variance | **untagged** | root leg of a 9-leg script loss: #1630, #1700, #1705, #1713, #1714, #1748, #1772, #1773, #1774; logged as a PASS: no money on it; reviewed for calibration |
| 1642 | Walter Clayton Jr. pra under 14.5 | 15.0 | 0.5431 (Medium) | pass | model 58%, market 52% | variance | **untagged** | root leg of a 9-leg script loss: #1642, #1643, #1647, #1648, #1650, #1652, #1749, #1751, #1770; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1643 | Daniel Gafford pr under 14.5 | 23.0 | 0.5484 (Medium) | pass | model 58%, market 51% | correlated | **untagged** | same game script as #1642 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1647 | Daniel Gafford pts under 7.5 | 18.0 | 0.5449 (Medium) | pass | model 46% (against), market 46% (against) | correlated | **untagged** | same game script as #1642 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1648 | Zaccharie Risacher pts under 6.5 | 11.0 | 0.5789 (Medium) | pass | model 45% (against), market 51% | correlated | **untagged** | same game script as #1642 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1650 | Zaccharie Risacher ra under 4.5 | 7.0 | 0.58 (Medium) | pass | model 51%, market 58% | correlated | **untagged** | same game script as #1642 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1652 | Nolan Traore tpm under 1.5 | 2.0 | 0.5428 (Medium) | pass | model 57%, market 49% (against) | correlated | **untagged** | same game script as #1642 (variance); own read: model bias; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 1654 | Paul George pts under 17.5 | 27.0 | 0.5882 (Medium) | pass | model 51%, market 50% | variance | **untagged** | root leg of a 18-leg script loss: #1654, #1655, #1656, #1659, #1660, #1661, #1663, #1664, #1665, #1694, #1718, #1722, #1753, #1755, #1756, #1757, #1758, #1769; logged as a PASS: no money on it; reviewed for calibration |
| 1655 | Neemias Queta pr under 16.5 | 22.0 | 0.5689 (Medium) | pass | model 59%, market 54% | correlated | **untagged** | same game script as #1654 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1656 | Kyle Kuzma pr under 14.5 | 31.0 | 0.5426 (Medium) | pass | model 54%, market 52% | correlated | **untagged** | same game script as #1654 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1659 | Brayden Burries pts under 10.5 | 13.0 | 0.5462 (Medium) | pass | model 48% (against), market 46% (against) | correlated | **untagged** | same game script as #1654 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1660 | Neemias Queta pts under 9.5 | 13.0 | 0.6387 (Medium) | lean | model 55%, market 56% | correlated | **untagged** | same game script as #1654 (variance); own read: variance |
| 1661 | Kyle Kuzma pts under 9.5 | 27.0 | 0.594 (Medium) | pass | model 54%, market 50% | correlated | **untagged** | same game script as #1654 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1663 | Mitchell Robinson pts under 5.5 | 12.0 | 0.6007 (Medium) | pass | model 50% (against), market 52% | correlated | **untagged** | same game script as #1654 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1664 | Jaime Jaquez Jr. reb over 4.5 | 2.0 | 0.5413 (Medium) | pass | model 56%, market 50% (against) | correlated | opportunity | same game script as #1654 (variance); own read: model bias; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 1665 | Tyler Herro reb over 4.0 | 1.0 | 0.5744 (Medium) | pass | model 52%, market 55% | correlated | **untagged** | same game script as #1654 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1667 | Darius Garland pts under 21.5 | 24.0 | 0.5664 (Medium) | pass | model 50%, market 48% (against) | model bias | **untagged** | root leg of a 14-leg script loss: #1667, #1670, #1671, #1672, #1674, #1675, #1676, #1677, #1679, #1682, #1683, #1698, #1728, #1761; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 1670 | Jeremiah Fears pts under 14.5 | 25.0 | 0.5645 (Medium) | pass | model 45% (against), market 49% (against) | correlated | **untagged** | same game script as #1667 (model bias); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1671 | Saddiq Bey pts under 12.5 | 13.0 | 0.549 (Medium) | pass | model 41% (against), market 48% (against) | correlated | **untagged** | same game script as #1667 (model bias); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1672 | Brook Lopez pts under 11.5 | 20.0 | 0.5428 (Medium) | pass | model 46% (against), market 46% (against) | correlated | **untagged** | same game script as #1667 (model bias); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1674 | Keaton Wagler pts under 11.5 | 15.0 | 0.5695 (Medium) | pass | model 51%, market 48% (against) | correlated | **untagged** | same game script as #1667 (model bias); own read: model bias; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 1675 | Darius Garland ra under 9.5 | 10.0 | 0.5412 (Medium) | pass | model 57%, market 51% | correlated | variance | same game script as #1667 (model bias); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1676 | Darius Garland ast under 7.0 | 10.0 | 0.5496 (Medium) | pass | model 49% (against), market 51% | correlated | **untagged** | same game script as #1667 (model bias); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1677 | Brook Lopez ra under 6.5 | 8.0 | 0.5465 (Medium) | pass | model 51%, market 53% | correlated | **untagged** | same game script as #1667 (model bias); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1679 | Rui Hachimura reb over 5.0 | 3.0 | 0.5628 (Medium) | pass | model 52%, market 53% | correlated | **untagged** | same game script as #1667 (model bias); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1682 | Keaton Wagler reb over 3.5 | 2.0 | 0.568 (Medium) | pass | model 54%, market 54% | correlated | **untagged** | same game script as #1667 (model bias); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1683 | Saddiq Bey tpm over 1.5 | 1.0 | 0.5457 (Medium) | pass | model 53%, market 52% | correlated | **untagged** | same game script as #1667 (model bias); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1684 | Darius Acuff Jr. pts under 24.5 | 32.0 | 0.5994 (Medium) | pass | model 55%, market 51% | variance | **untagged** | root leg of a 5-leg script loss: #1684, #1689, #1691, #1737, #1767; logged as a PASS: no money on it; reviewed for calibration |
| 1689 | De'Andre Hunter reb over 4.0 | 3.0 | 0.5762 (Medium) | pass | model 56%, market 54% | correlated | **untagged** | same game script as #1684 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1691 | Bobby Portis Jr. reb over 5.0 | 1.0 | 0.5864 (Medium) | pass | model 59%, market 55% | correlated | **untagged** | same game script as #1684 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1694 | Kyle Kuzma ast over 2.5 | 0.0 | 0.4811 (Low) | pass | model 48% (against), market 54% | correlated | **untagged** | same game script as #1654 (variance); own read: variance; we priced this side at 48%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 1698 | Kris Dunn pts under 8.5 | 14.0 | 0.5936 (Low) | pass | model 49% (against), market 52% | correlated | variance | same game script as #1667 (model bias); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1700 | Jaxson Hayes pts under 8.5 | 18.0 | 0.6026 (Medium) | lean | model 56%, market 51% | correlated | model bias | same game script as #1630 (variance); own read: variance |
| 1703 | Duncan Robinson pr over 17.5 | 12.0 | 0.5185 (Low) | pass | model 63%, market 52% | correlated | **untagged** | same game script as #1617 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1705 | Darryn Peterson pra under 24.5 | 36.0 | 0.5183 (Low) | pass | model 70%, market 52% | correlated | **untagged** | same game script as #1630 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1707 | Jalen Smith tpm under 1.5 | 2.0 | 0.5112 (Low) | pass | model 66%, market 51% | correlated | **untagged** | same game script as #1603 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1708 | LeBron James ast over 5.5 | 5.0 | 0.648 (High) | lean | model 68%, market 69% | correlated | **untagged** | same game script as #1603 (variance); own read: variance; closest possible loss (missed by the minimum) |
| 1710 | Caleb Wilson ast over 1.5 | 0.0 | 0.682 (High) | lean | model 70%, market 72% | correlated | **untagged** | same game script as #1603 (variance); own read: variance |
| 1713 | LaMelo Ball ast over 5.5 | 5.0 | 0.6408 (High) | lean | model 66%, market 68% | correlated | **untagged** | same game script as #1630 (variance); own read: variance; closest possible loss (missed by the minimum) |
| 1714 | Ayo Dosunmu ast over 3.5 | 1.0 | 0.6645 (High) | lean | model 72%, market 70% | correlated | **untagged** | same game script as #1630 (variance); own read: variance |
| 1718 | Paul George ra over 6.5 | 4.0 | 0.6497 (High) | lean | model 73%, market 72% | correlated | **untagged** | same game script as #1654 (variance); own read: variance |
| 1722 | Tyler Herro ast over 2.5 | 2.0 | 0.7 (High) | lean | model 77%, market 78% | correlated | **untagged** | same game script as #1654 (variance); own read: variance; closest possible loss (missed by the minimum) |
| 1728 | Dejounte Murray ast over 3.5 | 3.0 | 0.7 (High) | lean | model 77%, market 77% | correlated | **untagged** | same game script as #1667 (model bias); own read: variance; closest possible loss (missed by the minimum) |
| 1737 | Giannis Antetokounmpo ast over 3.5 | 3.0 | 0.7 (High) | lean | model 84%, market 80% | correlated | variance | same game script as #1684 (variance); own read: variance; closest possible loss (missed by the minimum) |
| 1739 | Austin Reaves pts under 25.5 | 43.0 | 0.5964 (Medium) | pass | model 55%, market 51% | correlated | **untagged** | same game script as #1617 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1742 | Collin Sexton pra under 16.5 | 21.0 | 0.5663 (Medium) | pass | model 50% (against), market 57% | correlated | **untagged** | same game script as #1617 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1745 | Collin Sexton pts under 11.5 | 17.0 | 0.5727 (Medium) | pass | model 50% (against), market 49% (against) | correlated | **untagged** | same game script as #1617 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1748 | Rudy Gobert pts under 8.5 | 10.0 | 0.5422 (Medium) | pass | model 41% (against), market 47% (against) | correlated | **untagged** | same game script as #1630 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1749 | Cooper Flagg ra under 13.5 | 17.0 | 0.547 (Medium) | pass | model 63%, market 55% | correlated | **untagged** | same game script as #1642 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1751 | Walter Clayton Jr. ast under 3.5 | 6.0 | 0.5673 (Medium) | pass | model 56%, market 52% | correlated | **untagged** | same game script as #1642 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1753 | Payton Pritchard pra under 20.5 | 21.0 | 0.5462 (Medium) | pass | model 58%, market 52% | correlated | **untagged** | same game script as #1654 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1755 | Brayden Burries pts under 11.5 | 13.0 | 0.5967 (Medium) | pass | model 53%, market 51% | correlated | **untagged** | same game script as #1654 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1756 | Neemias Queta ra under 8.5 | 13.0 | 0.5907 (Medium) | pass | model 61%, market 56% | correlated | **untagged** | same game script as #1654 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1757 | Kel'el Ware reb over 6.5 | 0.0 | 0.5456 (Medium) | pass | model 54%, market 51% | correlated | **untagged** | same game script as #1654 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1758 | AJ Green tpm over 1.5 | 1.0 | 0.5446 (Medium) | pass | model 64%, market 55% | correlated | **untagged** | same game script as #1654 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1761 | Brook Lopez pts under 12.5 | 20.0 | 0.6 (Medium) | pass | model 52%, market 52% | correlated | **untagged** | same game script as #1667 (model bias); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1767 | Davion Mitchell pts under 13.5 | 17.0 | 0.5678 (Medium) | pass | model 42% (against), market 50% (against) | correlated | **untagged** | same game script as #1684 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1769 | Jayson Tatum ast over 6.5 | 6.0 | 0.4961 (Low) | pass | model 57%, market 53% | correlated | variance | same game script as #1654 (variance); own read: variance; we priced this side at 50%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1770 | Caleb Martin ast under 1.5 | 2.0 | 0.5815 (Low) | pass | model 70% | correlated | variance | same game script as #1642 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1772 | Rudy Gobert pra under 22.5 | 27.0 | 0.5323 (Low) | pass | model 57%, market 50% | correlated | variance | same game script as #1630 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1773 | Ace Bailey reb over 6.0 | 2.0 | 0.5291 (Low) | pass | model 48% (against), market 50% | correlated | variance | same game script as #1630 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1774 | Darryn Peterson pts under 15.5 | 26.0 | 0.5125 (Low) | pass | model 69%, market 51% | correlated | correlated | same game script as #1630 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |

Lessons:
- #1599: 4 carries for 9 yds through three quarters, then 7 for 34 in the 4th with CIN up 14-17 and Chase Brown resting: the flagged worst case (CIN up 14+, 24% of runs, under 59% there). Backup-RB unders carry garbage-time risk when his team is favored
- #1664: 23 min vs 26.5 projected in a 20-point loss (blowout), 2 rebounds
- #1675: 32 min as projected, 0 reb + 10 ast = 10 vs 9.5: missed by the minimum
- #1698: 24 min vs 28.6 projected (fewer minutes) yet 4-7 for 14: shooting variance
- #1700: 29 min vs 23 projected and 6-6 from the field for 18: Utah tightened its rotation (Peterson also +6.5 min); shooting did the rest
- #1737: 34 min vs 32 projected; he scored 29 with 14 boards and dished 3: missed by the minimum in a normal role
- #1769: 29 min as projected; 6 vs 6.5 assists on 6-19 shooting: missed by the minimum (history-list Low pass)
- #1770: 19 min vs 17 projected; 2 vs 1.5 assists: missed by the minimum
- #1772: 31 min vs 27 projected, 15 rebounds: 27 vs 22.5 on a big rebounding night
- #1773: 32 min (29.5 projected), only 2 rebounds: normal role, rate miss
- #1774: 35 min vs 28.5 projected, 11-21 for 26: the same Utah rotation shift as #1700

## 2026-11-07: 105 losses from 23 independent causes

| # | Leg | Result | Our p | Action | Sources | Auto tag | Confirmed | Evidence |
|---|---|---|---|---|---|---|---|---|
| 1279 | Jamal Murray pts over 22.5 | 16.0 | 0.5501 (Medium) | pass | model 52%, market 53% | variance | **untagged** | root leg of a 7-leg script loss: #1279, #1281, #1284, #1288, #1292, #1294, #1470; logged as a PASS: no money on it; reviewed for calibration |
| 1281 | Pascal Siakam pts under 20.5 | 23.0 | 0.5832 (Medium) | pass | model 63%, market 50% | correlated | **untagged** | same game script as #1279 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1284 | Obi Toppin pr under 16.5 | 17.0 | 0.6258 (Medium) | pass | model 82%, market 54% | correlated | **untagged** | same game script as #1279 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1288 | Jamal Murray ra under 11.0 | 14.0 | 0.5571 (Medium) | pass | model 64%, market 49% (against) | correlated | **untagged** | same game script as #1279 (variance); own read: model bias; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 1292 | Obi Toppin reb under 4.5 | 7.0 | 0.5784 (Medium) | pass | model 79%, market 51% | correlated | **untagged** | same game script as #1279 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1294 | Pascal Siakam ast under 4.0 | 5.0 | 0.6285 (Medium) | lean | model 72%, market 54% | correlated | model bias | same game script as #1279 (variance); own read: variance |
| 1295 | Michael Porter Jr. pts under 22.5 | 25.0 | 0.5561 (Medium) | pass | model 52%, market 50% (against) | model bias | **untagged** | root leg of a 13-leg script loss: #1295, #1298, #1299, #1300, #1301, #1302, #1303, #1304, #1306, #1307, #1309, #1311, #1417; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 1298 | CJ McCollum pr over 15.5 | 13.0 | 0.5439 (Medium) | pass | model 67%, market 50% (against) | correlated | **untagged** | same game script as #1295 (model bias); own read: model bias; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 1299 | Nolan Traore pr under 13.5 | 20.0 | 0.5469 (Medium) | pass | model 55%, market 52% | correlated | **untagged** | same game script as #1295 (model bias); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1300 | Mikel Brown Jr. pts under 12.5 | 18.0 | 0.5825 (Medium) | pass | model 58%, market 52% | correlated | **untagged** | same game script as #1295 (model bias); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1301 | Julius Randle ra under 11.5 | 15.0 | 0.5535 (Medium) | pass | model 52%, market 52% | correlated | **untagged** | same game script as #1295 (model bias); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1302 | Luguentz Dort pr over 11.5 | 5.0 | 0.5699 (Medium) | pass | model 74%, market 51% | correlated | **untagged** | same game script as #1295 (model bias); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1303 | Nolan Traore pts under 11.5 | 19.0 | 0.5746 (Medium) | pass | model 56%, market 51% | correlated | **untagged** | same game script as #1295 (model bias); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1304 | Dyson Daniels pts over 10.5 | 9.0 | 0.5682 (Medium) | pass | model 62%, market 53% | correlated | **untagged** | same game script as #1295 (model bias); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1306 | Michael Porter Jr. ra under 9.5 | 10.0 | 0.5556 (Medium) | pass | model 53%, market 52% | correlated | **untagged** | same game script as #1295 (model bias); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1307 | Luguentz Dort pa over 9.5 | 4.0 | 0.578 (Medium) | pass | model 76%, market 52% | correlated | opportunity | same game script as #1295 (model bias); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1309 | Luguentz Dort pts over 8.5 | 3.0 | 0.556 (Medium) | pass | model 69%, market 49% (against) | correlated | **untagged** | same game script as #1295 (model bias); own read: model bias; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 1311 | Julius Randle ast under 4.5 | 8.0 | 0.5769 (Medium) | pass | model 49% (against), market 54% | correlated | **untagged** | same game script as #1295 (model bias); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1312 | Jalen Brunson pra under 36.5 | 46.0 | 0.5409 (Medium) | pass | model 62%, market 51% | variance | **untagged** | root leg of a 12-leg script loss: #1312, #1313, #1314, #1315, #1317, #1318, #1319, #1322, #1325, #1326, #1418, #1473; logged as a PASS: no money on it; reviewed for calibration |
| 1313 | Jalen Brunson pts under 26.5 | 31.0 | 0.5769 (Medium) | pass | model 58%, market 51% | correlated | **untagged** | same game script as #1312 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1314 | Donovan Mitchell pts under 23.5 | 37.0 | 0.5616 (Medium) | pass | model 53%, market 50% | correlated | **untagged** | same game script as #1312 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1315 | Karl-Anthony Towns pts under 19.5 | 29.0 | 0.5789 (Medium) | pass | model 59%, market 51% | correlated | **untagged** | same game script as #1312 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1317 | Mikal Bridges pra under 16.5 | 19.0 | 0.5492 (Medium) | pass | model 68%, market 51% | correlated | **untagged** | same game script as #1312 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1318 | Mikal Bridges pr under 13.5 | 15.0 | 0.5654 (Medium) | pass | model 69%, market 51% | correlated | **untagged** | same game script as #1312 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1319 | Evan Mobley ra under 12.5 | 14.0 | 0.5459 (Medium) | pass | model 58%, market 50% (against) | correlated | **untagged** | same game script as #1312 (variance); own read: model bias; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 1322 | Jalen Brunson ast under 6.5 | 9.0 | 0.6081 (Medium) | pass | model 70%, market 52% | correlated | **untagged** | same game script as #1312 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1325 | Peyton Watson reb under 5.0 | 6.0 | 0.5448 (Medium) | pass | model 62%, market 52% | correlated | **untagged** | same game script as #1312 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1326 | Andre Drummond pts over 4.5 | 0.0 | 0.5459 (Medium) | pass | model 54%, market 52% | correlated | **untagged** | same game script as #1312 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1329 | AJ Dybantsa pr under 22.5 | 25.0 | 0.5682 (Medium) | pass | model 72%, market 50% | variance | **untagged** | root leg of a 13-leg script loss: #1329, #1331, #1333, #1336, #1337, #1338, #1339, #1342, #1344, #1475, #1476, #1477, #1481; logged as a PASS: no money on it; reviewed for calibration |
| 1331 | AJ Dybantsa pts under 17.5 | 19.0 | 0.6318 (Medium) | lean | model 77%, market 52% | correlated | variance | same game script as #1329 (variance); own read: variance |
| 1333 | Jared McCain pts under 13.5 | 19.0 | 0.571 (Medium) | pass | model 53%, market 51% | correlated | **untagged** | same game script as #1329 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1336 | Bilal Coulibaly pr over 10.5 | 5.0 | 0.5521 (Medium) | pass | model 58%, market 53% | correlated | **untagged** | same game script as #1329 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1337 | Shai Gilgeous-Alexander ra under 10.0 | 11.0 | 0.5827 (Medium) | pass | model 69%, market 51% | correlated | **untagged** | same game script as #1329 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1338 | Kyshawn George ra under 9.5 | 13.0 | 0.5871 (Medium) | pass | model 57%, market 55% | correlated | **untagged** | same game script as #1329 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1339 | Isaiah Hartenstein pts over 8.0 | 2.0 | 0.5679 (Medium) | pass | model 58%, market 54% | correlated | **untagged** | same game script as #1329 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1342 | Bilal Coulibaly pts over 7.5 | 0.0 | 0.5427 (Medium) | pass | model 50% (against), market 53% | correlated | **untagged** | same game script as #1329 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1344 | Shai Gilgeous-Alexander ast under 5.5 | 9.0 | 0.606 (Medium) | pass | model 75%, market 50% | correlated | **untagged** | same game script as #1329 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1345 | Stephen Curry pra under 35.5 | 53.0 | 0.5437 (Medium) | pass | model 67%, market 50% | variance | **untagged** | root leg of a 10-leg script loss: #1345, #1346, #1347, #1348, #1349, #1356, #1357, #1358, #1360, #1364; logged as a PASS: no money on it; reviewed for calibration |
| 1346 | Yaxel Lendeborg pra under 30.5 | 34.0 | 0.5474 (Medium) | pass | model 72%, market 49% (against) | correlated | **untagged** | same game script as #1345 (variance); own read: model bias; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 1347 | Stephen Curry pr under 30.5 | 47.0 | 0.5522 (Medium) | pass | model 64%, market 50% | correlated | **untagged** | same game script as #1345 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1348 | Stephen Curry pts under 26.5 | 41.0 | 0.5795 (Medium) | pass | model 61%, market 50% | correlated | **untagged** | same game script as #1345 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1349 | Franz Wagner pts under 24.5 | 30.0 | 0.5489 (Medium) | pass | model 48% (against), market 50% (against) | correlated | **untagged** | same game script as #1345 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1356 | Stephen Curry ra under 9.0 | 12.0 | 0.6399 (Medium) | lean | model 81%, market 55% | correlated | model bias | same game script as #1345 (variance); own read: variance |
| 1357 | Jase Richardson ra under 6.5 | 8.0 | 0.5543 (Medium) | pass | model 51%, market 52% | correlated | **untagged** | same game script as #1345 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1358 | Tristan da Silva ra under 6.5 | 9.0 | 0.552 (Medium) | pass | model 51%, market 52% | correlated | **untagged** | same game script as #1345 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1360 | Brandin Podziemski reb under 5.5 | 7.0 | 0.5454 (Medium) | pass | model 70%, market 50% (against) | correlated | **untagged** | same game script as #1345 (variance); own read: model bias; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 1364 | Stephen Curry reb under 4.0 | 6.0 | 0.5877 (Medium) | pass | model 75%, market 53% | correlated | **untagged** | same game script as #1345 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1366 | Kevin Durant pra under 30.5 | 34.0 | 0.5424 (Medium) | pass | model 64%, market 51% | variance | **untagged** | root leg of a 12-leg script loss: #1366, #1368, #1371, #1372, #1373, #1378, #1381, #1382, #1384, #1385, #1386, #1387; logged as a PASS: no money on it; reviewed for calibration |
| 1368 | Miles Bridges pr under 22.5 | 23.0 | 0.5411 (Medium) | pass | model 51%, market 52% | correlated | **untagged** | same game script as #1366 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1371 | Jalen Green pr under 18.5 | 19.0 | 0.5477 (Medium) | pass | model 57%, market 52% | correlated | **untagged** | same game script as #1366 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1372 | Jalen Green pts under 15.5 | 16.0 | 0.5779 (Medium) | pass | model 56%, market 51% | correlated | **untagged** | same game script as #1366 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1373 | Amen Thompson pts under 14.5 | 17.0 | 0.5724 (Medium) | pass | model 56%, market 51% | correlated | **untagged** | same game script as #1366 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1378 | Reed Sheppard pa over 10.5 | 6.0 | 0.5604 (Medium) | pass | model 73%, market 51% | correlated | **untagged** | same game script as #1366 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1381 | Collin Gillespie pts over 8.5 | 7.0 | 0.5447 (Medium) | pass | model 50% (against), market 53% | correlated | **untagged** | same game script as #1366 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1382 | Reed Sheppard pts over 8.0 | 6.0 | 0.5813 (Medium) | pass | model 72%, market 52% | correlated | **untagged** | same game script as #1366 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1384 | Marcus Smart pts over 6.5 | 5.0 | 0.5527 (Medium) | pass | model 59%, market 52% | correlated | **untagged** | same game script as #1366 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1385 | Jalen Green ra under 6.5 | 9.0 | 0.5479 (Medium) | pass | model 57%, market 50% (against) | correlated | **untagged** | same game script as #1366 (variance); own read: model bias; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 1386 | Collin Gillespie ra under 6.5 | 7.0 | 0.5984 (Medium) | pass | model 52%, market 57% | correlated | variance | same game script as #1366 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1387 | Jabari Smith Jr. reb under 6.0 | 9.0 | 0.5403 (Medium) | pass | model 60%, market 52% | correlated | **untagged** | same game script as #1366 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1390 | Deni Avdija pr over 29.5 | 19.0 | 0.5609 (Medium) | pass | model 53%, market 56% | variance | **untagged** | root leg of a 8-leg script loss: #1390, #1391, #1392, #1393, #1401, #1402, #1404, #1414; logged as a PASS: no money on it; reviewed for calibration |
| 1391 | Deni Avdija pa over 29.5 | 16.0 | 0.5452 (Medium) | pass | model 55%, market 54% | correlated | **untagged** | same game script as #1390 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1392 | Deni Avdija pts over 23.5 | 15.0 | 0.5428 (Medium) | pass | model 51%, market 52% | correlated | **untagged** | same game script as #1390 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1393 | Damian Lillard pa over 23.5 | 19.0 | 0.559 (Medium) | pass | model 51%, market 57% | correlated | **untagged** | same game script as #1390 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1401 | Toumani Camara pa over 12.5 | 4.0 | 0.5503 (Medium) | pass | model 58%, market 54% | correlated | **untagged** | same game script as #1390 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1402 | Jrue Holiday pts over 12.5 | 11.0 | 0.5507 (Medium) | pass | model 50%, market 54% | correlated | **untagged** | same game script as #1390 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1404 | Donovan Clingan pts over 11.0 | 6.0 | 0.5461 (Medium) | pass | model 58%, market 51% | correlated | **untagged** | same game script as #1390 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1414 | Devin Vassell ast under 2.5 | 3.0 | 0.5408 (Medium) | pass | model 42% (against), market 51% | correlated | **untagged** | same game script as #1390 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1417 | Day'Ron Sharpe pra under 20.5 | 35.0 | 0.5399 (Low) | pass | model 58%, market 52% | correlated | role/lineup | same game script as #1295 (model bias); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1418 | Jalen Brunson ra under 9.5 | 15.0 | 0.5647 (Medium) | pass | model 66%, market 50% (against) | correlated | **untagged** | same game script as #1312 (variance); own read: model bias; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 1427 | Auston Matthews nhl_toi under 20.25 | 22.95 | 0.5716 (Low) | pass | model 69% | variance | **untagged** | root leg of a 5-leg script loss: #1427, #1436, #1438, #1440, #1490; logged as a PASS: no money on it; reviewed for calibration |
| 1428 | Ryker Evans nhl_blocks under 1.5 | 3.0 | 0.5712 (Low) | pass | model 61%, market 56% | variance | **untagged** | root leg of a 3-leg script loss: #1428, #1434, #1485; logged as a PASS: no money on it; reviewed for calibration |
| 1431 | Shea Theodore nhl_sog over 1.5 | 0.0 | 0.4861 (Low) | pass | model 59% | variance | **untagged** | we priced this side at 49%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 1434 | Chandler Stephenson nhl_fow over 8.5 | 8.0 | 0.5187 (Low) | pass | model 59% | correlated | **untagged** | same game script as #1428 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1435 | Brandon Hagel nhl_sog over 2.5 | 0.0 | 0.5571 (Low) | pass | model 63%, market 56% | variance | **untagged** | root leg of a 2-leg script loss: #1435, #1486; logged as a PASS: no money on it; reviewed for calibration |
| 1436 | Nick Suzuki nhl_assists over 0.5 | 0.0 | 0.5264 (Low) | pass | model 50%, market 53% | correlated | **untagged** | same game script as #1427 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1438 | Noah Dobson nhl_blocks under 1.5 | 3.0 | 0.5087 (Low) | pass | model 54% | correlated | **untagged** | same game script as #1427 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1440 | Auston Matthews nhl_fow over 8.5 | 8.0 | 0.5042 (Low) | pass | model 52% | correlated | **untagged** | same game script as #1427 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1443 | Emil Heineman nhl_sog under 1.5 | 2.0 | 0.4947 (Low) | pass | model 62%, market 49% (against) | model bias | **untagged** | root leg of a 2-leg script loss: #1443, #1487; we priced this side at 49%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 1446 | Ben Kindel nhl_points under 0.5 | 1.0 | 0.4807 (Low) | pass | model 66%, market 50% (against) | model bias | **untagged** | root leg of a 2-leg script loss: #1446, #1492; we priced this side at 48%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 1451 | Eli Stowers rec_yds over 5.5 | 0.0 | 0.9816 (Low) | pass | model 47% (against), market 100%, hist 50% (against) | variance | **untagged** | logged as a PASS: no money on it; reviewed for calibration |
| 1452 | Aaron Jones Sr. rush_att over 8.5 | 5.0 | 0.5496 (Low) | pass | model 57%, market 50% (against), hist 71% | variance | **untagged** | logged as a PASS: no money on it; reviewed for calibration |
| 1456 | Jadarian Price rush_rec_yds under 68.5 | 78.0 | 0.571 (Low) | pass | model 61%, market 50% (against), hist 100% | variance | **untagged** | root leg of a 3-leg script loss: #1456, #1466, #1501; logged as a PASS: no money on it; reviewed for calibration |
| 1465 | Chuba Hubbard rec_yds over 17.5 | 17.0 | 0.5271 (Low) | pass | model 51%, market 52%, hist 57% | variance | **untagged** | root leg of a 2-leg script loss: #1465, #1498; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1466 | Jadarian Price receptions under 1.5 | 4.0 | 0.5261 (Low) | pass | model 53%, market 50% (against), hist 50% (against) | correlated | **untagged** | same game script as #1456 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1467 | Dak Prescott pass_yds under 260.5 | 335.0 | 0.5186 (Low) | pass | model 52%, market 50% (against), hist 50% (against) | model bias | **untagged** | root leg of a 2-leg script loss: #1467, #1503; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 1470 | Obi Toppin pra under 16.5 | 19.0 | 0.5663 (Medium) | pass | model 76%, market 50% | correlated | **untagged** | same game script as #1279 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1473 | Landry Shamet pts over 9.5 | 9.0 | 0.5637 (Medium) | pass | model 49% (against), market 56% | correlated | **untagged** | same game script as #1312 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1475 | Isaiah Hartenstein pr over 18.5 | 16.0 | 0.5495 (Medium) | pass | model 58%, market 53% | correlated | **untagged** | same game script as #1329 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1476 | Isaiah Hartenstein pa over 11.5 | 8.0 | 0.5459 (Medium) | pass | model 59%, market 53% | correlated | **untagged** | same game script as #1329 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1477 | Aday Mara pts under 8.5 | 18.0 | 0.5509 (Medium) | pass | model 48% (against), market 50% (against) | correlated | **untagged** | same game script as #1329 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1481 | Trae Young ra over 11.5 | 8.0 | 0.4466 (Low) | pass | model 35% (against), market 56% | correlated | opportunity | same game script as #1329 (variance); own read: variance; we priced this side at 45%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 1482 | Leo Carlsson nhl_sog under 2.5 | 3.0 | 0.482 (Low) | pass | model 59% | variance | **untagged** | we priced this side at 48%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1483 | Sebastian Aho nhl_toi over 19.25 | 14.9 | 0.5551 (Low) | pass | model 81% | variance | **untagged** | root leg of a 2-leg script loss: #1483, #1488; logged as a PASS: no money on it; reviewed for calibration |
| 1485 | Matty Beniers nhl_sog under 1.5 | 2.0 | 0.5357 (Low) | pass | model 63%, market 54% | correlated | **untagged** | same game script as #1428 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1486 | Olli Maatta nhl_blocks over 1.5 | 1.0 | 0.5203 (Low) | pass | model 53%, market 52% | correlated | **untagged** | same game script as #1435 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1487 | Victor Eklund nhl_sog under 1.5 | 2.0 | 0.5202 (Low) | pass | model 63%, market 52% | correlated | **untagged** | same game script as #1443 (model bias); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1488 | William Carrier nhl_pm under 0.5 | 2.0 | 0.5156 (Low) | pass | model 58% | correlated | **untagged** | same game script as #1483 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1489 | Vincent Trocheck nhl_sog over 1.5 | 1.0 | 0.4946 (Low) | pass | model 50%, market 51% | variance | **untagged** | we priced this side at 49%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1490 | Nick Suzuki nhl_toi over 20.75 | 18.4 | 0.4912 (Low) | pass | model 55% | correlated | **untagged** | same game script as #1427 (variance); own read: variance; we priced this side at 49%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 1492 | Artemi Panarin nhl_toi over 21.75 | 21.2 | 0.4899 (Low) | pass | model 54% | correlated | **untagged** | same game script as #1446 (model bias); own read: variance; we priced this side at 49%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 1498 | Evan Engram receptions under 2.0 | 4.0 | 0.6121 (Medium) | lean | model 57%, market 63%, hist 71% | correlated | correlated | same game script as #1465 (variance); own read: variance |
| 1501 | Jadarian Price rush_rec_yds under 69.5 | 78.0 | 0.5621 (Low) | pass | model 61%, market 48% (against), hist 100% | correlated | **untagged** | same game script as #1456 (variance); own read: model bias; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 1502 | Brandin Cooks rec_yds under 16.5 | 25.0 | 0.5356 (Low) | pass | model 53%, market 50% (against), hist 100% | variance | **untagged** | logged as a PASS: no money on it; reviewed for calibration |
| 1503 | Laquon Treadwell rec_yds over 14.5 | 0.0 | 0.5228 (Low) | pass | model 50% (against), market 50% (against), hist 88% | correlated | **untagged** | same game script as #1467 (model bias); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1509 | Kenny Gainwell receptions under 1.5 | 3.0 | 0.5139 (Low) | pass | model 51%, market 50% (against), hist 50% (against) | variance | **untagged** | logged as a PASS: no money on it; reviewed for calibration |

Lessons:
- #1294: minutes projected 28 vs 33 in his last 5 (L28 WARN shown); played 32 and dished 5. Same finding as #1356: the minutes-WARN group beats its predictions, no drop rule
- #1307: 20 min vs 30 projected in a 3-point game (benched or foul trouble, not a blowout): volume, not rate
- #1331: 31 min vs 29 projected, 7-15 FG for 19 in a 39-point OKC blowout: normal role, ordinary shooting variance
- #1356: minutes projected 26 vs 30 in his last 5 (L28 WARN shown); played 36 in a 7-point game. Unders with the minutes WARN are 33-17 (66% vs 57% predicted, n=50), so no new drop rule: the WARN stays a warning
- #1386: 20 min vs 23 projected; 7 vs 6.5, missed by the minimum
- #1417: 32 min vs 22 projected, 10 reb 13 ast: his role expanded well past the projection; history-list Low pass
- #1481: history-list Low pass: 28 min vs 32 projected in a 39-point loss (blowout minutes cut), 1-6 FG
- #1498: 5 targets, 4 catches: the flagged risk (Carolina without both starting LBs who cover tight ends) played out; DEN won 26-21

Detail from the feeds:
- #1427 Auston Matthews: error=HTTPError
- #1428 Ryker Evans: error=HTTPError
- #1431 Shea Theodore: error=HTTPError
- #1434 Chandler Stephenson: error=HTTPError
- #1435 Brandon Hagel: error=HTTPError
- #1436 Nick Suzuki: error=HTTPError
- #1438 Noah Dobson: error=HTTPError
- #1440 Auston Matthews: error=HTTPError
- #1443 Emil Heineman: error=HTTPError
- #1446 Ben Kindel: error=HTTPError
- #1482 Leo Carlsson: error=HTTPError
- #1483 Sebastian Aho: error=HTTPError
- #1485 Matty Beniers: error=HTTPError
- #1486 Olli Maatta: error=HTTPError
- #1487 Victor Eklund: error=HTTPError
- #1488 William Carrier: error=HTTPError
- #1489 Vincent Trocheck: error=HTTPError
- #1490 Nick Suzuki: error=HTTPError
- #1492 Artemi Panarin: error=HTTPError

## 2026-11-06: 285 losses from 36 independent causes

| # | Leg | Result | Our p | Action | Sources | Auto tag | Confirmed | Evidence |
|---|---|---|---|---|---|---|---|---|
| 615 | Evan Mobley pra under 31.5 | 32.0 | 0.5774 (Medium) | pass | model 72%, market 51% | variance | **untagged** | root leg of a 20-leg script loss: #615, #622, #859, #862, #863, #933, #987, #1096, #1098, #1099, #1101, #1102, #1103, #1104, #1136, #1138, #1162, #1165, #1166, #1169; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 618 | Collin Murray-Boyles pr under 18.5 | 26.0 | 0.5464 (Low) | pass | model 72% | variance | role/lineup | root leg of a 31-leg script loss: #618, #624, #896, #897, #898, #900, #902, #1005, #1006, #1007, #1008, #1010, #1013, #1016, #1018, #1020, #1123, #1124, #1126, #1180, #1181, #1182, #1183, #1186, #1187, #1189, #1192, #1193, #1219, #1221, #1225; logged as a PASS: no money on it; reviewed for calibration |
| 621 | Naji Marshall ra over 7.5 | 6.0 | 0.4368 (Low) | pass | model 22% (against) | variance | **untagged** | root leg of a 17-leg script loss: #621, #634, #881, #882, #883, #884, #885, #888, #931, #934, #1000, #1001, #1004, #1115, #1118, #1119, #1120; we priced this side at 44%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 622 | Tyrese Maxey pra over 33.5 | 24.0 | 0.5087 (Low) | pass | model 40% (against), market 54% | correlated | **untagged** | same game script as #615 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 624 | Brayden Burries pa under 13.5 | 27.0 | 0.5076 (Low) | pass | model 54% | correlated | **untagged** | same game script as #618 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 632 | Deni Avdija tpm over 1.5 | 1.0 | 0.518 (Low) | pass | model 59% | variance | **untagged** | root leg of a 23-leg script loss: #632, #923, #925, #926, #927, #928, #1028, #1029, #1032, #1033, #1034, #1036, #1037, #1040, #1132, #1133, #1134, #1195, #1228, #1229, #1244, #1246, #1247; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 634 | Ace Bailey pra over 20.5 | 18.0 | 0.5528 (Medium) | pass | model 57%, market 55% | correlated | **untagged** | same game script as #621 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 635 | Cedric Coward ra over 10.0 | 9.0 | 0.507 (Low) | pass | model 54% | variance | **untagged** | root leg of a 5-leg script loss: #635, #865, #1107, #1212, #1235; logged as a PASS: no money on it; reviewed for calibration |
| 648 | Aryna Sabalenka tennis_games under 22.5 | 25.0 | 0.5184 (Low) | pass | model 59%, market 50% (against) | variance | **untagged** | root leg of a 2-leg script loss: #648, #649; logged as a PASS: no money on it; reviewed for calibration |
| 649 | Aryna Sabalenka tennis_games_won under 12.5 | 14.0 | 0.5687 (Low) | pass | model 57% | correlated | **untagged** | same game script as #648 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 652 | Elina Svitolina tennis_games_won over 11.5 | 4.0 | 0.5664 (Low) | pass | model 57% | variance | **untagged** | root leg of a 2-leg script loss: #652, #838; logged as a PASS: no money on it; reviewed for calibration |
| 653 | Matvei Gridin nhl_sog over 2.0 | 1.0 | 0.5462 (Low) | pass | model 50%, market 56% | variance | **untagged** | root leg of a 4-leg script loss: #653, #667, #668, #691; logged as a PASS: no money on it; reviewed for calibration |
| 659 | Kiefer Sherwood nhl_sog over 1.5 | 1.0 | 0.5312 (Low) | pass | model 56%, market 52% | variance | **untagged** | root leg of a 11-leg script loss: #659, #672, #676, #679, #683, #684, #687, #688, #692, #947, #948; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 661 | Olen Zellweger nhl_sog over 1.5 | 0.0 | 0.5621 (Low) | pass | model 59%, market 56% | variance | **untagged** | root leg of a 10-leg script loss: #661, #665, #670, #673, #685, #689, #690, #693, #944, #1076; logged as a PASS: no money on it; reviewed for calibration |
| 665 | Adam Fantilli nhl_toi over 21.25 | 18.87 | 0.5256 (Low) | pass | model 62% | correlated | **untagged** | same game script as #661 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 667 | Zach Whitecloud nhl_hits under 1.5 | 3.0 | 0.5222 (Low) | pass | model 61% | correlated | **untagged** | same game script as #653 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 668 | Mikael Granlund nhl_fow under 9.0 | 10.0 | 0.5214 (Low) | pass | model 61% | correlated | **untagged** | same game script as #653 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 670 | Jack Quinn nhl_sog under 2.5 | 3.0 | 0.519 (Low) | pass | model 50%, market 52% | correlated | **untagged** | same game script as #661 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 672 | Joel Eriksson Ek nhl_pm under 0.5 | 2.0 | 0.5165 (Low) | pass | model 58% | correlated | **untagged** | same game script as #659 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 673 | Beck Malenstyn nhl_hits under 3.5 | 4.0 | 0.516 (Low) | pass | model 58% | correlated | **untagged** | same game script as #661 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 676 | Maxim Shabanov nhl_points under 0.5 | 1.0 | 0.5134 (Low) | pass | model 54%, market 51% | correlated | **untagged** | same game script as #659 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 679 | Macklin Celebrini nhl_toi under 22.75 | 24.98 | 0.5095 (Low) | pass | model 55% | correlated | **untagged** | same game script as #659 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 683 | Yakov Trenin nhl_hits under 4.5 | 5.0 | 0.5077 (Low) | pass | model 54% | correlated | **untagged** | same game script as #659 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 684 | Will Smith nhl_points under 0.5 | 1.0 | 0.5073 (Low) | pass | model 59%, market 49% (against) | correlated | **untagged** | same game script as #659 (variance); own read: model bias; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 685 | Jason Zucker nhl_sog under 1.5 | 3.0 | 0.5069 (Low) | pass | model 53% | correlated | **untagged** | same game script as #661 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 687 | Olli Maatta nhl_blocks under 1.5 | 2.0 | 0.5046 (Low) | pass | model 52% | correlated | **untagged** | same game script as #659 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 688 | Adam Gaudette nhl_hits under 0.5 | 1.0 | 0.5043 (Low) | pass | model 52% | correlated | **untagged** | same game script as #659 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 689 | Sean Monahan nhl_hits under 0.5 | 1.0 | 0.5041 (Low) | pass | model 52% | correlated | **untagged** | same game script as #661 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 690 | Kent Johnson nhl_points under 0.5 | 2.0 | 0.502 (Low) | pass | model 56%, market 49% (against) | correlated | **untagged** | same game script as #661 (variance); own read: model bias; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 691 | Morgan Frost nhl_points under 0.5 | 2.0 | 0.4999 (Low) | pass | model 51%, market 50% (against) | correlated | **untagged** | same game script as #653 (variance); own read: model bias; we priced this side at 50%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 692 | Mason Marchment nhl_sog over 1.5 | 0.0 | 0.4984 (Low) | pass | model 52%, market 49% (against) | correlated | **untagged** | same game script as #659 (variance); own read: model bias; we priced this side at 50%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 693 | Valeri Nichushkin nhl_sog over 1.5 | 0.0 | 0.4883 (Low) | pass | model 52%, market 48% (against) | correlated | **untagged** | same game script as #661 (variance); own read: model bias; we priced this side at 49%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 699 | Kenny Gainwell receptions under 2.0 | 3.0 | 0.6041 (Medium) | lean | model 55%, market 64%, hist 67% | variance | variance | root leg of a 4-leg script loss: #699, #750, #754, #956 |
| 703 | Ja'Marr Chase receptions under 7.0 | 10.0 | 0.573 (Low) | pass | model 56%, market 56%, hist 67% | variance | **untagged** | root leg of a 2-leg script loss: #703, #772; logged as a PASS: no money on it; reviewed for calibration |
| 704 | Tetairoa McMillan receptions over 5.0 | 4.0 | 0.5695 (Low) | pass | model 54%, market 58%, hist 60% | variance | **untagged** | root leg of a 12-leg script loss: #704, #705, #731, #748, #749, #785, #787, #819, #823, #824, #954, #961; logged as a PASS: no money on it; reviewed for calibration |
| 705 | Jonah Coleman rush_rec_yds under 87.5 | 88.0 | 0.5692 (Low) | pass | model 62%, market 50% (against), hist 75% | correlated | **untagged** | same game script as #704 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 706 | Jadarian Price rush_rec_yds under 67.5 | 78.0 | 0.5615 (Low) | pass | model 60%, market 49% (against), hist 100% | model bias | **untagged** | root leg of a 5-leg script loss: #706, #741, #803, #960, #1068; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 707 | J.J. McCarthy rush_yds under 12.5 | 22.0 | 0.5678 (Low) | pass | model 56%, hist 67% | variance | **untagged** | root leg of a 6-leg script loss: #707, #784, #792, #812, #818, #1072; logged as a PASS: no money on it; reviewed for calibration |
| 709 | Rachaad White rush_rec_yds under 59.5 | 69.0 | 0.5651 (Low) | pass | model 61%, market 50% (against), hist 67% | variance | **untagged** | root leg of a 4-leg script loss: #709, #713, #716, #745; logged as a PASS: no money on it; reviewed for calibration |
| 710 | Woody Marks rush_att under 17.0 | 18.0 | 0.5608 (Low) | pass | model 55%, market 54%, hist 86% | variance | **untagged** | root leg of a 4-leg script loss: #710, #780, #786, #801; logged as a PASS: no money on it; reviewed for calibration |
| 712 | Jordan Love rush_yds under 3.5 | 13.0 | 0.5537 (Low) | pass | model 58%, market 50% (against), hist 75% | variance | **untagged** | root leg of a 4-leg script loss: #712, #756, #771, #796; logged as a PASS: no money on it; reviewed for calibration |
| 713 | Puka Nacua receptions under 8.0 | 14.0 | 0.5521 (Low) | pass | model 54%, market 56%, hist 40% (against) | correlated | **untagged** | same game script as #709 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 716 | Konata Mumpfield rec_yds under 16.5 | 20.0 | 0.5505 (Low) | pass | model 52%, hist 86% | correlated | **untagged** | same game script as #709 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 730 | Ashton Jeanty rush_att over 8.5 | 6.0 | 0.5398 (Low) | pass | model 55%, market 50% (against), hist 75% | variance | **untagged** | root leg of a 6-leg script loss: #730, #751, #769, #782, #783, #955; logged as a PASS: no money on it; reviewed for calibration |
| 731 | J.K. Dobbins rush_att over 7.5 | 4.0 | 0.5392 (Low) | pass | model 54%, market 50% (against), hist 75% | correlated | **untagged** | same game script as #704 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 734 | Braelon Allen rush_yds over 33.5 | 33.0 | 0.5377 (Low) | pass | model 52%, market 52%, hist 75% | variance | **untagged** | root leg of a 2-leg script loss: #734, #789; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 741 | Cooper Kupp rec_yds under 20.5 | 32.0 | 0.5338 (Low) | pass | model 52%, hist 62% | correlated | **untagged** | same game script as #706 (model bias); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 745 | Chig Okonkwo receptions under 3.5 | 6.0 | 0.5318 (Low) | pass | model 54%, market 50% (against), hist 60% | correlated | **untagged** | same game script as #709 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 746 | Tyler Goodson rush_rec_yds under 27.5 | 77.0 | 0.5311 (Low) | pass | model 54%, market 50% (against), hist 60% | variance | **untagged** | root leg of a 6-leg script loss: #746, #766, #767, #775, #816, #964; logged as a PASS: no money on it; reviewed for calibration |
| 748 | Courtland Sutton rec_yds under 36.5 | 45.0 | 0.5307 (Low) | pass | model 54%, market 49% (against), hist 62% | correlated | **untagged** | same game script as #704 (variance); own read: model bias; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 749 | Evan Engram rec_yds under 18.5 | 33.0 | 0.5307 (Low) | pass | model 52%, market 50% (against), hist 75% | correlated | **untagged** | same game script as #704 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 750 | Tez Johnson rec_yds under 14.5 | 76.0 | 0.5302 (Low) | pass | model 52%, hist 50% (against) | correlated | **untagged** | same game script as #699 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 751 | Brock Bowers rec_yds under 76.5 | 111.0 | 0.5291 (Low) | pass | model 52%, market 53%, hist 33% (against) | correlated | **untagged** | same game script as #730 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 754 | Luther Burden III rec_yds under 65.5 | 97.0 | 0.528 (Low) | pass | model 53%, market 49% (against), hist 75% | correlated | **untagged** | same game script as #699 (variance); own read: model bias; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 756 | Savion Williams rush_yds under 3.5 | 13.0 | 0.5274 (Low) | pass | model 54%, hist 0% (against) | correlated | **untagged** | same game script as #712 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 760 | Jahmyr Gibbs rec_yds over 31.5 | 0.0 | 0.5264 (Low) | pass | model 50% (against), market 54%, hist 43% (against) | variance | **untagged** | root leg of a 5-leg script loss: #760, #768, #774, #810, #959; logged as a PASS: no money on it; reviewed for calibration |
| 766 | Tyler Warren rec_yds under 42.5 | 44.0 | 0.5254 (Low) | pass | model 52%, market 50% (against), hist 67% | correlated | **untagged** | same game script as #746 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 767 | Seth McGowan rush_yds under 25.5 | 45.0 | 0.5253 (Low) | pass | model 53%, market 50% (against), hist 50% (against) | correlated | **untagged** | same game script as #746 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 768 | Jared Goff pass_att over 30.5 | 25.0 | 0.5245 (Low) | pass | model 52%, market 50% (against), hist 71% | correlated | **untagged** | same game script as #760 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 769 | Kirk Cousins pass_att over 36.0 | 32.0 | 0.5245 (Low) | pass | model 51%, market 53%, hist 38% (against) | correlated | **untagged** | same game script as #730 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 771 | Efton Chism III rec_yds under 30.5 | 49.0 | 0.5243 (Low) | pass | model 52%, market 50% (against), hist 57% | correlated | **untagged** | same game script as #712 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 772 | Bijan Robinson rec_yds under 25.5 | 47.0 | 0.5242 (Low) | pass | model 52%, market 50% (against), hist 62% | correlated | **untagged** | same game script as #703 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 774 | Amon-Ra St. Brown rec_yds under 76.5 | 86.0 | 0.5238 (Low) | pass | model 51%, market 50% (against), hist 71% | correlated | **untagged** | same game script as #760 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 775 | Javonte Williams rush_rec_yds under 86.5 | 124.0 | 0.5237 (Low) | pass | model 51%, market 50% (against), hist 75% | correlated | **untagged** | same game script as #746 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 778 | Denzel Boston rec_yds under 46.5 | 98.0 | 0.5219 (Low) | pass | model 51%, market 50% (against), hist 62% | variance | **untagged** | root leg of a 4-leg script loss: #778, #779, #802, #811; logged as a PASS: no money on it; reviewed for calibration |
| 779 | Juwan Johnson rec_yds under 29.5 | 34.0 | 0.5218 (Low) | pass | model 52%, hist 43% (against) | correlated | **untagged** | same game script as #778 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 780 | C.J. Stroud pass_td under 1.5 | 5.0 | 0.5216 (Low) | pass | model 53%, market 50% (against), hist 43% (against) | correlated | **untagged** | same game script as #710 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 782 | Jordan Watkins receptions under 1.5 | 4.0 | 0.5214 (Low) | pass | model 53%, market 50% (against), hist 33% (against) | correlated | **untagged** | same game script as #730 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 783 | Kaelon Black rush_yds under 39.5 | 70.0 | 0.5213 (Low) | pass | model 51%, market 50% (against), hist 71% | correlated | **untagged** | same game script as #730 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 784 | Malik Nabers receptions over 5.5 | 5.0 | 0.5212 (Low) | pass | model 51%, market 50% (against), hist 71% | correlated | **untagged** | same game script as #707 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 785 | Bo Nix pass_att under 32.5 | 37.0 | 0.5206 (Low) | pass | model 50%, market 50% (against), hist 75% | correlated | **untagged** | same game script as #704 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 786 | Keaton Mitchell rec_yds under 11.5 | 34.0 | 0.5205 (Low) | pass | model 52%, hist 43% (against) | correlated | **untagged** | same game script as #710 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 787 | Troy Franklin rec_yds under 6.5 | 31.0 | 0.5201 (Low) | pass | model 51%, market 50% (against), hist 57% | correlated | **untagged** | same game script as #704 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 789 | Kenyon Sadiq rec_yds under 17.5 | 49.0 | 0.52 (Low) | pass | model 51%, market 50% (against), hist 62% | correlated | **untagged** | same game script as #734 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 792 | Dallas Goedert rec_yds under 35.5 | 50.0 | 0.5189 (Low) | pass | model 54%, market 48% (against), hist 33% (against) | correlated | **untagged** | same game script as #707 (variance); own read: model bias; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 796 | DeMario Douglas receptions under 3.5 | 5.0 | 0.518 (Low) | pass | model 51%, market 50% (against), hist 62% | correlated | **untagged** | same game script as #712 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 801 | Tre' Harris receptions under 2.5 | 3.0 | 0.516 (Low) | pass | model 52%, market 50% (against), hist 33% (against) | correlated | **untagged** | same game script as #710 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 802 | Noah Fant rec_yds under 8.5 | 12.0 | 0.5155 (Low) | pass | model 51%, hist 40% (against) | correlated | **untagged** | same game script as #778 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 803 | Michael Wilson rec_yds under 49.5 | 60.0 | 0.515 (Low) | pass | model 52%, market 50% (against), hist 38% (against) | correlated | **untagged** | same game script as #706 (model bias); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 810 | Caleb Douglas rec_yds under 40.5 | 70.0 | 0.5109 (Low) | pass | model 51%, market 50% (against), hist 25% (against) | correlated | **untagged** | same game script as #760 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 811 | Chris Olave rec_yds under 71.5 | 98.0 | 0.5106 (Low) | pass | model 51%, market 49% (against), hist 43% (against) | correlated | **untagged** | same game script as #778 (variance); own read: model bias; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 812 | Isaiah Likely rec_yds under 43.5 | 53.0 | 0.5104 (Low) | pass | model 50%, market 50% (against), hist 43% (against) | correlated | **untagged** | same game script as #707 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 816 | Jonathan Taylor rec_yds under 17.5 | 18.0 | 0.5082 (Low) | pass | model 50%, market 50% (against), hist 38% (against) | correlated | **untagged** | same game script as #746 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 818 | Darnell Mooney rec_yds under 12.5 | 54.0 | 0.507 (Low) | pass | model 51%, market 48% (against), hist 43% (against) | correlated | **untagged** | same game script as #707 (variance); own read: model bias; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 819 | Darren Waller rec_yds under 18.5 | 90.0 | 0.507 (Low) | pass | model 50%, market 50% (against), hist 29% (against) | correlated | **untagged** | same game script as #704 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 823 | Tommy Tremble rec_yds under 16.5 | 24.0 | 0.5042 (Low) | pass | model 50%, market 48% (against), hist 43% (against) | correlated | **untagged** | same game script as #704 (variance); own read: model bias; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 824 | Mitchell Evans rec_yds under 7.5 | 20.0 | 0.5029 (Low) | pass | model 50%, market 50% (against), hist 14% (against) | correlated | **untagged** | same game script as #704 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 827 | Aaron Jones Sr. rush_rec_yds over 42.5 | 21.0 | 0.6149 (Medium) | lean | model 56%, market 52%, hist 57% | variance | **untagged** | root leg of a 5-leg script loss: #827, #828, #832, #833, #951 |
| 828 | Dawson Knox rec_yds under 7.5 | 37.0 | 0.4926 (Low) | pass | model 52%, market 50% (against), hist 86% | correlated | **untagged** | same game script as #827 (variance); own read: variance; we priced this side at 49%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 832 | James Cook III rush_att under 18.5 | 31.0 | 0.5226 (Low) | pass | model 54%, market 50% (against), hist 29% (against) | correlated | **untagged** | same game script as #827 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 833 | Khalil Shakir rec_yds under 38.5 | 58.0 | 0.5219 (Low) | pass | model 52%, market 51%, hist 43% (against) | correlated | **untagged** | same game script as #827 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 838 | Mirra Andreeva tennis_games over 21.5 | 16.0 | 0.4878 (Low) | pass | model 44% (against), market 50% (against) | correlated | **untagged** | same game script as #652 (variance); own read: variance; we priced this side at 49%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 839 | Jayson Tatum pr under 34.5 | 42.0 | 0.5596 (Medium) | pass | model 74%, market 51% | variance | **untagged** | root leg of a 20-leg script loss: #839, #840, #841, #843, #844, #846, #847, #849, #967, #968, #969, #972, #973, #1080, #1081, #1082, #1153, #1154, #1155, #1202; logged as a PASS: no money on it; reviewed for calibration |
| 840 | Jayson Tatum pa under 33.5 | 43.0 | 0.5495 (Medium) | pass | model 71%, market 51% | correlated | **untagged** | same game script as #839 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 841 | Brandon Miller pr over 26.5 | 10.0 | 0.5446 (Medium) | pass | model 65%, market 52% | correlated | **untagged** | same game script as #839 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 843 | Derrick White pra under 21.5 | 27.0 | 0.5589 (Medium) | pass | model 57%, market 52% | correlated | **untagged** | same game script as #839 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 844 | Payton Pritchard pra under 20.5 | 23.0 | 0.565 (Medium) | pass | model 63%, market 51% | correlated | **untagged** | same game script as #839 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 846 | Grayson Allen pa over 15.5 | 3.0 | 0.5413 (Medium) | pass | model 59%, market 53% | correlated | **untagged** | same game script as #839 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 847 | Naz Reid reb over 7.5 | 6.0 | 0.586 (Medium) | pass | model 68%, market 51% | correlated | **untagged** | same game script as #839 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 849 | Grayson Allen reb over 2.5 | 2.0 | 0.569 (Medium) | pass | model 60%, market 51% | correlated | **untagged** | same game script as #839 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 850 | Trae Young pra under 33.5 | 35.0 | 0.5769 (Medium) | pass | model 70%, market 51% | variance | **untagged** | root leg of a 19-leg script loss: #850, #851, #852, #855, #932, #976, #978, #980, #984, #986, #1062, #1084, #1085, #1088, #1092, #1094, #1135, #1159, #1199; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 851 | Onyeka Okongwu pra under 27.5 | 33.0 | 0.5426 (Medium) | pass | model 60%, market 50% (against) | correlated | **untagged** | same game script as #850 (variance); own read: model bias; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 852 | Alex Sarr pra under 21.5 | 24.0 | 0.542 (Medium) | pass | model 58%, market 50% (against) | correlated | **untagged** | same game script as #850 (variance); own read: model bias; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 855 | Trae Young ast under 9.5 | 10.0 | 0.5533 (Medium) | pass | model 71%, market 51% | correlated | **untagged** | same game script as #850 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 859 | Donovan Mitchell pa under 30.5 | 31.0 | 0.5539 (Medium) | pass | model 71%, market 51% | correlated | **untagged** | same game script as #615 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 862 | Donovan Mitchell reb under 5.0 | 7.0 | 0.5802 (Medium) | pass | model 65%, market 56% | correlated | **untagged** | same game script as #615 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 863 | James Harden reb under 5.0 | 6.0 | 0.5734 (Medium) | pass | model 61%, market 56% | correlated | **untagged** | same game script as #615 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 865 | Ajay Mitchell pra under 28.5 | 41.0 | 0.5537 (Medium) | pass | model 64%, market 50% (against) | correlated | **untagged** | same game script as #635 (variance); own read: model bias; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 874 | Jonathan Kuminga pra under 23.5 | 29.0 | 0.5454 (Medium) | pass | model 49% (against), market 52% | variance | **untagged** | root leg of a 7-leg script loss: #874, #905, #906, #1108, #1111, #1176, #1216; logged as a PASS: no money on it; reviewed for calibration |
| 881 | Lauri Markkanen pra under 29.5 | 33.0 | 0.5597 (Medium) | pass | model 67%, market 50% (against) | correlated | **untagged** | same game script as #621 (variance); own read: model bias; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 882 | Lauri Markkanen pr under 27.5 | 32.0 | 0.5469 (Medium) | pass | model 69%, market 51% | correlated | **untagged** | same game script as #621 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 883 | Lauri Markkanen pa under 23.5 | 25.0 | 0.5513 (Medium) | pass | model 70%, market 51% | correlated | **untagged** | same game script as #621 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 884 | Darryn Peterson pra under 21.5 | 28.0 | 0.5467 (Medium) | pass | model 58%, market 50% | correlated | **untagged** | same game script as #621 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 885 | Lauri Markkanen pts under 21.5 | 24.0 | 0.5791 (Medium) | pass | model 72%, market 54% | correlated | **untagged** | same game script as #621 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 888 | Jaxson Hayes pra under 16.5 | 17.0 | 0.5489 (Medium) | pass | model 56%, market 51% | correlated | **untagged** | same game script as #621 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 896 | RJ Barrett pra under 36.5 | 39.0 | 0.5668 (Medium) | pass | model 66%, market 51% | correlated | **untagged** | same game script as #618 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 897 | Tyler Herro pra under 29.5 | 38.0 | 0.5468 (Medium) | pass | model 53%, market 52% | correlated | **untagged** | same game script as #618 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 898 | Collin Murray-Boyles pra under 22.5 | 28.0 | 0.591 (Medium) | pass | model 79%, market 50% (against) | correlated | **untagged** | same game script as #618 (variance); own read: model bias; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 900 | Collin Murray-Boyles pr under 20.5 | 26.0 | 0.5778 (Medium) | pass | model 79%, market 51% | correlated | **untagged** | same game script as #618 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 902 | Collin Murray-Boyles pa under 16.5 | 21.0 | 0.5888 (Medium) | pass | model 81%, market 52% | correlated | **untagged** | same game script as #618 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 905 | Jonathan Kuminga reb under 6.0 | 8.0 | 0.5585 (Medium) | pass | model 59%, market 55% | correlated | **untagged** | same game script as #874 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 906 | Saddiq Bey reb under 4.0 | 5.0 | 0.5413 (Medium) | pass | model 59%, market 53% | correlated | **untagged** | same game script as #874 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 910 | Darius Acuff Jr. pra under 32.5 | 33.0 | 0.5485 (Medium) | pass | model 53%, market 52% | variance | **untagged** | root leg of a 18-leg script loss: #910, #911, #914, #916, #918, #920, #1022, #1024, #1026, #1027, #1237, #1238, #1239, #1240, #1241, #1270, #1274, #1275; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 911 | Stephon Castle pra under 28.5 | 29.0 | 0.5423 (Medium) | pass | model 58%, market 50% (against) | correlated | **untagged** | same game script as #910 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 914 | Keldon Johnson pr over 14.5 | 9.0 | 0.5485 (Medium) | pass | model 68%, market 51% | correlated | **untagged** | same game script as #910 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 916 | Keldon Johnson pts over 9.5 | 3.0 | 0.5572 (Medium) | pass | model 65%, market 53% | correlated | **untagged** | same game script as #910 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 918 | De'Aaron Fox ast over 5.5 | 4.0 | 0.5416 (Medium) | pass | model 59%, market 55% | correlated | **untagged** | same game script as #910 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 920 | De'Aaron Fox reb over 3.5 | 2.0 | 0.5489 (Medium) | pass | model 51%, market 51% | correlated | **untagged** | same game script as #910 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 923 | Scoot Henderson pra over 16.5 | 4.0 | 0.5529 (Medium) | pass | model 55%, market 55% | correlated | **untagged** | same game script as #632 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 925 | Quentin Grimes pts over 6.5 | 2.0 | 0.5644 (Medium) | pass | model 66%, market 54% | correlated | **untagged** | same game script as #632 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 926 | Sidy Cissoko reb over 2.5 | 2.0 | 0.5607 (Medium) | pass | model 60%, market 50% | correlated | **untagged** | same game script as #632 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 927 | Robert Williams III reb over 6.0 | 5.0 | 0.5612 (Medium) | pass | model 56%, market 51% | correlated | **untagged** | same game script as #632 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 928 | Toumani Camara reb under 4.0 | 6.0 | 0.5844 (Medium) | pass | model 71%, market 55% | correlated | **untagged** | same game script as #632 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 931 | Naji Marshall ra over 7.0 | 6.0 | 0.5626 (Low) | pass | model 24% (against), market 65% | correlated | **untagged** | same game script as #621 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 932 | Onyeka Okongwu pa under 18.5 | 23.0 | 0.5167 (Low) | pass | model 62%, market 49% (against) | correlated | **untagged** | same game script as #850 (variance); own read: model bias; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 933 | Evan Mobley pra under 30.5 | 32.0 | 0.5535 (Low) | pass | model 68%, market 49% (against) | correlated | **untagged** | same game script as #615 (variance); own read: model bias; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 934 | Keyonte George ra under 10.0 | 15.0 | 0.5299 (Low) | pass | model 62%, market 51% | correlated | **untagged** | same game script as #621 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 936 | Nathan MacKinnon nhl_sog under 3.5 | 4.0 | 0.4823 (Low) | pass | model 59%, market 48% (against) | model bias | **untagged** | we priced this side at 48%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 937 | Bobby McMann nhl_sog over 2.5 | 2.0 | 0.5237 (Low) | pass | model 52%, market 55% | variance | **untagged** | logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 940 | Philip Broberg nhl_sog over 1.5 | 1.0 | 0.5321 (Low) | pass | model 66% | variance | **untagged** | logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 944 | Rasmus Dahlin nhl_toi over 24.5 | 23.27 | 0.5111 (Low) | pass | model 56% | correlated | **untagged** | same game script as #661 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 947 | Kirill Kaprizov nhl_toi over 21.5 | 19.47 | 0.529 (Low) | pass | model 64% | correlated | **untagged** | same game script as #659 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 948 | Quinn Hughes nhl_sog over 2.5 | 2.0 | 0.5186 (Low) | pass | model 60%, market 50% (against) | correlated | **untagged** | same game script as #659 (variance); own read: model bias; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 949 | Jake Guentzel nhl_sog under 2.5 | 7.0 | 0.5067 (Low) | pass | model 53% | variance | **untagged** | root leg of a 2-leg script loss: #949, #1066; logged as a PASS: no money on it; reviewed for calibration |
| 950 | Alex Laferriere nhl_sog under 2.5 | 7.0 | 0.493 (Low) | pass | model 46% (against) | variance | **untagged** | we priced this side at 49%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 951 | Josh Allen completions under 20.5 | 21.0 | 0.5536 (Low) | pass | model 52%, market 57%, hist 57% | correlated | **untagged** | same game script as #827 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 954 | Jonah Coleman rush_yds under 55.5 | 57.0 | 0.5498 (Low) | pass | model 57%, market 49% (against), hist 100% | correlated | **untagged** | same game script as #704 (variance); own read: model bias; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 955 | Brandin Cooks receptions under 1.5 | 2.0 | 0.5487 (Low) | pass | model 56%, market 50% (against), hist 100% | correlated | **untagged** | same game script as #730 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 956 | Bucky Irving rec_yds under 13.5 | 28.0 | 0.5338 (Low) | pass | model 54%, market 49% (against), hist 88% | correlated | **untagged** | same game script as #699 (variance); own read: model bias; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 959 | Jahmyr Gibbs rush_rec_yds over 133.5 | 74.0 | 0.5257 (Low) | pass | model 50%, market 52%, hist 71% | correlated | **untagged** | same game script as #760 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 960 | Jadarian Price rec_yds under 9.5 | 54.0 | 0.5345 (Low) | pass | model 50%, market 53%, hist 100% | correlated | **untagged** | same game script as #706 (model bias); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 961 | J.K. Dobbins rec_yds under 3.5 | 4.0 | 0.5264 (Low) | pass | model 53%, market 51%, hist 50% (against) | correlated | **untagged** | same game script as #704 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 964 | Dak Prescott pass_yds under 263.5 | 335.0 | 0.5173 (Low) | pass | model 52%, market 49% (against), hist 50% (against) | correlated | **untagged** | same game script as #746 (variance); own read: model bias; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 967 | Jayson Tatum pra under 40.5 | 51.0 | 0.5789 (Medium) | pass | model 72%, market 51% | correlated | **untagged** | same game script as #839 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 968 | Neemias Queta pra over 17.5 | 8.0 | 0.5707 (Medium) | pass | model 49% (against), market 59% | correlated | **untagged** | same game script as #839 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 969 | Ryan Kalkbrenner pr over 12.5 | 9.0 | 0.6036 (Medium) | pass | model 54%, market 62% | correlated | **untagged** | same game script as #839 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 972 | Sion James reb over 3.5 | 3.0 | 0.5772 (Medium) | pass | model 56%, market 54% | correlated | **untagged** | same game script as #839 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 973 | Derrick White reb under 3.5 | 4.0 | 0.5419 (Medium) | pass | model 66%, market 51% | correlated | **untagged** | same game script as #839 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 976 | Trae Young pra under 32.5 | 35.0 | 0.5578 (Medium) | pass | model 65%, market 50% | correlated | **untagged** | same game script as #850 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 978 | Bilal Coulibaly pra under 12.5 | 14.0 | 0.5402 (Medium) | pass | model 49% (against), market 52% | correlated | **untagged** | same game script as #850 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 980 | Bub Carrington pra over 9.5 | 7.0 | 0.6202 (High) | pass | model 61%, market 62% | correlated | opportunity | same game script as #850 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 984 | Nickeil Alexander-Walker ra over 6.5 | 4.0 | 0.5405 (Medium) | pass | model 62%, market 52% | correlated | **untagged** | same game script as #850 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 986 | Nickeil Alexander-Walker reb over 3.0 | 2.0 | 0.5787 (Medium) | pass | model 72%, market 49% (against) | correlated | **untagged** | same game script as #850 (variance); own read: model bias; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 987 | Donovan Mitchell pra under 35.0 | 38.0 | 0.5653 (Medium) | pass | model 70%, market 49% (against) | correlated | **untagged** | same game script as #615 (variance); own read: model bias; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 1000 | Ace Bailey pts over 12.5 | 12.0 | 0.575 (Medium) | pass | model 52%, market 59% | correlated | **untagged** | same game script as #621 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1001 | P.J. Washington ra over 8.5 | 7.0 | 0.5557 (Medium) | pass | model 53%, market 56% | correlated | **untagged** | same game script as #621 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1004 | Naji Marshall ast under 3.5 | 5.0 | 0.5788 (Medium) | pass | model 67%, market 56% | correlated | **untagged** | same game script as #621 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1005 | RJ Barrett pra under 37.5 | 39.0 | 0.6828 (High) | pass | model 69%, market 65% | correlated | role/lineup | same game script as #618 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1006 | RJ Barrett pr under 32.5 | 34.0 | 0.6368 (High) | pass | model 67%, market 63% | correlated | role/lineup | same game script as #618 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1007 | RJ Barrett pa under 30.5 | 32.0 | 0.5513 (Medium) | pass | model 69%, market 51% | correlated | **untagged** | same game script as #618 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1008 | RJ Barrett pts under 25.5 | 27.0 | 0.5458 (Medium) | pass | model 66%, market 52% | correlated | **untagged** | same game script as #618 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1010 | Kyle Kuzma pra under 17.5 | 20.0 | 0.5408 (Medium) | pass | model 53%, market 51% | correlated | **untagged** | same game script as #618 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1013 | Collin Murray-Boyles pts under 14.5 | 19.0 | 0.6049 (Low) | pass | model 48% (against), market 64% | correlated | **untagged** | same game script as #618 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1016 | Collin Murray-Boyles ra under 8.5 | 9.0 | 0.5758 (Medium) | pass | model 69%, market 55% | correlated | **untagged** | same game script as #618 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1018 | AJ Green pts under 6.5 | 12.0 | 0.5433 (Medium) | pass | model 51%, market 55% | correlated | **untagged** | same game script as #618 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1020 | Tyler Herro ast under 4.0 | 10.0 | 0.5666 (Medium) | pass | model 60%, market 56% | correlated | **untagged** | same game script as #618 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1022 | Keldon Johnson pra over 15.5 | 15.0 | 0.5573 (Medium) | pass | model 70%, market 52% | correlated | **untagged** | same game script as #910 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1024 | Darius Acuff Jr. ra under 9.5 | 11.0 | 0.5477 (Medium) | pass | model 56%, market 55% | correlated | **untagged** | same game script as #910 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1026 | Malik Monk ra under 6.5 | 7.0 | 0.5647 (Medium) | pass | model 68%, market 53% | correlated | **untagged** | same game script as #910 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1027 | Zach LaVine ra under 5.5 | 7.0 | 0.5525 (Medium) | pass | model 62%, market 54% | correlated | **untagged** | same game script as #910 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1028 | Luka Dončić pra under 50.5 | 63.0 | 0.5674 (Medium) | pass | model 68%, market 50% | correlated | **untagged** | same game script as #632 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1029 | Luka Dončić pr under 43.5 | 58.0 | 0.5445 (Medium) | pass | model 66%, market 51% | correlated | **untagged** | same game script as #632 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1032 | Damian Lillard pts under 21.5 | 22.0 | 0.5516 (Medium) | pass | model 59%, market 54% | correlated | **untagged** | same game script as #632 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1033 | Sandro Mamukelashvili pra over 13.5 | 11.0 | 0.5412 (Medium) | pass | model 66%, market 51% | correlated | **untagged** | same game script as #632 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1034 | Sandro Mamukelashvili pr over 12.5 | 10.0 | 0.545 (Medium) | pass | model 62%, market 53% | correlated | **untagged** | same game script as #632 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1036 | Collin Sexton pts over 8.5 | 0.0 | 0.5415 (Medium) | pass | model 62%, market 52% | correlated | **untagged** | same game script as #632 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1037 | Luka Dončić reb over 7.0 | 5.0 | 0.6203 (Low) | pass | model 48% (against), market 61% | correlated | **untagged** | same game script as #632 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1040 | Deni Avdija ra under 13.0 | 20.0 | 0.5989 (Medium) | lean | model 62%, market 59% | correlated | opportunity | same game script as #632 (variance); own read: variance |
| 1043 | Kevin Durant pra under 29.5 | 34.0 | 0.5598 (Medium) | pass | model 60%, market 52% | variance | **untagged** | root leg of a 13-leg script loss: #1043, #1044, #1045, #1047, #1048, #1049, #1051, #1053, #1056, #1058, #1201, #1230, #1231; logged as a PASS: no money on it; reviewed for calibration |
| 1044 | Jabari Smith Jr. pra under 24.5 | 26.0 | 0.5507 (Medium) | pass | model 57%, market 51% | correlated | **untagged** | same game script as #1043 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1045 | Amen Thompson pr under 21.5 | 24.0 | 0.5411 (Medium) | pass | model 60%, market 52% | correlated | **untagged** | same game script as #1043 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1047 | Jabari Smith Jr. ra under 8.5 | 11.0 | 0.5422 (Medium) | pass | model 60%, market 53% | correlated | **untagged** | same game script as #1043 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1048 | Kevin Durant ra under 8.5 | 13.0 | 0.597 (Medium) | pass | model 63%, market 55% | correlated | **untagged** | same game script as #1043 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1049 | Reed Sheppard pts over 8.5 | 6.0 | 0.5444 (Medium) | pass | model 67%, market 51% | correlated | **untagged** | same game script as #1043 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1051 | Fred VanVleet ra over 7.5 | 7.0 | 0.563 (Medium) | pass | model 61%, market 55% | correlated | **untagged** | same game script as #1043 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1053 | Amen Thompson reb under 6.5 | 7.0 | 0.5707 (Medium) | pass | model 62%, market 56% | correlated | **untagged** | same game script as #1043 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1056 | Marcus Smart pts over 5.5 | 5.0 | 0.5534 (Medium) | pass | model 66%, market 52% | correlated | **untagged** | same game script as #1043 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1058 | Oso Ighodaro reb under 5.5 | 6.0 | 0.5445 (Medium) | pass | model 64%, market 51% | correlated | variance | same game script as #1043 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1062 | Onyeka Okongwu pa under 19.5 | 23.0 | 0.5061 (Low) | pass | model 49% (against), market 51% | correlated | **untagged** | same game script as #850 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1066 | Matt Boldy nhl_sog over 3.5 | 2.0 | 0.5531 (Low) | pass | model 46% (against), market 58% | correlated | **untagged** | same game script as #949 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1068 | Cooper Kupp rec_yds under 26.5 | 32.0 | 0.5266 (Low) | pass | model 52%, market 50% (against), hist 62% | correlated | **untagged** | same game script as #706 (model bias); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1072 | Malik Nabers rec_yds over 71.5 | 43.0 | 0.514 (Low) | pass | model 50%, market 50% (against), hist 57% | correlated | **untagged** | same game script as #707 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1075 | Sebastian Aho nhl_sog over 2.5 | 1.0 | 0.503 (Low) | pass | model 59%, market 50% | variance | **untagged** | root leg of a 2-leg script loss: #1075, #1077; logged as a PASS: no money on it; reviewed for calibration |
| 1076 | Owen Power nhl_sog under 1.5 | 3.0 | 0.5168 (Low) | pass | model 58%, market 50% (against) | correlated | **untagged** | same game script as #661 (variance); own read: model bias; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 1077 | Connor Bedard nhl_sog over 2.5 | 1.0 | 0.4946 (Low) | pass | model 47% (against) | correlated | **untagged** | same game script as #1075 (variance); own read: variance; we priced this side at 49%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 1080 | Ryan Kalkbrenner pra over 13.5 | 9.0 | 0.5487 (Medium) | pass | model 59%, market 54% | correlated | **untagged** | same game script as #839 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1081 | Royce O'Neale pts under 6.5 | 7.0 | 0.5961 (Medium) | pass | model 56%, market 60% | correlated | **untagged** | same game script as #839 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1082 | Sion James ast over 2.5 | 0.0 | 0.5573 (Medium) | pass | model 68%, market 55% | correlated | **untagged** | same game script as #839 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1084 | Trae Young pa under 31.5 | 33.0 | 0.5545 (Medium) | pass | model 60%, market 54% | correlated | **untagged** | same game script as #850 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1085 | Nickeil Alexander-Walker pa under 26.5 | 30.0 | 0.5666 (Medium) | pass | model 51%, market 58% | correlated | **untagged** | same game script as #850 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1088 | Nickeil Alexander-Walker pts under 22.5 | 28.0 | 0.54 (Medium) | pass | model 50% (against), market 55% | correlated | **untagged** | same game script as #850 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1092 | Onyeka Okongwu ra over 12.5 | 11.0 | 0.5463 (Medium) | pass | model 69%, market 51% | correlated | **untagged** | same game script as #850 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1094 | Dyson Daniels ast under 6.0 | 12.0 | 0.5613 (Medium) | pass | model 50% (against), market 58% | correlated | **untagged** | same game script as #850 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1096 | Donovan Mitchell pa under 29.5 | 31.0 | 0.5454 (Medium) | pass | model 68%, market 51% | correlated | **untagged** | same game script as #615 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1098 | Evan Mobley pr under 26.5 | 28.0 | 0.5529 (Medium) | pass | model 67%, market 52% | correlated | **untagged** | same game script as #615 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1099 | Evan Mobley pa under 21.5 | 26.0 | 0.5414 (Medium) | pass | model 65%, market 51% | correlated | **untagged** | same game script as #615 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1101 | VJ Edgecombe ra over 8.5 | 5.0 | 0.5624 (Medium) | pass | model 62%, market 55% | correlated | **untagged** | same game script as #615 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1102 | Kentavious Caldwell-Pope pra over 8.5 | 7.0 | 0.5518 (Medium) | pass | model 51%, market 56% | correlated | **untagged** | same game script as #615 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1103 | VJ Edgecombe reb over 5.5 | 3.0 | 0.5497 (Medium) | pass | model 59%, market 49% (against) | correlated | **untagged** | same game script as #615 (variance); own read: model bias; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 1104 | Donovan Mitchell ra under 10.0 | 15.0 | 0.5421 (Medium) | pass | model 62%, market 52% | correlated | **untagged** | same game script as #615 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1107 | Cam Spencer ra over 7.5 | 1.0 | 0.5423 (Medium) | pass | model 64%, market 52% | correlated | **untagged** | same game script as #635 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1108 | Bones Hyland pa over 11.5 | 4.0 | 0.5436 (Medium) | pass | model 62%, market 52% | correlated | **untagged** | same game script as #874 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1111 | Bones Hyland tpm over 1.5 | 1.0 | 0.5532 (Medium) | pass | model 59%, market 55% | correlated | **untagged** | same game script as #874 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1115 | Ace Bailey pr over 18.5 | 18.0 | 0.5431 (Medium) | pass | model 55%, market 54% | correlated | **untagged** | same game script as #621 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1118 | Daniel Gafford pa over 10.5 | 8.0 | 0.5522 (Medium) | pass | model 52%, market 56% | correlated | **untagged** | same game script as #621 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1119 | Daniel Gafford pts over 8.5 | 7.0 | 0.568 (Medium) | pass | model 52%, market 58% | correlated | **untagged** | same game script as #621 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1120 | Ace Bailey ra over 7.5 | 6.0 | 0.5477 (Medium) | pass | model 64%, market 52% | correlated | **untagged** | same game script as #621 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1123 | Collin Murray-Boyles pts under 13.5 | 19.0 | 0.5512 (Low) | pass | model 42% (against), market 58% | correlated | **untagged** | same game script as #618 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1124 | RJ Barrett ra under 11.5 | 12.0 | 0.5647 (Medium) | pass | model 64%, market 55% | correlated | **untagged** | same game script as #618 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1126 | Kel'el Ware tpm over 0.5 | 0.0 | 0.5465 (Medium) | pass | model 63%, market 53% | correlated | **untagged** | same game script as #618 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1132 | Austin Reaves pts under 22.5 | 25.0 | 0.5486 (Medium) | pass | model 59%, market 54% | correlated | **untagged** | same game script as #632 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1133 | Quentin Grimes pra over 12.5 | 2.0 | 0.542 (Medium) | pass | model 61%, market 52% | correlated | **untagged** | same game script as #632 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1134 | Walker Kessler ra under 11.5 | 14.0 | 0.5552 (Medium) | pass | model 60%, market 55% | correlated | **untagged** | same game script as #632 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1135 | Deandre Ayton reb under 6.5 | 11.0 | 0.516 (Low) | pass | model 52%, market 52% | correlated | **untagged** | same game script as #850 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1136 | Tyrese Maxey pr over 29.5 | 20.0 | 0.4593 (Low) | pass | model 39% (against), market 48% (against) | correlated | **untagged** | same game script as #615 (variance); own read: variance; we priced this side at 46%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration |
| 1138 | Jaylen Brown reb over 6.5 | 5.0 | 0.5364 (Low) | pass | model 51%, market 50% (against) | correlated | **untagged** | same game script as #615 (variance); own read: model bias; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 1153 | Ryan Kalkbrenner ra over 7.5 | 5.0 | 0.5504 (Medium) | pass | model 59%, market 54% | correlated | **untagged** | same game script as #839 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1154 | Ryan Kalkbrenner pa over 7.5 | 4.0 | 0.5447 (Medium) | pass | model 56%, market 54% | correlated | **untagged** | same game script as #839 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1155 | Sion James ra over 5.5 | 3.0 | 0.7 (Medium) | lean | model 73%, market 69% | correlated | opportunity | same game script as #839 (variance); own read: variance |
| 1159 | Deandre Ayton pr under 16.5 | 19.0 | 0.5755 (Medium) | pass | model 61%, market 57% | correlated | **untagged** | same game script as #850 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1162 | Evan Mobley pr under 27.5 | 28.0 | 0.5907 (Medium) | pass | model 70%, market 56% | correlated | **untagged** | same game script as #615 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1165 | Evan Mobley pa under 22.5 | 26.0 | 0.544 (Medium) | pass | model 60%, market 53% | correlated | **untagged** | same game script as #615 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1166 | Evan Mobley pts under 18.5 | 22.0 | 0.5658 (Medium) | pass | model 68%, market 54% | correlated | **untagged** | same game script as #615 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1169 | Kentavious Caldwell-Pope pa over 6.5 | 5.0 | 0.5436 (Medium) | pass | model 50% (against), market 56% | correlated | **untagged** | same game script as #615 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1176 | Jaylen Clark pra under 10.5 | 11.0 | 0.5482 (Medium) | pass | model 49% (against), market 53% | correlated | **untagged** | same game script as #874 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1180 | Collin Murray-Boyles pra under 24.5 | 28.0 | 0.6466 (Low) | pass | model 46% (against), market 66% | correlated | **untagged** | same game script as #618 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1181 | Jamal Shead pra under 23.5 | 29.0 | 0.5468 (Medium) | pass | model 58%, market 50% | correlated | **untagged** | same game script as #618 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1182 | Jamal Shead pa under 20.5 | 26.0 | 0.5969 (Medium) | pass | model 58%, market 60% | correlated | **untagged** | same game script as #618 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1183 | Kel'el Ware pra over 17.5 | 7.0 | 0.542 (Medium) | pass | model 57%, market 54% | correlated | **untagged** | same game script as #618 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1186 | Ja'Kobe Walter pts over 14.5 | 7.0 | 0.5636 (Medium) | pass | model 70%, market 53% | correlated | **untagged** | same game script as #618 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1187 | Kasparas Jakučionis pra over 10.5 | 5.0 | 0.5497 (Medium) | pass | model 64%, market 53% | correlated | **untagged** | same game script as #618 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1189 | Ryan Rollins ra over 7.5 | 2.0 | 0.5543 (Medium) | pass | model 49% (against), market 57% | correlated | **untagged** | same game script as #618 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1192 | Tyler Herro reb under 4.5 | 5.0 | 0.5454 (Medium) | pass | model 54%, market 55% | correlated | **untagged** | same game script as #618 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1193 | Kyle Kuzma reb over 4.5 | 4.0 | 0.5687 (Medium) | pass | model 50% (against), market 54% | correlated | **untagged** | same game script as #618 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1195 | Quentin Grimes pra over 11.5 | 2.0 | 0.5516 (Medium) | pass | model 67%, market 52% | correlated | **untagged** | same game script as #632 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1199 | Deandre Ayton pra under 17.5 | 22.0 | 0.5328 (Low) | pass | model 61%, market 48% (against) | correlated | **untagged** | same game script as #850 (variance); own read: model bias; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 1201 | Collin Gillespie reb under 2.5 | 3.0 | 0.5188 (Low) | pass | model 59% | correlated | **untagged** | same game script as #1043 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1202 | Hugo González pr under 6.5 | 9.0 | 0.5138 (Low) | pass | model 57% | correlated | **untagged** | same game script as #839 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1212 | Ajay Mitchell pa under 24.5 | 40.0 | 0.5518 (Medium) | pass | model 66%, market 52% | correlated | **untagged** | same game script as #635 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1216 | Jeremiah Fears pra under 21.5 | 34.0 | 0.5425 (Medium) | pass | model 56%, market 51% | correlated | **untagged** | same game script as #874 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1219 | Ja'Kobe Walter pr over 19.5 | 13.0 | 0.5549 (Medium) | pass | model 70%, market 52% | correlated | **untagged** | same game script as #618 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1221 | Ja'Kobe Walter pa over 17.5 | 9.0 | 0.5628 (Medium) | pass | model 73%, market 52% | correlated | **untagged** | same game script as #618 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1225 | Kasparas Jakučionis pts over 5.5 | 3.0 | 0.5403 (Medium) | pass | model 57%, market 53% | correlated | **untagged** | same game script as #618 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1228 | Luka Dončić pts under 35.5 | 53.0 | 0.5432 (Medium) | pass | model 65%, market 52% | correlated | **untagged** | same game script as #632 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1229 | Quentin Grimes pr over 9.5 | 2.0 | 0.5443 (Medium) | pass | model 62%, market 52% | correlated | **untagged** | same game script as #632 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1230 | Jalen Green pra under 22.5 | 25.0 | 0.5458 (Medium) | pass | model 59%, market 50% | correlated | **untagged** | same game script as #1043 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1231 | Oso Ighodaro ra under 8.5 | 9.0 | 0.5468 (Medium) | pass | model 56%, market 55% | correlated | **untagged** | same game script as #1043 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1235 | Cam Spencer pts over 7.5 | 7.0 | 0.5369 (Low) | pass | model 60%, market 52% | correlated | **untagged** | same game script as #635 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1237 | Stephon Castle pa under 23.5 | 26.0 | 0.5658 (Medium) | pass | model 61%, market 55% | correlated | **untagged** | same game script as #910 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1238 | Malik Monk pa under 16.5 | 19.0 | 0.5494 (Medium) | pass | model 58%, market 54% | correlated | **untagged** | same game script as #910 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1239 | Precious Achiuwa pra over 16.0 | 13.0 | 0.5706 (Medium) | pass | model 56%, market 57% | correlated | **untagged** | same game script as #910 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1240 | Precious Achiuwa pr over 14.5 | 13.0 | 0.5718 (Medium) | pass | model 55%, market 58% | correlated | **untagged** | same game script as #910 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1241 | Domantas Sabonis reb over 12.5 | 12.0 | 0.5498 (Medium) | pass | model 58%, market 50% (against) | correlated | **untagged** | same game script as #910 (variance); own read: model bias; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 1244 | Walker Kessler pr under 23.5 | 28.0 | 0.5717 (Medium) | pass | model 58%, market 57% | correlated | **untagged** | same game script as #632 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1246 | Collin Sexton pa over 10.5 | 1.0 | 0.5649 (Medium) | pass | model 65%, market 54% | correlated | **untagged** | same game script as #632 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1247 | Quentin Grimes reb over 2.5 | 0.0 | 0.544 (Medium) | pass | model 51%, market 50% | correlated | **untagged** | same game script as #632 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1257 | Ivica Zubac pra under 19.5 | 27.0 | 0.6149 (Low) | pass | model 90%, market 48% (against) | model bias | **untagged** | root leg of a 6-leg script loss: #1257, #1261, #1262, #1265, #1268, #1269; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 1261 | Andrew Nembhard ast under 7.5 | 8.0 | 0.5614 (Medium) | pass | model 68%, market 53% | correlated | **untagged** | same game script as #1257 (model bias); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1262 | Jamal Murray ast under 6.5 | 8.0 | 0.5873 (Medium) | pass | model 70%, market 56% | correlated | **untagged** | same game script as #1257 (model bias); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1265 | Jamal Murray reb under 4.5 | 6.0 | 0.556 (Medium) | pass | model 52%, market 57% | correlated | **untagged** | same game script as #1257 (model bias); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 1268 | Pascal Siakam tpm under 1.5 | 2.0 | 0.5501 (Medium) | pass | model 63%, market 53% | correlated | **untagged** | same game script as #1257 (model bias); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1269 | Obi Toppin pts over 10.5 | 10.0 | 0.4549 (Low) | pass | model 29% (against) | correlated | **untagged** | same game script as #1257 (model bias); own read: variance; we priced this side at 45%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1270 | Zach LaVine pra over 25.5 | 21.0 | 0.4914 (Low) | pass | model 53%, market 48% (against) | correlated | **untagged** | same game script as #910 (variance); own read: model bias; we priced this side at 49%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 1274 | Darius Acuff Jr. pra over 33.5 | 33.0 | 0.5304 (Low) | pass | model 57%, market 52% | correlated | **untagged** | same game script as #910 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 1275 | Domantas Sabonis ra over 18.5 | 17.0 | 0.5176 (Low) | pass | model 57%, market 50% | correlated | **untagged** | same game script as #910 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |

Lessons:
- #618: Root of the 31-leg Toronto script: priced at 21 min in the morning; three starters were ruled out and Murray-Boyles played 34. Alijah Martin went from ~8 min a game to 31 (27 points): a coach's role call no box score showed. Morning prices on a team with late scratches are stale: re-price at the lineup lock, and treat the replacement's volume as unknown until starters are announced.
- #699: 3 targets, 3 catches (60 yds) in a 27-24 one-score game: his normal role, one catch over
- #980: Bench over (projected 20.8 min) played 15 in a high-scoring game: the L28 bench-over minutes risk; no minutes gap was flagged because his last-5 average sat near 21.
- #1005: Priced at 31.9 min when only Kawhi was out; Barnes and Quickley were ruled out later and Barrett played 37 min on 21 FGA (27/7/5). With 3+ starters out the sim holds per-minute usage fixed while real usage concentrates on the remaining starters: re-price after late scratches and don't trust unders on the starters left standing.
- #1006: Same game and cause as #1005: usage concentration on RJ Barrett with three Toronto starters out.
- #1040: Under on a starter in a close game: projected 34 min, played 39 (124-118), and filled it (9 reb, 11 ast). The L28 starter-under risk in close games.
- #1058: 23 min vs 22 projected; 6 vs 5.5, missed by the minimum
- #1155: Projected 30 min vs 24 in his last 5 (the L28 minutes gap, flagged) and the game was a 39-point blowout: 21 min. The back-check had already withdrawn it (second book), so it was never published.

Detail from the feeds:
- #653 Matvei Gridin: error=HTTPError
- #659 Kiefer Sherwood: error=HTTPError
- #661 Olen Zellweger: error=HTTPError
- #665 Adam Fantilli: error=HTTPError
- #667 Zach Whitecloud: error=HTTPError
- #668 Mikael Granlund: error=HTTPError
- #670 Jack Quinn: error=HTTPError
- #672 Joel Eriksson Ek: error=HTTPError
- #673 Beck Malenstyn: error=HTTPError
- #676 Maxim Shabanov: error=HTTPError
- #679 Macklin Celebrini: error=HTTPError
- #683 Yakov Trenin: error=HTTPError
- #684 Will Smith: error=HTTPError
- #685 Jason Zucker: error=HTTPError
- #687 Olli Maatta: error=HTTPError
- #688 Adam Gaudette: error=HTTPError
- #689 Sean Monahan: error=HTTPError
- #690 Kent Johnson: error=HTTPError
- #691 Morgan Frost: error=HTTPError
- #692 Mason Marchment: error=HTTPError
- #693 Valeri Nichushkin: error=HTTPError
- #936 Nathan MacKinnon: error=HTTPError
- #937 Bobby McMann: error=HTTPError
- #940 Philip Broberg: error=HTTPError
- #944 Rasmus Dahlin: error=HTTPError
- #947 Kirill Kaprizov: error=HTTPError
- #948 Quinn Hughes: error=HTTPError
- #949 Jake Guentzel: error=HTTPError
- #950 Alex Laferriere: error=HTTPError
- #1066 Matt Boldy: error=HTTPError
- #1075 Sebastian Aho: error=HTTPError
- #1076 Owen Power: error=HTTPError
- #1077 Connor Bedard: error=HTTPError

## 2026-11-05: 37 losses from 13 independent causes

| # | Leg | Result | Our p | Action | Sources | Auto tag | Confirmed | Evidence |
|---|---|---|---|---|---|---|---|---|
| 519 | Jase Richardson pr under 11.5 | 12.0 | 0.494 (Low) | pass | model 47% (against) | variance | **untagged** | root leg of a 7-leg script loss: #519, #577, #580, #584, #601, #602, #606; we priced this side at 49%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 521 | Yaxel Lendeborg pra under 30.5 | 31.0 | 0.5225 (Low) | pass | model 63%, market 50% (against) | model bias | **untagged** | root leg of a 10-leg script loss: #521, #522, #592, #595, #596, #597, #598, #599, #600, #611; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 522 | Brandin Podziemski pa over 19.5 | 12.0 | 0.511 (Low) | pass | model 56% | correlated | **untagged** | same game script as #521 (model bias); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 526 | Malik Willis pass_td over 1.0 | 0.0 | 0.6574 (Low) | pass | model 55%, market 76%, hist 40% (against) | variance | **untagged** | logged as a PASS: no money on it; reviewed for calibration |
| 528 | Drew Lock rush_yds under 5.5 | 16.0 | 0.6547 (Low) | pass | model 58%, market 72%, hist 50% (against) | variance | **untagged** | root leg of a 3-leg script loss: #528, #531, #569; logged as a PASS: no money on it; reviewed for calibration |
| 531 | Jadarian Price rush_rec_yds under 62.5 | 78.0 | 0.5561 (Low) | pass | model 58%, market 49% (against), hist 100% | correlated | **untagged** | same game script as #528 (variance); own read: model bias; logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
| 532 | Dak Prescott rush_yds over 5.5 | 1.0 | 0.5344 (Low) | pass | model 52%, market 50% (against), hist 88% | variance | **untagged** | logged as a PASS: no money on it; reviewed for calibration |
| 533 | Ashton Jeanty rec_yds over 33.5 | -5.0 | 0.5323 (Low) | pass | model 49% (against), market 52%, hist 88% | variance | **untagged** | root leg of a 2-leg script loss: #533, #570; logged as a PASS: no money on it; reviewed for calibration |
| 534 | Bucky Irving receptions under 2.5 | 4.0 | 0.5675 (Low) | pass | model 61%, market 50% (against), hist 75% | variance | **untagged** | root leg of a 2-leg script loss: #534, #571; logged as a PASS: no money on it; reviewed for calibration |
| 535 | Geno Smith completions over 19.5 | 18.0 | 0.5622 (Low) | pass | model 53%, market 57%, hist 62% | variance | **untagged** | root leg of a 2-leg script loss: #535, #566; logged as a PASS: no money on it; reviewed for calibration |
| 543 | Dawson Knox receptions under 1.5 | 4.0 | 0.5743 (Low) | pass | model 56%, hist 71% | variance | **untagged** | root leg of a 3-leg script loss: #543, #544, #548; logged as a PASS: no money on it; reviewed for calibration |
| 544 | Jordan Mason receptions under 0.5 | 2.0 | 0.5502 (Low) | pass | model 54%, market 52%, hist 100% | correlated | **untagged** | same game script as #543 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 546 | Zay Flowers rec_yds over 47.5 | 6.0 | 0.5331 (Low) | pass | model 52%, market 50% (against), hist 86% | variance | **untagged** | root leg of a 3-leg script loss: #546, #565, #575; logged as a PASS: no money on it; reviewed for calibration |
| 548 | Dawson Knox rec_yds under 12.5 | 37.0 | 0.5653 (Low) | pass | model 54%, hist 86% | correlated | **untagged** | same game script as #543 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 555 | Mitch Marner nhl_assists over 0.5 | 0.0 | 0.4978 (Low) | pass | model 48% (against), market 50% | variance | **untagged** | we priced this side at 50%: losing was the more likely outcome; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 562 | Vincent Trocheck nhl_sog over 1.5 | 1.0 | 0.5364 (Low) | pass | model 56%, market 53% | variance | **untagged** | logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 565 | Joe Fagnano pass_td over 0.5 | 0.0 | 0.5384 (Low) | pass | model 57%, market 50% (against), hist 0% (against) | correlated | **untagged** | same game script as #546 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration; closest possible loss (missed by the minimum) |
| 566 | Geno Smith rush_yds under 6.5 | 8.0 | 0.5428 (Low) | pass | model 57%, market 50% (against), hist 50% (against) | correlated | **untagged** | same game script as #535 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 569 | Jadarian Price rush_rec_yds under 63.5 | 78.0 | 0.5619 (Low) | pass | model 59%, market 50% (against), hist 100% | correlated | **untagged** | same game script as #528 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 570 | Ashton Jeanty rec_yds over 35.5 | -5.0 | 0.5193 (Low) | pass | model 49% (against), market 50% (against), hist 88% | correlated | **untagged** | same game script as #533 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 571 | Bucky Irving rec_yds under 14.5 | 28.0 | 0.5412 (Low) | pass | model 54%, market 50% (against), hist 88% | correlated | **untagged** | same game script as #534 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 575 | Zay Flowers rec_yds over 48.5 | 6.0 | 0.5325 (Low) | pass | model 52%, market 50% (against), hist 86% | correlated | **untagged** | same game script as #546 (variance); own read: variance; logged as a PASS: no money on it; reviewed for calibration |
| 576 | Rachaad White rush_rec_yds under 62.5 | 69.0 | 0.5712 (Low) | pass | model 62%, market 49% (against), hist 83% | model bias | **untagged** | logged as a PASS: no money on it; reviewed for calibration; model was on our side, the market was against it, and the market was right |
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

# Post-mortems

Every graded loss is examined here, including passes and Low-confidence legs. `python -m edge review` writes the diagnosis; `python -m edge tag ID "tag" --lesson "..."` confirms the cause. Tags: `variance`, `opportunity`, `correlated`, `role/lineup`, `model bias`, `market info`, `stale line`, `data error`, `format misread`.

## 2026-11-10: 42 losses from 14 independent causes

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

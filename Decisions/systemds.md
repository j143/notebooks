### SystemML python pip install downloads

```sql

SELECT
  COUNT(*) AS num_downloads,
  SUBSTR(_TABLE_SUFFIX, 1, 6) AS `month`
FROM `the-psf.pypi.downloads*`
WHERE
  file.project = 'systemml'
  -- Only query the last 6 months of history
  AND _TABLE_SUFFIX
    BETWEEN FORMAT_DATE(
      '%Y%m01', DATE_SUB(CURRENT_DATE(), INTERVAL 6 MONTH))
    AND FORMAT_DATE('%Y%m%d', CURRENT_DATE())
GROUP BY `month`
ORDER BY `month` DESC
```

#### Results

| num_downloads | month |
| --- | --- |
| 5077 | 202006 |
| 6613 | 202005 |
| 10331 |202004 |
| 13483 | 202003 |
| 9150 | 202002 |
| 4207 | 202001 |
| 3443 | 201912 |

#### Graphic


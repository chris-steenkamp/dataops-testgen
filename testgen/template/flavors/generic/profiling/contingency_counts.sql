SELECT {CONTINGENCY_COLUMNS}, COUNT(*) as freq_ct
  FROM {DATA_SCHEMA}.{DATA_TABLE}
GROUP BY {CONTINGENCY_COLUMNS};

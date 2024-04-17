SELECT
	project_name,
	component_tool,
	"schema",
	connection_name,
	project_db,
	sample_min_count,
	group_id,
	uses_sampling,
	project_code,
	sample_percentage,
	profiling_table_set,
	profiling_include_mask,
	profiling_exclude_mask,
	component_type,
	component_key,
	component_name,
	column_names,
	table_name,
	test_suite,
	input_parameters,
	test_definition_id,
	"type",
	min_threshold,
	max_threshold,
	"name",
	description,
	start_time,
	end_time,
	dq_dimension,
	result_status,
    result_message,
    result_id,
	metric_value,
	measure_uom,
	measure_uom_description
FROM v_queued_observability_results
where project_code = '{PROJECT_CODE}'
and test_suite = '{TEST_SUITE}'
order by start_time asc
limit {MAX_QTY_EVENTS}

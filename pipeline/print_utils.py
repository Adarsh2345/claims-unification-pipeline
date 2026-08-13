def print_stage_log(stage_log):
    print(f"{'stage':<28}{'rows_in':>10}{'rows_out':>10}{'dropped':>10}")
    print("-" * 60)
    for entry in stage_log:
        print(f"{entry['stage']:<28}{entry['rows_in']:>10}{entry['rows_out']:>10}"
              f"{entry['dropped']:>10}")
        print(f"    -> {entry['notes']}")
# Numeric Consistency Checker Implementation

## Overview
Added `numeric_consistency_check()` function to `research-paper-analyzer/eval/eval_metrics.py` for validating internal consistency of numeric results in extracted papers.

## Location
- File: `research-paper-analyzer/eval/eval_metrics.py`
- Function: `numeric_consistency_check(paper: Dict[str, Any]) -> Dict[str, Any]`
- Integration: Added to `evaluate_pair()` function

## Checks Performed

### 1. Value Presence and Type Validation
- Ensures all result records have numeric `value` field
- Validates that values can be converted to float

### 2. Unit/Value Range Consistency
- **Percentages**: If unit is "%" or metric contains "percent", validates value ∈ [0, 100]
- **Accuracy/Precision/Recall/F1**: Validates appropriate ranges
  - If unit is "%": [0, 100]
  - If unit is not "%": [0, 1] (decimal form)
  - Flexible handling for either format

### 3. Confidence Score Validity
- If confidence field present, validates it's in [0, 1] range
- Checks numeric type

### 4. Baseline Comparison Logic
- If result has baseline, ours_is, and higher_is_better fields:
  - Searches for baseline's value in other results
  - Validates logical consistency:
    - `higher_is_better=True`: our_value ≥ baseline_value
    - `higher_is_better=False`: our_value ≤ baseline_value

### 5. Unit Consistency Across Same Metrics
- Tracks units used for each metric name across all results
- Flags if same metric uses different units (e.g., "Accuracy" reported as both "%" and decimal)

## Return Format

```python
{
    "consistency_score": float,  # (passed_checks / total_checks) or None if no results
    "total_checks": int,         # Number of validation checks performed
    "passed_checks": int,        # Number of checks that passed
    "failed_checks": [str],      # List of human-readable failure messages
    "notes": str                 # Summary message
}
```

## Example Failed Check Messages

```
"Result[0]: value is None or missing"
"Result[1]: percentage value 150.0 outside [0,100] range"
"Result[2]: confidence 1.5 outside [0,1] range"
"Result[3]: higher_is_better=True but ours (75.5) < baseline (78.2)"
"Metric 'accuracy' has inconsistent units: {'%', None}"
```

## Integration in Evaluation Pipeline

The function is automatically called in `evaluate_pair()`:

```python
# numeric consistency check (self-evaluation)
consistency = numeric_consistency_check(pred)
metrics["numeric_consistency"] = consistency.get("consistency_score")
metrics["numeric_consistency_details"] = consistency
```

## Usage Examples

### Standalone Usage
```python
from eval.eval_metrics import numeric_consistency_check

paper = {
    'results': [
        {
            'dataset': 'ImageNet',
            'metric': 'Top-1 Accuracy',
            'value': 85.5,
            'unit': '%',
            'higher_is_better': True,
            'baseline': 'ResNet50',
            'ours_is': 'MyModel',
            'confidence': 0.95
        }
    ]
}

result = numeric_consistency_check(paper)
print(f"Consistency Score: {result['consistency_score']}")
print(f"Passed: {result['passed_checks']}/{result['total_checks']}")
if result['failed_checks']:
    print("Failed checks:")
    for failure in result['failed_checks']:
        print(f"  - {failure}")
```

### In Batch Evaluation
The metric is automatically computed and included in evaluation results as:
- `numeric_consistency`: score (0.0 to 1.0)
- `numeric_consistency_details`: full check details

## Test Cases

### Valid Paper (Score = 1.0)
- All values numeric and in range
- Confidence scores in [0, 1]
- Baseline comparisons logically consistent
- Consistent units per metric

### Invalid Paper (Score < 1.0)
- Percentage value > 100
- Confidence > 1.0
- higher_is_better=True but ours < baseline
- Same metric with inconsistent units

## Notes

- Designed for **self-evaluation** (no gold standard needed)
- Conservative: only flags clear violations
- Gracefully handles missing optional fields
- Returns `None` score if no results to validate

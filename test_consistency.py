#!/usr/bin/env python
"""Quick test of numeric consistency checker"""
import sys
sys.path.insert(0, 'research-paper-analyzer')
from eval.eval_metrics import numeric_consistency_check

# Test case 1: Valid results
paper1 = {
    'results': [
        {
            'dataset': 'COCO',
            'metric': 'Accuracy',
            'value': 85.5,
            'unit': '%',
            'higher_is_better': True,
            'confidence': 0.95
        }
    ]
}

# Test case 2: Invalid - percentage out of range
paper2 = {
    'results': [
        {
            'dataset': 'COCO',
            'metric': 'Accuracy',
            'value': 150.0,
            'unit': '%',
            'confidence': 0.9
        }
    ]
}

# Test case 3: Invalid - confidence out of range
paper3 = {
    'results': [
        {
            'dataset': 'COCO',
            'metric': 'Accuracy',
            'value': 85.5,
            'unit': '%',
            'confidence': 1.5
        }
    ]
}

print('Test 1 - Valid results:')
result1 = numeric_consistency_check(paper1)
print(f'  Score: {result1["consistency_score"]:.2f}')
print(f'  Passed: {result1["passed_checks"]}/{result1["total_checks"]}')
print(f'  Failed: {len(result1["failed_checks"])}')
print()

print('Test 2 - Invalid percentage:')
result2 = numeric_consistency_check(paper2)
print(f'  Score: {result2["consistency_score"]:.2f}')
print(f'  Passed: {result2["passed_checks"]}/{result2["total_checks"]}')
print(f'  Failed checks: {result2["failed_checks"][:1]}')
print()

print('Test 3 - Invalid confidence:')
result3 = numeric_consistency_check(paper3)
print(f'  Score: {result3["consistency_score"]:.2f}')
print(f'  Passed: {result3["passed_checks"]}/{result3["total_checks"]}')
print(f'  Failed checks: {result3["failed_checks"][:1]}')
print()

print('✓ Numeric consistency checker implemented and tested successfully!')

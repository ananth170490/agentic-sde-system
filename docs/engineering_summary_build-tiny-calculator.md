## Implementation Plan and Rationale
Single-task implementation with retry.

## Generated Artifacts
- app/calc.py
- tests/test_calc.py

## Risks, Trade-offs, and Validation Approach
Retry loop validated by failing then passing pytest.

## Assumptions and Limitations
Assumes local python tooling availability.
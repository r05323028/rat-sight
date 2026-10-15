# Spec Delta

## Purpose
This synthetic capability exists only to exercise OpenSpec CLI and quality-gate integration behavior in isolated tests.

## ADDED Requirements

### Requirement: Fixture capability returns a constant
The fixture capability SHALL expose one stable result for integration testing.

#### Scenario: Fixture result is stable
- **WHEN** the fixture capability is evaluated
- **THEN** it returns the documented constant

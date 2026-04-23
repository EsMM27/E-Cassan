# Reasoning Presets


## Aggressive

Use when you want more opportunities and can tolerate more false positives.

		reasoning:
			debate_rounds: 2
			consensus_method: weighted
			consensus_threshold: 0.70
			confidence_divergence_threshold: 0.35
			high_confidence_threshold: 0.75
			low_confidence_threshold: 0.35
			max_iterations: 3
			timeout_seconds: 180

## Balanced

Use when you want a practical middle ground.

		reasoning:
			debate_rounds: 3
			consensus_method: weighted
			consensus_threshold: 0.80
			confidence_divergence_threshold: 0.30
			high_confidence_threshold: 0.80
			low_confidence_threshold: 0.30
			max_iterations: 5
			timeout_seconds: 300

## Conservative

Use when you prefer fewer but higher-conviction signals.

		reasoning:
			debate_rounds: 4
			consensus_method: weighted
			consensus_threshold: 0.90
			confidence_divergence_threshold: 0.20
			high_confidence_threshold: 0.85
			low_confidence_threshold: 0.25
			max_iterations: 6
			timeout_seconds: 420
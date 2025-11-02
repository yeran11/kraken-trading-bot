"""
Ensemble Weight Optimizer - Self-Improving AI System
Dynamically adjusts model weights based on performance
"""
import json
import os
from loguru import logger
from datetime import datetime

class EnsembleWeightOptimizer:
    """Optimize AI ensemble weights based on predictive accuracy."""

    def __init__(self, initial_weights: dict = None):
        """
        Initialize with starting weights.

        Args:
            initial_weights: dict like {'sentiment': 0.20, 'technical': 0.35, 'macro': 0.15, 'deepseek': 0.30}
        """
        if initial_weights is None:
            initial_weights = {
                'sentiment': 0.20,
                'technical': 0.35,
                'macro': 0.15,
                'deepseek': 0.30
            }

        self.weights = initial_weights
        self.weights_file = 'ensemble_weights.json'

        # Load saved weights if they exist
        self._load_weights()

        # Performance tracking
        self.performance_tracker = {
            'sentiment': {'correct': 0, 'total': 0},
            'technical': {'correct': 0, 'total': 0},
            'macro': {'correct': 0, 'total': 0},
            'deepseek': {'correct': 0, 'total': 0}
        }

        # Optimization history
        self.optimization_history = []

        logger.success(f"✓ Ensemble Weight Optimizer initialized")
        logger.info(f"Current weights: {self._format_weights()}")

    def _load_weights(self):
        """Load saved weights from file."""
        if os.path.exists(self.weights_file):
            try:
                with open(self.weights_file, 'r') as f:
                    data = json.load(f)
                    self.weights = data.get('weights', self.weights)
                    logger.info(f"Loaded saved ensemble weights from {self.weights_file}")
            except Exception as e:
                logger.warning(f"Could not load saved weights: {e}")

    def _save_weights(self):
        """Save current weights to file."""
        try:
            with open(self.weights_file, 'w') as f:
                json.dump({
                    'weights': self.weights,
                    'last_updated': datetime.now().isoformat(),
                    'optimization_count': len(self.optimization_history)
                }, f, indent=2)
            logger.debug(f"Weights saved to {self.weights_file}")
        except Exception as e:
            logger.error(f"Failed to save weights: {e}")

    def _format_weights(self):
        """Format weights for logging."""
        return ", ".join([f"{model}: {weight:.2%}" for model, weight in self.weights.items()])

    def record_prediction(self, model_predictions: dict, actual_outcome: str):
        """
        Record each model's prediction and the actual outcome.

        Args:
            model_predictions: dict like {'sentiment': 'BUY', 'technical': 'BUY', 'macro': 'HOLD', 'deepseek': 'BUY'}
            actual_outcome: 'WIN' or 'LOSS'
        """
        for model, prediction in model_predictions.items():
            if model not in self.performance_tracker:
                continue

            self.performance_tracker[model]['total'] += 1

            # Model was correct if:
            # 1. It predicted BUY and the trade was a WIN
            # 2. It predicted HOLD/SELL and the trade was a LOSS (correctly avoided)
            was_correct = (prediction == 'BUY' and actual_outcome == 'WIN') or \
                         (prediction in ['HOLD', 'SELL'] and actual_outcome == 'LOSS')

            if was_correct:
                self.performance_tracker[model]['correct'] += 1

        logger.debug(f"Recorded predictions: {model_predictions} -> {actual_outcome}")

    def optimize_weights(self, min_trades: int = 100):
        """
        Optimize ensemble weights based on accumulated performance.

        Args:
            min_trades: Minimum number of trades before optimizing

        Returns:
            dict: New optimized weights
        """
        # Check if we have enough data
        total_trades = self.performance_tracker['deepseek']['total']

        if total_trades < min_trades:
            logger.info(f"Not enough trades for optimization ({total_trades}/{min_trades})")
            return self.weights

        logger.info(f"🔧 OPTIMIZING ENSEMBLE WEIGHTS (based on {total_trades} trades)...")

        # Calculate accuracy for each model
        accuracies = {}
        for model, stats in self.performance_tracker.items():
            if stats['total'] > 0:
                accuracy = stats['correct'] / stats['total']
                accuracies[model] = accuracy
                logger.info(f"   {model}: {accuracy:.2%} accurate ({stats['correct']}/{stats['total']})")
            else:
                accuracies[model] = 0.5  # Default to 50% if no data

        # Calculate new weights proportional to accuracy
        total_accuracy = sum(accuracies.values())

        if total_accuracy == 0:
            logger.warning("Total accuracy is zero, keeping current weights")
            return self.weights

        new_weights = {
            model: accuracy / total_accuracy
            for model, accuracy in accuracies.items()
        }

        # Apply smoothing factor (don't change weights too drastically)
        smoothing_factor = 0.3  # 30% new, 70% old
        smoothed_weights = {
            model: (smoothing_factor * new_weights[model]) + \
                   ((1 - smoothing_factor) * self.weights[model])
            for model in self.weights
        }

        # Normalize to sum to 1.0
        total_weight = sum(smoothed_weights.values())
        optimized_weights = {
            model: weight / total_weight
            for model, weight in smoothed_weights.items()
        }

        # Log changes
        logger.info("📊 WEIGHT CHANGES:")
        for model in self.weights:
            old = self.weights[model]
            new = optimized_weights[model]
            change = ((new - old) / old) * 100 if old > 0 else 0
            arrow = "📈" if change > 0 else "📉" if change < 0 else "➡️"
            logger.info(f"   {arrow} {model}: {old:.2%} → {new:.2%} ({change:+.1f}%)")

        # Store optimization history
        self.optimization_history.append({
            'timestamp': datetime.now().isoformat(),
            'trades_analyzed': total_trades,
            'old_weights': self.weights.copy(),
            'new_weights': optimized_weights.copy(),
            'accuracies': accuracies.copy()
        })

        # Update weights
        self.weights = optimized_weights
        self._save_weights()

        # Reset performance tracker for next optimization cycle
        for model in self.performance_tracker:
            self.performance_tracker[model] = {'correct': 0, 'total': 0}

        logger.success(f"✅ Ensemble weights optimized!")
        logger.info(f"New weights: {self._format_weights()}")

        return self.weights

    def get_current_weights(self):
        """Get current ensemble weights."""
        return self.weights.copy()

    def get_performance_summary(self):
        """Get current performance stats."""
        summary = {}
        for model, stats in self.performance_tracker.items():
            if stats['total'] > 0:
                summary[model] = {
                    'accuracy': stats['correct'] / stats['total'],
                    'correct': stats['correct'],
                    'total': stats['total']
                }
            else:
                summary[model] = {
                    'accuracy': 0.0,
                    'correct': 0,
                    'total': 0
                }
        return summary

    def should_optimize(self, optimization_interval: int = 100):
        """
        Check if it's time to optimize weights.

        Args:
            optimization_interval: Optimize every N trades

        Returns:
            bool: True if optimization should run
        """
        total_trades = self.performance_tracker['deepseek']['total']
        return total_trades >= optimization_interval and total_trades % optimization_interval == 0

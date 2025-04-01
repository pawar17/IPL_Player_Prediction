import numpy as np
import pandas as pd
from typing import Dict, Any, List
import logging
from pathlib import Path
import json

class SimplePredictor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.weights = {
            'recent_form': 0.4,
            'historical': 0.3,
            'context': 0.3
        }
        # Minimum required data points for reliable prediction
        self.min_required_matches = 3
        self.max_days_since_last_match = 30
        
    def predict(self, player_data: Dict[str, Any]) -> Dict[str, Any]:
        """Make predictions using weighted statistical analysis"""
        try:
            # Validate data completeness
            if not self._validate_data(player_data):
                self.logger.warning("Insufficient data for reliable prediction")
                return self._get_default_predictions()
            
            # 1. Calculate Recent Form Score (40%)
            recent_form = self._calculate_recent_form(player_data)
            
            # 2. Calculate Historical Performance Score (30%)
            historical = self._calculate_historical_score(player_data)
            
            # 3. Calculate Match Context Score (30%)
            context = self._calculate_context_score(player_data)
            
            # Combine scores with weights
            predictions = {}
            metrics = ['runs', 'wickets', 'strike_rate', 'economy_rate']
            
            for metric in metrics:
                weighted_prediction = (
                    recent_form[metric] * self.weights['recent_form'] +
                    historical[metric] * self.weights['historical'] +
                    context[metric] * self.weights['context']
                )
                
                # Calculate confidence interval based on historical variance
                std = player_data.get(f'{metric}_std', weighted_prediction * 0.2)
                predictions[f'{metric}'] = max(0, round(weighted_prediction, 2))
                predictions[f'{metric}_ci'] = (
                    max(0, round(weighted_prediction - 1.96 * std, 2)),
                    max(0, round(weighted_prediction + 1.96 * std, 2))
                )
            
            # Add form and confidence metrics
            predictions['form'] = self._determine_form(recent_form['runs'], historical['runs'])
            predictions['confidence'] = self._calculate_confidence(player_data)
            predictions['data_quality'] = self._assess_data_quality(player_data)
            
            return predictions
            
        except Exception as e:
            self.logger.error(f"Error making predictions: {str(e)}")
            return self._get_default_predictions()
    
    def _validate_data(self, player_data: Dict[str, Any]) -> bool:
        """Validate if we have sufficient data for prediction"""
        # Check minimum required matches
        if player_data.get('last_5_matches_runs_avg') is None:
            return False
            
        # Check data recency
        days_since_last = player_data.get('days_since_last_match', float('inf'))
        if days_since_last > self.max_days_since_last_match:
            return False
            
        # Check historical data
        if not all(player_data.get(f'{metric}_mean') is not None 
                  for metric in ['runs', 'wickets', 'strike_rate', 'economy_rate']):
            return False
            
        return True
    
    def _assess_data_quality(self, player_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess the quality of input data"""
        quality = {
            'recent_data': True,
            'historical_data': True,
            'context_data': True,
            'issues': []
        }
        
        # Check recent data quality
        if player_data.get('days_since_last_match', 0) > 14:
            quality['recent_data'] = False
            quality['issues'].append('Data more than 2 weeks old')
        
        # Check historical data quality
        if not all(player_data.get(f'{metric}_std') is not None 
                  for metric in ['runs', 'wickets', 'strike_rate', 'economy_rate']):
            quality['historical_data'] = False
            quality['issues'].append('Missing historical variance data')
        
        # Check context data quality
        if not all(player_data.get(field) is not None 
                  for field in ['is_home_game', 'is_powerplay_batsman', 'is_death_bowler']):
            quality['context_data'] = False
            quality['issues'].append('Missing context information')
        
        return quality
    
    def _calculate_recent_form(self, player_data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate recent form using exponentially weighted averages"""
        recent_metrics = {
            'runs': player_data.get('last_5_matches_runs_avg', 0),
            'wickets': player_data.get('last_5_matches_wickets_avg', 0),
            'strike_rate': player_data.get('last_5_matches_sr_avg', 0),
            'economy_rate': player_data.get('last_5_matches_er_avg', 0)
        }
        
        # Apply form factor adjustment with recency consideration
        form_factor = player_data.get('form_factor', 1.0)
        days_since_last = player_data.get('days_since_last_match', 0)
        
        # Adjust form factor based on recency
        if days_since_last > 7:
            form_factor *= 0.95  # Slight reduction for data older than a week
        elif days_since_last > 14:
            form_factor *= 0.9   # Further reduction for data older than two weeks
        
        return {k: v * form_factor for k, v in recent_metrics.items()}
    
    def _calculate_historical_score(self, player_data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate historical performance score"""
        return {
            'runs': player_data.get('runs_mean', 0),
            'wickets': player_data.get('wickets_mean', 0),
            'strike_rate': player_data.get('strike_rate_mean', 0),
            'economy_rate': player_data.get('economy_rate_mean', 0)
        }
    
    def _calculate_context_score(self, player_data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate context-adjusted scores"""
        base_scores = self._calculate_historical_score(player_data)
        
        # Apply context adjustments
        context_multiplier = 1.0
        
        # Home advantage
        if player_data.get('is_home_game', False):
            context_multiplier *= 1.1
        
        # Role-based adjustments
        if player_data.get('is_powerplay_batsman', False):
            base_scores['runs'] *= 1.2
            base_scores['strike_rate'] *= 1.1
        
        if player_data.get('is_death_bowler', False):
            base_scores['wickets'] *= 1.2
            base_scores['economy_rate'] *= 0.9
        
        # Pressure index adjustment
        pressure_index = player_data.get('pressure_index', 0.5)
        context_multiplier *= (1 + (pressure_index - 0.5) * 0.2)
        
        return {k: v * context_multiplier for k, v in base_scores.items()}
    
    def _determine_form(self, recent_runs: float, historical_runs: float) -> str:
        """Determine player's current form"""
        if recent_runs == 0 or historical_runs == 0:
            return 'Unknown'
        
        form_ratio = recent_runs / historical_runs
        
        if form_ratio > 1.3:
            return 'Excellent'
        elif form_ratio > 1.1:
            return 'Good'
        elif form_ratio > 0.9:
            return 'Average'
        else:
            return 'Poor'
    
    def _calculate_confidence(self, player_data: Dict[str, Any]) -> float:
        """Calculate prediction confidence score"""
        confidence = 0.0
        
        # Data completeness (50%)
        required_fields = [
            'last_5_matches_runs_avg', 'last_5_matches_wickets_avg',
            'runs_mean', 'wickets_mean', 'form_factor'
        ]
        completeness = sum(1 for field in required_fields if player_data.get(field) is not None) / len(required_fields)
        confidence += completeness * 0.5
        
        # Consistency (30%)
        consistency_score = player_data.get('consistency_score', 0.5)
        confidence += consistency_score * 0.3
        
        # Recent data quality (20%)
        days_since_last = player_data.get('days_since_last_match', 30)
        recency_score = max(0, 1 - (days_since_last / 30))
        confidence += recency_score * 0.2
        
        return min(1.0, confidence)
    
    def _get_default_predictions(self) -> Dict[str, Any]:
        """Return default predictions when calculation fails"""
        return {
            'runs': 0,
            'runs_ci': (0, 0),
            'wickets': 0,
            'wickets_ci': (0, 0),
            'strike_rate': 0,
            'strike_rate_ci': (0, 0),
            'economy_rate': 0,
            'economy_rate_ci': (0, 0),
            'form': 'Unknown',
            'confidence': 0
        } 
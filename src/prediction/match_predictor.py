from typing import Dict

class MatchPredictor:
    def _calculate_performance_probability(self, player_features: Dict, player_role: str, match_data: Dict) -> float:
        """Calculate probability of good performance based on features"""
        try:
            # Get venue conditions
            venue_conditions = self.data_processor.get_venue_conditions(match_data['venue'])
            
            # Get venue-specific performance
            venue_performance = self.data_processor.get_venue_performance(
                player_features['name'],
                match_data['venue']
            )
            
            # Get head-to-head stats if opponent is known
            h2h_stats = {}
            if 'opponent' in match_data:
                h2h_stats = self.data_processor.get_head_to_head_stats(
                    player_features['name'],
                    match_data['opponent']
                )
            
            # Get pressure metrics
            pressure_metrics = self.data_processor._calculate_pressure_metrics(player_features)
            
            # Calculate base probability from form
            base_prob = self._calculate_base_probability(player_features, player_role)
            
            # Adjust probability based on venue conditions
            if venue_conditions:
                if player_role == 'batsman':
                    if venue_conditions['is_spinner_friendly'] and player_features.get('is_spinner', False):
                        base_prob *= 1.2
                    if venue_conditions['is_pacer_friendly'] and player_features.get('is_pacer', False):
                        base_prob *= 1.2
                elif player_role == 'bowler':
                    if venue_conditions['is_spinner_friendly'] and player_features.get('is_spinner', False):
                        base_prob *= 1.2
                    if venue_conditions['is_pacer_friendly'] and player_features.get('is_pacer', False):
                        base_prob *= 1.2
            
            # Adjust for venue performance
            if venue_performance:
                venue_factor = min(1.5, max(0.5, venue_performance.get('win_rate', 0.5)))
                base_prob *= venue_factor
            
            # Adjust for head-to-head performance
            if h2h_stats and player_features['name'] in h2h_stats:
                h2h_factor = min(1.3, max(0.7, h2h_stats[player_features['name']]['win_rate']))
                base_prob *= h2h_factor
            
            # Adjust for pressure situations
            if pressure_metrics:
                if match_data.get('is_knockout', False):
                    if player_role == 'batsman':
                        pressure_factor = min(1.4, max(0.6, 
                            pressure_metrics.get('knockout_batting_avg', 0) / 
                            max(1, player_features.get('batting_average', 0))
                        ))
                    else:
                        pressure_factor = min(1.4, max(0.6,
                            pressure_metrics.get('knockout_bowling_avg', 0) / 
                            max(1, player_features.get('bowling_average', 0))
                        ))
                    base_prob *= pressure_factor
                
                if match_data.get('is_chase', False):
                    if player_role == 'batsman':
                        chase_factor = min(1.3, max(0.7,
                            pressure_metrics.get('chase_batting_avg', 0) / 
                            max(1, player_features.get('batting_average', 0))
                        ))
                        base_prob *= chase_factor
            
            # Normalize probability
            return min(1.0, max(0.0, base_prob))
            
        except Exception as e:
            self.logger.error(f"Error calculating performance probability: {str(e)}")
            return 0.5 
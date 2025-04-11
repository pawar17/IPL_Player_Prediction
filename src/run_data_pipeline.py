from src.data.data_pipeline import DataPipeline
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    try:
        # Initialize and run the pipeline
        pipeline = DataPipeline()
        combined_data = pipeline.run_pipeline()
        
        # Print some basic statistics about the combined dataset
        print("\nDataset Statistics:")
        print(f"Total number of matches: {len(combined_data)}")
        print(f"Date range: {combined_data['date'].min()} to {combined_data['date'].max()}")
        print(f"Number of unique players: {combined_data['player_of_match'].nunique()}")
        print(f"Number of unique venues: {combined_data['venue'].nunique()}")
        
        # Print sample of the combined data
        print("\nSample of combined data:")
        print(combined_data.head())
        
    except Exception as e:
        logging.error(f"Error running data pipeline: {str(e)}")
        raise

if __name__ == "__main__":
    main() 
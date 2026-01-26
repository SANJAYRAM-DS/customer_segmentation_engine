
import pandas as pd

def map_segment_metadata(segment_series: pd.Series):
    """
    Maps segment IDs to metadata (name, confidence).
    Returns (segment_id, segment_name, segment_confidence)
    """
    # Placeholder mapping based on typical clusters
    # Ideally this should be loaded from a config or model metadata
    mapping = {
        0: "Power User",
        1: "Loyal Customer",
        2: "At Risk",
        3: "Hibernating",
    }
    
    # Ensure series is int
    # segment_series might be floats with NaNs.
    # We should handle that.
    
    # Map
    segment_name = segment_series.map(mapping).fillna("Unknown")
    
    # Confidence placeholder (1.0 for hard assignment)
    segment_confidence = pd.Series([1.0] * len(segment_series), index=segment_series.index)
    
    return segment_series, segment_name, segment_confidence

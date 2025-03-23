"""
Utility functions for working with the vector database.
"""
import os
import json
import glob
from typing import List, Dict, Any, Optional
from src.vector_store import VectorStore
from src.report_generator import ReportGenerator

def find_incomplete_reports(data_dir: str = None) -> List[str]:
    """
    Find all incomplete reports in the data directory.

    Args:
        data_dir: Path to the data directory. If None, use default.

    Returns:
        List of video IDs with incomplete reports.
    """
    if data_dir is None:
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

    incomplete_reports = []
    report_files = glob.glob(os.path.join(data_dir, "*_report.json"))

    for report_file in report_files:
        try:
            with open(report_file, "r", encoding="utf-8") as f:
                report = json.load(f)

            # Check if the report is incomplete
            analysis = report.get("analysis", {})
            unable_count = 0

            for key, value in analysis.items():
                if isinstance(value, list) and len(value) > 0:
                    if "Unable to parse" in value[0]:
                        unable_count += 1
                elif isinstance(value, str) and "Unable to" in value:
                    unable_count += 1

            # If more than 3 fields are incomplete, consider the report incomplete
            if unable_count >= 3:
                video_id = os.path.basename(report_file).replace("_report.json", "")
                incomplete_reports.append(video_id)
                print(f"Found incomplete report for video {video_id}")
        except Exception as e:
            print(f"Error processing report file {report_file}: {e}")

    return incomplete_reports

def reprocess_incomplete_reports(data_dir: str = None) -> List[str]:
    """
    Reprocess all incomplete reports.

    Args:
        data_dir: Path to the data directory. If None, use default.

    Returns:
        List of video IDs that were successfully reprocessed.
    """
    if data_dir is None:
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

    report_generator = ReportGenerator()
    vector_store = VectorStore()

    incomplete_reports = find_incomplete_reports(data_dir)
    reprocessed_reports = []

    for video_id in incomplete_reports:
        print(f"\nReprocessing report for video {video_id}")

        # Get original report to extract video info
        report_file = os.path.join(data_dir, f"{video_id}_report.json")
        try:
            with open(report_file, "r", encoding="utf-8") as f:
                original_report = json.load(f)

            # Create video_info dict
            video_info = {
                "id": video_id,
                "title": original_report["video_title"],
                "channel_title": original_report.get("channel_title", "Unknown")
            }

            # Backup the original report
            backup_file = os.path.join(data_dir, f"{video_id}_report.bak.json")
            with open(backup_file, "w", encoding="utf-8") as f:
                json.dump(original_report, f, indent=2)

            # Get transcript
            transcript = report_generator.get_transcript(video_id)
            if not transcript:
                print(f"Could not retrieve transcript for video {video_id}")
                continue

            # Analyze transcript
            new_analysis = report_generator.analyze_transcript(video_info, transcript)
            if not new_analysis:
                print(f"Analysis failed for video {video_id}")
                continue

            # Update report in vector store
            vector_store.index_report(new_analysis)

            reprocessed_reports.append(video_id)
            print(f"Successfully reprocessed report for video {video_id}")

        except Exception as e:
            print(f"Error reprocessing report for video {video_id}: {e}")

    return reprocessed_reports

def reprocess_specific_video(video_id: str, data_dir: str = None) -> bool:
    """
    Reprocess a specific video report.

    Args:
        video_id: YouTube video ID to reprocess.
        data_dir: Path to the data directory. If None, use default.

    Returns:
        True if reprocessing was successful, False otherwise.
    """
    if data_dir is None:
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

    report_generator = ReportGenerator()
    vector_store = VectorStore()

    print(f"\nReprocessing report for video {video_id}")

    # Get original report to extract video info
    report_file = os.path.join(data_dir, f"{video_id}_report.json")
    try:
        with open(report_file, "r", encoding="utf-8") as f:
            original_report = json.load(f)

        # Create video_info dict
        video_info = {
            "id": video_id,
            "title": original_report["video_title"],
            "channel_title": original_report.get("channel_title", "Unknown")
        }

        # Backup the original report
        backup_file = os.path.join(data_dir, f"{video_id}_report.bak.json")
        with open(backup_file, "w", encoding="utf-8") as f:
            json.dump(original_report, f, indent=2)

        # Get transcript
        transcript = report_generator.get_transcript(video_id)
        if not transcript:
            print(f"Could not retrieve transcript for video {video_id}")
            return False

        # Analyze transcript
        new_analysis = report_generator.analyze_transcript(video_info, transcript)
        if not new_analysis:
            print(f"Analysis failed for video {video_id}")
            return False

        # Update report in vector store
        vector_store.index_report(new_analysis)

        print(f"Successfully reprocessed report for video {video_id}")
        return True

    except Exception as e:
        print(f"Error reprocessing report for video {video_id}: {e}")
        return False

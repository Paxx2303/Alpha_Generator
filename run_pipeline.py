#!/usr/bin/env python3
"""
run_pipeline.py — Entrypoint to run the full (or partial) data pipeline.

Usage:
    python run_pipeline.py                          # run all steps
    python run_pipeline.py --only clean,classify    # run specific steps
    python run_pipeline.py --only chunk,index       # run from chunk onward
"""
import argparse
import sys
from pipeline.clean    import CleanStep
from pipeline.classify import ClassifyStep
from pipeline.chunk    import ChunkStep
from pipeline.index    import IndexStep

ALL_STEPS = {
    "clean":    CleanStep,
    "classify": ClassifyStep,
    "chunk":    ChunkStep,
    "index":    IndexStep,
}


def run_pipeline(step_names: list[str] | None = None) -> bool:
    """
    Run the pipeline.  Returns True if all steps succeeded.
    """
    names = step_names or list(ALL_STEPS.keys())

    # Validate requested step names
    unknown = [n for n in names if n not in ALL_STEPS]
    if unknown:
        print(f"❌ Unknown steps: {unknown}.  Valid: {list(ALL_STEPS.keys())}")
        return False

    steps = [(name, ALL_STEPS[name]()) for name in names]

    print("🚀 Running pipeline:", " → ".join(names))
    for name, step in steps:
        print(f"\n▶  {name} ({step.__class__.__name__})...")
        result = step.run()
        if result.success:
            print(f"   ✅ {result.summary}")
        else:
            print(f"   ❌ {result.summary}")
            if result.error:
                print(f"      Error: {result.error}")
            return False

    print("\n🎉 Pipeline complete!")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Alpha Generator Data Pipeline")
    parser.add_argument(
        "--only",
        type=str,
        default=None,
        help="Comma-separated list of steps to run (clean, classify, chunk, index)",
    )
    args = parser.parse_args()

    step_list = None
    if args.only:
        step_list = [s.strip() for s in args.only.split(",")]

    success = run_pipeline(step_list)
    sys.exit(0 if success else 1)

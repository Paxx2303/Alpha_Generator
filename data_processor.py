#!/usr/bin/env python3
"""
Alpha Research Data Processor
Cleans and organizes raw data for alpha research and market analysis
"""

import os
import shutil
import re
from pathlib import Path
from typing import Dict, List, Set

class AlphaDataProcessor:
    def __init__(self, raw_data_path: str, processed_data_path: str):
        self.raw_data_path = Path(raw_data_path)
        self.processed_data_path = Path(processed_data_path)
        
        # Define categories and their keywords
        self.categories = {
            'research_insights': {
                'keywords': ['alpha', 'sharpe', 'correlation', 'weight', 'factor', 'portfolio', 
                           'optimization', 'overfitting', 'neutralization', 'turnover', 'drawdown',
                           'signal', 'noise', 'backtest', 'performance', 'strategy', 'momentum',
                           'value', 'quality', 'earnings', 'analyst', 'surprise'],
                'description': 'Practical alpha research insights and community Q&A'
            },
            'technical_indicators': {
                'keywords': ['rsi', 'macd', 'bollinger', 'moving average', 'momentum', 'volatility',
                           'oscillator', 'trend', 'support', 'resistance', 'volume', 'price action'],
                'description': 'Technical analysis indicators and trading concepts'
            },
            'core_concepts': {
                'keywords': ['risk', 'return', 'beta', 'variance', 'covariance', 'regression',
                           'statistics', 'probability', 'distribution', 'correlation coefficient',
                           'standard deviation', 'mean', 'median', 'quantile', 'capm', 'black scholes',
                           'option pricing', 'derivatives'],
                'description': 'Fundamental financial and statistical concepts'
            },
            'platform_guides': {
                'keywords': ['brain', 'platform', 'simulation', 'expression', 'language', 'data',
                           'submission', 'getting started', 'tutorial', 'guide', 'documentation'],
                'description': 'WorldQuant Brain platform specific guides and documentation'
            },
            'academic_papers': {
                'keywords': ['fama', 'french', 'kahneman', 'tversky', 'prospect theory', 'behavioral',
                           'jegadeesh', 'titman', 'black', 'scholes', 'merton', 'markowitz', 'capm',
                           'efficient market', 'anomaly', 'empirical', 'journal', 'research'],
                'description': 'Academic research papers and theoretical foundations'
            },
            'quantitative_methods': {
                'keywords': ['risk parity', 'factor investing', 'smart beta', 'optimization',
                           'portfolio construction', 'quantitative', 'systematic', 'algorithmic',
                           'machine learning', 'statistical arbitrage', 'pairs trading'],
                'description': 'Advanced quantitative methods and systematic strategies'
            }
        }
        
        # Files to exclude (noise/irrelevant content)
        self.exclude_patterns = [
            r'.*personal.*',
            r'.*weight.*loss.*',
            r'.*diet.*',
            r'.*health.*'
        ]
        
    def is_relevant_content(self, file_path: Path) -> bool:
        """Check if file contains relevant alpha research content"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read().lower()
                
            # Check for exclusion patterns
            for pattern in self.exclude_patterns:
                if re.search(pattern, content):
                    # Double check - if it also contains alpha research terms, keep it
                    alpha_terms = ['alpha', 'sharpe', 'correlation', 'weight factor', 'portfolio']
                    if not any(term in content for term in alpha_terms):
                        return False
                        
            # Must contain at least one relevant keyword
            all_keywords = []
            for category in self.categories.values():
                all_keywords.extend(category['keywords'])
                
            return any(keyword in content for keyword in all_keywords)
            
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return False
    
    def categorize_file(self, file_path: Path) -> str:
        """Determine the best category for a file based on content analysis"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read().lower()
                
            # Score each category
            category_scores = {}
            for category, info in self.categories.items():
                score = sum(1 for keyword in info['keywords'] if keyword in content)
                category_scores[category] = score
                
            # Return category with highest score, default to research_insights
            if max(category_scores.values()) == 0:
                return 'research_insights'  # Default category
                
            return max(category_scores, key=category_scores.get)
            
        except Exception as e:
            print(f"Error categorizing {file_path}: {e}")
            return 'research_insights'
    
    def clean_filename(self, filename: str) -> str:
        """Clean and standardize filename"""
        # Remove special characters and normalize
        cleaned = re.sub(r'[^\w\s-]', '', filename)
        cleaned = re.sub(r'\s+', '_', cleaned.strip())
        cleaned = re.sub(r'_+', '_', cleaned)
        
        # Remove common prefixes
        cleaned = re.sub(r'^BRAIN_TIPS_', '', cleaned)
        cleaned = re.sub(r'^\[BRAIN_TIPS\]_', '', cleaned)
        
        return cleaned
    
    def process_files(self):
        """Main processing function"""
        print("🔄 Starting Alpha Research Data Processing...")
        
        stats = {
            'total_files': 0,
            'processed_files': 0,
            'excluded_files': 0,
            'categories': {cat: 0 for cat in self.categories.keys()}
        }
        
        # Process each source directory
        for source_dir in ['brain_tips', 'documentation', 'investopedia', 'research_papers', 'alpha_examples', 'quantitative_strategies']:
            source_path = self.raw_data_path / source_dir
            if not source_path.exists():
                continue
                
            print(f"\n📁 Processing {source_dir}...")
            
            for file_path in source_path.glob('*.md'):
                stats['total_files'] += 1
                
                # Check if file is relevant
                if not self.is_relevant_content(file_path):
                    stats['excluded_files'] += 1
                    print(f"❌ Excluded: {file_path.name}")
                    continue
                
                # Categorize file
                category = self.categorize_file(file_path)
                stats['categories'][category] += 1
                
                # Clean filename
                clean_name = self.clean_filename(file_path.stem) + '.md'
                
                # Copy to appropriate category folder
                dest_dir = self.processed_data_path / category
                dest_dir.mkdir(parents=True, exist_ok=True)
                dest_path = dest_dir / clean_name
                
                # Handle duplicate names
                counter = 1
                while dest_path.exists():
                    name_part = self.clean_filename(file_path.stem)
                    dest_path = dest_dir / f"{name_part}_{counter}.md"
                    counter += 1
                
                shutil.copy2(file_path, dest_path)
                stats['processed_files'] += 1
                print(f"✅ {file_path.name} → {category}/{dest_path.name}")
        
        # Print summary
        print(f"\n📊 Processing Summary:")
        print(f"Total files found: {stats['total_files']}")
        print(f"Files processed: {stats['processed_files']}")
        print(f"Files excluded: {stats['excluded_files']}")
        print(f"\n📂 Category Distribution:")
        for category, count in stats['categories'].items():
            desc = self.categories[category]['description']
            print(f"  {category}: {count} files - {desc}")
        
        # Create index file
        self.create_index_file(stats)
        
    def create_index_file(self, stats: Dict):
        """Create an index file documenting the processed data"""
        index_content = f"""# Alpha Research Data Index

## Overview
This directory contains cleaned and organized data for alpha research and market analysis.
All noise and irrelevant content has been filtered out.

## Processing Statistics
- **Total files processed**: {stats['processed_files']}
- **Files excluded**: {stats['excluded_files']}
- **Processing date**: {Path(__file__).stat().st_mtime}

## Directory Structure

"""
        
        for category, count in stats['categories'].items():
            desc = self.categories[category]['description']
            index_content += f"### {category}/ ({count} files)\n{desc}\n\n"
            
        index_content += """
## Data Quality Standards
- ✅ Contains relevant alpha research, market analysis, or trading concepts
- ✅ Provides actionable insights for quantitative research
- ✅ Includes technical indicators, risk metrics, or statistical methods
- ✅ Platform-specific guides and documentation
- ❌ Personal questions unrelated to finance
- ❌ Duplicate content
- ❌ Noise or irrelevant information

## Usage Guidelines
This processed data is optimized for:
- Training AI models on alpha research
- Building knowledge bases for quantitative analysis
- Creating educational content for algorithmic trading
- Developing automated research assistants
"""
        
        index_path = self.processed_data_path / 'README.md'
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(index_content)
        
        print(f"📋 Created index file: {index_path}")

if __name__ == "__main__":
    # Configuration
    raw_data_path = r"c:\Using\Alpha_Generator\alpha_skills\rawdata"
    processed_data_path = r"c:\Using\Alpha_Generator\alpha_skills\processed_data"
    
    # Initialize and run processor
    processor = AlphaDataProcessor(raw_data_path, processed_data_path)
    processor.process_files()
    
    print("\n🎉 Data processing completed successfully!")
import json
import os
import re
from pathlib import Path
from typing import List, Dict

class KnowledgeRetriever:
    def __init__(self, skills_dir: str = None):
        if skills_dir is None:
            # Default to the directory containing this file
            self.skills_dir = Path(__file__).parent
        else:
            self.skills_dir = Path(skills_dir)
            
        self.reference_dir = self.skills_dir / "reference"
        self.final_dataset_dir = self.skills_dir / "final_dataset"
        
        self.dataset_file = self.final_dataset_dir / "alpha_research_dataset.json"

    def search(self, query: str, top_k: int = 3) -> str:
        """
        Search the knowledge base (JSON and markdown files) for the given query.
        Returns a formatted string containing the top results.
        """
        results = []
        
        # 1. Search in the JSON dataset
        results.extend(self._search_json(query))
        
        # 2. Search in markdown reference files
        results.extend(self._search_markdown(query))
        
        # 3. Rank and format results
        # Simple ranking based on occurrences of query terms (case-insensitive)
        query_terms = query.lower().split()
        
        def score_result(res: Dict) -> int:
            text = (res['title'] + " " + res['content']).lower()
            score = 0
            for term in query_terms:
                score += len(re.findall(re.escape(term), text))
            return score

        # Filter out 0 score results
        results = [r for r in results if score_result(r) > 0]
        
        # Sort by score descending
        results.sort(key=score_result, reverse=True)
        
        top_results = results[:top_k]
        
        if not top_results:
            return f"No results found for query: '{query}'"
            
        formatted_output = f"### Top {len(top_results)} Search Results for '{query}'\n\n"
        for i, res in enumerate(top_results, 1):
            formatted_output += f"#### Result {i}: {res['title']}\n"
            formatted_output += f"**Source:** {res['source']}\n"
            content = res['content']
            # Truncate content if too long
            if len(content) > 1000:
                content = content[:1000] + "...\n[Content Truncated]"
            formatted_output += f"**Content Extract:**\n{content}\n"
            formatted_output += "---\n"
            
        return formatted_output

    def _search_json(self, query: str) -> List[Dict]:
        results = []
        if not self.dataset_file.exists():
            return results
            
        try:
            with open(self.dataset_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            documents = data.get("documents", [])
            for doc in documents:
                doc_title = doc.get("metadata", {}).get("title", doc.get("id", "Unknown Document"))
                doc_content = doc.get("content", "")
                
                results.append({
                    "title": doc_title,
                    "content": doc_content,
                    "source": f"JSON Dataset ({doc.get('metadata', {}).get('category', 'unknown')})"
                })
        except Exception as e:
            print(f"Error reading JSON dataset: {e}")
            
        return results

    def _search_markdown(self, query: str) -> List[Dict]:
        results = []
        if not self.reference_dir.exists():
            return results
            
        try:
            for root, _, files in os.walk(self.reference_dir):
                for file in files:
                    if file.endswith(".md"):
                        file_path = Path(root) / file
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            
                        # Try to extract a title from the first heading
                        title = file
                        match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
                        if match:
                            title = match.group(1)
                            
                        results.append({
                            "title": title,
                            "content": content,
                            "source": f"Markdown Reference ({file})"
                        })
        except Exception as e:
            print(f"Error reading markdown files: {e}")
            
        return results

if __name__ == "__main__":
    # Simple test
    retriever = KnowledgeRetriever()
    print(retriever.search("momentum", top_k=1))

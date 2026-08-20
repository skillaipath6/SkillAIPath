"""
RAG Query System for PR Reviewer
Queries Unity Catalog tables to provide context-aware, intelligent reviews
"""

from typing import List, Dict, Optional
from datetime import datetime, timedelta


def get_knowledge_base():
    """Initialize knowledge base connection"""
    return KnowledgeBase()


class KnowledgeBase:
    """Queries Unity Catalog tables for PR review intelligence"""
    
    def __init__(self):
        try:
            from pyspark.sql import SparkSession
            self.spark = SparkSession.builder.getOrCreate()
            self.enabled = True
        except:
            self.enabled = False
    
    def query_pr_history(self, file_path: str, issue_type: str, days_back: int = 90) -> List[Dict]:
        """
        Check if similar issue was flagged before in this file
        Returns list of past occurrences with PR IDs
        """
        if not self.enabled:
            return []
        
        try:
            cutoff = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
            
            df = self.spark.sql(f"""
                SELECT 
                    pr_id,
                    pr_title,
                    issue_text,
                    severity,
                    line_number,
                    author,
                    resolved,
                    resolution_notes,
                    timestamp
                FROM sap_dev.pr_reviews.pr_history
                WHERE file_path = '{file_path}'
                  AND issue_type = '{issue_type}'
                  AND timestamp >= '{cutoff}'
                ORDER BY timestamp DESC
                LIMIT 5
            """)
            
            rows = df.collect()
            return [row.asDict() for row in rows]
        except Exception as e:
            print(f"Warning: Could not query pr_history: {e}")
            return []
    
    def query_codebase_patterns(self, domain: str = None, pattern_type: str = None) -> List[Dict]:
        """
        Get learned patterns from codebase
        Returns conventions, best practices, and architecture rules
        """
        if not self.enabled:
            return []
        
        try:
            where_clauses = ["frequency >= 5", "confidence_score >= 0.7"]
            
            if domain:
                where_clauses.append(f"domain = '{domain}'")
            
            if pattern_type:
                where_clauses.append(f"pattern_type = '{pattern_type}'")
            
            where_sql = " AND ".join(where_clauses)
            
            df = self.spark.sql(f"""
                SELECT 
                    pattern_id,
                    pattern_type,
                    pattern_name,
                    pattern_text,
                    example_code,
                    frequency,
                    confidence_score,
                    domain
                FROM sap_dev.pr_reviews.codebase_patterns
                WHERE {where_sql}
                ORDER BY frequency DESC, confidence_score DESC
                LIMIT 20
            """)
            
            rows = df.collect()
            return [row.asDict() for row in rows]
        except Exception as e:
            print(f"Warning: Could not query codebase_patterns: {e}")
            return []
    
    def get_developer_history(self, developer: str) -> List[Dict]:
        """
        Get past feedback for this developer
        Used to personalize tone and avoid nagging
        """
        if not self.enabled:
            return []
        
        try:
            df = self.spark.sql(f"""
                SELECT 
                    issue_type,
                    times_flagged,
                    last_flagged,
                    resolved_count,
                    still_unresolved_count,
                    improvement_trend,
                    notes
                FROM sap_dev.pr_reviews.developer_feedback
                WHERE developer = '{developer}'
                  AND times_flagged >= 2
                ORDER BY times_flagged DESC
            """)
            
            rows = df.collect()
            return [row.asDict() for row in rows]
        except Exception as e:
            print(f"Warning: Could not query developer_feedback: {e}")
            return []
    
    def check_pattern_violation(self, code: str, domain: str = None) -> List[Dict]:
        """
        Check if code violates learned architecture patterns
        Returns list of violated patterns with examples
        """
        if not self.enabled:
            return []
        
        try:
            patterns = self.query_codebase_patterns(domain=domain, pattern_type='anti_pattern')
            violations = []
            
            code_lower = code.lower()
            for pattern in patterns:
                # Simple substring check (could be enhanced with regex)
                pattern_indicators = pattern.get('pattern_text', '').lower().split()
                if any(indicator in code_lower for indicator in pattern_indicators[:5]):
                    violations.append(pattern)
            
            return violations
        except:
            return []
    
    def get_architecture_rules(self, domain: str = None) -> List[Dict]:
        """
        Get architecture-level rules learned from codebase
        Returns rules about layering, dependencies, data flow
        """
        if not self.enabled:
            return []
        
        return self.query_codebase_patterns(domain=domain, pattern_type='architecture_rule')
    
    def log_review(self, pr_id: str, pr_title: str, file_path: str, 
                   issue_type: str, issue_text: str, severity: str, 
                   line_number: int, author: str):
        """
        Log this review to pr_history for future learning
        Called after each review is completed
        """
        if not self.enabled:
            return
        
        try:
            from pyspark.sql.types import StructType, StructField, StringType, IntegerType, BooleanType, TimestampType, DateType
            
            now = datetime.now()
            
            schema = StructType([
                StructField("pr_id", StringType(), False),
                StructField("pr_title", StringType(), True),
                StructField("file_path", StringType(), False),
                StructField("issue_type", StringType(), False),
                StructField("issue_text", StringType(), False),
                StructField("severity", StringType(), False),
                StructField("line_number", IntegerType(), True),
                StructField("author", StringType(), False),
                StructField("resolved", BooleanType(), True),
                StructField("resolution_notes", StringType(), True),
                StructField("timestamp", TimestampType(), False),
                StructField("review_date", DateType(), False),
            ])
            
            data = [(
                pr_id,
                pr_title,
                file_path,
                issue_type,
                issue_text,
                severity,
                line_number,
                author,
                False,  # resolved - will be updated later
                None,   # resolution_notes
                now,
                now.date()
            )]
            
            df = self.spark.createDataFrame(data, schema)
            df.write.mode("append").saveAsTable("sap_dev.pr_reviews.pr_history")
            
        except Exception as e:
            print(f"Warning: Could not log review: {e}")
    
    def parse_pr_context(self, pr_description: str, pr_title: str) -> Dict[str, any]:
        """
        Parse PR description for context that should affect review
        Returns dict with: design_decisions, known_issues, team_agreements
        """
        context = {
            "design_decisions": [],
            "known_issues": [],
            "skip_patterns": []
        }
        
        if not pr_description:
            return context
        
        desc_lower = (pr_description + " " + pr_title).lower()
        
        # Common phrases that indicate intentional decisions
        skip_indicators = [
            ("intentionally", "design_decision"),
            ("by design", "design_decision"),
            ("known issue", "known_issue"),
            ("tech debt", "known_issue"),
            ("will fix later", "known_issue"),
            ("agreed with team", "team_agreement"),
            ("discussed offline", "team_agreement"),
            ("temporary", "temporary_code"),
            ("workaround for", "workaround"),
        ]
        
        for phrase, category in skip_indicators:
            if phrase in desc_lower:
                context["skip_patterns"].append({
                    "phrase": phrase,
                    "category": category,
                    "context": desc_lower[max(0, desc_lower.index(phrase)-50):desc_lower.index(phrase)+100]
                })
        
        return context
    
    def save_feedback(self, pr_id: str, pr_url: str, file_path: str, 
                     issue_type: str, original_comment: str, 
                     edited_comment: Optional[str], action: str, reviewer: str,
                     pr_context: str = ""):
        """
        Log what the reviewer did with the generated comment
        Actions: 'kept' (unchanged), 'edited' (modified), 'removed' (deleted)
        This is how we learn what suggestions are helpful vs noise
        """
        if not self.enabled:
            return
        
        try:
            from pyspark.sql.types import StructType, StructField, StringType, TimestampType, DateType
            
            now = datetime.now()
            
            schema = StructType([
                StructField("pr_id", StringType(), False),
                StructField("pr_url", StringType(), True),
                StructField("file_path", StringType(), False),
                StructField("issue_type", StringType(), False),
                StructField("original_comment", StringType(), False),
                StructField("edited_comment", StringType(), True),
                StructField("action", StringType(), False),
                StructField("reviewer", StringType(), False),
                StructField("pr_context", StringType(), True),
                StructField("timestamp", TimestampType(), False),
                StructField("feedback_date", DateType(), False),
            ])
            
            data = [(
                pr_id,
                pr_url,
                file_path,
                issue_type,
                original_comment,
                edited_comment,
                action,
                reviewer,
                pr_context,
                now,
                now.date()
            )]
            
            # Ensure table exists
            self.spark.sql("""
                CREATE TABLE IF NOT EXISTS sap_dev.pr_reviews.review_feedback_loop (
                    pr_id STRING NOT NULL,
                    pr_url STRING,
                    file_path STRING NOT NULL,
                    issue_type STRING NOT NULL,
                    original_comment STRING NOT NULL,
                    edited_comment STRING,
                    action STRING NOT NULL,
                    reviewer STRING NOT NULL,
                    pr_context STRING,
                    timestamp TIMESTAMP NOT NULL,
                    feedback_date DATE NOT NULL
                )
                USING DELTA
                PARTITIONED BY (feedback_date)
                COMMENT 'Tracks reviewer edits to learn what suggestions to skip'
            """)
            
            df = self.spark.createDataFrame(data, schema)
            df.write.mode("append").saveAsTable("sap_dev.pr_reviews.review_feedback_loop")
            
        except Exception as e:
            print(f"Warning: Could not save feedback: {e}")
    
    def query_rejected_patterns(self, issue_type: str, threshold: int = 2) -> List[Dict]:
        """
        Find patterns that reviewers consistently remove or edit
        If an issue_type has been removed 2+ times, we should stop suggesting it
        Returns list of patterns to skip
        """
        if not self.enabled:
            return []
        
        try:
            df = self.spark.sql(f"""
                WITH rejection_counts AS (
                    SELECT 
                        issue_type,
                        action,
                        COUNT(*) as count,
                        COLLECT_SET(SUBSTRING(original_comment, 1, 100)) as sample_comments
                    FROM sap_dev.pr_reviews.review_feedback_loop
                    WHERE issue_type = '{issue_type}'
                      AND action IN ('removed', 'edited')
                      AND feedback_date >= DATE_SUB(CURRENT_DATE(), 90)
                    GROUP BY issue_type, action
                )
                SELECT 
                    issue_type,
                    action,
                    count,
                    sample_comments
                FROM rejection_counts
                WHERE count >= {threshold}
                ORDER BY count DESC
            """)
            
            rows = df.collect()
            return [row.asDict() for row in rows]
        except Exception as e:
            print(f"Warning: Could not query rejected patterns: {e}")
            return []

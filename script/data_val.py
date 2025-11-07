import os
from sql_generator.sql_via_python import query_executor
import pandas as pd
from datetime import datetime
import sys


class DataValRunner:
    """Run SQL analysis files and display results."""

    def __init__(self):
        self.result = {}
        self.quality_issues = []
        self.quality_issues_count = 0
        self.total_checks = 0
        self.passed_checks = 0
        self.failed_checks = 0

    def read_sql_file(self, filename):
        """Read SQL file and extract queries."""
        filepath = f"../sql/validation/{filename}.sql"

        with open(filepath, "r") as f:
            content = f.read()

        # Split by semicolon to get individual queries
        queries = [q.strip() for q in content.split(";") if q.strip()]
        return queries

    def run_analysis_file(self, filename, check_name, csv_export=None, file_name=None):
        self.total_checks += 1

        try:
            queries = self.read_sql_file(filename)
            query = queries[0] if queries else ""
            sql_lines = [
                line for line in query.split("\n") if not line.strip().startswith("--")
            ]
            clean_query = "\n".join(sql_lines).strip()

            db = query_executor(clean_query)
            db.connect_to_db()
            results = db.execute()

            if results:
                columns = [desc[0] for desc in db.cur.description]
                df = pd.DataFrame(results, columns=columns)
                self.result[check_name] = df

                if not df.empty:
                    count = df.iloc[0, 0] if len(df.columns) > 0 else 0

                    if count > 0:
                        self.failed_checks += 1
                        issue = {
                            "check_name": check_name,
                            "count": count,
                            "description": f"Found {count:,} {check_name.replace('_', ' ')} issues",
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        }
                        self.quality_issues.append(issue)
                        self.quality_issues_count += count
                        print(f"FAIL: {check_name} - {count:,} issues found")
                    else:
                        self.passed_checks += 1
                        print(f"PASS: {check_name} - No issues found")
                else:
                    self.passed_checks += 1
                    print(f"PASS: {check_name} - No data returned")

                if csv_export and not df.empty:
                    csv_path = f"../result/{file_name}.csv"
                    df.to_csv(csv_path, index=False)
                    print(f"Exported: {csv_path}")

            else:
                self.passed_checks += 1
                print(f"PASS: {check_name} - No results returned")

            db.close()

        except Exception as e:
            self.failed_checks += 1
            print(f"ERROR: {check_name} - {str(e)}")

        return self.result

    def print_summary(self):
        """Print a concise summary of all data validation results."""
        print("== SUMMARY ==")

        print(f"Total Checks: {self.total_checks}")
        print(f"Passed: {self.passed_checks}")
        print(f"Failed: {self.failed_checks}")

        if self.total_checks > 0:
            success_rate = (self.passed_checks / self.total_checks) * 100
            print(f"Success Rate: {success_rate:.1f}%")

        if self.quality_issues_count > 0:
            print(f"\nTotal Issues: {self.quality_issues_count:,}")
            for issue in self.quality_issues:
                print(f"  {issue['check_name']}: {issue['count']:,} issues")
        else:
            print("\nNo data quality issues found")

        print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    def export_summary_report(self, filename="data_validation_report.txt"):
        """Export a text summary report to file."""
        report_path = f"../result/{filename}"

        with open(report_path, "w") as f:
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"Total Checks: {self.total_checks}\n")
            f.write(f"Passed Checks: {self.passed_checks}\n")
            f.write(f"Failed Checks: {self.failed_checks}\n")

            if self.total_checks > 0:
                success_rate = (self.passed_checks / self.total_checks) * 100
                f.write(f"Success Rate: {success_rate:.1f}%\n")

            f.write(f"\nTotal Issues Found: {self.quality_issues_count}\n\n")

            if self.quality_issues:
                f.write("DETAILED ISSUES\n")
                f.write("-" * 15 + "\n")
                for issue in self.quality_issues:
                    f.write(
                        f"• {issue['check_name'].replace('_', ' ').title()}: {issue['count']} issues\n"
                    )
                    f.write(f"  Description: {issue['description']}\n")
                    f.write(f"  Timestamp: {issue['timestamp']}\n\n")

        print(f"Report exported: {report_path}")
        return report_path


if __name__ == "__main__":
    runner = DataValRunner()
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    runner.run_analysis_file("product_without_seller", "product_without_seller")
    runner.run_analysis_file("missing_email", "missing_email")
    runner.run_analysis_file("price_val", "price_val")
    runner.run_analysis_file("orders_without_payment", "orders_without_payment")

    runner.print_summary()
    runner.export_summary_report()

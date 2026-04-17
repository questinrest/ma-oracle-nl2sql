from dataclasses import dataclass
from typing import Iterable
import asyncio

from openai import OpenAI
from vanna.capabilities.agent_memory import ToolMemorySearchResult

from app.config import Settings
from app.schema import DatabaseSchema


class SqlGenerationError(RuntimeError):
    """Raised when the LLM cannot generate usable SQL."""


@dataclass(frozen=True)
class PromptContext:
    question: str
    schema_text: str
    memory_examples: tuple[ToolMemorySearchResult, ...]


class SQLGenerator:
    def __init__(self, settings: Settings, schema: DatabaseSchema) -> None:
        self.settings = settings
        self.schema = schema
        self._client = (
            OpenAI(
                base_url=settings.llm_base_url,
                api_key=settings.groq_api_key,
            )
            if settings.groq_api_key
            else None
        )

    async def generate_sql(
        self,
        question: str,
        memory_examples: Iterable[ToolMemorySearchResult],
    ) -> str:
        if self._client is None:
            raise SqlGenerationError("Missing GROQ_API_KEY environment variable.")

        prompt_context = PromptContext(
            question=question,
            schema_text=self.schema.format_for_prompt(),
            memory_examples=tuple(memory_examples),
        )
        try:
            response = await asyncio.to_thread(
                self._client.chat.completions.create,
                model=self.settings.llm_model,
                temperature=0,
                messages=[
                    {
                        "role": "system",
                        "content": self._build_system_prompt(prompt_context),
                    },
                    {
                        "role": "user",
                        "content": f"Question: {question}",
                    },
                ],
            )
        except Exception as exc:
            raise SqlGenerationError(f"LLM request failed: {exc}") from exc

        content = response.choices[0].message.content if response.choices else None
        if isinstance(content, list):
            content = "".join(
                part.text for part in content if getattr(part, "text", None)
            )
        if not content:
            raise SqlGenerationError("The LLM returned an empty response.")
        return content

    def _build_system_prompt(self, prompt_context: PromptContext) -> str:
        examples = self._format_examples(prompt_context.memory_examples)
        return f"""
You are an expert SQLite analyst. Convert the user's question into exactly one safe, accurate SQLite query.

=== CORE RULES ===
- Return ONLY one SQLite SELECT query — no explanation, no markdown, no backticks.
- The query MUST start with SELECT or WITH.
- NEVER use INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, PRAGMA, ATTACH, or multiple statements.
- NEVER use semicolons or SQL comments (-- or /* */).
- Only reference tables and columns that exist in the schema below.

=== ACCURACY RULES (read carefully — these prevent wrong answers) ===

1. DEDUPLICATION — annual rows can appear multiple times (amendments, restated filings).
   Always add: ORDER BY filed_date DESC LIMIT 1
   when fetching a SINGLE point-in-time value (e.g. "what was X's revenue in 2024?").

2. ANNUAL DATA QUALITY — filter `filing_type = '10-K'` whenever you filter `is_annual = 1`.
   Some 10-Q rows are incorrectly tagged is_annual = 1. Use both conditions together:
     AND is_annual = 1 AND filing_type = '10-K'

3. BALANCE SHEET ITEMS — NEVER use SUM() on: Assets, Liabilities, StockholdersEquity,
   AssetsCurrent, LiabilitiesCurrent, Goodwill, PropertyPlantAndEquipmentNet.
   These are snapshot values, not additive flows. Use MAX(value) or a direct row fetch instead.

4. REVENUE CONCEPT ALIASES — the revenue concept name changed across XBRL filings years.
   Always use IN (...) with all known aliases when asking for revenue/sales:
     f.concept IN (
       'RevenueFromContractWithCustomerExcludingAssessedTax',
       'Revenues',
       'SalesRevenueNet',
       'RevenueFromContractWithCustomerIncludingAssessedTax'
     )

5. COST OF REVENUE ALIASES — similarly for cost of goods/services:
     f.concept IN ('CostOfGoodsAndServicesSold', 'CostOfRevenue', 'CostOfGoodsSold')

6. FISCAL YEAR CALENDARS — these companies have NON-CALENDAR fiscal years:
   - AAPL (Apple):     FY ends in late September   (FY2024 = period_end '2024-09-28')
   - MSFT (Microsoft): FY ends in late June         (FY2024 = period_end '2024-06-30')
   - NVDA (NVIDIA):    FY ends in late January      (FY2025 = period_end '2026-01-26')
   - CRM (Salesforce): FY ends in late January      (FY2025 = period_end '2026-01-31')
   - SNOW (Snowflake): FY ends in late January      (FY2025 = period_end '2026-01-31')
   - CRWD (CrowdStrike): FY ends in late January    (FY2025 = period_end '2026-01-31')
   When the user mentions a fiscal year for these companies, filter by fiscal_year column
   (NOT by period_end LIKE '20XX%') — the fiscal_year column stores the correct value.

7. LATEST VALUE — when the user asks for the "latest" or "most recent" value for a metric,
   use a correlated subquery or window function to get the row with the MAX period_end per company:
     AND f.period_end = (
       SELECT MAX(f2.period_end) FROM financial_facts f2
       WHERE f2.cik = f.cik AND f2.concept = f.concept
     )

8. JOINS — always join on companies.cik = financial_facts.cik when you need company names or tickers.
   Use companies.ticker for filtering by stock symbol (e.g. WHERE c.ticker = 'AAPL').

=== DATABASE SCHEMA ===
{prompt_context.schema_text}

=== REFERENCE EXAMPLES (from prior successful queries) ===
{examples}
""".strip()

    @staticmethod
    def _format_examples(memory_examples: tuple[ToolMemorySearchResult, ...]) -> str:
        if not memory_examples:
            return "- No prior examples available."

        lines: list[str] = []
        for index, result in enumerate(memory_examples, start=1):
            lines.append(f"Example {index} question: {result.memory.question}")
            lines.append(f"Example {index} SQL: {result.memory.args.get('sql', '')}")
            lines.append("")
        return "\n".join(lines).strip()

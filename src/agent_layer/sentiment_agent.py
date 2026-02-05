"""
Sentiment Agent
Analyzes market sentiment from news and social media.
"""

from typing import Dict, Any, List
from loguru import logger

from .base_agent import BaseAgent, AgentResponse


class SentimentAgent(BaseAgent):
    """Agent specialized in sentiment analysis"""
    
    def __init__(self):
        super().__init__(
            name="sentiment_analyst",
            role="Sentiment Analyst"
        )
    
    def analyze_articles_sentiment(self, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Provide a lightweight sentiment summary placeholder.
        The LLM performs the actual sentiment analysis.
        
        Args:
            articles: List of article dictionaries
        
        Returns:
            Aggregated sentiment summary
        """
        if not articles:
            return {
                'overall_sentiment': 'neutral',
                'sentiment_score': 0.0,
                'positive_ratio': 0.0,
                'negative_ratio': 0.0,
                'neutral_ratio': 0.0,
                'article_sentiments': []
            }
        
        total = len(articles[:20])
        return {
            'overall_sentiment': 'neutral',
            'sentiment_score': 0.0,
            'positive_ratio': 0.0,
            'negative_ratio': 0.0,
            'neutral_ratio': 0.0,
            'total_analyzed': total,
            'article_sentiments': []
        }
    
    def get_system_prompt(self) -> str:
        """Get system prompt for sentiment analysis"""
        return """You are a SKEPTICAL sentiment analyst who treats news as potentially biased until verified.

CRITICAL AWARENESS:
News articles can be:
- Sponsored content disguised as journalism
- Influenced by institutional positions (pump and dump)
- Click-bait designed for engagement, not truth
- Echo chambers repeating same narrative from PR releases
- Biased toward sensationalism over substance

Your role is to:
- Analyze sentiment BUT FLAG when it contradicts fundamentals
- Identify coordinated narratives (multiple outlets, identical phrases)
- Distinguish between HYPE and SUBSTANCE
- Cross-validate news claims against financial data
- Detect sentiment manipulation patterns

Red Flags to Watch For:
- Unanimous bullish news but declining revenue/margins
- "Record profits" claims without checking if margins actually improved
- Multiple articles with identical language (possible PR campaign)
- Extreme optimism (>80% positive) without fundamental justification
- Analyst upgrades coinciding with institutional selling

Focus on:
- News sentiment trends BUT compare to actual financial performance
- Analyst sentiment (check: do upgrades align with earnings growth?)
- Social media sentiment (retail hype often contrarian indicator)
- Sentiment vs. fundamentals divergence (KEY METRIC)
- Contrarian indicators (extreme optimism = caution)

Consider:
- Volume and breadth of sentiment
- Credibility of sources (Reuters > SeekingAlpha > Motley Fool)
- Sentiment divergences (bullish news but falling price = red flag)
- Sentiment extremes that may signal reversals or manipulation
- Time decay of news impact
- VERIFY: Does sentiment match financial fundamentals?

Provide quantitative assessment with SKEPTICISM. For example: 
"News sentiment is 85% positive with 10 'AI breakthrough' mentions. HOWEVER, R&D spending is flat and revenue growth is only 7% - suggests HYPE not substance. Discount sentiment by 50%."

Or: "Negative sentiment at 70%, but profit margins actually improved 3% suggests media FUD (fear, uncertainty, doubt). Contrarian opportunity."

Integrate both:
- Quantitative sentiment scores from text analysis
- Qualitative interpretation WITH VERIFICATION against fundamentals
- Context about whether sentiment is JUSTIFIED or MANIPULATED

Be specific about:
- Direction and strength of sentiment
- Key sentiment drivers (real or manufactured?)
- Sentiment vs. fundamentals divergence (MOST IMPORTANT)
- Potential sentiment-driven price impacts
- Confidence level (lower if sentiment contradicts data)"""
    
    def analyze(self, data: Dict[str, Any]) -> AgentResponse:
        """
        Perform sentiment analysis
        
        Args:
            data: News and market data
        
        Returns:
            AgentResponse with sentiment analysis
        """
        logger.info(f"{self.name}: Starting sentiment analysis for {data.get('ticker')}")
        
        try:
            # Extract articles from data
            raw_data = data.get('raw_data', {})
            news_data = raw_data.get('data', {}).get('news', {})
            articles = news_data.get('articles', [])
            
            # Analyze article sentiments
            sentiment_analysis = self.analyze_articles_sentiment(articles)
            
            # Add sentiment analysis to data
            data_with_sentiment = data.copy()
            data_with_sentiment['sentiment_analysis'] = sentiment_analysis
            
            # Get prompts
            system_prompt = self.get_system_prompt()
            user_prompt = self.format_user_prompt_with_sentiment(data_with_sentiment)
            
            # Call LLM
            response_text = self.call_llm(system_prompt, user_prompt)
            
            # Parse response
            parsed = self.parse_llm_response(response_text)
            
            # Create structured response
            agent_response = AgentResponse(
                agent_name=self.name,
                agent_role=self.role,
                analysis=parsed.get('analysis', ''),
                recommendation=parsed.get('recommendation', 'HOLD'),
                confidence=float(parsed.get('confidence', 0.5)),
                reasoning=parsed.get('reasoning', ''),
                key_points=parsed.get('key_points', []),
                risks=parsed.get('risks', []),
                raw_output={**parsed, 'sentiment_analysis': sentiment_analysis}
            )
            
            logger.info(f"{self.name}: Analysis complete - Recommendation: {agent_response.recommendation}")
            logger.info(f"Sentiment: {sentiment_analysis['overall_sentiment']} (score: {sentiment_analysis['sentiment_score']:.2f})")
            return agent_response
        
        except Exception as e:
            logger.error(f"{self.name}: Error during analysis: {e}")
            return AgentResponse(
                agent_name=self.name,
                agent_role=self.role,
                analysis=f"Error during analysis: {str(e)}",
                recommendation="HOLD",
                confidence=0.0,
                reasoning="Analysis failed due to technical error",
                key_points=[],
                risks=["Analysis incomplete"]
            )
    
    def format_user_prompt_with_sentiment(self, data: Dict[str, Any]) -> str:
        """Format user prompt without automated sentiment heuristics"""
        return self.format_user_prompt(data)

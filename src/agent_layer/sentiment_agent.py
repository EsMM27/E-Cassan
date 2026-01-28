"""
Sentiment Agent
Analyzes market sentiment from news and social media
currently uses FinBERT for sentiment analysis
change to my own model later
"""

from typing import Dict, Any, List
from loguru import logger

from .base_agent import BaseAgent, AgentResponse
from ..config import config


class SentimentAgent(BaseAgent):
    """Agent specialized in sentiment analysis"""
    
    def __init__(self, use_finbert: bool = False):
        super().__init__(
            name="sentiment_analyst",
            role="Sentiment Analyst"
        )
        
        self.use_finbert = use_finbert  # Disabled by default
        self.sentiment_model = None
        self.tokenizer = None

    
    def _initialize_finbert(self):
        """Initialize FinBERT model for sentiment analysis"""
        try:
            model_name = config.model_config.get('sentiment', {}).get('model_name', 'ProsusAI/finbert')
            device = config.model_config.get('sentiment', {}).get('device', 'cpu')
            
            logger.info(f"Loading FinBERT model: {model_name}")
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.sentiment_model = AutoModelForSequenceClassification.from_pretrained(model_name)
            
            # Move to GPU if available
            if device == 'cuda' and torch.cuda.is_available():
                self.sentiment_model = self.sentiment_model.cuda()
                logger.info("FinBERT loaded on CUDA")
            else:
                logger.info("FinBERT loaded on CPU")
        
        except Exception as e:
            logger.warning(f"Failed to load FinBERT: {e}. Will use LLM-based sentiment.")
            self.use_finbert = False
    
    def analyze_text_sentiment(self, text: str) -> Dict[str, float]:
        """
        Analyze sentiment of a single text using FinBERT
        
        Args:
            text: Text to analyze
        
        Returns:
            Dict with sentiment scores {positive, negative, neutral}
        """
        if not self.use_finbert or not self.sentiment_model:
            return {'positive': 0.33, 'negative': 0.33, 'neutral': 0.34}
        
        try:
            inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512, padding=True)
            
            if torch.cuda.is_available() and next(self.sentiment_model.parameters()).is_cuda:
                inputs = {k: v.cuda() for k, v in inputs.items()}
            
            with torch.no_grad():
                outputs = self.sentiment_model(**inputs)
            
            # Get probabilities
            probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
            scores = probs.cpu().numpy()[0]
            
            # FinBERT outputs: [positive, negative, neutral]
            return {
                'positive': float(scores[0]),
                'negative': float(scores[1]),
                'neutral': float(scores[2])
            }
        
        except Exception as e:
            logger.error(f"Error in sentiment analysis: {e}")
            return {'positive': 0.33, 'negative': 0.33, 'neutral': 0.34}
    
    def analyze_articles_sentiment(self, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze sentiment across multiple news articles
        
        Args:
            articles: List of article dictionaries
        
        Returns:
            Aggregated sentiment analysis
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
        
        article_sentiments = []
        
        for article in articles[:20]:  # Limit to 20 articles for performance
            title = article.get('title', '')
            description = article.get('description', '')
            text = f"{title}. {description}"
            
            if len(text.strip()) < 10:
                continue
            
            sentiment = self.analyze_text_sentiment(text)
            article_sentiments.append({
                'title': title,
                'sentiment': sentiment,
                'dominant': max(sentiment.items(), key=lambda x: x[1])[0]
            })
        
        # Aggregate sentiments
        if not article_sentiments:
            return {
                'overall_sentiment': 'neutral',
                'sentiment_score': 0.0,
                'positive_ratio': 0.0,
                'negative_ratio': 0.0,
                'neutral_ratio': 0.0,
                'article_sentiments': []
            }
        
        total = len(article_sentiments)
        positive_count = sum(1 for a in article_sentiments if a['dominant'] == 'positive')
        negative_count = sum(1 for a in article_sentiments if a['dominant'] == 'negative')
        neutral_count = sum(1 for a in article_sentiments if a['dominant'] == 'neutral')
        
        # Calculate overall sentiment score (-1 to 1)
        sentiment_score = (positive_count - negative_count) / total if total > 0 else 0.0
        
        # Determine overall sentiment
        if sentiment_score > 0.2:
            overall = 'positive'
        elif sentiment_score < -0.2:
            overall = 'negative'
        else:
            overall = 'neutral'
        
        return {
            'overall_sentiment': overall,
            'sentiment_score': sentiment_score,
            'positive_ratio': positive_count / total,
            'negative_ratio': negative_count / total,
            'neutral_ratio': neutral_count / total,
            'total_analyzed': total,
            'article_sentiments': article_sentiments
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
        """Format user prompt with sentiment analysis results"""
        sentiment_data = data.get('sentiment_analysis', {})
        
        base_prompt = self.format_user_prompt(data)
        
        sentiment_section = f"""

## Automated Sentiment Analysis Results
- Overall Sentiment: {sentiment_data.get('overall_sentiment', 'neutral').upper()}
- Sentiment Score: {sentiment_data.get('sentiment_score', 0):.2f} (range: -1 to +1)
- Positive Articles: {sentiment_data.get('positive_ratio', 0):.1%}
- Negative Articles: {sentiment_data.get('negative_ratio', 0):.1%}
- Neutral Articles: {sentiment_data.get('neutral_ratio', 0):.1%}
- Total Articles Analyzed: {sentiment_data.get('total_analyzed', 0)}

Use this quantitative sentiment analysis along with your qualitative interpretation of the news content.
"""
        
        return base_prompt + sentiment_section

import Anthropic from '@anthropic-ai/sdk';

const anthropic = new Anthropic({
  apiKey: process.env.ANTHROPIC_API_KEY,
});

/**
 * AI 메시지 분석 서비스
 * 교수의 메시지를 분석하여 감정, 오해 소지, 개선 제안을 제공
 */
export class AIMessageService {
  /**
   * 메시지 종합 분석
   * @param {string} message - 원본 메시지
   * @param {boolean} isGroupMessage - 그룹 메시지 여부
   * @returns {Promise<Object>} 분석 결과
   */
  static async analyzeMessage(message, isGroupMessage = false) {
    const messageType = isGroupMessage ? '단체 메시지' : '개별 메시지';

    const prompt = `당신은 교육 전문가이자 커뮤니케이션 전문가입니다. 교수가 학생에게 보내려는 ${messageType}를 분석해주세요.

<원본 메시지>
${message}
</원본 메시지>

다음 항목들을 분석하여 JSON 형식으로 답변해주세요:

1. emotion_analysis: 메시지에서 감지되는 감정 (예: 중립적, 긍정적, 부정적, 화남, 실망, 격려 등)
2. risk_level: 오해의 소지나 부적절한 표현의 위험 수준 ("low", "medium", "high")
3. issues: 발견된 문제점들 (배열 형태)
   - 감정적 표현
   - 모호한 표현
   - 공격적이거나 비난조의 표현
   - 오해의 소지가 있는 부분
4. improved_message: 개선된 메시지 (전문적이고, 명확하고, 감정이 배제되고, 오해의 소지가 없는 메시지)
5. suggestions: 추가 개선 제안사항 (배열 형태)
6. tone_assessment: 메시지 톤 평가 (전문적, 친근한, 격식있는, 비격식적 등)

${isGroupMessage ? `
특별히 단체 메시지이므로 다음 사항도 고려해주세요:
- 특정 학생을 겨냥한 표현이 있는지
- 그룹 전체에게 적절한 내용인지
- 일부 학생이 소외감을 느낄 수 있는 표현이 있는지
` : ''}

응답은 반드시 유효한 JSON 형식이어야 합니다.`;

    try {
      const response = await anthropic.messages.create({
        model: 'claude-3-5-sonnet-20241022',
        max_tokens: 2000,
        messages: [{
          role: 'user',
          content: prompt
        }]
      });

      const analysisText = response.content[0].text;

      // JSON 추출 (코드 블록으로 감싸진 경우 처리)
      let jsonText = analysisText;
      const jsonMatch = analysisText.match(/```json\n([\s\S]*?)\n```/) ||
                       analysisText.match(/```\n([\s\S]*?)\n```/) ||
                       analysisText.match(/\{[\s\S]*\}/);

      if (jsonMatch) {
        jsonText = jsonMatch[1] || jsonMatch[0];
      }

      const analysis = JSON.parse(jsonText);

      return {
        success: true,
        analysis: {
          emotionAnalysis: analysis.emotion_analysis,
          riskLevel: analysis.risk_level,
          issues: analysis.issues || [],
          improvedMessage: analysis.improved_message,
          suggestions: analysis.suggestions || [],
          toneAssessment: analysis.tone_assessment
        }
      };
    } catch (error) {
      console.error('AI analysis error:', error);
      return {
        success: false,
        error: 'AI 분석 중 오류가 발생했습니다.',
        details: error.message
      };
    }
  }

  /**
   * 간단한 감정 필터링
   * @param {string} message - 원본 메시지
   * @returns {Promise<Object>} 필터링 결과
   */
  static async quickEmotionFilter(message) {
    const prompt = `다음 메시지에서 감정적이거나 공격적인 표현을 찾아 중립적으로 바꿔주세요:

"${message}"

JSON 형식으로 답변:
{
  "has_emotional_content": true/false,
  "filtered_message": "필터링된 메시지"
}`;

    try {
      const response = await anthropic.messages.create({
        model: 'claude-3-5-sonnet-20241022',
        max_tokens: 1000,
        messages: [{
          role: 'user',
          content: prompt
        }]
      });

      const resultText = response.content[0].text;
      const jsonMatch = resultText.match(/\{[\s\S]*\}/);
      const result = JSON.parse(jsonMatch[0]);

      return {
        success: true,
        hasEmotionalContent: result.has_emotional_content,
        filteredMessage: result.filtered_message
      };
    } catch (error) {
      console.error('Quick filter error:', error);
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * 메시지 명확성 검증
   * @param {string} message - 검증할 메시지
   * @returns {Promise<Object>} 검증 결과
   */
  static async validateClarity(message) {
    const prompt = `교수가 학생에게 보낼 다음 메시지가 명확하고 오해의 소지가 없는지 검증해주세요:

"${message}"

JSON 형식으로 답변:
{
  "is_clear": true/false,
  "clarity_score": 0-100,
  "ambiguous_parts": ["모호한 부분들"],
  "recommendations": ["개선 권장사항들"]
}`;

    try {
      const response = await anthropic.messages.create({
        model: 'claude-3-5-sonnet-20241022',
        max_tokens: 1000,
        messages: [{
          role: 'user',
          content: prompt
        }]
      });

      const resultText = response.content[0].text;
      const jsonMatch = resultText.match(/\{[\s\S]*\}/);
      const result = JSON.parse(jsonMatch[0]);

      return {
        success: true,
        ...result
      };
    } catch (error) {
      console.error('Clarity validation error:', error);
      return {
        success: false,
        error: error.message
      };
    }
  }
}

export default AIMessageService;

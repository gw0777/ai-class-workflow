from typing import Dict, List, Any
import os


class AIGenerator:
    """Generate presentation support content using AI or rule-based approaches"""

    def __init__(self, api_key: str = None):
        """
        Initialize AI Generator

        Args:
            api_key: Anthropic API key (optional)
        """
        self.api_key = api_key
        self.has_api = bool(api_key and api_key.strip())

        if self.has_api:
            try:
                import anthropic
                self.client = anthropic.Anthropic(api_key=api_key)
            except ImportError:
                self.has_api = False
                self.client = None
        else:
            self.client = None

    def generate_script(self, parsed_data: Dict[str, Any],
                       total_time: int = 10,
                       style: str = "professional") -> Dict[str, Any]:
        """
        Generate presentation script

        Args:
            parsed_data: Parsed presentation data
            total_time: Total presentation time in minutes
            style: Presentation style (professional, casual, academic)

        Returns:
            Generated script
        """
        slides = parsed_data.get('slides', [])

        if self.has_api:
            return self._generate_script_with_ai(slides, total_time, style)
        else:
            return self._generate_script_rule_based(slides, total_time, style)

    def _generate_script_with_ai(self, slides: List[Dict],
                                 total_time: int,
                                 style: str) -> Dict[str, Any]:
        """Generate script using Claude API"""
        try:
            # Prepare slide content
            slides_text = "\n\n".join([
                f"슬라이드 {s['slide_number']}:\n{s['content']}"
                for s in slides if s.get('content')
            ])

            prompt = f"""다음 발표 슬라이드 내용을 바탕으로 {total_time}분 분량의 발표 스크립트를 작성해주세요.

발표 스타일: {style}
총 슬라이드 수: {len(slides)}
총 발표 시간: {total_time}분

슬라이드 내용:
{slides_text}

다음 형식으로 작성해주세요:
1. 각 슬라이드별로 발표 스크립트 작성
2. 각 슬라이드의 예상 발표 시간 명시
3. 청중의 관심을 끌 수 있는 표현 사용
4. 자연스러운 전환 문구 포함

JSON 형식으로 응답해주세요:
{{
    "total_time": {total_time},
    "scripts": [
        {{
            "slide_number": 1,
            "time_allocation": 1.5,
            "script": "발표 스크립트...",
            "key_points": ["핵심 포인트 1", "핵심 포인트 2"]
        }}
    ]
}}"""

            message = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = message.content[0].text

            # Parse JSON response
            import json
            # Extract JSON from response (handle markdown code blocks)
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()

            result = json.loads(response_text)
            result['generated_by'] = 'ai'
            return result

        except Exception as e:
            print(f"AI generation failed: {e}")
            return self._generate_script_rule_based(slides, total_time, style)

    def _generate_script_rule_based(self, slides: List[Dict],
                                    total_time: int,
                                    style: str) -> Dict[str, Any]:
        """Generate script using rule-based approach"""
        scripts = []

        # Calculate time per slide
        total_slides = len(slides)
        avg_time_per_slide = total_time / max(total_slides, 1)

        for slide in slides:
            slide_num = slide['slide_number']
            content = slide.get('content', '')
            word_count = slide.get('word_count', 0)

            # Adjust time based on content length
            if word_count > 100:
                time_allocation = avg_time_per_slide * 1.5
            elif word_count < 30:
                time_allocation = avg_time_per_slide * 0.5
            else:
                time_allocation = avg_time_per_slide

            # Generate basic script
            if slide_num == 1:
                script = f"안녕하십니까. 오늘 발표를 시작하겠습니다.\n\n{content}\n\n이번 발표의 주요 내용을 소개하겠습니다."
            elif slide_num == total_slides:
                script = f"{content}\n\n이상으로 발표를 마치겠습니다. 감사합니다."
            else:
                script = f"다음으로, {content}"

            # Extract key points (simple split by newlines or periods)
            key_points = [p.strip() for p in content.split('\n') if p.strip()][:3]

            scripts.append({
                'slide_number': slide_num,
                'time_allocation': round(time_allocation, 1),
                'script': script,
                'key_points': key_points
            })

        return {
            'total_time': total_time,
            'scripts': scripts,
            'generated_by': 'rule-based'
        }

    def generate_qa(self, parsed_data: Dict[str, Any], count: int = 5) -> Dict[str, Any]:
        """
        Generate expected Q&A

        Args:
            parsed_data: Parsed presentation data
            count: Number of questions to generate

        Returns:
            Generated Q&A
        """
        slides = parsed_data.get('slides', [])

        if self.has_api:
            return self._generate_qa_with_ai(slides, count)
        else:
            return self._generate_qa_rule_based(slides, count)

    def _generate_qa_with_ai(self, slides: List[Dict], count: int) -> Dict[str, Any]:
        """Generate Q&A using Claude API"""
        try:
            slides_text = "\n\n".join([
                f"슬라이드 {s['slide_number']}:\n{s['content']}"
                for s in slides if s.get('content')
            ])

            prompt = f"""다음 발표 내용을 바탕으로 청중이 할 만한 질문 {count}개와 그에 대한 답변을 작성해주세요.

슬라이드 내용:
{slides_text}

다양한 유형의 질문을 포함해주세요:
1. 세부 사항에 대한 질문
2. 실용적 적용에 대한 질문
3. 도전적이거나 비판적 질문
4. 확장 가능성에 대한 질문

JSON 형식으로 응답해주세요:
{{
    "questions": [
        {{
            "question": "질문 내용",
            "type": "detail|application|critical|expansion",
            "answer": "답변 내용",
            "related_slide": 1
        }}
    ]
}}"""

            message = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=3000,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = message.content[0].text

            # Parse JSON response
            import json
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()

            result = json.loads(response_text)
            result['generated_by'] = 'ai'
            return result

        except Exception as e:
            print(f"AI Q&A generation failed: {e}")
            return self._generate_qa_rule_based(slides, count)

    def _generate_qa_rule_based(self, slides: List[Dict], count: int) -> Dict[str, Any]:
        """Generate Q&A using rule-based approach"""
        questions = []

        question_templates = [
            {
                "template": "슬라이드 {num}의 내용에 대해 좀 더 자세히 설명해주시겠습니까?",
                "type": "detail",
                "answer_template": "네, 슬라이드 {num}의 주요 내용은 다음과 같습니다: {content}"
            },
            {
                "template": "이 내용을 실제로 어떻게 적용할 수 있나요?",
                "type": "application",
                "answer_template": "실제 적용 방법은 다양합니다. 예를 들어, {content}를 활용하여..."
            },
            {
                "template": "예산이나 리소스 제약이 있다면 어떻게 하시겠습니까?",
                "type": "critical",
                "answer_template": "리소스 제약 상황에서는 우선순위를 조정하여..."
            }
        ]

        for i in range(min(count, len(slides))):
            slide = slides[i]
            template = question_templates[i % len(question_templates)]

            questions.append({
                "question": template["template"].format(num=slide['slide_number']),
                "type": template["type"],
                "answer": template["answer_template"].format(
                    num=slide['slide_number'],
                    content=slide.get('content', '')[:100]
                ),
                "related_slide": slide['slide_number']
            })

        return {
            'questions': questions,
            'generated_by': 'rule-based'
        }

    def generate_tips(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate presentation tips and checklist

        Args:
            parsed_data: Parsed presentation data

        Returns:
            Tips and checklist
        """
        total_slides = parsed_data.get('total_slides', 0)
        total_words = parsed_data.get('total_words', 0)

        tips = {
            'preparation': [
                '발표 자료를 최소 3회 이상 리허설하세요',
                '예상 질문에 대한 답변을 미리 준비하세요',
                '발표 시간을 측정하고 조절하세요',
                '핵심 수치와 메시지를 암기하세요',
                '백업 자료를 준비하세요'
            ],
            'delivery': [
                '청중과 아이 컨택을 유지하세요',
                '핵심 포인트에서 제스처를 활용하세요',
                '목소리 톤과 속도를 조절하세요',
                '간결하고 명확하게 표현하세요',
                '열정과 확신을 전달하세요'
            ],
            'time_management': [
                f'총 {total_slides}개 슬라이드를 적절히 배분하세요',
                '중요한 슬라이드에 더 많은 시간을 할애하세요',
                '질의응답 시간을 고려하세요',
                '여유 시간을 2-3분 남겨두세요'
            ],
            'common_mistakes': [
                '슬라이드를 그대로 읽지 마세요',
                '너무 빠르게 진행하지 마세요',
                '청중을 무시하지 마세요',
                '시간 관리를 소홀히 하지 마세요',
                '준비 없이 즉흥적으로 답변하지 마세요'
            ],
            'checklist': [
                {'item': '발표 자료 최종 확인', 'checked': False},
                {'item': '리허설 3회 이상 완료', 'checked': False},
                {'item': '시간 측정 및 조절', 'checked': False},
                {'item': '예상 질문 답변 준비', 'checked': False},
                {'item': '발표 환경 사전 점검', 'checked': False},
                {'item': '백업 자료 준비', 'checked': False},
                {'item': '핵심 메시지 암기', 'checked': False},
                {'item': '복장 및 외모 확인', 'checked': False}
            ]
        }

        return tips
